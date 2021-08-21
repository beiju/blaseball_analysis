import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple, Union, Optional

import matplotlib.pyplot as plt, mpld3
import numpy as np
import pandas as pd
from dateutil.parser import parse as parse_date
from lark import Lark, Transformer
from matplotlib.collections import LineCollection
from mpld3 import plugins

SEASON_TIME_URL = "https://api.sibr.dev/corsmechanics/time/season/"

FALSE_POSITIVES = {
    (2980034044015368671, 15193173511404081830)
}

CATEGORIES = ['thwack', 'party', 'lotp', 'hotelmotel', 'consumers', 'lcd',
              'recongealed', 'shadow', 'nightshift']
CATEGORY_COLORS = ['#e41a1c', '#4daf4a', '#ff7f00', '#ffff33', '#377eb8',
                   '#f781bf', '#a65628', '#999999', '#984ea3']
LABEL_NAMES = ["Deploy", "Player generation", "Party", "Party (LOTP)",
               "Party (Hotel Motel)", "Consumer attack", "LCD Soundsystem",
               "Recongealed differently", "Shadowed", "Night shift"]


class SeasonTimes:
    def __init__(self, number, start, end, election):
        self.number = number
        self.start = parse_date(start)
        self.end = parse_date(end)
        self.election = election

    @property
    def duration(self):
        return self.end - self.start

    def contains(self, timestamp):
        if timestamp is None:
            return False
        return self.start < timestamp < self.end


class Entry:
    def __init__(self,
                 pos: int,
                 state: Tuple[Tuple[int, int], int],
                 name: Union[str, Tuple[str, str]],
                 timestamp: Optional[datetime] = None):
        self.pos = pos
        self.state = state
        try:
            (self.name, self.type) = name
        except ValueError:
            self.name = name
            self.type = None
        self.timestamp = timestamp


class Fragment:
    def __init__(self, aligned: bool, anchors: List[Entry],
                 events: List[Entry]):
        self.aligned = aligned
        self.anchors = anchors
        self.events = events


class FragmentsTransformer(Transformer):
    def true(self, _):
        return True

    def false(self, _):
        return False

    def fragments(self, node):
        return node

    def fragment(self, node):
        assert len(node) == 3
        return Fragment(*node)

    def anchors(self, node):
        # This function does do something -- it unwraps from a parser type to a
        # python type
        return node

    def events(self, node):
        return node

    def anchor_entry(self, node):
        return Entry(*node)

    def event_entry(self, node):
        return Entry(*node)

    def pos(self, node):
        assert len(node) == 1
        return int(node[0].value)

    def state(self, node):
        assert len(node) == 3
        return ((int(node[0].value), int(node[1].value)),
                int(node[2].value))

    def name_any(self, node):
        assert len(node) == 1
        return node[0].value

    def name_roll(self, node):
        assert len(node) == 2
        return (node[0].value, node[1].value)

    def timestamp(self, node):
        assert len(node) == 1
        return parse_date(node[0].value)


def fragments_to_plot(season: SeasonTimes, fragments: List[Fragment]):
    for fragment in fragments:
        timestamps = [(e.timestamp, e.type) for e in fragment.events
                      if season.contains(e.timestamp)]

        if timestamps:
            yield season.number, *zip(*timestamps)

        # if timestamps:
        #     min_t = min(timestamps)
        #     max_t = max(timestamps)
        #
        #     duration: timedelta = max_t - min_t
        #     middle: datetime = min_t + duration / 2
        #
        #     yield ([(middle - season.start).total_seconds()],
        #            duration.total_seconds())


async def time_from_url(session, url, key):
    async with session.get(url) as response:
        return parse_date((await response.json())[0][key])


async def season_times(session, season):
    url = f"{SEASON_TIME_URL}{season}/day/"
    d0_start = time_from_url(session, url + "0", "startTime")
    d98_end = time_from_url(session, url + "98", "endTime")
    return season, await d0_start, await d98_end


async def main():
    print("Creating parser...")
    parser = Lark(r"""
fragments: fragment*

fragment: _frag_start anchors events _frag_end

_frag_start: "----- FRAGMENT START (aligned? " bool ")" _NEWLINE
_frag_end: "----- FRAGMENT END" _NEWLINE

anchors: "anchors:" _NEWLINE anchor_entry*
events: "events:" _NEWLINE event_entry*

anchor_entry: "-" pos state name_any _NEWLINE
event_entry: "-" pos state name_roll timestamp _NEWLINE

pos: "pos=" INT
state: "state=(" INT "," INT ")+" INT
name_any: "name=" ANY
name_roll: "name=" NAME "/" ROLL_TYPE
timestamp.2: "timestamp=" DATE
bool: "true" -> true
    | "false" -> false

ANY: /[^\n]+/
NAME: /[^\/\n]+/
ROLL_TYPE: WORD
BOOL: "true" | "false"
DATE: INT "-" INT "-" INT "T" INT ":" INT ":" INT ("." INT)? "Z"
_NEWLINE: NEWLINE

%import common.INT
%import common.WS
%import common.WORD
%import common.NEWLINE
%ignore " "
""", start='fragments', debug=True)
    print("Parsing fragments...")
    with open('all_stats8.txt', 'r') as f:
        fragments_raw = parser.parse(f.read())

    print("Transforming parse tree...")
    fragments = FragmentsTransformer().transform(fragments_raw)

    print("Getting season times...")
    seasons = pd.read_csv('season_times.csv')

    with open('deploys.txt', 'r') as f:
        deploys = [parse_date(line) for line in f.readlines()]

    print("Massaging data...")

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
                if event.state[0] in FALSE_POSITIVES:
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
