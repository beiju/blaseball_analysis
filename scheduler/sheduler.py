import random
from collections import defaultdict

import numpy as np
from itertools import chain, combinations

from tqdm import tqdm


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def get_tour(adjancency, start_node, total_edge_follows, phase_edge_follows):
    return get_path_until(adjancency, start_node, start_node,
                          total_edge_follows, phase_edge_follows)


def obeys_induced_subgraph_condition(adjancency, a, c,
                                     total_edge_follows, phase_edge_follows):
    adjancency = adjancency.copy()
    total_edge_follows = total_edge_follows.copy()
    phase_edge_follows = phase_edge_follows.copy()

    # Follow this edge
    adjancency[a, c] -= 1
    adjancency[c, a] -= 1

    total_edge_follows[a, c] += 1
    phase_edge_follows[a, c] += 1

    masks = np.unpackbits(
        np.arange(2 ** adjancency.shape[0], dtype=np.uint32)
            .reshape((1, -1)).view(np.uint8),
        count=adjancency.shape[0], axis=0).view(bool)

    stride = 1000000
    for i in tqdm(range(0, 2**adjancency.shape[0], stride)):
        masks_2d = masks[:, None, i:i+stride] * ~masks[None, :, i:i+stride]

        directed_out = (total_edge_follows[:, :, None] * masks_2d).sum(axis=(0, 1))
        directed_in = (total_edge_follows[:, :, None] * np.transpose(masks_2d, (1, 0, 2))).sum(axis=(0, 1))
        undirected = (adjancency[:, :, None] * masks_2d).sum(axis=(0, 1))

        total_edges = directed_in + directed_out + undirected

        directed_diff = directed_out - directed_in

        cond_1, cond_2 = directed_diff, total_edges % 2 == 0

        case_1 = cond_1 & cond_2
        # max(0, directed_diff - undirected) == 0
        # directed_diff - undirected > 0
        # directed_diff > undirected
        if not np.all(directed_diff[case_1] > undirected[case_1]):
            return False

        case_2 = cond_1 & ~cond_2
        # max(1, directed_diff - undirected) == 0
        # directed_diff - undirected == 0
        # directed_diff == undirected
        if not np.all(directed_diff[case_2] == undirected[case_2]):
            return False

        case_3 = ~cond_1 & cond_2
        # min(0, directed_diff + undirected) == 0
        # directed_diff + undirected >= 0
        # directed_diff >= -undirected
        if not np.all(directed_diff[case_3] >= -undirected[case_3]):
            return False

        case_4 = ~cond_1 & ~cond_2
        # min(-1, directed_diff + undirected) == 0
        # directed_diff + undirected == 0
        # directed_diff == -undirected
        if not np.all(directed_diff[case_4] == -undirected[case_4]):
            return False

    print("Deficiency check passed")

    return True


def get_path_until(adjancency, start_node, end_node, total_edge_follows,
                   phase_edge_follows, came_from=None):
    # Recursion base case
    if came_from is not None and start_node == end_node:
        return []

    # Get a list of candidates for which node to jump to next
    candidates0 = adjancency[start_node].nonzero()[0]

    assert candidates0.size > 0

    candidates1 = candidates0[
        [i for i, c in enumerate(candidates0)
         if obeys_induced_subgraph_condition(
            adjancency, start_node, c, total_edge_follows, phase_edge_follows)]
    ]

    assert candidates1.size > 0

    # Sort candidates by how many extra edges in the respective node pair are
    # already pointed this direction. If fewer are pointed this direction than
    # the other direction, then choosing that candidate is more helpful so it
    # goes to the beginning. If more are pointed this direction than the other
    # direction, then choosing that candidate takes us further from our goal so
    # it goes to the end. Then the frontmost candidate is selected.
    total_net_edge_follows = (total_edge_follows[start_node, candidates1] -
                              total_edge_follows[candidates1, start_node])
    phase_net_edge_follows = (phase_edge_follows[start_node, candidates1] -
                              phase_edge_follows[candidates1, start_node])
    net_edge_follows = np.minimum(total_net_edge_follows,
                                  phase_net_edge_follows)
    candidates2 = candidates1[net_edge_follows == net_edge_follows.min()]

    remaining_nodes = adjancency[candidates2].sum(axis=1)
    candidates3 = candidates2[remaining_nodes == remaining_nodes.max()]

    next_node = random.choice(candidates3)

    # Net follows in this direction if all remaining nodes were assigned in
    # the opposite direction must be at most 1
    assert (total_edge_follows[start_node, next_node] -
            total_edge_follows[next_node, start_node] -
            adjancency[start_node, next_node]) <= 1
    assert (phase_edge_follows[start_node, next_node] -
            phase_edge_follows[next_node, start_node] -
            adjancency[start_node, next_node]) <= 1
    # print("SKIPPED CANDIDATE")
    # continue

    total_edge_follows[start_node, next_node] += 1
    phase_edge_follows[start_node, next_node] += 1

    assert adjancency[start_node, next_node] > 0
    assert adjancency[next_node, start_node] > 0
    adjancency[start_node, next_node] -= 1
    adjancency[next_node, start_node] -= 1

    assert (total_edge_follows[start_node, next_node] -
            total_edge_follows[next_node, start_node] -
            adjancency[start_node, next_node]) <= 1
    assert (phase_edge_follows[start_node, next_node] -
            phase_edge_follows[next_node, start_node] -
            adjancency[start_node, next_node]) <= 1

    path_rest = get_path_until(adjancency, start_node=next_node,
                               end_node=end_node,
                               total_edge_follows=total_edge_follows,
                               phase_edge_follows=phase_edge_follows,
                               came_from=start_node)

    if path_rest is None:
        # Undo modifications to adjacency and edge_follows
        total_edge_follows[start_node, next_node] -= 1
        phase_edge_follows[start_node, next_node] -= 1
        adjancency[start_node, next_node] += 1
        adjancency[next_node, start_node] += 1

    return [(start_node, next_node)] + path_rest

    # print("BACKTRACKED")
    # return None


def get_euler_tour(adjancency, start_node, total_edge_follows,
                   phase_edge_follows):
    tour = get_tour(adjancency, start_node, total_edge_follows,
                    phase_edge_follows)
    # Classic-style for loop allows modifying the list while traversing it
    i = 0
    while i < len(tour):
        a, b = tour[i]

        # Check if there is an unused edge on node B
        if adjancency[b].nonzero()[0].size > 0:
            # If so, find a tour from it and splice the nested tour into the
            # main tour
            nested_tour = get_tour(adjancency, b, total_edge_follows,
                                   phase_edge_follows)
            # This is python's idiosyncratic way of splicing lists
            tour[i + 1:i + 1] = nested_tour

            # Check
            pa, pb = tour[-1]
            for ta, tb in tour:
                assert ta == pb
                pa, pb = ta, tb

        i += 1

    return tour


def phase_for_day(day):
    if day <= 27:
        return 0
    elif day < 72:
        return 1
    else:
        return 2


def test_matchups(matchups_by_day, all_teams):
    team_ids = sorted(all_teams)
    index_for_team = {team_id: i for i, team_id in enumerate(team_ids)}
    num_teams = len(team_ids)

    # Separate adjacency matrix for each phase
    adjancency_by_phase = [np.zeros((num_teams + 1, num_teams + 1), dtype=int)
                           for _ in range(3)]

    # Key is a tuple (phase, a, b) two team indices such that a < b
    # Value is a list of days on which this pair of teams plays
    matchup_days = defaultdict(lambda: [])

    for day, days in matchups_by_day.items():
        for (team_a, team_b) in days:
            a, b = sorted((index_for_team[team_a], index_for_team[team_b]))
            assert a != b

            phase = phase_for_day(day)
            matchup_days[(phase, a, b)].append(day)
            adjancency_by_phase[phase][a, b] += 1
            adjancency_by_phase[phase][b, a] += 1

    for adjancency in adjancency_by_phase:
        # Adjacency needs to be symmetrical
        assert np.all(adjancency.T == adjancency)

        # At this edge adjacency is an adjacency matrix where teams have an edge
        # if they play an odd number of sets together. Need to add an edge from
        # each team with an odd number of edges to the virtual "X" team (whose
        # team index is `num_teams`)
        adjancency[:, num_teams] = adjancency[num_teams, :] = \
            adjancency.sum(axis=1) % 2
        assert np.all(adjancency.sum(axis=0) % 2 == 0)
        assert np.all(adjancency.sum(axis=1) % 2 == 0)

        assert np.all(adjancency.T == adjancency)

    schedule = defaultdict(lambda: [])

    total_edge_follows = np.zeros_like(adjancency_by_phase[0])

    # The euler tours for the 3 phases must share a start node. Any team
    # will do because they're all guaranteed to have games in each phase.
    start_node = 1  # np.random.randint(0, num_teams)
    for phase in range(0, 3):
        phase_edge_follows = np.zeros_like(adjancency_by_phase[0])
        tour = get_euler_tour(adjancency_by_phase[phase], start_node,
                              total_edge_follows, phase_edge_follows)

        for a, b in tour:
            if a == num_teams or b == num_teams:
                # Then this is an edge to team X; ignore it
                continue

            day = matchup_days[(phase, a, b) if a < b else (phase, b, a)].pop()
            schedule[day].append((b, a))  # Home game second

    # This should have drained all the adjacency matrices
    for adjancency in adjancency_by_phase:
        assert adjancency.sum() == 0

    # And should have drained matchup_days
    for days in matchup_days.values():
        assert len(days) == 0

    return schedule
