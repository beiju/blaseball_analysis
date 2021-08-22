import functools
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Callable, Dict, Optional

import memcache
import pandas as pd
from blaseball_mike import eventually
from dateutil.parser import isoparse as parse_date

QUERY_BASE = {
    # Data needs to be sorted by a unique key or else the paging skips items
    'sortby': '{id}',
    # Prehistory is back-dated to the 1980s, and Discipline has incomplete
    # backfilled data. This filters out both.
    'after': '2021-01-01T00:00:00+00:00'
}
DT_MIN = datetime.min.replace(tzinfo=timezone.utc)
ONE_HOUR = timedelta(hours=1)
mc = memcache.Client(['localhost:11211'],
                     server_max_value_length=32 * 1024 * 1024)


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


def cache_dataframe(path_format: str, save_kwargs, read_kwargs):
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


def ceil_dt(dt, delta):
    return DT_MIN + math.ceil((dt - DT_MIN) / delta) * delta


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
            postseason_gap_start = ceil_dt(starts[gap_i], ONE_HOUR)
            postseason_gap_end = floor_dt(ends[gap_i - 1], ONE_HOUR)

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
