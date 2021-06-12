from collections import defaultdict

import ebcic
import matplotlib.pyplot as plt
import numpy as np
from blaseball_mike import chronicler

plot_season = 19


def error_bounds(data):
    p = ebcic.Params(
        k=np.count_nonzero(data),
        n=len(data),
        confi_perc=99.0
    )

    return ebcic.exact(p)


def main():
    scaled_hype_levels = defaultdict(lambda: 0)  # Indexed by stadium
    home_outcomes_by_hype = defaultdict(lambda: [])

    zero_hype_losses = defaultdict(lambda: 0)
    zero_hype_nonlosses = defaultdict(lambda: 0)

    games_by_day = defaultdict(lambda: [])
    print("Querying games")
    for g in chronicler.get_games(season=plot_season):
        games_by_day[g["data"]["day"]].append(g["data"])
    print("Crunching numbers")

    teams = set(g['homeTeam'] for games in games_by_day.values() for g in games)
    stadiums = set(
        g['stadiumId'] for games in games_by_day.values() for g in games)

    plot_pts = []
    for day in sorted(games_by_day.keys()):
        if day >= 99:
            # Don't process postseason games
            break
        games = games_by_day[day]

        print("Day", day)
        assert len(games) == 12
        for game in games:
            initial_hype = scaled_hype_levels[game["stadiumId"]]

            if game["homeScore"] > game["awayScore"]:
                home_outcomes_by_hype[initial_hype].append(1)

                if initial_hype == 0:
                    zero_hype_nonlosses[game["homeTeam"]] += 1
                    zero_hype_losses[game["awayTeam"]] += 1
            else:
                home_outcomes_by_hype[initial_hype].append(0)

                if initial_hype == 0:
                    zero_hype_nonlosses[game["awayTeam"]] += 1
                    zero_hype_losses[game["homeTeam"]] += 1

            if game["shame"]:
                scaled_hype_levels[game["stadiumId"]] += 9
            else:
                scaled_hype_levels[game["stadiumId"]] -= 1
            if scaled_hype_levels[game["stadiumId"]] < 0:
                scaled_hype_levels[game["stadiumId"]] = 0

        plot_row = []
        for stadium_id in stadiums:
            plot_row.append(scaled_hype_levels[stadium_id])
        assert len(plot_row) == 24
        plot_pts.append(plot_row)

    fig, home_ax = plt.subplots(1, 1, figsize=[8, 6])

    max_hype = max(home_outcomes_by_hype.keys())

    outcomes_mean = np.array([np.mean(home_outcomes_by_hype[hype]) for hype in
                              range(0, max_hype + 1)])
    outcomes_wilson = np.array([error_bounds(home_outcomes_by_hype[hype]) for hype in
                                range(0, max_hype + 1)])

    outcomes_errbars = (
        outcomes_mean - outcomes_wilson[:, 0],
        outcomes_wilson[:, 1] - outcomes_mean
    )

    displayed_hype = [hype * 0.03 for hype in range(0, max_hype + 1)]

    home_ax.errorbar(displayed_hype, outcomes_mean,
                     yerr=outcomes_errbars,
                     ecolor="lightgrey")
    home_ax.set_title("Home Win % vs Hype")
    home_ax.set_ylabel("Home Win %")
    home_ax.set_xlabel("Hype")
    home_ax.set_ylim(0, 1.05)

    # size_ax.plot(displayed_hype, num_data_points_by_hype)
    # size_ax.set_title("Number of data points")
    # size_ax.set_ylabel("Data points")
    # size_ax.set_xlabel("Hype")
    # size_ax.set_ylim(0, 64)

    # zero_hype_records = [(team, zero_hype_nonlosses[team] / (
    #         zero_hype_losses[team] + zero_hype_nonlosses[team]))
    #                      for team in teams]
    #
    # zero_hype_records = sorted(zero_hype_records, key=lambda tup: tup[1],
    #                            reverse=True)
    #
    # nicknames = {team: models.Team.load(team).nickname for team in teams}
    # max_name_len = max(len(nickname) for nickname in nicknames.values())
    # for team, record in zero_hype_records:
    #     num_games = zero_hype_losses[team] + zero_hype_nonlosses[team]
    #     print(f"{nicknames[team].rjust(max_name_len)} "
    #           f"had record {record:.2f} " +
    #           f"({zero_hype_nonlosses[team]}-{zero_hype_losses[team]}) ".ljust(8) +
    #           f"in {num_games:2d} zero-hype games")

    # while True:
    #     plt.pause(1)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
