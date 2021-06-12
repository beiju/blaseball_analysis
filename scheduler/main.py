import json
import random
import time
from collections import defaultdict
from itertools import count
from multiprocessing import Process, Value

from scheduler.sheduler2 import test_matchups


def phase_for_day(day):
    if day <= 27:
        return 0
    elif day <= 72:
        return 1
    else:
        return 2


def get_season(season):
    with open(f"season-{season}-matchups.json", "r") as f:
        matchups_by_day = json.load(f)

    # Turn keys from strings to ints
    return {int(k): v for k, v in matchups_by_day.items()}


def get_random(teams):
    matchups_by_day = {i: [] for i in range(1, 99, 3)}
    for day in matchups_by_day.keys():
        teams_today = list(teams)
        random.shuffle(teams_today)

        for i in range(0, len(teams_today), 2):
            matchups_by_day[day].append(teams_today[i:i + 2])

    return matchups_by_day


def validate(all_teams, schedule):
    team_home_minus_away = defaultdict(lambda: 0)
    team_home_minus_away_by_phase = [defaultdict(lambda: 0) for _ in range(3)]
    pair_count = defaultdict(lambda: 0)
    pair_count_by_phase = [defaultdict(lambda: 0) for _ in range(3)]

    for day, games in schedule.items():
        phase = phase_for_day(day)

        # Check there are 12 games
        assert len(games) == 12

        # Check every team plays
        assert {i for i_s in games for i in i_s} == set(range(24))

        for (away, home) in games:
            team_home_minus_away[home] += 1
            team_home_minus_away[away] -= 1
            pair_count[(away, home)] += 1

            team_home_minus_away_by_phase[phase][home] += 1
            team_home_minus_away_by_phase[phase][away] -= 1
            pair_count_by_phase[phase][away, home] += 1

    assert all(abs(n) <= 1 for n in team_home_minus_away.values())

    for a in all_teams:
        for b in all_teams:
            assert abs(pair_count[a, b] - pair_count[b, a]) <= 1

    for phase in range(3):
        assert all(abs(n) <= 1 for n in
                   team_home_minus_away_by_phase[phase].values())

        for a in range(24):
            for b in range(24):
                assert abs(pair_count_by_phase[phase][a, b] -
                           pair_count_by_phase[phase][b, a]) <= 1


def validate_random(teams, counter: Value):
    for _ in count():
        matchups_by_day = get_random(teams)
        schedule = test_matchups(matchups_by_day, teams)
        validate(teams, schedule)

        with counter.get_lock():
            counter.value += 1


def main():
    # For debugging
    # np.random.seed(0)

    teams = None
    for season in range(13, 20):
        matchups_by_day = get_season(season)
        teams = set(team for pairs in matchups_by_day.values()
                    for pair in pairs for team in pair)

        schedule = test_matchups(matchups_by_day, teams)
        validate(teams, schedule)
        print(f"Validated on season {season}!")

    counter = Value('i', 0)
    processes = [Process(target=validate_random, args=(teams, counter), daemon=True)
                 for _ in range(12)]

    for process in processes:
        process.start()

    while True:
        time.sleep(5)
        with counter.get_lock():
            current_count = counter.value
        print(f"Validated on {current_count} randomly generated seasons")


if __name__ == '__main__':
    main()
