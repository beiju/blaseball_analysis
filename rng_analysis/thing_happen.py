import re
from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot

from rng_analysis.load_fragments import RngEntry
from rng_analysis.thing_happen_data import get_season_times, get_merged_events, \
    get_rng_entries

# Some false positives are included in the output. Exclude known ones.
IGNORE_EVENTS = {
    (2980034044015368671, 15193173511404081830)
}

CATEGORIES = ['thwack', 'party', 'lotp', 'hotelmotel', 'consumers', 'lcd',
              'tangled', 'recongealed', 'shadow', 'nightshift', 'infuse',
              'reroll', 'boost', 'alternate']
CATEGORY_COLORS = ['#e41a1c', '#4daf4a', '#ff7f00', '#ffff33', '#377eb8',
                   '#f781bf', '#deadbe', '#a65628', '#555', '#984ea3',
                   '#deadbe', '#deadbe', '#deadbe', '#deadbe']
LABEL_NAMES = ["Player generation", "Party", "Party (LOTP)",
               "Party (Hotel Motel)", "Consumer attack", "LCD Soundsystem",
               "Tangled", "Recongealed differently", "Shadowed", "Night shift",
               "Infusion", "Re-roll", "Boost", "Alternated"]

COLOR_MAP = {cat: color for cat, color in zip(CATEGORIES, CATEGORY_COLORS)}
LABEL_MAP = {cat: label for cat, label in zip(CATEGORIES, LABEL_NAMES)}

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
        all_plot_seasons[in_season] = season + 1

    return all_plot_locs, all_plot_seasons


def save_figure(fig):
    # Method to add clickable links is taken directly from
    # https://community.plotly.com/t/hyperlink-to-markers-on-map/17858/6

    # Get HTML representation of plotly.js and this figure
    plot_div = plot(fig, output_type='div', include_plotlyjs=True)

    # Get id of html div element that looks like
    # <div id="301d22ab-bfba-4621-8f5d-dc4fd855bb33" ... >
    res = re.search('<div id="([^"]*)"', plot_div)
    div_id = res.groups()[0]

    # Build JavaScript callback for handling clicks
    # and opening the URL in the trace's customdata
    js_callback = f"""
    <script>
    var plot_element = document.getElementById("{div_id}");
    plot_element.on('plotly_click', function(data){{
        var point = data.points[0]
        if (point && point.customdata) {{
            window.open(point.customdata)
        }}
    }})
    </script>
    """

    # Build HTML string
    html_str = f"""
    <html>
    <head>
        <title>Thing Happen</title>
        <style>
            .shapelayer {{
                stroke-linecap: round;
            }}
        </style>
    </head>
    <body>
        {plot_div}
        {js_callback}
    </body>
    </html>
    """

    # Write out HTML file
    with open('thing_happen_latest.html', 'w') as f:
        f.write(html_str)


def main():
    seasons: pd.DataFrame = get_season_times()
    now_utc = pd.Timestamp.now(tz=seasons.iloc[0]['season_start'].tz)
    seasons['next_season_start'] = seasons['season_start'].shift(
        -1, fill_value=now_utc)
    deploys = pd.read_csv('data/deploys.txt',
                          names=['time'], parse_dates=['time'])

    merged_events: pd.DataFrame = get_merged_events()
    # Uhh yeah just load it again
    rng_entries: pd.DataFrame = get_rng_entries()
    # I'll optimize this if I get more than one or two entries in it
    for s0, s1 in IGNORE_EVENTS:
        rng_entries = rng_entries[(rng_entries['s0'] != s0) &
                                  (rng_entries['s1'] != s1)]
    rng_entries.sort_values('timestamp', inplace=True, kind='stable')

    fragment_bounds = rng_entries['timestamp'].groupby(
        rng_entries['fragment'].diff().ne(0).cumsum())

    fig = go.Figure()

    plot_game_lines(fig, seasons, 'season_start', 'season_end')
    plot_game_lines(fig, seasons, 'postseason_start', 'postseason_gap_start')
    plot_game_lines(fig, seasons, 'postseason_gap_end', 'postseason_end')

    plot_fragment_lines(fig, seasons, fragment_bounds)

    plot_deploys(fig, seasons, deploys)
    plot_events(fig, seasons, merged_events)

    fig.update_layout(title="Thing Happen", legend_title="Things",
                      xaxis_showgrid=False, yaxis_showgrid=False,
                      # Requires development version of plotly
                      legend_groupclick='toggleitem')
    fig.update_yaxes(autorange="reversed", title_text="Season",
                     tick0=12, dtick=1)
    fig.update_xaxes(title_text="Game-day-ish")

    save_figure(fig)


def plot_fragment_lines(fig, seasons, fragment_bounds):
    season_line = (seasons['season_start'], seasons['season_end'])
    post1_line = (seasons['postseason_start'], seasons['postseason_gap_start'])
    post2_line = (seasons['postseason_gap_end'], seasons['postseason_end'])
    ind = (fragment_bounds.max() -
           fragment_bounds.min()) > pd.Timedelta(minutes=10)
    for fragment_min, fragment_max in zip(fragment_bounds.min()[ind],
                                          fragment_bounds.max()[ind]):
        # Plot the through line
        (start_x,), (start_y,) = map_times(seasons, pd.Series([fragment_min]))
        (end_x,), (end_y,) = map_times(seasons, pd.Series([fragment_max]))
        if pd.isnull(start_x) or pd.isnull(start_y) or start_x >= end_x:
            continue
        fig.add_shape(
            type='line', xref='x', yref='y',
            x0=start_x, y0=start_y, x1=end_x, y1=end_y,
            layer='below', line={'color': '#999', 'width': 2}
        )

        for line_start, line_end in (season_line, post1_line, post2_line):
            season = int(end_y) - 1  # This is pretty bad programming
            (seg_start_x,), (seg_start_y,) = map_times(
                seasons, pd.Series([max(fragment_min, line_start[season])]))
            (seg_end_x,), (seg_end_y,) = map_times(
                seasons, pd.Series([min(fragment_max, line_end[season])]))

            if (pd.isnull(seg_start_x) or pd.isnull(seg_start_y) or
                    seg_start_x >= seg_end_x):
                continue
            fig.add_shape(
                type='line', xref='x', yref='y',
                x0=seg_start_x, y0=seg_start_y, x1=seg_end_x, y1=seg_end_y,
                layer='below', line={'color': '#999', 'width': 6}
            )


def plot_events(fig, seasons, feed_events):
    # In plotly to get every type to have a separate legend entry I have to
    # plot every type separately
    all_x, all_y = map_times(seasons, feed_events['timestamp_feed'])
    for event_type in CATEGORIES:
        of_type = feed_events['type_feed'] == event_type  # Indexer
        is_localized = ~feed_events[of_type]['timestamp_rng'].isnull()

        plot_some_events(fig, all_x[of_type][is_localized],
                         all_y[of_type][is_localized],
                         feed_events[of_type][is_localized],
                         event_type, True, "Localized")

        plot_some_events(fig, all_x[of_type][~is_localized],
                         all_y[of_type][~is_localized],
                         feed_events[of_type][~is_localized],
                         event_type, False, "Not localized")


def build_description_html(row):
    child_desc = row['description'].replace("\n", "<br />")
    parent_desc = row['parent_description'].replace("\n", "<br />")

    if child_desc in parent_desc:
        event_desc = parent_desc
    else:
        event_desc = parent_desc + "<br />" + child_desc

    if pd.isnull(row['timestamp_rng']):
        rng_desc = "Not (yet) localized"
    else:
        if row['is_aligned']:
            align_desc = f"+{row['offset']}"
        else:
            align_desc = "<br /><i>Offset unknown</i>"
        rng_desc = (f"Localized at ({row['s0']},{row['s1']}){align_desc}"
                    f"<br />Click to explore")

    return (f"<b>Season {row['season'] + 1} Day {row['day'] + 1}</b><br />"
            f"{event_desc}<br /><br />"
            f"{rng_desc}")


def plot_some_events(fig, x, y, e, event_type, fill, legend_group):
    descriptions = e.apply(build_description_html, axis=1)
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers',
        marker={
            'color': COLOR_MAP[event_type] if fill else 'rgba(0,0,0,0)',
            'line': {
                'color': COLOR_MAP[event_type],
                'width': 1
            }
        },
        legendgrouptitle={
            'font': {'size': 13},
            'text': legend_group,
        },
        legendgroup=legend_group,
        # Just one description if they're the same, both otherwise
        text=descriptions,
        name=LABEL_MAP[event_type],
        # This disables all the extra stuff plotly puts in the tooltips
        hovertemplate="%{text}<extra></extra>",
        # Link to Nominative Determinism explorer
        customdata=np.where(pd.isnull(e['timestamp_rng']), "",
                            "https://rng.sibr.dev/?s0=" +
                            e['s0'].astype(str) + "&s1=" +
                            e['s1'].astype(str) + "&offset=" +
                            e['offset'].astype(str)),

    ))


def plot_deploys(fig, seasons, deploys):
    x, y = map_times(seasons, deploys['time'])
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers',
        marker={'color': '#000', 'symbol': 'diamond-tall', 'size': 8},
        text=["Deploy at " + t.isoformat() for t in deploys['time']],
        name="Deploys",
        # This disables all the extra stuff plotly puts in the tooltips
        hovertemplate="%{text}<extra></extra>",
    ))


def plot_game_lines(fig, seasons, from_key, to_key):
    start_x, start_y = map_times(seasons, seasons[from_key])
    end_x, end_y = map_times(seasons, seasons[to_key])
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


if __name__ == '__main__':
    main()
