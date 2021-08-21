import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main():
    data = pd.read_csv("run_differential_all_s13.csv")

    # Remove playoffs
    data = data[data['day'] < 99]

    # Whoops. Made my data backwards.
    # data['differential'] = -data['differential']

    # This data only has away games. Add an inverted copy to get home games
    data_inv = data.copy()
    data_inv[['team', 'opponent']] = data[['opponent', 'team']]
    data_inv['differential'] = -data['differential']
    data_inv['nickname'] = ""  # Nicknames unknown

    data = pd.concat((data, data_inv))

    # Add a teensy amount to get things to round in the direction I want
    data.loc[data['differential'] > 0, 'differential'] += 0.001
    data.loc[data['differential'] < 0, 'differential'] -= 0.001

    bins = np.arange(math.floor(data['differential'].min()), math.ceil(data['differential'].max() + 1))
    axes = data.hist(column="differential", by="team", bins=bins, grid=False, figsize=(16, 12), sharey=True, sharex=True)

    for ax in axes.flat:
        team = ax.get_title()
        if team:
            nickname = sorted(data[data['team'] == team]['nickname'].unique())[-1]
        else:
            nickname = "?"
        ax.set_title(f"{nickname}")
        display_bins = bins[1::3]
        ax.set_xticks(display_bins)
        ax.set_xticklabels(display_bins)

    # Add another axis on top of the rest just for labels
    # add a big axis, hide frame
    plt.gcf().add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Frequency")
    plt.ylabel("Run Differential")
    # plt.title("Regular Season 13     Run Differentials")

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
