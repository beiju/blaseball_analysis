from abc import ABC
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import List, Optional, Generator

import pandas as pd
import requests_cache
from blaseball_mike import chronicler
from blaseball_mike.session import _SESSIONS_BY_EXPIRY
from parsy import string, Parser, alt, eof, fail, regex

from nd.rng import Rng

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
    "cinnamon"
]


def chron_get_by_key(type_: str, first_update: dict, key: str):
    items = {item['entityId']: item['data'] for item in chronicler.v2.get_entities(
        type_=type_,
        id_=[first_update['data']['home' + key],
             first_update['data']['away' + key]],
        at=first_update['timestamp'],
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
            # This is the "runner advance" check
            if prev_update['basesOccupied']:
                rng.next()

            if 2 in prev_update['basesOccupied']:
                rng.next()  # rgsots check??

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

        # On second thought it is impossible for this to be how it works. Regardless, it makes the
        # rolls line up for now
        if self.score:
            eight = rng.next()
        else:
            eight = None

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
            unknown_roll_7=eight,
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
        rng.next()  # ???
        rng.next()  # ???

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
        regex(r"\d{1,4}").map(int) << string(" Birds")
    ).map(lambda _: Birds())


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


def sacrifice(prev_update: Optional[dict], batting_team: TeamInfo, pitching_team: TeamInfo) -> Parser:
    if prev_update is None:
        return fail("Can't score on a sacrifice before the game starts")
    if not prev_update['baseRunners']:
        return fail("Can't score on a sacrifice if nobody's on base")

    batter = batting_team.active_batter()
    if batter is None:
        return fail("No active batter")

    return string(
        f"{batting_team.batter_by_id(prev_update['baseRunners'][-1])['name']}  scores on the sacrifice."
    ).map(lambda _: Sacrifice(batter=batter, pitcher=pitching_team.pitcher))


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


def parser(update: dict, prev_update: dict,
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
        string("Game over.").map(lambda _: GameOver()),
    )


def apply_game_update(update: dict, prev_update: dict, rng: Rng, home: TeamInfo,
                      away: TeamInfo) -> Optional[EventInfo]:
    update_data = update['data']
    prev_update_data = None if prev_update is None else prev_update['data']
    print(update_data['lastUpdate'])

    # Top of inning resets 1 event too quickly
    if prev_update_data is None or prev_update_data['topOfInning']:
        p = parser(update_data, prev_update_data, away, home)
    else:
        p = parser(update_data, prev_update_data, home, away)

    return p.parse(update_data['lastUpdate']).apply(rng, update_data, prev_update_data)


GameGenerator = Generator[None, Rng, None]


def game_generator(game_id) -> GameGenerator:
    game_updates = chronicler.get_game_updates(
        game_ids=game_id,
        cache_time=None
    )
    home_team, away_team = chron_get_by_key("team", game_updates[0], "Team")
    home_pitcher, away_pitcher = chron_get_by_key("player", game_updates[0], "Pitcher")
    home_lineup = chron_get_lineup(game_updates[0]['timestamp'], home_team)
    away_lineup = chron_get_lineup(game_updates[0]['timestamp'], away_team)

    home = TeamInfo(team=home_team, pitcher=home_pitcher,
                    lineup=home_lineup)
    away = TeamInfo(team=away_team, pitcher=away_pitcher,
                    lineup=away_lineup)

    data_rows = []
    prev_update = None
    for update in game_updates:
        # This is a fun inversion
        game_rng = yield

        # We don't know why these offsets are required
        if update["data"]["_id"] == "ad3f8b4a-7914-b7cb-17cb-e5f52929db8c":
            game_rng.step(1)

        # There's a missing event here and by counting the rolls it seems to be a foul with a
        # basestealing check (7 rolls). TODO Restructure the code so I can insert a deduced event
        if update["hash"] == "50140ef4-ef62-dbd6-8b52-937fc8d4002e":
            print("Advancing past deduced foul", update["data"]["_id"])
            game_rng.step(7)

        # Must persist active batter because sometimes it goes away while we
        # still need it (e.g. home runs)
        if update["data"]["awayBatter"]:
            away.active_batter_id = update["data"]["awayBatter"]
        if update["data"]["homeBatter"]:
            home.active_batter_id = update["data"]["homeBatter"]

        event_info = apply_game_update(update, prev_update, game_rng, home, away)
        if event_info is not None:
            data_rows.append(event_info)

        prev_update = update

    df = pd.json_normalize([asdict(obj) for obj in data_rows])
    df.to_csv(f"game_{game_id}.csv")


def main():
    # game_rng = Rng((2009851709471025379, 7904764474545764681), 8)
    game_rng = Rng((16992747869295392778, 489180923418420395), 38)
    game_rng.step(-1)

    # games = [game_generator('ea55d541-1abe-4a02-8cd8-f62d1392226b')]
    games = [game_generator('731e7e33-4cd3-47de-b9fe-850d7131c4d6')]

    # Start all the generators
    for game in games:
        next(game)

    def advance_game(g: GameGenerator) -> bool:
        try:
            g.send(game_rng)
        except StopIteration:
            return False

        return True

    while games:
        # Advance the game and remove it from the list when it's finished
        games[:] = [game for game in games if advance_game(game)]


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
