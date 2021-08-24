import functools
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from itertools import chain
from typing import List, Callable, Dict, Optional

import numpy as np
import pandas as pd
from blaseball_mike import eventually
from dateutil.parser import isoparse as parse_date
from tqdm import tqdm

from rng_analysis.load_fragments import load_fragments, RngEntry

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
    116,  # Player incineration replacement -- incins
    117,  # Player stat increase
    118,  # Player stat decrease
    119,  # Player stat reroll
    136,  # Player hatched on newly created team (needed for incinerations)
    145,  # Player alternated (how is this different from 119?)
]

SHOE_THIEVES_ID = 'bfd38797-8404-4b38-8b82-341da28b1f83'


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


@dataclass
class RngEntriesDataRow:
    fragment: int
    timestamp: datetime
    player_name: str
    type: str
    s0: int
    s1: int
    offset: int
    is_aligned: bool


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
                # Round-trip through save-read to ensure the value is the same
                # on every call
                result = pd.read_csv(path, **read_kwargs)

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


def query_eventually(query):
    for event in eventually.search(cache_time=None, limit=-1,
                                   query=dict(QUERY_BASE, **query)):
        event['created'] = parse_date(event['created'])
        yield event


def get_postseason_births():
    return list(query_eventually({
        'type': '109',
        'description': 'earned a Postseason Birth',
    }))


def get_roams():
    return list(query_eventually({
        'type': '115_or_109',
        'description': 'roam',
    }))


def get_bottom_dwells():
    return list(query_eventually({
        'type': '117',
        'description': 'Bottom Dwellers',
    }))


def get_team_formations():
    return list(query_eventually({'type': 138}))


def get_tunes_for_psychoacoustics():
    return list(query_eventually({
        'type': 57,
        'description': 'for PsychoAcoustics',
    }))


def get_localizations():
    return list(query_eventually({
        'type': 109,
        'description': 'Localized into the',
    }))


def get_aboardings():
    return list(query_eventually({
        'type': 109,
        'description': 'came aboard the',
        'expand_parent': 'true'
    }))


def get_vault_leavings():
    return list(query_eventually({
        'type': 197
    }))


def get_odysseys():
    players_q = {
        'type': '106_or_107',
        'metadata.mod': 'NEWADVENTURE',
        # Override after so it picks up Parker
        'after': '1700-01-01T01:01:01Z'
    }

    odyssey_players = defaultdict(lambda: Timespan(None, None))
    for event in query_eventually(players_q):
        if event['type'] == 106:  # Gained mod
            odyssey_players[event['playerTags'][0]].start = event['created']
        else:  # Lost mod
            odyssey_players[event['playerTags'][0]].end = event['created']

    odysseys = []
    for player_id, timespan in odyssey_players.items():
        odysseys.extend(query_eventually({
            'type': '115_or_109_or_244',
            'playerTags': player_id
        }))

    return odysseys


def joined_team(event, send_or_receive):
    if event['type'] == 115:
        return event['metadata'][send_or_receive + 'TeamId']
    elif event['type'] == 109 or event['type'] == 244:
        return event['metadata']['teamId']

    raise RuntimeError("Can't get joined team for event of type " +
                       str(event['type']))


def get_feed_event_parent(child, postseason_births, roams, dwells, formations,
                          tunes, localizations, aboardings, vault_leavings,
                          odysseys):
    time_threshold = timedelta(seconds=5)
    try:
        parent = child['metadata']['parent']
    except KeyError:
        # There's a return in the else block so pass just saves indentation
        pass
    else:
        parent['created'] = parse_date(parent['created'])
        return parent

    # Is this a postseason birth?
    if child['type'] == 109 and "a Postseason Birth" in child['description']:
        # These are one of the few events that are complete in their own right.
        # Cheat slightly by returning the event as its own parent
        return child

    # Is this a shadow boost?
    if child['type'] == 117 and "entered the Shadows" in child['description']:
        # Is the boost from a postseason birth?
        qualifying_births = [
            birth for birth in postseason_births if
            birth['playerTags'][0] == child['playerTags'][0] and
            abs(birth['created'] - child['created']) < time_threshold]

        if len(qualifying_births) == 1:
            return qualifying_births[0]

        # Is the boost from roaming directly into the shadows?
        qualifying_roams = [
            roam for roam in roams if
            roam['playerTags'][0] == child['playerTags'][0] and
            joined_team(roam, 'receive') == child['teamTags'][0] and
            abs(roam['created'] - child['created']) < time_threshold]

        if len(qualifying_roams) == 1:
            return qualifying_roams[0]

        # Is the boost from joining a team as it's formed?
        qualifying_vault_leavings = [
            formation for formation in formations if
            formation['teamTags'][0] == child['teamTags'][0] and
            abs(formation['created'] - child['created']) < time_threshold]

        if len(qualifying_vault_leavings) == 1:
            return qualifying_vault_leavings[0]

        # Is the boost from leaving a team as it's disbanded?
        qualifying_vault_leavings = [
            vault_leaving for vault_leaving in vault_leavings if
            vault_leaving['playerTags'][0] == child['playerTags'][0] and
            abs(vault_leaving['created'] - child['created']) < time_threshold]

        if len(qualifying_vault_leavings) == 1:
            return qualifying_vault_leavings[0]

    # Is this a good riddance party?
    if (child['type'] == 117 and "is Partying!" in child['description'] and
            child['teamTags'][0] == SHOE_THIEVES_ID):
        qualifying_roams = [
            roam for roam in roams if
            joined_team(roam, 'send') == SHOE_THIEVES_ID and
            abs(roam['created'] - child['created']) < time_threshold]

        if len(qualifying_roams) == 1:
            return qualifying_roams[0]

    # The parent event for Bottom Dwellers is also returned by the child query,
    # discard it.
    if child['type'] == 117 and "are Bottom Dwellers" in child['description']:
        return None

    # Is this a generic boost?
    if child['type'] == 117 and "was boosted." in child['description']:
        # Was the boost from a Bottom Dwell?
        qualifying_dwells = [
            dwell for dwell in dwells if
            dwell['teamTags'][0] == child['teamTags'][0] and
            abs(dwell['created'] - child['created']) < time_threshold]

        if len(qualifying_dwells) == 1:
            return qualifying_dwells[0]

        # Was the boost from On An Odyssey
        qualifying_odysseys = [
            odyssey for odyssey in odysseys if
            child['playerTags'][0] in odyssey['playerTags'] and
            joined_team(odyssey, 'receive') == child['teamTags'][0] and
            abs(odyssey['created'] - child['created']) < time_threshold]

        if len(qualifying_odysseys) == 1:
            return qualifying_odysseys[0]

    # Is this a Wyatt from building PsychoAcoustics??
    if (child['type'] == 136 and
            "was pulled through the Rift" in child['description']):
        # This is a two-level one. You have to get to a localization by player
        # id and then to a tune by team id
        qualifying_localizations = [
            localization for localization in localizations if
            localization['playerTags'][0] == child['playerTags'][0] and
            abs(localization['created'] - child['created']) < time_threshold]

        if len(qualifying_localizations) == 1:
            localization = qualifying_localizations[0]

            qualifying_tunes = [
                tune for tune in tunes if
                tune['teamTags'][0] == localization['teamTags'][0] and
                abs(tune['created'] - child['created']) < time_threshold]

            if len(qualifying_tunes) == 1:
                # I want all 3 descriptions, but I only support a parent-child
                # hierarchy and not a 3-level one. Cheat by editing the text
                # for the localization onto the tune
                tune = qualifying_tunes[0]
                tune['description'] = (tune['description'] + "\n" +
                                       localization['description'])
                return tune

    if child['type'] == 136 and "joined the ILB" in child['description']:
        # This is a weird one. It's been used for Uncle and Liquid, who were
        # existing players outside the ILB who were added to a team by blessing,
        # and for Magi Ruiz, who was totally new. I'm just going to exclude the
        # detectives manually.
        if child['playerTags'][0] in {'fedbceb8-e2aa-4868-ac35-74cd0445893f',
                                      'd1a198d6-b05a-47cf-ab8e-39a6fa1ed831'}:
            return None

        qualifying_aboardings = [
            aboarding for aboarding in aboardings if
            aboarding['playerTags'][0] == child['playerTags'][0] and
            abs(aboarding['created'] - child['created']) < time_threshold]

        if len(qualifying_aboardings) == 1:
            # It's another 3-level one. Cheat again like with Localization
            aboarding = qualifying_aboardings[0]
            aboarding['description'] = (
                    aboarding['metadata']['parent']['description'] + "\n" +
                    aboarding['description'])
            return aboarding

    raise RuntimeError("Event", child['id'], "had no parent. Type:",
                       child['type'], "Description:", child['description'])


@cache_dataframe("data/feed_events.csv",
                 read_kwargs={
                     'index_col': 0,
                     'parse_dates': ['timestamp']
                 })
def get_feed_events() -> pd.DataFrame:
    postseason_births = get_postseason_births()
    roams = get_roams()
    dwells = get_bottom_dwells()
    formations = get_team_formations()
    tunes = get_tunes_for_psychoacoustics()
    localizations = get_localizations()
    aboardings = get_aboardings()
    vault_leavings = get_vault_leavings()
    odysseys = get_odysseys()
    q = {
        'type': '_or_'.join(str(t) for t in RNG_EVENT_TYPES),
        'expand_parent': 'true',
    }
    rows: List[FeedEventsDataRow] = []

    # Postseason births are both a parent type (for the shadow boost) and an
    # event in their own right
    for child in chain(query_eventually(q), postseason_births):
        parent = get_feed_event_parent(child, postseason_births, roams, dwells,
                                       formations, tunes, localizations,
                                       aboardings, vault_leavings, odysseys)

        if parent is None:
            continue

        assert parent['season'] == child['season']
        assert parent['day'] == child['day']
        assert (parent['created'] - child['created']) < timedelta(seconds=5)

        # The Chorby Soul filter
        # I checked and as of when I checked this literally only finds chorby
        d = child['metadata']
        if child['type'] == 118 and abs(d['before'] - d['after']) < 0.0002:
            continue

        # Filter out events which give flat boosts
        if parent['type'] == 51 or parent['type'] == 52:
            # Blooddrain (51 is normal, 52 is siphon), flat 0.1
            continue
        elif parent['type'] == 47:
            # Peanut, flat 0.2
            continue
        elif (parent['type'] == 59 and
              parent['description'] == "Decree Passed: Based Evolution"):
            # Evolved and was boosted to evolution floor, many flat 0.01s
            continue
        elif (parent['type'] == 60 and parent['description'].startswith(
                "Blessing Won: Targeted Evolution")):
            # Evolved and was boosted to evolution floor, many flat 0.01s
            continue
        elif (parent['type'] == 60 and parent['description'].startswith(
                "Blessing Won: Shadow Evolution")):
            # Evolved and was boosted to evolution floor, many flat 0.01s
            continue
        elif (parent['type'] == 176 and
              parent['description'] == "BASED EVOLUTION"):
            # Evolved and was boosted to evolution floor, many flat 0.01s
            continue
        elif parent['type'] == 30 or parent['type'] == 31:
            # Compressed by gamma (30) or caught some rays (31), flat 0.01
            continue
        elif ("picked up Hitting intuitively" in child['description'] or
              "picked up Pitching intuitively" in child['description']):
            # Intuitive (I guessed at the Pitching message), flat 0.1
            continue

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


@cache_dataframe("data/rng_entries.csv",
                 read_kwargs={
                     'index_col': 0,
                     'parse_dates': ['timestamp']
                 })
def get_rng_entries():
    fragments = load_fragments('data/all_stats8.txt')

    rows: List[RngEntriesDataRow] = []

    for fragment_i, fragment in enumerate(fragments):
        event: RngEntry
        for event in fragment.events:
            (s0, s1), offset = event.state
            rows.append(RngEntriesDataRow(
                fragment=fragment_i,
                timestamp=event.timestamp,
                player_name=event.name,
                type=event.type,
                s0=s0,
                s1=s1,
                offset=offset,
                is_aligned=fragment.aligned
            ))

    rows.sort(key=lambda row: row.timestamp)

    return pd.DataFrame(rows)


def event_typename(row: pd.Series):
    if row['parent_event_type'] == 24:
        return 'party'
    elif row['parent_event_type'] == 40:
        return 'tangled'
    elif row['parent_event_type'] == 41:
        return 'lcd'
    elif row['parent_event_type'] == 54 or row['event_type'] == 136:
        # 54 is incineration, 136 is the Magi Ruiz blessing
        return 'thwack'
    elif row['parent_event_type'] == 67:
        return 'consumers'
    elif row['parent_event_type'] == 84:
        return 'recongealed'
    elif row['event_type'] == 145:
        return 'alternate'
    elif (row['parent_event_type'] == 252 and
          "clocked in" in row['description']):
        # Need to look for "clocked in" otherwise it thinks the shadow boost is
        # also a night shift
        return 'nightshift'
    elif "entered the Shadows" in row['description']:
        return 'shadow'
    elif "a Postseason Birth" in row['description']:
        return 'thwack'
    elif ("is Infused" in row['description'] or
          "is Outfused" in row['description']):
        return 'infuse'
    elif "was re-rolled" in row['description']:
        return 'reroll'
    elif ("was boosted" in row['description'] or
          "were boosted" in row['description'] or
          "was impaired" in row['description'] or
          "Flotation Protocols Activated" in row['description']):
        return 'boost'
    elif "is Partying!" in row['description']:
        # Parties from the shoe thieves' thing are in the Blessing type
        return 'party'

    raise ValueError("Unknown event type")


@cache_dataframe("data/merged_entries.csv",
                 read_kwargs={
                     'index_col': 0,
                     'parse_dates': ['timestamp_feed', 'timestamp_rng']
                 })
def get_merged_events():
    feed_events = get_feed_events()
    feed_events['type'] = feed_events.apply(event_typename, axis=1)
    rng_entries = get_rng_entries()
    time_threshold = pd.Timedelta(seconds=70)

    rng_names_lower = rng_entries['player_name'].str.lower()

    def match_feed_event(feed_event):
        type_matches = rng_entries['type'] == feed_event['type']
        # The space is because of Wyatts Mason nothing through XIII
        name_contained = rng_names_lower.apply(
            lambda s: s in feed_event['description'].lower())
        timestamp_close = rng_entries['timestamp'].apply(
            lambda ts: abs(feed_event['timestamp'] - ts) < time_threshold)
        matches = rng_entries[type_matches & name_contained & timestamp_close]

        if len(matches) == 0:
            return pd.Series([-1, np.nan, "", "", -1, -1, -1, False],
                             index=rng_entries.columns)

        # Temp hack until the rng entries get player ids. If it found multiple
        # entries that match, check if it's because some players' names are
        # substrings of other players' names.
        longest_name_i = matches['player_name'].str.len().argmax()
        longest_name = matches.iloc[longest_name_i]['player_name']
        if all(i == longest_name_i or
               (n in longest_name and n != longest_name)
               for i, n in enumerate(matches['player_name'])):
            # Then all other matches are a strict substring of the longest name,
            # and it's safe to assume the longest name is correct
            return matches.iloc[longest_name_i]

        raise RuntimeError("Multiple matches for feed event")

    tqdm.pandas()
    event_matches = feed_events.progress_apply(match_feed_event, axis=1)
    merged_events = feed_events.join(event_matches,
                                     lsuffix='_feed', rsuffix='_rng')
    return merged_events
