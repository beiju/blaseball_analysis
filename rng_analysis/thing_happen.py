import re
from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot

from rng_analysis.load_fragments import RngEntry
from rng_analysis.thing_happen_data import get_season_times, get_merged_events

# Some false positives are included in the output. Exclude known ones.
IGNORE_EVENTS = {
    (2980034044015368671, 15193173511404081830)
}

CATEGORIES = ['thwack', 'party', 'lotp', 'hotelmotel', 'consumers', 'lcd',
              'recongealed', 'shadow', 'nightshift', 'infuse', 'reroll',
              'boost']
CATEGORY_COLORS = ['#e41a1c', '#4daf4a', '#ff7f00', '#ffff33', '#377eb8',
                   '#f781bf', '#a65628', '#999999', '#984ea3', '#deadbe',
                   '#deadbe', '#deadbe']
LABEL_NAMES = ["Player generation", "Party", "Party (LOTP)",
               "Party (Hotel Motel)", "Consumer attack", "LCD Soundsystem",
               "Recongealed differently", "Shadowed", "Night shift",
               "Infusion", "Re-roll", "Boost"]

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

    fig = go.Figure()

    plot_game_lines(fig, seasons, 'season_start', 'season_end')
    plot_game_lines(fig, seasons, 'postseason_start', 'postseason_gap_start')
    plot_game_lines(fig, seasons, 'postseason_gap_end', 'postseason_end')

    plot_deploys(fig, seasons, deploys)

    plot_events(fig, seasons, merged_events)

    # Reverse Y axis
    fig.update_yaxes(autorange="reversed", title_text="Season",
                     tick0=12, dtick=1)
    fig.update_xaxes(title_text="Game-day-ish")
    fig.update_layout(title="Thing Happen", legend_title="Things",
                      xaxis_showgrid=False, yaxis_showgrid=False)

    save_figure(fig)


def plot_events(fig, seasons, feed_events):
    # In plotly to get every type to have a separate legend entry I have to
    # plot every type separately
    x, y = map_times(seasons, feed_events['timestamp_feed'])
    for event_type in set(feed_events['type_feed']):
        ind = feed_events['type_feed'] == event_type  # Indexer

        e = feed_events[ind]
        fill_color = np.where(feed_events[ind]['timestamp_rng'].isnull(),
                              'rgba(0, 0, 0, 0)', COLOR_MAP[event_type])

        child_desc = e['description'].str.replace("\n", "<br />")
        parent_desc = e['parent_description'].str.replace("\n", "<br />")
        fig.add_trace(go.Scatter(
            x=x[ind], y=y[ind],
            mode='markers',
            marker={
                'color': fill_color,
                'line': {
                    'color': COLOR_MAP[event_type],
                    'width': 1
                }
            },
            # Just one description if they're the same, both otherwise
            text="<b>Season " + e['season'].astype(str) +
                 " Day " + e['day'].astype(str) + "</b><br />" +
                 np.where(child_desc == parent_desc, child_desc,
                          parent_desc + "<br />" + child_desc) +
                 "<br /><br />" +
                 np.where(pd.isnull(e['timestamp_rng']), "Not (yet) localized",
                          "Localized at (" + e['s0'].astype(str) + "," +
                          e['s1'].astype(str) + ")" +
                          np.where(e['is_aligned'],
                                   "+" + e['offset'].astype(str),
                                   "<br /><i>Offset unknown</i>") +
                          "<br />Click to explore"),
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
        marker={'color': '#000', 'symbol': 'diamond'},
        text=["Deploy at " + t.isoformat() for t in deploys['time']],
        name="Deploys",
        # This disables all the extra stuff plotly puts in the tooltips
        hovertemplate="%{text}<extra></extra>",
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


if __name__ == '__main__':
    main()
