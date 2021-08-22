import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import Dict, List, Tuple, Callable, Any

import matplotlib.pyplot as plt
import memcache
import mpld3
import numpy as np
import pandas as pd
from blaseball_mike import eventually
from dateutil.parser import isoparse as parse_date
from matplotlib.collections import LineCollection
from matplotlib.patheffects import Stroke
from memorised.decorators import memorise
from mpld3.plugins import Zoom, PointLabelTooltip, PluginBase, BoxZoom

from rng_analysis.load_fragments import load_fragments, Fragment, RngEntry

SEASON_TIME_URL = "https://api.sibr.dev/corsmechanics/time/season/"

# Some false positives are included in the output. Exclude known ones.
IGNORE_EVENTS = {
    (2980034044015368671, 15193173511404081830)
}

CATEGORIES = ['thwack', 'party', 'lotp', 'hotelmotel', 'consumers', 'lcd',
              'recongealed', 'shadow', 'nightshift']
CATEGORY_COLORS = ['#e41a1c', '#4daf4a', '#ff7f00', '#ffff33', '#377eb8',
                   '#f781bf', '#a65628', '#999999', '#984ea3']
LABEL_NAMES = ["Deploy", "Player generation", "Party", "Party (LOTP)",
               "Party (Hotel Motel)", "Consumer attack", "LCD Soundsystem",
               "Recongealed differently", "Shadowed", "Night shift"]

COLOR_MAP = {cat: color for cat, color in zip(CATEGORIES, CATEGORY_COLORS)}

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

QUERY_BASE = {
    'sortby': '{id}',  # This needs to be a stable sort or it skips items
    'sortorder': 'asc',
    # Prehistory is back-dated to the 1980s, and Discipline has incomplete
    # backfilled data. This filters out both.
    'after': '2021-01-01T00:00:00+00:00'
}

FAR_FUTURE = datetime(year=3030, month=1, day=1, tzinfo=timezone.utc)
DT_MIN = datetime.min.replace(tzinfo=timezone.utc)
ONE_HOUR = timedelta(hours=1)

# Need a custom client to tell memorise that I increased the memcache server's
# max value size
mc = memcache.Client(['localhost:11211'],
                     server_max_value_length=32 * 1024 * 1024)

FeedEvent = dict


@dataclass
class MergedEvent:
    feed_event: FeedEvent
    rng_entry: RngEntry
    plot_hours: float


@dataclass
class EventGroups:
    regular_season: List[MergedEvent]
    wildcard_selection: List[MergedEvent]
    postseason: List[MergedEvent]
    election: List[MergedEvent]

    regular_season_durations: Dict[int, Tuple[float, float]]
    postseason_durations: Dict[int, Tuple[float, float]]


class CustomCss(PluginBase):
    def __init__(self, css):
        # This name is where mpld3 looks for css
        self.css_ = css
        # This must exist or it errors
        self.dict_ = {}


# https://stackoverflow.com/a/32657466
def ceil_dt(dt, delta):
    return DT_MIN + math.ceil((dt - DT_MIN) / delta) * delta


def floor_dt(dt, delta):
    return DT_MIN + math.floor((dt - DT_MIN) / delta) * delta


async def time_from_url(session, url, key):
    async with session.get(url) as response:
        return parse_date((await response.json())[0][key])


async def season_times(session, season):
    url = f"{SEASON_TIME_URL}{season}/day/"
    d0_start = time_from_url(session, url + "0", "startTime")
    d98_end = time_from_url(session, url + "98", "endTime")
    return season, await d0_start, await d98_end


def all_events_of_interest_gen():
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


@memorise(mc)
def all_events_of_interest():
    return list(all_events_of_interest_gen())


@memorise(mc)
def all_rng_relevant_events(cachebust):
    print(cachebust)
    all_children = {}
    all_parents = []
    for event in all_events_of_interest():
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


def season_endpoint(day: int, event_types: List[int], min_or_max,
                    round_func: Callable[[datetime, timedelta], datetime]) -> \
        Dict[int, datetime]:
    """
    Find beginnings of seasons by querying Eventually for day 1 "Play Ball!"
    events
    :return:
    """
    print("Refreshing season_endpoint day", day)
    q = {
        # Sets sort order and filtering by date
        **QUERY_BASE,
        'type': "_or_".join(str(et) for et in event_types),
        'day': str(day)
    }
    seasons = defaultdict(lambda: [])
    for event in eventually.search(cache_time=None, limit=-1, query=q):
        seasons[event['season']].append(
            round_func(parse_date(event['created']), ONE_HOUR))

    return {season: min_or_max(dates) for season, dates in seasons.items()}


@memorise(mc)
def get_season_starts():
    return season_endpoint(0, [1], min, floor_dt)


@memorise(mc)
def get_season_ends():
    return season_endpoint(98, [11, 250, 246], max, ceil_dt)


@memorise(mc)
def get_postseason_times(cachebust) -> \
        Tuple[Dict[int, Tuple[datetime, datetime]],
              Dict[int, Tuple[datetime, datetime]]]:
    print("get_postseason_gaps cachebusted:", cachebust)
    q = {
        # Sets sort order and filtering by date
        **QUERY_BASE,
        'type': '1_or_11',
        'day_min': '98',  # The server does strictly greater than
    }
    seasons: Any = defaultdict(lambda: defaultdict(lambda: [None, None]))
    for event in eventually.search(cache_time=None, limit=-1, query=q):
        season = event['season']
        day = event['day']
        t = {1: 0, 11: 1}[event['type']]
        seasons[season][day][t] = parse_date(event['created'])

    postseason_times = {}
    postseason_gaps = {}
    for season, days in seasons.items():
        starts, ends = zip(*days.values())
        postseason_times[season] = (
            floor_dt(min(starts), ONE_HOUR),
            ceil_dt(max(ends), ONE_HOUR)
        )

        gap_i = max(range(1, len(starts)),
                    key=lambda i: starts[i] - ends[i - 1])
        gap_len = starts[gap_i] - ends[gap_i - 1]
        print(f"Season {season + 1} postseason gap is "
              f"{gap_len.total_seconds() / (60 * 60):.1f} hours")

        postseason_gaps[season] = (
            ceil_dt(ends[gap_i - 1], ONE_HOUR),
            floor_dt(starts[gap_i], ONE_HOUR)
        )

    return postseason_times, postseason_gaps


def is_postseason_birth(event):
    return "Postseason Birth" in event['description']


def is_election(event):
    desc: str = event['description']
    return (desc.startswith("Decree Passed") or
            desc.startswith("Blessing Won") or
            desc.startswith("Will Received"))


@memorise(mc)
def find_times_by_event(events: List[dict], filter_func: Callable[[dict], bool],
                        what: str) -> Dict[int, Tuple[datetime, datetime]]:
    by_season = defaultdict(lambda: [])
    for event in events:
        if filter_func(event):
            by_season[event['season']].append(event)

    found_times = {}
    for season, events in by_season.items():
        dates = [event['created'] for event in events]
        min_date = min(dates)
        max_date = max(dates)

        time_diff = max_date - min_date
        if not time_diff < timedelta(seconds=60):
            print(f"Warning: season {season + 1} {what} lasted "
                  f"{time_diff.total_seconds() / 60:.2f} minutes. "
                  f"Is this correct?")
        # Falsehood alert. This breaks if a day 99 game ends within 30 seconds
        # of wildcard selection.
        found_times[season] = (min_date - timedelta(seconds=30),
                               max_date + timedelta(seconds=30))

    return found_times


def is_rng_relevant(event):
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

        return True

    return False


def get_events_grouped(fragments: List[Fragment]):
    feed_events = all_rng_relevant_events(3)
    season_starts = get_season_starts()
    season_ends = get_season_ends()
    wildcard_times = find_times_by_event(feed_events, is_postseason_birth,
                                         "wildcard selection")
    election_times = find_times_by_event(feed_events, is_election, "elections")
    postseason_times, postseason_gaps = get_postseason_times(4)

    rng_entries = defaultdict(lambda: [])
    for fragment in fragments:
        for entry in fragment.events:
            if entry.timestamp is not None:
                timestamp = floor_dt(entry.timestamp, timedelta(seconds=1))
                rng_entries[timestamp].append(entry)

    groups = EventGroups([], [], [], [], {}, {})

    assert season_starts.keys() == season_ends.keys()
    for season in season_starts.keys():
        duration = season_ends[season] - season_starts[season]
        groups.regular_season_durations[season] = total_hours(duration)

    assert postseason_times.keys() == postseason_gaps.keys()
    for season in postseason_times.keys():
        start, end = postseason_times[season]
        gap_start, gap_end = postseason_gaps[season]

        duration = (end - start) - (gap_end - gap_start)
        groups.postseason_durations[season] = total_hours(duration)

    for event in feed_events:
        if not is_rng_relevant(event):
            continue

        event_time = event['created']
        season = event['season']

        season_start = season_starts[season]
        season_end = season_ends[season]
        # Has default because some seasons don't have postseasons or elections.
        # Or, for short, season 24 is a problem
        wc_selection_start, wc_selection_end = wildcard_times.get(
            season, (FAR_FUTURE, FAR_FUTURE))
        postseason_start, postseason_end = postseason_times.get(
            season, (FAR_FUTURE, FAR_FUTURE))
        postseason_gap_start, postseason_gap_end = postseason_gaps.get(
            season, (FAR_FUTURE, FAR_FUTURE))
        election_start, election_end = election_times.get(
            season, (FAR_FUTURE, FAR_FUTURE))

        # Test every assumption about ordering
        assert season_start < season_end or season_start == FAR_FUTURE
        assert season_end < wc_selection_start or season_end == FAR_FUTURE
        assert wc_selection_start <= wc_selection_end or wc_selection_start == FAR_FUTURE
        assert wc_selection_end < postseason_start or wc_selection_end == FAR_FUTURE
        assert postseason_start < postseason_gap_start or postseason_start == FAR_FUTURE
        assert postseason_gap_start < postseason_gap_end or postseason_gap_start == FAR_FUTURE
        assert postseason_gap_end < postseason_end or postseason_gap_end == FAR_FUTURE
        assert postseason_end < election_start or postseason_end == FAR_FUTURE
        assert election_start <= election_end or election_start == FAR_FUTURE

        assert not postseason_gap_start < event_time < postseason_gap_end

        if event_time >= postseason_start:
            plot_time = event_time - postseason_start

            if event_time > postseason_gap_start:
                plot_time -= postseason_gap_end - postseason_gap_start
        else:
            plot_time = event_time - season_start

        plotHours = total_hours(plot_time)

        # Let's face it this is not the least efficient thing in this script.
        # It's close though
        rng_entry = None
        for fragment in fragments:
            for possible_rng_entry in fragment.events:
                if (possible_rng_entry.timestamp is not None and
                        abs(possible_rng_entry.timestamp -
                            event['created']) < timedelta(seconds=10) and
                        possible_rng_entry.name in event['description']):
                    rng_entry = possible_rng_entry
                    break

        merged_event = MergedEvent(event, rng_entry, plotHours)
        if season_start <= event_time <= season_end:
            groups.regular_season.append(merged_event)
        elif wc_selection_start <= event_time <= wc_selection_end:
            groups.wildcard_selection.append(merged_event)
        elif postseason_start <= event_time <= postseason_end:
            groups.postseason.append(merged_event)
        elif election_start <= event_time <= election_end:
            groups.election.append(merged_event)
        else:
            print(f"Warning: Couldn't categorize "
                  f"\"{event['description']}\"")

    return groups


def total_hours(dt):
    return dt.total_seconds() / (60 * 60)


def line_color(e: MergedEvent):
    event = e.feed_event
    if event['type'] == 54:
        return COLOR_MAP['thwack']
    elif event['type'] == 24:
        return COLOR_MAP['party']
    elif event['type'] == 67:
        return COLOR_MAP['consumers']
    elif event['type'] == 84:
        return COLOR_MAP['recongealed']
    elif event['type'] == 191:  # Fax
        return COLOR_MAP['shadow']
    elif event['type'] == 41:  # Feedback
        return COLOR_MAP['lcd']
    elif event['type'] == 228:  # Voicemail
        return COLOR_MAP['shadow']
    breakpoint()


def face_color(e: MergedEvent):
    if e.rng_entry is None:
        return 0, 0, 0, 0

    return COLOR_MAP[e.rng_entry.type]


def main():
    fragments: List[Fragment] = load_fragments('data/all_stats8.txt')
    data: EventGroups = get_events_grouped(fragments)

    fig, ax = plt.subplots(1, figsize=[15, 7.75])

    all_points = []
    all_labels = []

    def plot_timeline(durations, to_plot, x_offset=0):
        # Plot season lines
        line_points = [[(x_offset, -season), (duration + x_offset, -season)]
                       for season, duration in durations.items()]
        lines = LineCollection(line_points, zorder=0, linewidths=4,
                               colors='#ccc',
                               path_effects=[Stroke(capstyle="round")])
        ax.add_collection(lines)
        points = ax.scatter([e.plot_hours + x_offset for e in to_plot],
                            [-e.feed_event['season'] for e in to_plot],
                            edgecolors=[line_color(e) for e in to_plot],
                            facecolors=[face_color(e) for e in to_plot])
        all_points.append(points)
        all_labels.append([f"Day {e.feed_event['day'] + 1}: "
                           f"{e.feed_event['description']}"
                           for e in to_plot])

    plot_timeline(data.regular_season_durations, data.regular_season)
    plot_timeline(data.postseason_durations, data.postseason, x_offset=110)

    # Configure presentation
    ax.set_title("Thing Happen")
    ax.set_xlabel("Hour since season start")
    ax.set_ylabel("Season")
    ax.set_yticks([-season for season in data.regular_season_durations.keys()])
    ax.set_yticklabels([str(season)
                        for season in data.regular_season_durations.keys()])
    fig.tight_layout()

    # Add mpld3 functionality
    mpld3.plugins.connect(fig, Zoom())
    # noinspection PyTypeChecker
    for points, labels in zip(all_points, all_labels):
        mpld3.plugins.connect(fig, PointLabelTooltip(points, labels))
    mpld3.plugins.connect(fig, CustomCss(
        ".mpld3-paths { stroke-linecap: round; }"))

    with open('thing_happen_latest.html', 'w') as f:
        f.write(mpld3.fig_to_html(fig))


async def main_old():
    seasons = pd.read_csv('data/season_times.csv')

    with open('data/deploys.txt', 'r') as f:
        deploys = [parse_date(line) for line in f.readlines()]

    fragments = load_fragments('data/all_stats8.txt')

    fig, ax = plt.subplots(1, figsize=[24, 6])
    ax.set_title("Thing Happen")
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    fragment_lines = []
    for season in range(24):
        start = seasons[(seasons['season'] == season) &
                        (seasons['type'] == 'season')]['start'].iloc[0]
        # This is for season 24, which didn't have a postseason
        try:
            end = seasons[(seasons['season'] == season) &
                          (seasons['type'] == 'postseason')]['end'].iloc[0]
        except IndexError:
            end = seasons[(seasons['season'] == season) &
                          (seasons['type'] == 'season')]['end'].iloc[0]

        start, end = parse_date(start + "Z"), parse_date(end + "Z")
        duration = end - start
        type_timestamp = {category: [] for category in CATEGORIES}
        for fragment in fragments:
            events = []
            for event in fragment.events:
                if event.timestamp is None:
                    continue
                if event.state[0] in IGNORE_EVENTS:
                    continue
                event_time_as_delta: timedelta = event.timestamp - start

                if timedelta(0) < event_time_as_delta < duration:
                    hours = event_time_as_delta.total_seconds() / (
                            60 * 60)
                    events.append(hours)
                    type_timestamp[event.type].append(hours)

            if len(events) > 1:
                fragment_lines.append(
                    ((min(events), season + 1), (max(events), season + 1))
                )

        season_deploys = [(d - start).total_seconds() / (60 * 60)
                          for d in deploys
                          if start < d < end]

        ax.scatter(season_deploys, [season + 1] * len(season_deploys),
                   c='black', marker='d', zorder=5)

        ax.eventplot([type_timestamp[c] for c in CATEGORIES], zorder=5,
                     lineoffsets=[season + 1] * len(type_timestamp),
                     colors=CATEGORY_COLORS)

    ax.add_collection(LineCollection(fragment_lines,
                                     linewidths=7,
                                     colors=(0.75, 0.75, 0.75),
                                     linestyle='solid'))

    ax.legend(LABEL_NAMES, bbox_to_anchor=(1.004, 0.5),
              loc="center left", borderaxespad=0)

    # high before low to invert the axis
    ax.set_ylim(24.5, 0.5)
    ax.set_ylabel("Season")
    ax.set_yticks(np.arange(24) + 1)

    ax.set_xlabel("Hour")
    ax.set_xlim(0)
    ax.grid(axis='y')

    mpld3.plugins.connect(fig, BoxZoom())

    fig.tight_layout()
    mpld3.show()


if __name__ == '__main__':
    main()
