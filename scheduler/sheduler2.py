import json
import random
from collections import defaultdict
from itertools import count

import mip


def phase_for_day(day):
    if day <= 27:
        return 0
    elif day <= 72:
        return 1
    else:
        return 2


def test_matchups(matchups_by_day, all_teams):
    m = mip.Model()
    m.emphasis = 1  # 1 = feasibility emphasis
    m.verbose = 0

    games_at_phase = [0 for _ in range(3)]

    vars_by_day = {k: [] for k in matchups_by_day.keys()}
    team_total_sums = {team: 0 for team in all_teams}
    team_phase_sums = [{team: 0 for team in all_teams} for _ in range(3)]
    team_matchup_sums = {team: {t: 0 for t in all_teams} for team in all_teams}
    team_phase_matchup_sums = [
        {team: {t: 0 for t in all_teams} for team in all_teams} for _ in
        range(3)]
    for day, matchups in matchups_by_day.items():
        phase = phase_for_day(day)
        games_at_phase[phase] += 1

        for (a, b) in matchups:
            forward = m.add_var(var_type=mip.BINARY)
            backward = m.add_var(var_type=mip.BINARY)
            vars_by_day[day].append((forward, backward))

            m += forward + backward == 1

            # The forward-facing game counts for a and against b, and
            # the backward-facing game is the reverse
            team_total_sums[a] = team_total_sums[a] + forward - backward
            team_total_sums[b] = team_total_sums[b] + backward - forward

            # Same as the total, but also indexed by phase
            team_phase_sums[phase][a] = \
                team_phase_sums[phase][a] + forward - backward
            team_phase_sums[phase][b] = \
                team_phase_sums[phase][b] + backward - forward

            team_matchup_sums[a][b] = \
                team_matchup_sums[a][b] + forward - backward
            team_matchup_sums[b][a] = \
                team_matchup_sums[b][a] + backward - forward

            team_phase_matchup_sums[phase][a][b] = \
                team_phase_matchup_sums[phase][a][b] + forward - backward
            team_phase_matchup_sums[phase][b][a] = \
                team_phase_matchup_sums[phase][b][a] + backward - forward

    for summed in team_total_sums.values():
        m += summed <= 1
        m += summed >= -1

    for phase_summed in team_phase_sums:
        for summed in phase_summed.values():
            if summed is not 0:  # Do not use == here, it is overridden
                m += summed <= 1
                m += summed >= -1

    for matchup_summed in team_matchup_sums.values():
        for summed in matchup_summed.values():
            if summed is not 0:  # Do not use == here, it is overridden
                m += summed <= 1
                m += summed >= -1

    for phase_summed in team_phase_matchup_sums:
        for matchup_summed in phase_summed.values():
            for summed in matchup_summed.values():
                if summed is not 0:  # Do not use == here, it is overridden
                    m += summed <= 1
                    m += summed >= -1

    status = m.optimize()
    assert (status == mip.OptimizationStatus.OPTIMAL or
            status == mip.OptimizationStatus.FEASIBLE)

    team_to_num = {team_id: i for i, team_id in enumerate(all_teams)}
    schedule = defaultdict(lambda: [])
    for day in matchups_by_day.keys():
        for teams, variables in zip(matchups_by_day[day], vars_by_day[day]):
            if variables[0].x > 0:
                assert variables[1].x == 0
                schedule[day].append((team_to_num[teams[0]],
                                      team_to_num[teams[1]]))
            else:
                assert variables[1].x > 0
                schedule[day].append((team_to_num[teams[1]],
                                      team_to_num[teams[0]]))

    return schedule
