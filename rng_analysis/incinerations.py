import json
from collections import defaultdict
from datetime import timedelta
from functools import partial
from itertools import cycle, islice

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from blaseball_mike.models import Player, Team
from dateutil.parser import parse

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError, \
    player_size_after_thwack


def natural_rate(r):
    return r['death rate']['stable'][1][0] / 100000


def unstable_rate(r):
    return r['death rate']['unstable'][1][0] / 100000


def locate_incin(players, max_player_name_len, row):
    replacement = players[row['replacement id']]

    # Compute data
    walkers = list(rng_walker_for_birth(replacement))
    gen_size = player_size_after_thwack(replacement)
    expected_locs = [-5, -4, -3, gen_size, gen_size + 1]
    incin_roll, incin_roll_loc = min(
        min((walker[i], i) for i in expected_locs)
        for walker in walkers)
    synced = len(walkers) == 1

    # Format and print data
    name = replacement['data']['name']
    unstable = "(u)" if row['unstable'] else "   "
    spaces = " " * (max_player_name_len - len(name))
    season_day = f"s{row['season'] + 1}d{row['day'] + 1}"
    inferred = "" if synced else " (inferred)"
    print(f"{spaces}{name} {unstable} {season_day:<6} probable incin roll: "
          f"{incin_roll:.10f} at thwack {incin_roll_loc}{inferred}")

    return pd.Series([incin_roll, incin_roll_loc,
                      synced, row['replacement id']],
                     index=['incin roll', 'incin roll location',
                            'synced', 'replacement id'])


def main():
    try:
        incins = pd.read_csv('incinerations_with_rolls.csv')
    except FileNotFoundError:
        incins_input = pd.read_csv('incinerations_v2.csv')

        players_oldest = load_players_oldest_records(exclude_initial=False)
        players = {player['entityId']: player for player in players_oldest}

        max_player_name_len = max(
            len(p['data']['name']) for p in players_oldest)

        func = partial(locate_incin, players, max_player_name_len)
        derived_data = incins_input.apply(func=func, axis=1)

        incins = incins_input.merge(derived_data, on='replacement id')
        incins.to_csv('incinerations_with_rolls.csv')

    with open('observed_incin_rates.json', 'r') as f:
        observed_rates = json.load(f)

    observed_seasons = [r['season'] + 1 for r in observed_rates if
                        r['season'] != 'aggregate']
    observed_natural = [natural_rate(r) for r in observed_rates if
                        r['season'] != 'aggregate']
    observed_unstable = [unstable_rate(r) for r in observed_rates if
                         r['season'] != 'aggregate']

    fig, (stable_ax, unstable_ax) = plt.subplots(2, figsize=(12, 8))

    for ax in (stable_ax, unstable_ax):
        ax.set_ylim(24.5, 0.5)  # high before low to invert the axis
        ax.set_ylabel("Season")
        ax.set_yticks(np.arange(24) + 1)

        yticks = ax.get_yticks()
        for y0, y1 in zip(yticks[::2], yticks[1::2]):
            ax.axhspan(y0 - 0.5, y1 - 0.5, color='black', alpha=0.1, zorder=0)

    stable_incins = incins[~incins['unstable']]
    unstable_incins = incins[incins['unstable']]

    theorized_base_rate = 0.00025
    theorized_unstable_multiplier = 40

    stable_ax.scatter(stable_incins['incin roll'],
                      stable_incins['season'] + 1)
    stable_ax.scatter(observed_natural, observed_seasons)
    stable_ax.set_title("Natural incineration rolls")
    stable_ax.vlines([theorized_base_rate], 0, 24, colors='red')
    stable_ax.set_xlim(0, 0.001)

    unstable_ax.scatter(unstable_incins['incin roll'],
                        unstable_incins['season'] + 1)
    unstable_ax.scatter(observed_unstable, observed_seasons)
    unstable_ax.set_title("Unstable incineration rolls")
    unstable_ax.vlines([theorized_base_rate * theorized_unstable_multiplier],
                       0, 24, colors='red')
    unstable_ax.set_xlim(0, 0.01)

    fig.tight_layout()
    plt.show()


def plot_probabilities(normal_rolls_by_season, normal_ax):
    # One indexed
    groups = [(2, 3), (3, 4), (4, 8), (8, 13), (13, 15)]
    # Transform it to zero indexed
    groups = [(l - 1, u - 1) for l, u in groups]

    for lower, upper in groups:
        num = sum(len(normal_rolls_by_season[s]) for s in range(lower, upper) if
                  s in normal_rolls_by_season)
        highest = max(
            max(normal_rolls_by_season[s]) for s in range(lower, upper) if
            s in normal_rolls_by_season)

        thresholds = []
        probs = []
        for i in range(1000):
            threshold = 0.001 * i / 1000
            thresholds.append(threshold)
            if threshold < highest:
                probs.append(0)
            else:
                prob = (highest / threshold) ** num
                probs.append(prob)
        max_prob = max(probs)
        probs = [prob / max_prob for prob in probs]
        ys = [prob * (lower - upper) + upper + 0.5 for prob in probs]

        normal_ax.plot(thresholds, ys)


def incin_rolls_to_plot_format(olls_by_season):
    xs = []
    ys = []
    for season, rolls in olls_by_season.items():
        for roll in rolls:
            xs.append(roll)
            ys.append(season + 1)
    return xs, ys


if __name__ == '__main__':
    main()
