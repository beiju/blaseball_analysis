import copy
import math

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError

s1_steaks_hitters = {
    "17397256-c28c-4cad-85f2-a21768c66e67",
    "c83f0fe0-44d1-4342-81e8-944bb38f8e23",
    "c83a13f6-ee66-4b1c-9747-faa67395a6f1",
    "81a0889a-4606-4f49-b419-866b57331383",
    "14d88771-7a96-48aa-ba59-07bae1733e96",
    "82d1b7b4-ce00-4536-8631-a025f05150ce",
    "05bd08d5-7d9f-450b-abfa-1788b8ee8b91",
    "083d09d4-7ed3-4100-b021-8fbe30dd43e8",
    "76c4853b-7fbc-4688-8cda-c5b8de1724e4",
}

hitting_stats_s1_boost = [
    "buoyancy",
    "patheticism",
    "musclitude",
    "divinity",
    "moxie",
    "thwackability",
    "martyrdom",
    "tragicness",
]


def adjust(player_full):
    player_full = copy.copy(player_full)
    player = player_full['data']
    if player_full['entityId'] in s1_steaks_hitters:
        for attr in hitting_stats_s1_boost:
            if attr in {'patheticism', 'tragicness'}:
                player[attr] += 0.1
                player[attr] = min(player[attr], 0.99)
            else:
                player[attr] -= 0.1

    return player_full


def main():
    players_oldest = load_players_oldest_records()

    total_found = 0
    total_synced = 0
    for player in players_oldest:
        name = player['data']['name']

        adjusted_player = adjust(player)

        try:
            walkers = list(rng_walker_for_birth(adjusted_player))
        except RngMatcherError as e:
            print(f"{name} could not be derived: {e}")
        else:
            print(f"{name} found")
            total_found += 1
            for walker in walkers:
                assert abs(player['data']['thwackability'] - walker[0]) < 1e-12

                if walker.synced:
                    # If synced then there's only one walker so this inside a
                    # loop should be fine.
                    total_synced += 1

    print(f"{len(players_oldest)} exist, found states for {total_found}, "
          f"found fully-specified states for {total_synced}")


def find_paws(players_oldest):
    ruff = \
        [p for p in players_oldest if p['data']['name'] == 'Ruffian Scrobbles'][
            0]
    milli = [p for p in players_oldest if p['data']['name'] == 'Milli Kalette'][
        0]
    walkers = list(rng_walker_for_birth(ruff))
    for walker in walkers:
        for i in range(100000):
            if validate(milli['data'], walker, i):
                breakpoint()

            if i % 1000 == 0:
                print("Checked", i // 1000, "thousand values")


def validate(player, walker, i):
    if player['soul'] != int(walker[-i] * 8 + 2):
        return False

    if 'peanutAllergy' in player:
        if player['peanutAllergy'] != (walker[-i + 1] < 0.5):
            return False

    if 'fate' in player:
        if player['fate'] != int(walker[-i + 2] * 100):
            return False

    # Skip pregame ritual
    if player['blood'] != int(walker[-i + 4] * 13):
        return False

    if player['coffee'] != int(walker[-i - 5] * 13):
        return False

    return True


if __name__ == '__main__':
    main()
