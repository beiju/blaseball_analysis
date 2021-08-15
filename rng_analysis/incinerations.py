from collections import defaultdict
from itertools import cycle, islice

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError

pattern_breakers = {
    'Goobie Ballson',
    'Yusef Puddles',
    'Quack Enjoyable',
    'Kiki Familia',
    'Charlatan Seabright',
}


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


def main():
    incin_replacements = pd.read_csv('incinerations_mused.csv')
    players_oldest = load_players_oldest_records(exclude_initial=True)

    normal_rolls_by_season = defaultdict(lambda: [])
    unstable_rolls_by_season = defaultdict(lambda: [])
    total_synced = 0
    max_player_name_len = max(len(p['data']['name']) for p in players_oldest)
    for player in players_oldest:
        name = player['data']['name']

        incin = incin_replacements.loc[incin_replacements['name'] == name]
        if len(incin) == 0:
            continue
        season = incin['season'].iloc[0]

        try:
            walkers = rng_walker_for_birth(player)
        except RngMatcherError as e:
            print(f"{player['data']['name']} could not be derived: {e}")
        else:
            spaces = " " * (max_player_name_len - len(name))
            lowest_lowest_of_knowns = None
            lowest_lowest_of_knowns_i = None
            lowest_lowest_roll = None
            lowest_lowest_roll_i = None

            synced = ""
            for walker in walkers:
                assert player['data']['thwackability'] == walker[0]
                lowest_roll, lowest_roll_i = min(
                    (walker[-i], i) for i in range(200))
                if not walker.synced:
                    synced = " (inferred)"
                else:
                    total_synced += 1
                at_99 = walker[-99]
                at_98 = walker[-98]
                at_5 = walker[-5]
                at_4 = walker[-4]
                at_3 = walker[-3]

                if name == 'Quack Enjoyable':
                    for i in range(100000):
                        val = walker[-i]
                        if val < 0.0005:
                            print(f"Quack -{i}: {val}")

                lowest_of_knowns, lowest_of_knowns_i = min(
                    [(at_3, 3), (at_4, 4), (at_5, 5), (at_98, 98), (at_99, 99)])

                if lowest_lowest_of_knowns is None or \
                        lowest_of_knowns < lowest_lowest_of_knowns:
                    lowest_lowest_of_knowns = lowest_of_knowns
                    lowest_lowest_of_knowns_i = lowest_of_knowns_i
                    lowest_lowest_roll = lowest_roll
                    lowest_lowest_roll_i = lowest_roll_i

            if name not in pattern_breakers:
                if incin['unstable'].iloc[0]:
                    unstable_rolls_by_season[season].append(
                        lowest_lowest_of_knowns)
                else:
                    normal_rolls_by_season[season].append(
                        lowest_lowest_of_knowns)
            print(f"{spaces}{name} s{season + 1:<2} lowest of 3, 4, 5, 98, 99: "
                  f"{lowest_lowest_of_knowns:.5f} at "
                  f"{lowest_lowest_of_knowns_i:>2}, lowest within 200: "
                  f"{lowest_lowest_roll:.5f} at "
                  f"{lowest_lowest_roll_i:>2}{synced}")

    print(total_synced)

    fig, (normal_ax, unstable_ax) = plt.subplots(2, figsize=(12, 8))

    for ax in (normal_ax, unstable_ax):
        ax.set_ylim(24.5, 0.5)  # high before low to invert the axis
        ax.set_ylabel("Season")
        ax.set_yticks(np.arange(24) + 1)

        yticks = ax.get_yticks()
        for y0, y1 in zip(yticks[::2], yticks[1::2]):
            ax.axhspan(y0 - 0.5, y1 - 0.5, color='black', alpha=0.1, zorder=0)

    normal_ax.scatter(*incin_rolls_to_plot_format(normal_rolls_by_season))
    normal_ax.set_title("Natural incineration rolls")
    normal_ax.set_xlim(0, 0.001)

    unstable_ax.scatter(*incin_rolls_to_plot_format(unstable_rolls_by_season))
    unstable_ax.set_title("Unstable incineration rolls")
    unstable_ax.set_xlim(0, 0.01)

    fig.tight_layout()
    plt.show()


def incin_rolls_to_plot_format(olls_by_season):
    xs = []
    ys = []
    for season, rolls in olls_by_season.items():
        for roll in rolls:
            xs.append(roll)
            ys.append(season + 1)
    return xs, ys


def connect_replacements(players_oldest):
    plums = None
    kiki = None
    fraiser = None
    quack = None
    beans = None
    cory = None
    melon = None
    for player in players_oldest:
        if player['data']['name'] == 'Carmelo Plums':
            plums = player
        if player['data']['name'] == 'Kiki Familia':
            kiki = player
        if player['data']['name'] == 'Frasier Shmurmgle':
            fraiser = player
        if player['data']['name'] == 'Quack Enjoyable':
            quack = player
        if player['data']['name'] == 'Beans McBlase':
            beans = player
        if player['data']['name'] == 'Cory Twelve':
            cory = player
        if player['data']['name'] == 'Collins Melon':
            melon = player
        if player['data']['name'] == 'Trinity Smaht':
            trin = player
        if player['data']['name'] == 'Jon Halifax':
            jon = player
        if player['data']['name'] == 'Zeruel Kramer':
            ze = player
        if player['data']['name'] == 'Trinity Roche':
            trint = player
        if player['data']['name'] == 'Morrow Doyle':
            morrow = player
    walkers = list(rng_walker_for_birth(trint))
    for walker in walkers:
        walker[0]
        for i, num in enumerate(walker.cached_generator):
            if num == ze['data']['thwackability']:
                print("Found ze from trin in", i, "rolls")
                return

            if i % 1000 == 0:
                print("Tested", i, "rolls")


if __name__ == '__main__':
    main()
