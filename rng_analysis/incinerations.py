import json
from functools import partial

import matplotlib.cm
import matplotlib.colors
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from blaseball_mike import chronicler
from blaseball_mike.models import Stadium

from rng_analysis.rng import Rng
from rng_analysis.util import load_players_oldest_records

HALL_BLUE = (89 / 255, 136 / 255, 255 / 255)


def get_player_team(player_id, at_time):
    for team in chronicler.get_entities('team', at=at_time):
        if player_id in team['data']['lineup']:
            return team['data']
        elif player_id in team['data']['rotation']:
            return team['data']

    raise RuntimeError("Player not found")


def roll_offsets(season, unstable):
    gen_len = 26
    if season > 1:
        # cinnamon, fate, allergy, uhh
        gen_len += 3
    if season > 11:
        # ritual, blood, coffee
        gen_len += 3

    if season < 6:
        return {
            'incin': -3,
            'pitcher_or_batter': gen_len,
            'position': gen_len + 1
        }
    elif season < 11:
        if unstable:
            return {
                'chain': gen_len,
                'incin': gen_len + 1,
                'position': gen_len + 2,
            }
        else:
            return {
                'incin': gen_len,
                'position': gen_len + 2,
            }
    elif season < 15:
        return {
            'incin': -4
        }
    else:
        return {
            'incin': -5
        }


highest_pitcher, lowest_batter = 0, 1


def locate_incin(players, max_player_name_len, row):
    global highest_pitcher, lowest_batter
    if row['replacement id'] not in players:
        return pd.Series([0, 0, 0, row['replacement id'], 0, 0, 0],
                         index=['incin roll', 'incin roll location',
                                'chain roll', 'replacement id',
                                's0', 's1', 'offset'])

    replacement = players[row['replacement id']]
    offsets = roll_offsets(row['season'], row['unstable'])
    # Compute data
    rng = Rng((replacement['state']['s0'], replacement['state']['s1']),
              replacement['state']['offset'])

    incin_roll_loc = offsets['incin']
    incin_roll = rng[incin_roll_loc]

    def query(offset_type):
        if offset_type not in offsets:
            return 0
        return rng[offsets[offset_type]]

    team = get_player_team(row['replacement id'], replacement['timestamp'])

    # if row['season'] > 5:
    #     print("highest pitcher", highest_pitcher,
    #           "lowest batter", lowest_batter)

    if 'pitcher_or_batter' in offsets:
        if query('pitcher_or_batter') < 0.1:
            pred_victim_id = team['rotation'][row['day'] % len(team['rotation'])]
            highest_pitcher = max(query('pitcher_or_batter'), highest_pitcher)
        else:
            pred_victim_i = int(len(team['lineup']) * query('position'))
            pred_victim_id = team['lineup'][pred_victim_i]
            lowest_batter = min(query('pitcher_or_batter'), lowest_batter)
    else:
        index = int((len(team['lineup']) + 2) * query('position'))
        if index == 0:
            pred_victim_id = team['rotation'][row['day'] % len(team['rotation'])]
        elif index == len(team['lineup']) + 1:
            pred_victim_id = "<active>"
        else:
            pred_victim_id = team['lineup'][index - 1]

    try:
        pred_victim = players[pred_victim_id]
        predicted_victim_name = pred_victim['name']
    except KeyError:
        predicted_victim_name = "?"

    # Format and print data
    name = replacement['name']
    unstable = "(u)" if row['unstable'] else "   "
    spaces = " " * (max_player_name_len - len(name))
    season_day = f"s{row['season'] + 1}d{row['day'] + 1}"
    inferred = " "  # if synced else "*"
    print(f"{spaces}{name} {unstable} {season_day:<6}, "
          f"{incin_roll:.7f} at thwack {incin_roll_loc}{inferred} "
          f"predicted using position: {predicted_victim_name}")

    chain_roll = query('chain') if 'chain' in offsets else -1

    # Need to get thwack last so .get_state is in the right position
    assert rng[0]
    return pd.Series([incin_roll, incin_roll_loc, chain_roll,
                      row['replacement id'], *rng.get_state()],
                     index=['incin roll', 'incin roll location', 'chain roll',
                            'replacement id', 's0', 's1', 'offset'])


def seasonal_forts(season):
    if season > 12:
        return [s.fortification for s in
                Stadium.load_all_by_gameday(season, 80).values()]
    return [0.5] * 24


def main():
    try:
        incins = pd.read_csv('incinerations_with_rolls.csv')
    except FileNotFoundError:
        incins_input = pd.read_csv('incinerations_v2.csv')

        players_oldest = load_players_oldest_records(exclude_initial=False)
        players = {player['id']: player for player in players_oldest}

        max_player_name_len = max(len(p['name']) for p in players_oldest if p['name'] is not None)

        func = partial(locate_incin, players, max_player_name_len)
        derived_data = incins_input.apply(func=func, axis=1)

        incins = incins_input.merge(derived_data, on='replacement id')
        incins.to_csv('incinerations_with_rolls.csv')

    with open('observed_incin_rates.json', 'r') as f:
        observed_rates = json.load(f)

    observed_seasons = [r['season'] + 1 for r in observed_rates if
                        r['season'] != 'aggregate']
    observed_stable = [r['death rate']['stable'][1][0] / 100000
                       for r in observed_rates if r['season'] != 'aggregate']
    observed_unstable = [r['death rate']['unstable'][1][0] / 100000
                         for r in observed_rates if r['season'] != 'aggregate']

    ee = incins
    ee = ee[~ee['unstable']]
    ee = ee[ee['incin roll'] != 0]

    thresholds = 0.0001 + (1 - ee['fortification']) * 0.0003
    thresholds[ee['season'] == 1] = 0.000075
    thresholds[ee['season'] == 2] = 0.0005
    thresholds[ee['season'] == 3] = 0.00015
    thresholds[ee['season'] == 4] = 0.00015
    thresholds[ee['season'] == 5] = 0.00015
    thresholds[ee['season'] == 6] = float('nan')
    thresholds[ee['season'] == 7] = 0.00025
    thresholds[ee['season'] == 8] = 0.00025
    thresholds[ee['season'] == 9] = 0.00025

    closeness = ee['incin roll'] / thresholds

    fig, ax = plt.subplots(1)
    ax.set_yscale('log')
    ax.scatter(ee['day'], closeness, c=ee['season'])
    ax.set_xlabel("Day")
    ax.set_ylabel("Degree of failure")
    ax.set_title("How bad did you fail your incin roll")

    fig.tight_layout()
    plt.show()

    fig, (stable_ax, unstable_ax) = plt.subplots(2, figsize=(12, 8),
                                                 constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=12. / 72., h_pad=24. / 72.,
                                    hspace=0. / 72., wspace=0. / 72.)
    for ax in (stable_ax, unstable_ax):
        ax.set_ylim(24.5, 0.5)  # high before low to invert the axis
        ax.set_ylabel("Season")
        ax.set_yticks(np.arange(24) + 1)

        # Create the even-odd shading
        yticks = ax.get_yticks()
        for y0, y1 in zip(yticks[::2], yticks[1::2]):
            ax.axhspan(y0 - 0.5, y1 - 0.5, color='black', alpha=0.1, zorder=0)

    stable_incins = incins[~incins['unstable']]
    unstable_incins = incins[incins['unstable']]

    def add_threshold(start_season, threshold, alpha=0.015,
                      seasons=1, threshold_start=0.0):
        for season in range(start_season, start_season + seasons):
            forts = seasonal_forts(season)
            min_fort_i = min((f, i) for i, f in enumerate(forts))[1]
            for i, fort in enumerate(forts):
                t = threshold * (40 / 25 - fort * 30 / 25)
                patch = matplotlib.patches.Rectangle(
                    (threshold_start, season - 0.5), t - threshold_start,
                    1, facecolor=(*HALL_BLUE, alpha),
                    edgecolor=(HALL_BLUE if i == min_fort_i else None)
                )
                stable_ax.add_patch(patch)

    add_threshold(2, 0.000075)
    add_threshold(3, 0.0005)
    add_threshold(3, 0.001, threshold_start=0.0005, alpha=0.002)
    add_threshold(4, 0.00015, seasons=3)
    add_threshold(8, 0.00025, seasons=3)
    add_threshold(12, 0.00025, seasons=12)

    cmap = matplotlib.cm.autumn
    norm = matplotlib.colors.TwoSlopeNorm(vmin=0, vcenter=0.5, vmax=1)

    stable_ax.scatter(stable_incins['incin roll'],
                      stable_incins['season'] + 1,
                      c=cmap(stable_incins['fortification']), zorder=4)
    stable_ax.scatter(observed_stable, observed_seasons,
                      c='black', marker='d', zorder=5)
    stable_ax.set_title("Natural incineration rolls")
    stable_ax.set_xlim(0, 0.0005)
    stable_ax.text(0.000502, 3.5, "*", va='center',
                   fontsize='x-large', fontweight='bold')

    unstable_ax.scatter(unstable_incins['incin roll'],
                        unstable_incins['season'] + 1,
                        c=cmap(unstable_incins['fortification']), zorder=4)
    unstable_ax.scatter(observed_unstable, observed_seasons,
                        c='black', marker='d', zorder=5)
    unstable_ax.set_title("Unstable incineration rolls")
    # unstable_ax.vlines([theorized_base_rate * theorized_unstable_multiplier],
    #                    0.5, 24.5, colors='red')
    unstable_ax.set_xlim(0, 0.01)

    fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), aspect=40,
                 pad=0, ax=[stable_ax, unstable_ax], label='Fortification')
    plt.figtext(0.45, 0.51,
                "* Season 3 had two incinerations with rolls above 0.0005. "
                "The threshold was then changed from 0.001 to 0.0005 on Day 5.",
                ha="center", fontsize=10)
    # fig.tight_layout()
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
