import functools
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Callable, Dict, Optional

import pandas as pd
from blaseball_mike import eventually
from dateutil.parser import isoparse as parse_date

DT_MIN = datetime.min.replace(tzinfo=timezone.utc)
ONE_HOUR = timedelta(hours=1)

QUERY_BASE = {
    # Data needs to be sorted by a unique key or else the paging skips items
    'sortby': '{id}',
    # Prehistory is back-dated to the 1980s, and Discipline has incomplete
    # backfilled data. This filters out both.
    'after': '2021-01-01T00:00:00+00:00'
}

# https://www.blaseball.wiki/w/SIBR:Feed#Event_types
# TODO Figure out what event the breach teams generation is associated with
RNG_EVENT_TYPES = [
    -1,  # Mysterious and vault-related. Necessary for building the tree
    24,  # Partying
    41,  # Feedback (relevant because of LCD Soundsystem)
    54,  # Incineration (successful only)
    # 57,  # Renovation built (relevant for Wyatts, stadium stats changes)
    59,  # Decree passed (used to detect elections, relevant for, e.g., Bats)
    60,  # Blessing won (used to detect elections, relevant for some)
    61,  # Will received (used to detect elections, relevant for some)
    67,  # Consumer attack (including unsuccessful)
    84,  # Return from Elsewhere (relevant for "recongealed differently")
    106,  # Mod Added
    107,  # Mod removed -- comes along with Elsewhere
    109,  # Player added to team (incl. postseason births)
    110,  # Necromancy (includes shadow boost)
    112,  # Player remove from team -- Ambush from dead team, Dust, etc
    113,  # Player trade -- feedback, Will results
    114,  # Player move within team -- Will results
    115,  # Player add to team -- Roam, probably others
    116,  # Player incineration replacement -- incins
    117,  # Player stat increase
    118,  # Player stat decrease
    119,  # Player stat reroll
    125,  # Player entered hall of flame (comes along with incinerations)
    126,  # Player exited hall of flame
    127,  # Player gained item (can this be used to detect item generation?)
    128,  # Player dropped item, comes along with blessings
    133,  # Team incineration replacement (replace 54?)
    136,  # Player hatched on newly created team (needed for incinerations)
    137,  # Player hatched from Hall (needed for incinerations)
    138,  # Team forms (needed for incinerations)
    139,  # Player evolves (comes along with decrees, blessings)
    144,  # Mod change (as in Reform)
    145,  # Player alternated (how is this different from 119?)
    146,  # Mod added due to other mod. Necessary for building event tree
    147,  # Mod removed due to other mod. Necessary for building event tree
    149,  # Necromancy
    151,  # Decree narration, needed for decrees
    152,  # Will results (e.g. Foreshadow)
    161,  # Gained blood type. Necessary for building event tree
    153,  # Team stat adjustment (todo random?)
    166,  # Lineup sort. Necessary for building event tree
    175,  # Detective activity. Necessary for building event tree
    # 177,  # Glitter crate drop (item generation)
    179,  # Single-attribute increase (may not be detectable)
    180,  # Single-attribute decrease (may not be detectable)
    185,  # Item breaks (connected to consumer attacks)
    186,  # Item damaged (connected to consumer attacks)
    187,  # Broken item repaired. Necessary for building event tree
    188,  # Damaged item repaired. Necessary for building event tree
    # 189,  # Community chest (many item generations)
    190,  # No free item slot. Necessary for building event tree
    191,  # Fax machine, gives shadow boosts
    197,  # Player left the vault. Necessary for building event tree
    199,  # Soul increase. Necessary for building event tree
    203,  # Mod ratified. Necessary for building event tree
    210,  # New league rule. Necessary for building event tree
    217,  # Sun(Sun) pressure. Necessary for building event tree
    223,  # Weather Event, generic I guess
    224,  # Element added to item. Necessary for building event tree
    228,  # Voicemail, gives shadow boosts
    253,  # Tarot card changed. Necessary for building event tree
]


@dataclass
class Timespan:
    start: Optional[datetime]
    end: Optional[datetime]

    @property
    def duration(self):
        if self.start is None or self.end is None:
            return None
        return self.end - self.start


@dataclass
class SeasonTimesDataRow:
    season: int
    # Not using Timespan because the purpose of this class is Pandas
    # serialization, which is flat
    season_start: datetime
    season_end: datetime
    wildcard_selection_start: datetime
    wildcard_selection_end: datetime
    postseason_start: datetime
    postseason_end: datetime
    postseason_gap_start: datetime
    postseason_gap_end: datetime
    election_start: datetime
    election_end: datetime


@dataclass
class FeedEventsDataRow:
    season: int
    day: int
    timestamp: datetime
    description: str
    event_type: int
    parent_description: str
    parent_event_type: int


def cache_dataframe(path_format: str, save_kwargs=None, read_kwargs=None):
    if save_kwargs is None:
        save_kwargs = {}
    if read_kwargs is None:
        read_kwargs = {}

    def decorator_cache_dataframe(func):
        @functools.wraps(func)
        def wrapper_cache_dataframe(*args, **kwargs):
            path = path_format.format(*args, **kwargs)
            try:
                result = pd.read_csv(path, **read_kwargs)
            except FileNotFoundError:
                result: pd.DataFrame = func(*args, **kwargs)
                result.to_csv(path, **save_kwargs)

            return result

        return wrapper_cache_dataframe

    return decorator_cache_dataframe


# Modified from https://stackoverflow.com/a/32657466
def ceil_dt(dt, delta):
    return DT_MIN + math.ceil((dt - DT_MIN) / delta) * delta


# Modified from https://stackoverflow.com/a/32657466
def floor_dt(dt, delta):
    return DT_MIN + math.floor((dt - DT_MIN) / delta) * delta


def is_postseason_birth(event):
    return "Postseason Birth" in event['description']


def is_election(event):
    desc: str = event['description']
    return (desc.startswith("Decree Passed") or
            desc.startswith("Blessing Won") or
            desc.startswith("Will Received"))


def find_times_by_events(event_types: List[int],
                         filter_func: Callable[[dict], bool],
                         what: str) -> Dict[int, Timespan]:
    q = {
        # Sets sort order and filtering by date
        **QUERY_BASE,
        'type': '_or_'.join(str(et) for et in event_types),
    }

    event_dates: Dict[int, List[datetime]] = defaultdict(lambda: [])
    for event in eventually.search(cache_time=None, limit=-1, query=q):
        if filter_func(event):
            event_dates[event['season']].append(parse_date(event['created']))

    timespans: Dict[int, Timespan] = {}
    season: int
    dates: List[datetime]
    for season, dates in event_dates.items():

        span = Timespan(start=min(dates), end=max(dates))

        if not span.duration < timedelta(seconds=60):
            print(f"Warning: season {season + 1} {what} lasted "
                  f"{span.duration.total_seconds() / 60:.2f} minutes. "
                  f"Is this correct?")
        timespans[season] = span

    return timespans


def get_day_map() -> Dict[int, Dict[int, Timespan]]:
    q = {
        # Sets sort order and filtering by date
        **QUERY_BASE,
        'type': '1_or_11',  # Game start or end events
    }
    day_times: Dict[int, Dict[int, List[datetime]]] = \
        defaultdict(lambda: defaultdict(lambda: []))

    for event in eventually.search(cache_time=None, limit=-1, query=q):
        season = int(event['season'])
        day = int(event['day'])
        day_times[season][day].append(parse_date(event['created']))

    print("Queried", sum(len(day)
                         for season in day_times.values()
                         for day in season.values()), "game start/end events")

    day_map: Dict[int, Dict[int, Timespan]] = defaultdict(lambda: {})
    for season, days in day_times.items():
        for day, times in days.items():
            lowest = min(times)
            highest = max(times)

            duration = (highest - lowest).total_seconds() / 60
            if not 10 < duration < 59:
                print(f"s{season}d{day} was {duration:.1f} minutes long")

            day_map[season][day] = Timespan(start=lowest, end=highest)

    return day_map


@cache_dataframe("data/season_times.csv",
                 save_kwargs={'index': False},
                 read_kwargs={
                     'index_col': 'season',
                     'parse_dates': ['season_start', 'season_end',
                                     'wildcard_selection_start',
                                     'wildcard_selection_end',
                                     'postseason_start', 'postseason_end',
                                     'postseason_gap_start',
                                     'postseason_gap_end', 'election_start',
                                     'election_end']
                 })
def get_season_times() -> pd.DataFrame:
    day_map = get_day_map()

    wildcard_times = find_times_by_events([109], is_postseason_birth,
                                          "wildcard selection")
    election_times = find_times_by_events([59, 60, 61], is_election,
                                          "elections")

    rows = []
    for season in day_map.keys():
        last_game_day = max(day_map[season].keys())

        postseason_days = sorted((day, times)
                                 for day, times in day_map[season].items()
                                 if day >= 99)
        if len(postseason_days) == 0:
            # Season 24 :(
            postseason_start = None
            postseason_end = None
            postseason_gap_start = None
            postseason_gap_end = None
        else:
            starts = [times.start for day, times in postseason_days]
            ends = [times.end for day, times in postseason_days]
            gap_i = max(range(1, len(starts)),
                        key=lambda i: starts[i] - ends[i - 1])
            gap_len = starts[gap_i] - ends[gap_i - 1]
            print(f"Season {season + 1} postseason gap is "
                  f"{gap_len.total_seconds() / (60 * 60):.1f} hours")

            postseason_start = day_map[season][99].start
            postseason_end = day_map[season][last_game_day].end
            postseason_gap_start = ceil_dt(ends[gap_i - 1], ONE_HOUR)
            postseason_gap_end = floor_dt(starts[gap_i], ONE_HOUR)

        # Season 24 strikes again
        wildcard_times_season = wildcard_times.get(season, Timespan(None, None))
        election_times_season = election_times.get(season, Timespan(None, None))
        rows.append(SeasonTimesDataRow(
            season=season,
            season_start=day_map[season][0].start,
            season_end=day_map[season][98].end,
            wildcard_selection_start=wildcard_times_season.start,
            wildcard_selection_end=wildcard_times_season.end,
            postseason_start=postseason_start,
            postseason_end=postseason_end,
            postseason_gap_start=postseason_gap_start,
            postseason_gap_end=postseason_gap_end,
            election_start=election_times_season.start,
            election_end=election_times_season.end,
        ))

    # Not strictly necessary, but makes the CSV more intelligible
    rows.sort(key=lambda row: row.season)

    return pd.DataFrame(rows)


def get_relevant_events_raw():
    q = {
        # Sets sort order and filtering by date
        **QUERY_BASE,
        'type': "_or_".join(str(et) for et in RNG_EVENT_TYPES),
    }

    fetched = 0
    for event in eventually.search(cache_time=None, limit=-1, query=q):
        event['created'] = parse_date(event['created'])
        yield event

        fetched += 1
        if fetched % 1000 == 0:
            print("Fetched", fetched // 1000, "thousand events")


def add_children_to(parent, all_children):
    if parent['metadata'] is None or 'children' not in parent['metadata']:
        return

    for i, child_id in enumerate(parent['metadata']['children']):
        try:
            child = all_children.pop(child_id)
        except KeyError:
            # Incineration events have a runs child and I am not about to query
            # all the runs
            if parent['type'] == 54:
                child = {'id': child_id}
            else:
                raise
        else:
            add_children_to(child, all_children)

        parent['metadata']['children'][i] = child


def get_relevant_event_trees():
    all_children = {}
    all_parents = []
    for event in get_relevant_events_raw():
        if (event['metadata'] is not None and 'parent' in event['metadata'] or
                # Redacted events have none (useful) metadata so im just going
                # to declare they're all children
                event['type'] == -1):
            all_children[event['id']] = event
        else:
            all_parents.append(event)

    for parent in all_parents:
        add_children_to(parent, all_children)

    all_parents.sort(key=lambda e: e['created'])

    return all_parents


def get_relevant_children(event):
    if event['metadata'] is None:
        return False

    if 'children' not in event['metadata']:
        return False

    for child in event['metadata']['children']:
        if 'type' not in child:
            continue

        if child['type'] not in {117, 118, 119, 137}:
            continue

        # The Chorby Soul filter
        # I checked and as of when I checked this literally only finds chorby
        d = child['metadata']
        if child['type'] == 118 and abs(d['before'] - d['after']) < 0.0002:
            continue

        if "Evolved to Base" in child['description']:
            continue

        # This is a mod addition, so shouldn't be in the stat increase category,
        # but what are you gonna do
        if "picked up Hitting intuitively" in child['description']:
            continue

        yield child


@cache_dataframe("data/feed_events.csv",
                 read_kwargs={
                     'index_col': 0,
                     'parse_dates': ['timestamp']
                 })
def get_feed_events() -> pd.DataFrame:
    rows: List[FeedEventsDataRow] = []

    for parent in get_relevant_event_trees():
        for child in get_relevant_children(parent):
            assert parent['season'] == child['season']
            assert parent['day'] == child['day']
            assert (parent['created'] - child['created']) < timedelta(seconds=5)

            rows.append(FeedEventsDataRow(
                season=child['season'],
                day=child['day'],
                timestamp=child['created'],
                description=child['description'],
                event_type=child['type'],
                parent_description=parent['description'],
                parent_event_type=parent['type'],
            ))

    # Not strictly necessary, but makes the CSV more intelligible
    rows.sort(key=lambda row: row.timestamp)

    return pd.DataFrame(rows)
