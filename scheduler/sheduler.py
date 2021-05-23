import json
import random
from collections import defaultdict

import numpy as np

season = 19


def is_connected_without(adjancency, edge):
    x, y = edge
    test_matrix = adjancency.astype(np.uint64)
    test_matrix[x, y] = 0
    test_matrix[y, x] = 0
    test_matrix += np.identity(test_matrix.shape[0], dtype=np.uint64)

    t_2 = test_matrix @ test_matrix
    t_4 = t_2 @ t_2
    t_8 = t_4 @ t_4
    t_16 = t_8 @ t_8
    t_24 = t_8 @ t_16

    # If none of these entries are zero, it's fully connected
    return np.count_nonzero(t_24) == t_24.size


def get_tour(adjancency, start_node):
    tour = []
    a, b = None, start_node
    while True:
        # Advance a to b
        a = b
        # Advance b to a random element connected to a
        b = np.random.choice(adjancency[a].nonzero()[0])

        assert adjancency[a, b] == 1
        assert adjancency[b, a] == 1
        adjancency[a, b] = 0
        adjancency[b, a] = 0

        tour.append((a, b))

        if b == start_node:
            return tour


def get_euler_tour(adjancency):
    if np.all(adjancency == 0):
        return None

    adjancency_before = adjancency.copy()
    # This finds a random node in a way that guarantees that at least one edge
    # is incident to it
    start_node = random.choice(np.nonzero(adjancency)[0])
    tour = get_tour(adjancency, start_node)

    # Classic-style for loop allows modifying the list while traversing it
    i = 0
    while i < len(tour):
        a, b = tour[i]

        # Check if there is an unused edge on node B
        if adjancency[b].nonzero()[0].size > 0:
            # If so, find a tour from it and splice the nested tour into the
            # main tour
            nested_tour = get_tour(adjancency, b)
            # This is python's idiosyncratic way of splicing lists
            tour[i + 1:i + 1] = nested_tour

            # Check
            pa, pb = tour[-1]
            for ta, tb in tour:
                assert ta == pb
                pa, pb = ta, tb

        i += 1

    return tour


def main():
    with open(f"season-{season}-matchups.json", "r") as f:
        matchups_by_day = json.load(f)

    matchups_by_day = {int(k): v for k, v in matchups_by_day.items()}

    team_ids = sorted(
        team_id for matchup in matchups_by_day[1] for team_id in matchup)
    index_for_team = {team_id: i for i, team_id in enumerate(team_ids)}
    num_teams = len(team_ids)

    adjancency = np.zeros((num_teams + 1, num_teams + 1), dtype=int)

    def is_adjacent(x, y):
        assert x != y
        assert adjancency[x, y] == adjancency[y, x]
        return adjancency[x, y] == 1

    def clear_adjacent(x, y):
        assert is_adjacent(x, y)
        adjancency[x, y] = 0
        adjancency[y, x] = 0

    def get_random_adjacent(y):
        nonzeroes, = adjancency[:, y].nonzero()
        np.random.shuffle(nonzeroes)
        for x in nonzeroes:
            if is_connected_without(adjancency, (x, y)):
                return x
            print((x, y), "would disconnect graph")

        print("Must disconnect graph")
        return nonzeroes[0]

    # Key is a tuple (a, b) two team indices such that a < b
    # Value is a list of days on which this pair of teams plays
    matchup_days = defaultdict(lambda: [])

    for day, matchups in matchups_by_day.items():
        for (team_a, team_b) in matchups:
            a, b = sorted((index_for_team[team_a], index_for_team[team_b]))
            assert a != b

            matchup_days[(a, b)].append(day)
            adjancency[a, b] = 1 - adjancency[a, b]

    # Adjacency needs to be symmetrical while we're using it
    adjancency += adjancency.T

    # At this edge adjacency is an adjacency matrix where teams have an edge if
    # they play an odd number of sets together. Need to add an edge from each
    # team with an odd number of edges to the virtual "X" team (whose team index
    # is `num_teams`)
    adjancency[:, num_teams] = adjancency[num_teams, :] = adjancency.sum(
        axis=1) % 2
    assert np.all(adjancency.sum(axis=0) % 2 == 0)
    assert np.all(adjancency.sum(axis=1) % 2 == 0)

    assert np.all(adjancency.T == adjancency)

    schedule = defaultdict(lambda: [])

    odd_matchups = {}
    for key, sets_together in matchup_days.items():
        # Avoid biasing lexicographically earlier teams having more home games
        if random.choice([True, False]):
            a, b = key
        else:
            b, a = key

        # Shuffle days to avoid biasing towards an alternating schedule
        random.shuffle(sets_together)

        # Assign sets in pairs of home/away until only 0 or 1 sets are left
        while len(sets_together) > 1:
            home_day, away_day = sets_together.pop(), sets_together.pop()

            # B(l)aseball schedules list the home team second
            schedule[home_day].append((b, a))
            schedule[away_day].append((a, b))

        # If there's anything left, add it to odd_matchups
        if sets_together:
            odd_matchups[key] = sets_together[0]

    del matchup_days

    while (tour := get_euler_tour(adjancency)) is not None:
        for a, b in tour:
            if a == num_teams or b == num_teams:
                # Then this is an edge to team X; ignore it
                continue

            remaining_day = odd_matchups.pop((a, b) if a < b else (b, a))

            # Assign A home
            schedule[remaining_day].append((b, a))

    assert adjancency.sum() == 0

    # Validation
    team_home_minus_away = defaultdict(lambda: 0)
    pair_count = defaultdict(lambda: 0)

    team_indices_set = set(index_for_team.values())
    for day, games in schedule.items():
        # Check there are 12 games
        assert len(games) == 12

        # Check every team plays
        assert {i for i_s in games for i in i_s} == team_indices_set

        for (away, home) in games:
            team_home_minus_away[home] += 1
            team_home_minus_away[away] -= 1
            pair_count[(away, home)] += 1

    assert all(abs(count) <= 1 for count in team_home_minus_away.values())

    for i in range(num_teams):
        for j in range(i, num_teams):
            assert abs(pair_count[i, j] - pair_count[j, i]) <= 1

    print("Validated!")


if __name__ == '__main__':
    main()
