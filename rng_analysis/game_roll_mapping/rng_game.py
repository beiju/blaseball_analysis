from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

import pandas as pd
import requests_cache
from blaseball_mike import chronicler
from blaseball_mike.session import _SESSIONS_BY_EXPIRY
from parsy import string, Parser, seq, regex, alt

from nd.rng import Rng

BIRDS_WEATHER = 11

# Persist blaseball-mike's None-timeout cache to disk to speed up requests
session = requests_cache.CachedSession("blaseball-mike-cache",
                                       backend="sqlite", expire_after=None)
_SESSIONS_BY_EXPIRY[None] = session


def chron_get_by_key(type_: str, first_update: dict, key: str):
    return [item['data'] for item in chronicler.v2.get_entities(
        type_=type_,
        id_=[first_update['data']['home' + key],
             first_update['data']['away' + key]],
        at=first_update['timestamp'],
        cache_time=None,
    )]


@dataclass
class TeamInfo:
    team: dict
    pitcher: dict
    lineup: List[dict]
    active_batter_id: Optional[str] = field(default=None)

    def active_batter(self) -> Optional[dict]:
        if not self.active_batter_id:
            return None

        for batter in self.lineup:
            if batter['_id'] == self.active_batter_id:
                return batter

        raise ValueError("Couldn't find active batter in lineup")


class EventType(Enum):
    Weather = auto()
    StrikeLooking = auto()
    StrikeSwinging = auto()
    Ball = auto()
    Foul = auto()
    GroundOut = auto()
    HomeRun = auto()
    Single = auto()
    Double = auto()
    Triple = auto()
    Steal = auto()
    CaughtStealing = auto()


@dataclass(init=True)
class EventInfo:
    event_type: EventType
    weather_val: float
    has_runner: bool = field(default=False)
    mystery_val: Optional[float] = field(default=None)
    steal_val: Optional[float] = field(default=None)
    strike_zone_val: Optional[float] = field(default=None)
    pitcher_ruth: Optional[float] = field(default=None)
    swing_val: Optional[float] = field(default=None)
    batter_path: Optional[float] = field(default=None)
    batter_moxie: Optional[float] = field(default=None)
    contact_val: Optional[float] = field(default=None)
    foul_val: Optional[float] = field(default=None)
    one_val: Optional[float] = field(default=None)
    hit_val: Optional[float] = field(default=None)
    three_val: Optional[float] = field(default=None)


class Event(ABC):
    def __init__(self, batter: Optional[dict] = None,
                 pitcher: Optional[dict] = None):
        self.batter = batter
        self.pitcher = pitcher

    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        raise NotImplementedError("Method on ABC called")


class PlayBall(Event):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        return None


class InningStart(Event):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        return None


class BatterUp(Event):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        return None


def top_of_inning(top_or_bottom: str, batting_team: TeamInfo) -> Parser:
    return seq(
        string(top_or_bottom),
        string(" of "),
        regex(r"\d+"),
        string(", "),
        string(batting_team.team['fullName']),
        string(" batting.")
    ).map(lambda _: InningStart())


def batter_up(update: dict, batting_team: TeamInfo) -> Parser:
    if update['topOfInning']:
        batter_name = update['awayBatterName']
    else:
        batter_name = update['homeBatterName']
    return seq(
        string(batter_name),
        string(" batting for the "),
        string(batting_team.team['nickname']),
        string(".")
    ).map(lambda _: BatterUp())


def weather_check(rng: Rng, weather: int,
                  weather_happened: bool = False) -> float:
    roll = rng.next()
    if weather == BIRDS_WEATHER and (roll < 0.05) != weather_happened:
        print("ERROR @ {}: WRONG BIRDS".format(rng.get_state_str()))
    return roll


def runner_check(rng: Rng) -> float:
    return rng.next()


def swing_threshold(batter_moxie):
    return 0.5 + batter_moxie * -0.3


def strike_threshold(pitcher_ruth):
    return 0.35 + pitcher_ruth * 0.35


def strike_swing_check(rng: Rng, pitcher: dict, batter: dict, outcome: str):
    strike_roll = rng.next()
    swing_roll = rng.next()

    pitcher_ruth = pitcher["ruthlessness"]
    batter_moxie = batter["moxie"]

    strike_pred = strike_roll < strike_threshold(pitcher_ruth)
    swing_pred = swing_roll < swing_threshold(batter_moxie)

    if outcome in ["b"] and strike_pred:
        print(
            "ERROR @ {}: rolled {}, too low for ball".format(
                rng.get_state_str(), strike_roll
            )
        )

    if outcome in ["sl"] and not strike_pred:
        print(
            "ERROR @ {}: rolled {}, too high for strike looking".format(
                rng.get_state_str(), strike_roll
            )
        )

    return strike_roll, swing_roll


class PitchEvent(Event, ABC):
    def apply_common(self, rng: Rng, update: dict) -> dict:
        weather_roll = weather_check(rng, update['weather'])
        mystery = rng.next()

        if update['baseRunners']:
            steal = runner_check(rng)
        else:
            steal = None

        return dict(
            weather_val=weather_roll,
            mystery_val=mystery,
            has_runner=bool(update['baseRunners']),
            steal_val=steal,
            pitcher_ruth=self.pitcher["ruthlessness"],
            batter_path=self.batter["patheticism"],
            batter_moxie=self.batter["moxie"],
        )


class StrikeLooking(PitchEvent):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update)
        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "sl")

        return EventInfo(
            event_type=EventType.StrikeLooking,
            strike_zone_val=strike,
            swing_val=swing,
            **common
        )


class FoulBall(PitchEvent):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "f")
        contact = rng.next()
        fair = rng.next()

        batter_musc = self.batter["musclitude"]
        if fair > 0.36:
            print(
                "warn @ {}: rolled high fair on foul ({}) with musc {:.03f}".format(
                    rng.get_state_str(), fair, batter_musc
                )
            )

        return EventInfo(
            event_type=EventType.Foul,
            strike_zone_val=strike,
            swing_val=swing,
            contact_val=contact,
            foul_val=fair,
            **common
        )


class StrikeSwinging(PitchEvent):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update)
        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "ss")
        contact = rng.next()

        return EventInfo(
            event_type=EventType.StrikeSwinging,
            strike_zone_val=strike,
            swing_val=swing,
            contact_val=contact,
            **common
        )


class Ball(PitchEvent):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "b")

        return EventInfo(
            event_type=EventType.Ball,
            strike_zone_val=strike,
            swing_val=swing,
            **common
        )


class HomeRun(PitchEvent):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "h")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        rng.next()

        return EventInfo(
            event_type=EventType.HomeRun,
            strike_zone_val=strike,
            swing_val=swing,
            contact_val=contact,
            foul_val=fair,
            one_val=one,
            hit_val=hit,
            **common
        )


class Birds(Event):
    def apply(self, rng: Rng, update: dict) -> Optional[EventInfo]:
        weather_roll = weather_check(rng, update['weather'], True)
        # TODO Check bird message index and number
        rng.next()
        rng.next()
        return EventInfo(
            event_type=EventType.Weather,
            weather_val=weather_roll
        )


def strike_looking(update: dict, batting_team: TeamInfo,
                   pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    return string(
        f"Strike, looking. {update['atBatBalls']}-{update['atBatStrikes']}"
    ).map(lambda _: StrikeLooking(batter=batter, pitcher=pitching_team.pitcher))


def strike_swinging(update: dict, batting_team: TeamInfo,
                    pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    return string(
        f"Strike, swinging. {update['atBatBalls']}-{update['atBatStrikes']}"
    ).map(
        lambda _: StrikeSwinging(batter=batter, pitcher=pitching_team.pitcher))


def foul_ball(update: dict, batting_team: TeamInfo,
              pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    return string(
        f"Foul Ball. {update['atBatBalls']}-{update['atBatStrikes']}"
    ).map(lambda _: FoulBall(batter=batter, pitcher=pitching_team.pitcher))


def ball(update: dict, batting_team: TeamInfo,
         pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    return string(
        f"Ball. {update['atBatBalls']}-{update['atBatStrikes']}"
    ).map(lambda _: Ball(batter=batter, pitcher=pitching_team.pitcher))


def home_run(update: dict, batting_team: TeamInfo,
             pitching_team: TeamInfo) -> Optional[Parser]:
    batter = batting_team.active_batter()
    if not batter:
        # Seems like the library is happy to skip None parsers
        return None

    if len(update['baseRunners']) == 0:
        hr_type = "solo"
    else:
        hr_type = str(len(update['baseRunners']) + 1) + "-run"

    return string(
        f"{batter['name']} hits a {hr_type} home run!"
    ).map(lambda _: HomeRun(batter=batter, pitcher=pitching_team.pitcher))


def birds() -> Parser:
    return alt(
        string("These birds hate Blaseball!")
    ).map(lambda _: Birds())


def parser(update: dict, top_or_bottom: str, batting_team: TeamInfo,
           pitching_team: TeamInfo) -> Parser:
    return alt(
        string("Play ball!").map(lambda _: PlayBall()),
        top_of_inning(top_or_bottom, batting_team),
        batter_up(update, batting_team),
        strike_looking(update, batting_team, pitching_team),
        foul_ball(update, batting_team, pitching_team),
        birds(),
        ball(update, batting_team, pitching_team),
        home_run(update, batting_team, pitching_team),
        strike_swinging(update, batting_team, pitching_team),
    )


def apply_game_update(update: dict, rng: Rng, home: TeamInfo,
                      away: TeamInfo) -> Optional[EventInfo]:
    update_data = update['data']
    print(update_data['lastUpdate'])

    if update_data['topOfInning']:
        p = parser(update_data, "Top", away, home)
    else:
        p = parser(update_data, "Batting", home, away)

    return p.parse(update_data['lastUpdate']).apply(rng, update_data)


def main():
    game_id = 'ea55d541-1abe-4a02-8cd8-f62d1392226b'

    game_rng = Rng((2009851709471025379, 7904764474545764681), 8)
    game_rng.step(-1)
    game_updates = chronicler.get_game_updates(
        game_ids=game_id,
        cache_time=None
    )
    home_team, away_team = chron_get_by_key("team", game_updates[0],
                                            "Team")
    home_pitcher, away_pitcher = chron_get_by_key("player",
                                                  game_updates[0],
                                                  "Pitcher")
    home_lineup = chron_get_lineup(game_updates[0]['timestamp'],
                                   home_team)
    away_lineup = chron_get_lineup(game_updates[0]['timestamp'],
                                   away_team)

    home = TeamInfo(team=home_team, pitcher=home_pitcher,
                    lineup=home_lineup)
    away = TeamInfo(team=away_team, pitcher=away_pitcher,
                    lineup=away_lineup)

    data_rows = []
    for update in game_updates:
        # We don't know why these offsets are required
        if update["data"]["_id"] == "ad3f8b4a-7914-b7cb-17cb-e5f52929db8c":
            game_rng.step(1)

        # Must persist active batter because sometimes it goes away while we
        # still need it (e.g. home runs)
        if update["data"]["awayBatter"]:
            away.active_batter_id = update["data"]["awayBatter"]
        if update["data"]["homeBatter"]:
            home.active_batter_id = update["data"]["homeBatter"]

        event_info = apply_game_update(update, game_rng, home, away)
        if event_info is not None:
            data_rows.append(event_info)

    pd.DataFrame(data_rows).to_csv(f"game_{game_id}.csv")


def chron_get_lineup(timestamp: str, team: dict):
    return [item['data'] for item in chronicler.v2.get_entities(
        type_="player",
        id_=team["lineup"],
        at=timestamp,
        cache_time=None,
    )]


if __name__ == '__main__':
    main()
