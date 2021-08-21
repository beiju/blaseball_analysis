import asyncio
from datetime import timedelta

import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pandas as pd
from dateutil.parser import parse as parse_date
from matplotlib.collections import LineCollection
from mpld3 import plugins

from rng_analysis.load_fragments import load_fragments

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


async def time_from_url(session, url, key):
    async with session.get(url) as response:
        return parse_date((await response.json())[0][key])


async def season_times(session, season):
    url = f"{SEASON_TIME_URL}{season}/day/"
    d0_start = time_from_url(session, url + "0", "startTime")
    d98_end = time_from_url(session, url + "98", "endTime")
    return season, await d0_start, await d98_end


async def main():
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

    plugins.connect(fig, plugins.Zoom())

    fig.tight_layout()
    mpld3.show()


if __name__ == '__main__':
    asyncio.run(main())
