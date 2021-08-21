from datetime import datetime, timezone
from itertools import islice

import numpy as np
from blaseball_mike.models import League, Team
from colorutils import Color
import matplotlib.pyplot as plt
import pytz
from dateutil.parser import isoparse


def main():
    tz = pytz.timezone('US/Eastern')
    before_exhibition = isoparse('2021-07-25 00:27:00.000000')
    after_exhibition = isoparse('2021-07-25 03:40:56.77879')

    league = League.load()

    print("Got list of teams")

    team_lineup_size_before = []
    team_rotation_size_before = []
    team_lineup_size_after = []
    team_rotation_size_after = []
    team_hue = []
    for team in islice(league.teams.values(), 300):
        team_before_exhibition = Team.load_at_time(team.id, before_exhibition)
        team_after_exhibition = Team.load_at_time(team.id, after_exhibition)

        team_lineup_size_before.append(len(team_before_exhibition.lineup))
        team_rotation_size_before.append(len(team_before_exhibition.rotation))
        team_lineup_size_after.append(len(team_after_exhibition.lineup))
        team_rotation_size_after.append(len(team_after_exhibition.rotation))

        team_hue.append(Color(hex=team.main_color).hsv[0])

        print("Processed", team.full_name)

    sort_order = np.argsort(team_hue)

    team_hue = np.array(team_hue)[sort_order]
    team_lineup_size_before = np.array(team_lineup_size_before)[sort_order]
    team_rotation_size_before = np.array(team_rotation_size_before)[sort_order]
    team_lineup_size_after = np.array(team_lineup_size_after)[sort_order]
    team_rotation_size_after = np.array(team_rotation_size_after)[sort_order]

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)

    ax1.plot(team_lineup_size_before, team_hue, label="Before bicentennial")
    ax2.plot(team_rotation_size_before, team_hue, label="Before bicentennial")
    ax1.plot(team_lineup_size_after, team_hue, label="After bicentennial")
    ax2.plot(team_rotation_size_after, team_hue, label="After bicentennial")

    ax1.set_title("Lineup")
    ax1.legend()
    ax2.set_title("Rotation")
    ax2.legend()

    fig.suptitle("Team size changes due to Bicentennial", fontsize=16)
    fig.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axes
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False,
                    right=False)
    plt.grid(False)
    plt.xlabel("Team size")
    plt.ylabel("Team's primary color's hue")

    plt.show()


if __name__ == '__main__':
    main()
