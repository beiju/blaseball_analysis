import colorsys
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import Dict, List, Tuple

import matplotlib.colors as mpl_colors
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from blaseball_mike import eventually
from dateutil.parser import isoparse as parse_date
from matplotlib.collections import LineCollection
from matplotlib.patheffects import Stroke
from memorised.decorators import memorise
from mpld3.plugins import PluginBase, PointHTMLTooltip

from rng_analysis.load_fragments import load_fragments, Fragment, RngEntry
# Fix bug in someone else's code
from rng_analysis.thing_happen_data import QUERY_BASE, mc, floor_dt, \
    get_season_times

PointHTMLTooltip.JAVASCRIPT = """
mpld3.register_plugin("htmltooltip", HtmlTooltipPlugin);
HtmlTooltipPlugin.prototype = Object.create(mpld3.Plugin.prototype);
HtmlTooltipPlugin.prototype.constructor = HtmlTooltipPlugin;
HtmlTooltipPlugin.prototype.requiredProps = ["id"];
HtmlTooltipPlugin.prototype.defaultProps = {labels:null,
                                            target:null,
                                            hoffset:0,
                                            voffset:10,
                                            targets:null};
function HtmlTooltipPlugin(fig, props){
    mpld3.Plugin.call(this, fig, props);
};

HtmlTooltipPlugin.prototype.draw = function(){
    var obj = mpld3.get_element(this.props.id);
    var labels = this.props.labels;
    var targets = this.props.targets;
    var tooltip = d3.select("body").append("div")
        .attr("class", "mpld3-tooltip")
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden");

    obj.elements()
        .on("mouseover", function(d, i){
            tooltip.html(labels[i])
                .style("visibility", "visible");
        })
        .on("mousemove", function(d, i){
            tooltip
            .style("top", d3.event.pageY + this.props.voffset + "px")
            .style("left",d3.event.pageX + this.props.hoffset + "px");
        }.bind(this))
        .on("mousedown.callout", function(d, i){
            if (targets[i]) window.open(targets[i],"_blank");
        })
        .on("mouseout", function(d, i){
            tooltip.style("visibility", "hidden");
        });
};
"""

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

FAR_FUTURE = datetime(year=3030, month=1, day=1, tzinfo=timezone.utc)
MAX_TIME = pd.Timestamp.max.tz_localize('UTC')
ONE_HOUR = pd.Timedelta(hours=1)

# Need a custom client to tell memorise that I increased the memcache server's
# max value size

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


@memorise(mc)
def get_events_grouped() -> Tuple[EventGroups, List[Fragment]]:
    fragments: List[Fragment] = load_fragments('data/all_stats8.txt')
    feed_events = all_rng_relevant_events(3)

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
                            event['created']) < timedelta(seconds=30) and
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

    return groups, fragments


def total_hours(dt):
    return dt.total_seconds() / (60 * 60)


def event_typename(e: MergedEvent):
    event = e.feed_event
    if event['type'] == 54:
        return 'thwack'
    elif event['type'] == 24:
        return 'party'
    elif event['type'] == 67:
        return 'consumers'
    elif event['type'] == 84:
        return 'recongealed'
    elif event['type'] == 191:  # Fax
        return 'shadow'
    elif event['type'] == 41:  # Feedback
        return 'lcd'
    elif event['type'] == 228:  # Voicemail
        return 'shadow'
    breakpoint()


def line_color(e: MergedEvent):
    return COLOR_MAP[event_typename(e)]


def face_color(e: MergedEvent):
    if e.rng_entry is None:
        return 0, 0, 0, 0

    return COLOR_MAP[e.rng_entry.type]


def label_html(e):
    localized_str = "Not (yet) localized"
    if e.rng_entry is not None:
        (s0, s1), offset = e.rng_entry.state
        localized_str = f"Localized to ({s0},&#8203;{s1})+{offset}. " \
                        f"Click to explore."

    return f"""
    <div class="tooltip tooltip-{event_typename(e)}">
        <p>{e.feed_event['description']}</p>
        <p>{localized_str}</p>
    </div>
    """


def label_url(e):
    if e.rng_entry is None:
        return None

    (s0, s1), offset = e.rng_entry.state
    return f"https://rng.sibr.dev/?s0={s0}&s1={s1}&offset={offset}"


def adjust_lightness(color, amount=0.5):
    try:
        c = mpl_colors.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mpl_colors.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])


def season_row_i_for_timestamp(interval, value):
    try:
        return interval.get_loc(value)
    except KeyError:
        return np.nan


def map_times(seasons, times):
    all_plot_locs = np.empty(len(times))
    all_plot_locs[:] = np.nan
    all_plot_seasons = np.empty(len(times))
    all_plot_seasons[:] = np.nan

    for season, row in seasons.iterrows():
        in_season = ((row['season_start'] <= times) &
                     (times < row['next_season_start']))

        # Start with the time into this season
        plot_locs = times[in_season] - row['season_start']

        # If after postseason start, reset to start postseason graph at 110 hrs
        in_postseason = times[in_season] >= row['postseason_start']
        plot_locs[in_postseason] = (times[in_season][in_postseason] -
                                    row['postseason_start'] +
                                    timedelta(hours=110))

        # Get what proportion of the postseason gap has passed
        postseason_gap_duration = (row['postseason_gap_end'] -
                                   row['postseason_gap_start'])
        if not pd.isnull(postseason_gap_duration):
            desired_duration = postseason_gap_duration - pd.Timedelta(hours=5)
            gap_portion = np.clip(((times[in_season] -
                                    row['postseason_gap_start'])
                                   / postseason_gap_duration), 0, 1)
            # Scale down postseason gap to the desired duration
            plot_locs -= (postseason_gap_duration -
                          desired_duration) * gap_portion

        # Get what proportion of the season break has passed
        season_break_duration = (row['next_season_start'] - row['election_end'])
        desired_duration = pd.Timedelta(hours=5)
        # Season 24
        if not pd.isnull(season_break_duration):
            gap_portion = np.clip(((times[in_season] - row['election_end'])
                                   / season_break_duration), 0, 1)

        else:
            season_break_duration = (
                    row['next_season_start'] - row['season_end'])
            gap_portion = np.clip(((times[in_season] - row['season_end'])
                                   / season_break_duration), 0, 1)
        # Scale down season break to the desired duration
        plot_locs -= (season_break_duration - desired_duration) * gap_portion

        all_plot_locs[in_season] = plot_locs / ONE_HOUR
        all_plot_seasons[in_season] = season

    return all_plot_locs, all_plot_seasons


def main():
    seasons: pd.DataFrame = get_season_times()
    now_utc = pd.Timestamp.now(tz=seasons.iloc[0]['season_start'].tz)
    seasons['next_season_start'] = seasons['season_start'].shift(
        -1, fill_value=now_utc)
    deploys = pd.read_csv('data/deploys.txt',
                          names=['time'], parse_dates=['time'])

    # data, fragments = get_events_grouped()
    #
    # with open('data/deploys.txt', 'r') as f:
    #     deploys = [parse_date(s.strip()) for s in f.readlines()]
    #
    fig = go.Figure()

    # fig.add_trace(go.Scatter(
    #     x=[e.plot_hours for e in data.regular_season],
    #     y=[e.feed_event['season'] for e in data.regular_season],
    #     mode='markers',
    #     marker={
    #         'color': [line_color(e) for e in data.regular_season],
    #     }
    # ))

    plot_game_lines(fig, seasons, 'season_start', 'season_end')
    plot_game_lines(fig, seasons, 'postseason_start', 'postseason_gap_start')
    plot_game_lines(fig, seasons, 'postseason_gap_end', 'postseason_end')

    plot_deploys(fig, deploys, seasons)

    # Reverse Y axis
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)

    fig.show()


def plot_deploys(fig, deploys, seasons):
    x, y = map_times(seasons, deploys['time'])
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers',
        marker={'color': '#000', 'symbol': 'diamond'},
        text=["Deploy at " + t.isoformat() for t in deploys['time']],
        name="Deploys",
    ))


def plot_game_lines(fig, seasons, from_key, to_key):
    start_x, start_y = map_times(seasons, seasons[from_key])
    end_x, end_y = map_times(seasons, seasons[to_key])
    # Use a scatter plot to fake line endcaps
    fig.add_trace(go.Scatter(
        x=start_x, y=start_y,
        mode='markers',
        marker={'color': '#ccc'},
        hoverinfo='skip',
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=end_x, y=end_y,
        mode='markers',
        marker={'color': '#ccc'},
        hoverinfo='skip',
        showlegend=False,
    ))
    for x0, y0, x1, y1 in zip(start_x, start_y, end_x, end_y):
        if not pd.isnull(x0) and not pd.isnull(x1):
            fig.add_shape(
                type='line',
                xref='x', yref='y',
                x0=x0, y0=y0, x1=x1, y1=y1,
                layer='below',
                line={
                    'color': '#ccc',
                    'width': 6,
                }
            )


def main_mpld3():
    data, fragments = get_events_grouped()

    fig, ax = plt.subplots(1, figsize=[15, 7.75])

    all_points = []
    all_labels = []
    all_urls = []

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
        all_labels.append([label_html(e) for e in to_plot])
        all_urls.append([label_url(e) for e in to_plot])

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

    classes = "\n".join(f""".tooltip-{typename} {{ background: rgb({
    ','.join(str(c * 255) for c in adjust_lightness(color, 1.4 if typename != 'lcd' else 1))
    }); }}"""
                        for typename, color in COLOR_MAP.items())

    # Add mpld3 functionality
    # mpld3.plugins.connect(fig, Zoom())
    # noinspection PyTypeChecker
    for points, labels, urls in zip(all_points, all_labels, all_urls):
        mpld3.plugins.connect(fig, PointHTMLTooltip(points, labels, urls, css="""
        .tooltip {
            background-color: #ddd;
            padding: 10px 12px;
            border-radius: 4px;
            border: 1px solid #444;
            box-shadow: 0px 2px 3px rgb(0 0 0 / 30%);
            font-family: sans-serif;
            max-width: 250px;
        }
        
        .tooltip :first-child { margin-top: 0; }
        .tooltip :last-child { margin-bottom: 0; }
        """ + classes))
    mpld3.plugins.connect(fig, CustomCss(
        ".mpld3-paths { stroke-linecap: round; }"))

    with open('thing_happen_latest.html', 'w') as f:
        f.write(mpld3.fig_to_html(fig))


if __name__ == '__main__':
    main()
