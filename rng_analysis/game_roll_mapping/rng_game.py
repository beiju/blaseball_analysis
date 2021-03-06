import math
from abc import ABC
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import List, Optional, Generator, Tuple

import pandas as pd
import requests_cache
from blaseball_mike import chronicler
from blaseball_mike.session import _SESSIONS_BY_EXPIRY
from parsy import string, Parser, alt, eof, fail, regex, seq

from nd.rng import Rng


@dataclass
class GameDay:
    rng_state: Tuple[Tuple[int, int], int]
    game_ids: List[str]
    skip: int = field(default=0)
    start_time: Optional[str] = field(default=None)
    pull_data_at: Optional[str] = field(default=None)


DAYS = [
    # 103. four games. hubris!
    GameDay(rng_state=((6123107629886474, 17247484357964131183), 15),
            game_ids=[
                '952de7c0-5b17-4e8f-8b56-caf01025a6a7',
                'fabe1105-58b3-47c4-8bce-9d0824404141',
                '1d8bc613-0ad4-4551-9570-27857e5cac42',
                '7e23e6d3-911e-45a6-87d2-3a2efbcbae6f',
            ],
            skip=1,
            # Starts at Langley Wheeler's incineration
            start_time="2020-08-08T16:19:13.000Z"),
    # 108. two games. fear
    GameDay(rng_state=((5533805311492506700, 15692468723559200702), 48),
            game_ids=['5bb9abd8-96a1-4edf-9fce-1c227f79bd1a',
                      '8f6ca425-6bc0-493f-99d8-3fc145e265a9'],
            start_time="2020-08-08T21:14:03Z"),
    GameDay(rng_state=((6293080272763260934, 11654195519702723052), 60),
            game_ids=['aa1b7fde-f077-4e4b-825f-0d1538d02822']),
    # 111
    GameDay(rng_state=((17566190603851880960, 15992894597385991666), 26),
            game_ids=['ea55d541-1abe-4a02-8cd8-f62d1392226b']),
    # 112
    GameDay(rng_state=((16992747869295392778, 489180923418420395), 38),
            game_ids=['731e7e33-4cd3-47de-b9fe-850d7131c4d6']),
    # 113
    GameDay(rng_state=((12352002204426442393, 16214116944942565884), 48),
            game_ids=['b38e0917-43da-470c-a7bb-5712368a2492']),
]

BIRDS_WEATHER = 11

# Persist blaseball-mike's None-timeout cache to disk to speed up requests
session = requests_cache.CachedSession("blaseball-mike-cache",
                                       backend="sqlite", expire_after=None)
_SESSIONS_BY_EXPIRY[None] = session

ATTRIBUTES = [
    "thwackability",
    "moxie",
    "divinity",
    "musclitude",
    "patheticism",
    "buoyancy",
    "baseThirst",
    "laserlikeness",
    "groundFriction",
    "continuation",
    "indulgence",
    "martyrdom",
    "tragicness",
    "shakespearianism",
    "suppression",
    "unthwackability",
    "coldness",
    "overpowerment",
    "ruthlessness",
    "omniscience",
    "tenaciousness",
    "watchfulness",
    "anticapitalism",
    "chasiness",
    "pressurization",
    "cinnamon",
    "vibes"  # fake attribute from calculating vibes per day
]


def chron_get_by_key(type_: str, first_update: dict, timestamp: str, key: str):
    items = {item['entityId']: item['data'] for item in chronicler.v2.get_entities(
        type_=type_,
        id_=[first_update['data']['home' + key],
             first_update['data']['away' + key]],
        at=timestamp,
        cache_time=None,
    )}

    return [items[first_update['data']['home' + key]], items[first_update['data']['away' + key]]]


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

    def batter_by_id(self, batter_id: str):
        for batter in self.lineup:
            if batter["_id"] == batter_id:
                return batter

        raise ValueError("Batter not found")

    def team_id(self):
        if '_id' in self.team:
            return self.team['_id']
        return self.team['id']


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
    FieldersChoice = auto()
    DoublePlay = auto()
    Sacrifice = auto()


@dataclass(init=True)
class EventInfo:
    event_type: EventType
    weather_roll: float
    has_runner: bool = field(default=False)
    mystery_roll: Optional[float] = field(default=None)
    should_try_to_steal_roll: Optional[float] = field(default=None)
    pitch_in_strike_zone_roll: Optional[float] = field(default=None)
    batter_swings_roll: Optional[float] = field(default=None)
    contact_roll: Optional[float] = field(default=None)
    foul_roll: Optional[float] = field(default=None)
    unknown_roll_1: Optional[float] = field(default=None)
    hit_or_out_roll: Optional[float] = field(default=None)
    unknown_roll_2: Optional[float] = field(default=None)
    unknown_roll_3: Optional[float] = field(default=None)
    unknown_roll_4: Optional[float] = field(default=None)
    unknown_roll_5: Optional[float] = field(default=None)
    unknown_roll_6: Optional[float] = field(default=None)
    unknown_roll_7: Optional[float] = field(default=None)
    fielder_selection_roll: Optional[float] = field(default=None)
    unknown_after_fielder_selection_roll: Optional[float] = field(default=None)
    bird_number_roll: Optional[float] = field(default=None)
    bird_message_roll: Optional[float] = field(default=None)

    batter: Optional[dict] = field(default=None)
    pitcher: Optional[dict] = field(default=None)
    thief: Optional[dict] = field(default=None)


class Event(ABC):
    def __init__(self, batter: Optional[dict] = None,
                 pitcher: Optional[dict] = None):
        self.batter = batter
        self.pitcher = pitcher

    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        raise NotImplementedError("Method on ABC called")


class PlayBall(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        return None


class InningStart(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        return None


class BatterUp(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        return None


class GameOver(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        return None


def top_of_inning(update: dict, batting_team: TeamInfo) -> Parser:
    top_or_bottom = "Top" if update['topOfInning'] else "Bottom"
    return string(
        f"{top_or_bottom} of {update['inning'] + 1}, {batting_team.team['fullName']} batting."
    ).map(lambda _: InningStart())


def batter_up(batting_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")

    if batter['bat']:
        item_str = f", wielding {batter['bat']}"
    else:
        item_str = ""

    return string(
        f"{batter['name']} batting for the {batting_team.team['nickname']}{item_str}."
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
    def apply_common(self, rng: Rng, update: dict, prev_update: dict) -> dict:
        weather_roll = weather_check(rng, update['weather'])
        mystery = rng.next()

        if prev_update['baseRunners']:
            should_steal = runner_check(rng)
        else:
            should_steal = None

        return dict(
            weather_roll=weather_roll,
            mystery_roll=mystery,
            has_runner=bool(update['baseRunners']),
            should_try_to_steal_roll=should_steal,
            pitcher={k: self.pitcher.get(k, None) for k in ATTRIBUTES},
            batter={k: self.batter.get(k, None) for k in ATTRIBUTES},
        )


class StrikeLooking(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)
        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "sl")

        return EventInfo(
            event_type=EventType.StrikeLooking,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            **common
        )


class FoulBall(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

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
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            **common
        )


class StrikeSwinging(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)
        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "ss")
        contact = rng.next()

        return EventInfo(
            event_type=EventType.StrikeSwinging,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            **common
        )


class Ball(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "b")

        return EventInfo(
            event_type=EventType.Ball,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            **common
        )


class HomeRun(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "h")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()

        return EventInfo(
            event_type=EventType.HomeRun,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            **common
        )


def advance_bases(occupied, amount):
    occupied = [b + amount for b in occupied]
    return [b for b in occupied if b < 3]


class BaseHit(PitchEvent):
    def __init__(self, batter: dict, pitcher: dict, bases_occupied: List[int], hit_type: str):
        super().__init__(batter, pitcher)
        self.bases_occupied = bases_occupied
        self.hit_type = hit_type
        if hit_type == "Single":
            self.hit_bases = 1
        elif hit_type == "Double":
            self.hit_bases = 2
        elif hit_type == "Triple":
            self.hit_bases = 3
        else:
            raise RuntimeError("Unexpected hit type " + hit_type)

    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "h")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        five = rng.next()
        six = rng.next()

        # copied from astrid but what else is new
        bases = advance_bases(prev_update['basesOccupied'], self.hit_bases)
        # roll for runner advancement
        if len(bases) == 1:
            rng.next()
        elif len(bases) == 2:
            # guaranteed advancement
            rng.next()

            # super special edge case for singles only
            # effectively asking "did anyone score on a single from second"
            if update['basesOccupied'] != [2, 1, 0]:
                # ...because after advancing every baserunner (incl second->third)
                # the runner now on third advanced to home, freeing up third base
                # for the new, super special, bonus advancement roll from second->third
                rng.next()

            # i'm sure there's a fun way to do this for 3+ bases but, lol, lmao

        return EventInfo(
            event_type=EventType.HomeRun,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            unknown_roll_4=five,
            unknown_roll_5=six,
            **common
        )


class FieldingOutEvent(PitchEvent):
    def __init__(self, batter: dict, pitcher: dict, possible_fielders: List[int]):
        super().__init__(batter, pitcher)
        # Should always be a list of one until we get to late expansion
        self.possible_fielders = possible_fielders

    def check_fielder(self, fielder, rng):
        if int(fielder * 9) not in self.possible_fielders:
            print(
                "ERROR @ {}: ground out rolled {}, wrong fielder".format(
                    rng.get_state_str(), fielder
                )
            )


class GroundOut(FieldingOutEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        fielder = rng.next()

        if not prev_update['halfInningOuts'] == 2:
            for base in prev_update['basesOccupied']:
                rng.next()

                if base == 2:
                    rng.next()  # sac fly roll?

        self.check_fielder(fielder, rng)

        return EventInfo(
            event_type=EventType.HomeRun,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            fielder_selection_roll=fielder,
            **common
        )


class Flyout(FieldingOutEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        fielder = rng.next()
        postfielder = rng.next()  # not gonna call this three bc it's after the fielder roll

        if not prev_update['halfInningOuts'] == 2:
            # This is the "runner advance" check
            if prev_update['basesOccupied']:
                rng.next()

        self.check_fielder(fielder, rng)

        return EventInfo(
            event_type=EventType.HomeRun,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            fielder_selection_roll=fielder,
            unknown_after_fielder_selection_roll=postfielder,
            **common
        )


class FieldersChoice(PitchEvent):
    def __init__(self, batter: dict, pitcher: dict, score: bool):
        super().__init__(batter, pitcher)
        self.score = score

    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        five = rng.next()
        six = rng.next()
        zeven = rng.next()

        return EventInfo(
            event_type=EventType.FieldersChoice,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            unknown_roll_4=five,
            unknown_roll_5=six,
            unknown_roll_6=zeven,
            **common
        )


class DoublePlay(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        five = rng.next()
        six = rng.next()
        zeven = rng.next()

        return EventInfo(
            event_type=EventType.DoublePlay,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            unknown_roll_4=five,
            unknown_roll_5=six,
            unknown_roll_6=zeven,
            **common
        )


class Sacrifice(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        five = rng.next()
        six = rng.next()
        zeven = rng.next()

        return EventInfo(
            event_type=EventType.Sacrifice,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            unknown_roll_4=five,
            unknown_roll_5=six,
            unknown_roll_6=zeven,
            **common
        )


class SacScore(PitchEvent):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        # This line must be first
        common = self.apply_common(rng, update, prev_update)

        strike, swing = strike_swing_check(rng, self.pitcher, self.batter, "go")
        contact = rng.next()
        fair = rng.next()
        one = rng.next()
        hit = rng.next()
        three = rng.next()
        four = rng.next()
        five = rng.next()

        return EventInfo(
            event_type=EventType.Sacrifice,
            pitch_in_strike_zone_roll=strike,
            batter_swings_roll=swing,
            contact_roll=contact,
            foul_roll=fair,
            unknown_roll_1=one,
            hit_or_out_roll=hit,
            unknown_roll_2=three,
            unknown_roll_3=four,
            unknown_roll_4=five,
            **common
        )


class Steal(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        weather_roll = weather_check(rng, update['weather'])
        mystery = rng.next()

        steal_roll = rng.next()
        rng.next()  # steal success

        return EventInfo(
            event_type=EventType.Steal,
            weather_roll=weather_roll,
            mystery_roll=mystery,
            has_runner=True,
            should_try_to_steal_roll=steal_roll,
            pitcher={k: self.pitcher.get(k, None) for k in ATTRIBUTES},
            thief={k: self.batter.get(k, None) for k in ATTRIBUTES},
        )


class CaughtStealing(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        weather_roll = weather_check(rng, update['weather'])
        mystery = rng.next()

        steal_roll = rng.next()
        rng.next()  # steal success
        # unsure why this should matter but ???it fits data??
        if len(prev_update['baseRunners']) == 1:
            rng.next()
            rng.next()

        return EventInfo(
            event_type=EventType.CaughtStealing,
            weather_roll=weather_roll,
            mystery_roll=mystery,
            has_runner=True,
            should_try_to_steal_roll=steal_roll,
            pitcher={k: self.pitcher.get(k, None) for k in ATTRIBUTES},
            thief={k: self.batter.get(k, None) for k in ATTRIBUTES},
        )


class Birds(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        weather_roll = weather_check(rng, update['weather'], True)
        # TODO Check bird message index and number
        bird_number_roll = rng.next()
        bird_message_roll = rng.next()
        return EventInfo(
            event_type=EventType.Weather,
            weather_roll=weather_roll,
            bird_number_roll=bird_number_roll,
            bird_message_roll=bird_message_roll
        )


def strike_looking(update: dict, batting_team: TeamInfo,
                   pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")

    return alt(
        string(f"Strike, looking. {update['atBatBalls']}-{update['atBatStrikes']}"),
        string(f"{batter['name']} strikes out looking.")
    ).map(lambda _: StrikeLooking(batter=batter, pitcher=pitching_team.pitcher))


def strike_swinging(update: dict, batting_team: TeamInfo,
                    pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")
    return alt(
        string(f"Strike, swinging. {update['atBatBalls']}-{update['atBatStrikes']}"),
        string(f"{batter['name']} struck out swinging.")
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
    if batter is None:
        return fail("No batter")

    return alt(
        string(f"Ball. {update['atBatBalls']}-{update['atBatStrikes']}"),
        string(f"{batter['name']} draws a walk.")
    ).map(lambda _: Ball(batter=batter, pitcher=pitching_team.pitcher))


def home_run(prev_update: dict, batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if not batter:
        return fail("No batter")

    if len(prev_update['baseRunners']) == 0:
        hr_type = "solo"
    else:
        hr_type = str(len(prev_update['baseRunners']) + 1) + "-run"

    return string(
        f"{batter['name']} hits a {hr_type} home run!"
    ).map(lambda _: HomeRun(batter=batter, pitcher=pitching_team.pitcher))


def birds() -> Parser:
    return alt(
        string("These birds hate Blaseball!"),
        string("I hardly think a few birds are going to bring about the end of the world."),
        string("Don't feed the birds"),
        string("The birds are after the children..."),
        string("Do these birds have souls?"),
        string("They're clearing feathers off the field..."),
        string("Where did these birds come from?"),
        string("Have you ever seen this many birds?"),
        string("BIRD NOISES"),
        string("What are we gonna do with all these birds?"),
        string("The birds are mad at you. You specifically. You know who you are."),
        string("Several birds are pecking..."),
        string("This is too many birds."),
        string("The birds are very loud!"),
        string("The birds are paralyzed! They can't move!"),
        string("The birds continue to stare."),
        string("Oh dear Gods..."),
        string("There's just too many birds!"),
        regex(r"\d{1,4}").map(int) << string(" Birds")
    ).desc("Birds").map(lambda _: Birds())


def ground_out(batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")

    return (
            string(f"{batter['name']} hit a ground out to ") >>
            alt(*[string(fielder['name']) for fielder in pitching_team.lineup])
            << string(".")
    ).map(lambda name: GroundOut(batter=batter, pitcher=pitching_team.pitcher,
                                 possible_fielders=[i for i, f in enumerate(pitching_team.lineup)
                                                    if f['name'] == name]))


def flyout(batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")

    return (
            string(f"{batter['name']} hit a flyout to ") >>
            alt(*[string(fielder['name']) for fielder in pitching_team.lineup])
            << string(".")
    ).map(lambda name: Flyout(batter=batter, pitcher=pitching_team.pitcher,
                              possible_fielders=[i for i, f in enumerate(pitching_team.lineup)
                                                 if f['name'] == name]))


def base_hit(prev_update: dict, batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No batter")

    # man the auto-formatter really just doesnt know what to do with this one
    return (
            string(f"{batter['name']} hits a ") >>
            alt(string("Single"), string("Double"), string("Triple"))
            << string("!")
            << alt(
        eof,
        string(" 1 scores."),
        string(" 2s score."),
        string(" 3s score.")
    )
    ).map(lambda hit_type: BaseHit(batter=batter, pitcher=pitching_team.pitcher,
                                   bases_occupied=prev_update['basesOccupied'], hit_type=hit_type))


def base_name(num: int) -> str:
    if num == 0:
        return "first"
    elif num == 1:
        return "second"
    elif num == 2:
        return "third"
    elif num == 3:
        return "fourth"

    raise ValueError("Not a valid base")


def fielders_choice(prev_update: dict, batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    if prev_update is None or not prev_update['baseRunners']:
        return fail("Nobody on base")
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No active batter")

    # man the auto-formatter really just doesnt know what to do with this one
    return (
            string(f"{batter['name']} reaches on fielder's choice. ") >>
            alt(*[string(
                f"{batting_team.batter_by_id(runner)['name']} out at {base_name(base + 1)} base.")
                for runner, base
                in zip(prev_update['baseRunners'], prev_update['basesOccupied'])]) >>
            # I think only one player can score on an FC
            alt(*[string(f" {batting_team.batter_by_id(runner)['name']} scores")
                  for runner in prev_update['baseRunners']]).optional()
    ).map(lambda score: FieldersChoice(batter=batter, pitcher=pitching_team.pitcher,
                                       score=score is not None))


def double_play(batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    batter = batting_team.active_batter()
    if batter is None:
        return fail("No active batter")

    return string(
        f"{batter['name']} hit into a double play!"
    ).map(lambda _: DoublePlay(batter=batter, pitcher=pitching_team.pitcher))


def sacrifice(prev_update: Optional[dict], batting_team: TeamInfo,
              pitching_team: TeamInfo) -> Parser:
    if prev_update is None:
        return fail("Can't score on a sacrifice before the game starts")
    if not prev_update['baseRunners']:
        return fail("Can't score on a sacrifice if nobody's on base")

    batter = batting_team.active_batter()
    if batter is None:
        return fail("No active batter")

    return string(
        f"{batting_team.batter_by_id(prev_update['baseRunners'][0])['name']}  scores on the sacrifice."
    ).map(lambda _: Sacrifice(batter=batter, pitcher=pitching_team.pitcher))


def sac_score(prev_update: Optional[dict], batting_team: TeamInfo,
              pitching_team: TeamInfo) -> Parser:
    if prev_update is None:
        return fail("Can't score on a sacrifice before the game starts")
    if not prev_update['baseRunners']:
        return fail("Can't score on a sacrifice if nobody's on base")

    batter = batting_team.active_batter()
    if batter is None:
        return fail("No active batter")

    return string(
        f"{batter['name']} hit a sacrifice fly. " +
        f"{batting_team.batter_by_id(prev_update['baseRunners'][0])['name']} tags up and scores!"
    ).map(lambda _: SacScore(batter=batter, pitcher=pitching_team.pitcher))


def steal_helper(batting_team: TeamInfo, runner_id: str, base: int, intertext: str,
                 punct: str) -> Parser:
    runner = batting_team.batter_by_id(runner_id)
    return string(f"{runner['name']}{intertext}{base_name(base + 1)} base{punct}").result(runner)


def steal(prev_update: dict, batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    if prev_update is None:
        return fail("Can't steal before the game starts")

    return alt(*[
        steal_helper(batting_team, runner, base, " steals ", "!")
        for runner, base in zip(prev_update['baseRunners'], prev_update['basesOccupied'])
        # Pretend the thief is the batter
    ]).map(lambda thief: Steal(batter=thief, pitcher=pitching_team.pitcher))


def caught_stealing(prev_update: dict, batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    if prev_update is None:
        return fail("Can't get caught stealing before the game starts")

    return alt(*[
        steal_helper(batting_team, runner, base, " gets caught stealing ", ".")
        for runner, base in zip(prev_update['baseRunners'], prev_update['basesOccupied'])
        # Pretend the thief is the batter
    ]).map(lambda thief: CaughtStealing(batter=thief, pitcher=pitching_team.pitcher))


class Incineration(Event):
    def apply(self, rng: Rng, update: dict, prev_update: dict) -> Optional[EventInfo]:
        incin_roll = rng.next()
        if incin_roll > 0.001:
            print("ERROR: incin roll too high?")
        # name, stats, info, location
        rng.step(2 + 26 + 3 + 2)

        return EventInfo(
            event_type=EventType.Weather,
            weather_roll=incin_roll,
        )


def apply_incineration(victim_team: TeamInfo, timestamp: str, day: int,
                       victim_name: str, replacement_name: str) -> Incineration:
    slot = next(i for i, p in enumerate(victim_team.lineup) if p['name'] == victim_name)
    victim_id = victim_team.lineup[slot]['_id']
    next_versions = chronicler.v2.get_versions(
        type_="team",
        id_=victim_team.team_id(),
        after=timestamp,
        count=10,  # Just in case it doesn't update right away
        cache_time=None,
    )
    new_player_id = next(version['data']['lineup'][slot] for version in next_versions
                         if version['data']['lineup'][slot] != victim_id)
    # Get first version for this player
    new_player = next(chronicler.v2.get_versions(
        type_="player",
        id_=new_player_id,
        count=1,
        order="asc",
        cache_time=None,
    ))["data"]
    assert new_player["name"] == replacement_name
    new_player['vibes'] = vibes(new_player, day)
    victim_team.lineup[slot] = new_player

    return Incineration()


def incineration(update: dict, pitching_team: TeamInfo) -> Parser:
    # At this point in the game only the fielding team can be incinerated
    # Eventually I'll need to add pitcher incins
    return seq(
        string(f"Rogue Umpire incinerated {pitching_team.team['nickname']} hitter ") >>
        alt(*[string(player['name']) for player in pitching_team.lineup])
        << string("! Replaced by "),
        regex(".*$")
    ).map(lambda res: apply_incineration(pitching_team, update["timestamp"], update['day'],
                                         res[0], res[1]))


def parser(update: dict, prev_update: Optional[dict],
           batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    return alt(
        string("Play ball!").map(lambda _: PlayBall()),
        top_of_inning(update, batting_team),
        batter_up(batting_team),
        strike_looking(update, batting_team, pitching_team),
        foul_ball(update, batting_team, pitching_team),
        birds(),
        ball(update, batting_team, pitching_team),
        home_run(prev_update, batting_team, pitching_team),
        strike_swinging(update, batting_team, pitching_team),
        ground_out(batting_team, pitching_team),
        base_hit(prev_update, batting_team, pitching_team),
        fielders_choice(prev_update, batting_team, pitching_team),
        flyout(batting_team, pitching_team),
        steal(prev_update, batting_team, pitching_team),
        caught_stealing(prev_update, batting_team, pitching_team),
        double_play(batting_team, pitching_team),
        sacrifice(prev_update, batting_team, pitching_team),
        sac_score(prev_update, batting_team, pitching_team),
        string("Game over.").map(lambda _: GameOver()),
        incineration(update, pitching_team),
    )


def apply_game_update(update: dict, prev_update: dict, rng: Rng, home: TeamInfo,
                      away: TeamInfo) -> Optional[EventInfo]:
    update_data = update['data']
    update_data["timestamp"] = update["timestamp"]
    prev_update_data = None if prev_update is None else prev_update['data']
    print(update_data['lastUpdate'])

    # Top of inning resets 1 event too quickly
    if update_data['topOfInning'] if prev_update_data is None else prev_update_data['topOfInning']:
        p = parser(update_data, prev_update_data, away, home)
    else:
        p = parser(update_data, prev_update_data, home, away)

    return p.parse(update_data['lastUpdate']).apply(rng, update_data, prev_update_data)


GameGenerator = Generator[None, Rng, None]


def vibes(player, day):
    frequency = 6 + round(10 * player['buoyancy'])
    phase = math.pi * ((2 / frequency) * day + 0.5)

    range = 0.5 * (player['pressurization'] + player['cinnamon'])
    return (range * math.sin(phase)) - (0.5 * player['pressurization']) + (0.5 * player['cinnamon'])


def init_vibes(team: TeamInfo, day: int):
    team.pitcher['vibes'] = vibes(team.pitcher, day)
    for batter in team.lineup:
        batter['vibes'] = vibes(batter, day)


def game_generator(game_id, start_time: Optional[str],
                   pull_data_at: Optional[str], skip_first: bool) -> GameGenerator:
    game_updates = chronicler.get_game_updates(
        game_ids=game_id,
        after=start_time,
        cache_time=None
    )
    if pull_data_at is None:
        pull_data_at = game_updates[0]['timestamp']

    home_team, away_team = chron_get_by_key("team", game_updates[0], pull_data_at, "Team")
    home_pitcher, away_pitcher = chron_get_by_key("player", game_updates[0], pull_data_at,
                                                  "Pitcher")
    home_lineup = chron_get_lineup(pull_data_at, home_team)
    away_lineup = chron_get_lineup(pull_data_at, away_team)

    home = TeamInfo(team=home_team, pitcher=home_pitcher,
                    lineup=home_lineup)
    away = TeamInfo(team=away_team, pitcher=away_pitcher,
                    lineup=away_lineup)

    init_vibes(home, game_updates[0]['data']['day'])
    init_vibes(away, game_updates[0]['data']['day'])

    if start_time is not None and not skip_first:
        prev_update = chronicler.get_game_updates(
            game_ids=game_id,
            before=start_time,
            count=1,
            order="desc"
        )[0]
    else:
        prev_update = None

    if skip_first:
        prev_update = game_updates.pop(0)

    if prev_update is not None and prev_update["data"]["awayBatter"]:
        away.active_batter_id = prev_update["data"]["awayBatter"]
    if prev_update is not None and prev_update["data"]["homeBatter"]:
        home.active_batter_id = prev_update["data"]["homeBatter"]

    data_rows = []
    for i, update in enumerate(game_updates):
        # This is a fun inversion
        game_rng = yield update["timestamp"]

        update_id = update["data"]['_id'] if '_id' in update['data'] else update['data']['id']

        # There's a missing event here and by counting the rolls it seems to be a foul with a
        # basestealing check (7 rolls). TODO Restructure the code so I can insert a deduced event
        if update["hash"] in ["50140ef4-ef62-dbd6-8b52-937fc8d4002e",
                              "e5b743d3-0a26-63c9-7781-fac2e8705c5b"]:
            print("Advancing past deduced foul with baserunner")
            game_rng.step(7)
        elif update["hash"] in ['6c058a18-1f49-7c83-d422-7bb0ba668e94',
                                'ccdc2eae-4e27-c57e-941e-ef51650db48b',
                                '643860d1-bac7-894e-9f04-b1f73c077e00']:
            print("Advancing past deduced foul")
            game_rng.step(6)
        elif update["hash"] == 'c99e8d4f-4306-0174-4027-8547d0594d36':
            print("Advancing past 2 consecutive deduced fouls")
            game_rng.step(12)
        elif update["hash"] == 'ad3f8b4a-7914-b7cb-17cb-e5f52929db8c':
            print("Advancing past 3 consecutive deduced fouls (hi fish)")
            game_rng.step(18)
        elif update["hash"] == '4dcc8d09-6a69-2cc3-8a0e-a6b05c937858':
            print("Advancing past ground out advancement")
            game_rng.step(2)

        # Must persist active batter because sometimes it goes away while we
        # still need it (e.g. home runs)
        if update["data"]["awayBatter"]:
            away.active_batter_id = update["data"]["awayBatter"]
        if update["data"]["homeBatter"]:
            home.active_batter_id = update["data"]["homeBatter"]

        game_rng.step(1)
        print(update["timestamp"][14:19], update_id[:8], f"{i:>3}", game_rng.state[0], end=' - ')
        game_rng.step(-1)
        event_info = apply_game_update(update, prev_update, game_rng, home, away)
        if event_info is not None:
            data_rows.append(event_info)

        prev_update = update

    df = pd.json_normalize([asdict(obj) for obj in data_rows])
    df.to_csv(f"game_{game_id}.csv")


def main():
    for i, day in enumerate(DAYS):
        print(f"Starting {i + 1}th game")
        run_day(day)


def run_day(day: GameDay):
    game_rng = Rng(*day.rng_state)
    game_rng.step(-1)

    games = [game_generator(game_id, day.start_time, day.pull_data_at, i < day.skip)
             for i, game_id in enumerate(day.game_ids)]

    # Start all the generators and get the first event timestamps
    games = [(next(game), game) for game in games]

    while games:
        (i, (prev_timestamp, game)) = min(enumerate(games), key=lambda g: g[1][0])
        try:
            next_timestamp = game.send(game_rng)
        except StopIteration:
            games.pop(i)
        else:
            games[i] = (next_timestamp, game)
            # Temp hack: At this specific time, move the game to the end of the list
            # if next_timestamp == '2020-08-08T16:19:29.172Z':
            #     games.append(games.pop(i))

    game_rng.step(3)
    print("Next day start state should be", game_rng.get_state_str())


def chron_get_lineup(timestamp: str, team: dict):
    players = {item['entityId']: item['data'] for item in chronicler.v2.get_entities(
        type_="player",
        id_=team["lineup"],
        at=timestamp,
        cache_time=None,
    )}

    return [players[player_id] for player_id in team['lineup']]


if __name__ == '__main__':
    main()
