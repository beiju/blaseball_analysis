import json
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

SEASON_ID = "cd1b6714-f4de-4dfc-a030-851b3459d8d1"  # NS1
# SEASON_ID = "7af53acf-1fb9-40e8-96c7-ab8308a353f9"  # NS2
TEAM_ID = "8d87c468-699a-47a8-b40d-cfb73a5660ad"


def expand_list(l: list, size: int):
    while len(l) < size:
        l.append(0)


def hist_push(l: list, value: int):
    expand_list(l, value + 1)
    l[value] += 1


def main():
    with open("games.json", "r") as f:
        data = json.load(f)

    runs_allowed_hist = defaultdict(lambda: [])
    runs_scored_hist = defaultdict(lambda: [])
    for item in data["items"]:
        data = item["data"]
        if data["seasonId"] != SEASON_ID:
            continue
        if data["homeTeam"]["id"] == TEAM_ID:
            if not data["gameStates"]:
                print("Skipping game with missing gameStates")
                continue
            game_state = data["gameStates"][0]

            hist_push(runs_scored_hist[data["homePitcher"]["name"]], game_state["homeScore"])
            hist_push(runs_allowed_hist[data["homePitcher"]["name"]], game_state["awayScore"])
        elif data["awayTeam"]["id"] == TEAM_ID:
            if not data["gameStates"]:
                print("Skipping game with missing gameStates")
                continue
            game_state = data["gameStates"][0]

            hist_push(runs_allowed_hist[data["awayPitcher"]["name"]], game_state["homeScore"])
            hist_push(runs_scored_hist[data["awayPitcher"]["name"]], game_state["awayScore"])

    assert len(runs_scored_hist) == len(runs_allowed_hist)
    fig, axes = plt.subplots(len(runs_allowed_hist), 2, sharex=True, sharey=True, layout='tight')

    fig.suptitle("Crabs NS1")

    for (allowed_ax, scored_ax), pitcher_name in zip(axes, runs_scored_hist.keys()):
        scored_hist = runs_scored_hist[pitcher_name]
        scored_ax.bar(np.arange(len(scored_hist)), scored_hist)
        runs_scored_mean = sum(n * i for i, n in enumerate(scored_hist)) / sum(scored_hist)
        scored_ax.axvline(runs_scored_mean, color='r')
        scored_ax.set_xlabel(f"Runs Scored with {pitcher_name} pitching")
        scored_ax.set_ylabel("Occurrences")
        allowed_hist = runs_allowed_hist[pitcher_name]
        allowed_ax.bar(np.arange(len(allowed_hist)), allowed_hist)
        runs_allowed_mean = sum(n * i for i, n in enumerate(allowed_hist)) / sum(allowed_hist)
        allowed_ax.axvline(runs_allowed_mean, color='r')
        allowed_ax.set_xlabel(f"Runs Allowed by {pitcher_name}")
        allowed_ax.set_ylabel("Occurrences")

    plt.show()


if __name__ == '__main__':
    main()
