import copy
import math
from itertools import chain

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError

explained_failures = {
    # '083d09d4-7ed3-4100-b021-8fbe30dd43e8': "Maxed in s1 election"
}

clones = {
    "2c4b2a6d-9961-4e40-882c-a338f4e72117",
    "57290370-6723-4d33-929e-b4fc190e6a9a",
    "c3ae0552-59e8-44bf-ba66-48a96aff35e6",
}

jaylen_hotdogfingers_memorial_cinnamon_peanut_allergy_and_fate_problems_list = {
    "04e14d7b-5021-4250-a3cd-932ba8e0a889",
    "31f83a89-44e3-47b7-8c9e-0dfdcd8bd30f",
    "8ba7e1ff-4c6d-4963-8e0f-7096d14f4b12",
    "a071a713-a6a1-4b4c-bb3f-45d9fba7a08c",
    "ef32eb48-4866-49d0-ae58-9c4982e01142",
}

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

s1_crabs_hitters = {
    "1a93a2d2-b5b6-479b-a595-703e4a2f3885",
    "c675fcdf-6117-49a6-ac32-99a89a3a88aa",
    "7dcf6902-632f-48c5-936a-7cf88802b93a",
    "84a2b5f6-4955-4007-9299-3d35ae7135d3",
    "f8c20693-f439-4a29-a421-05ed92749f10",
    "4ecee7be-93e4-4f04-b114-6b333e0e6408",
    "d35ccee1-9559-49a1-aaa4-7809f7b5c46e",
    "d6c69d2d-9344-4b19-85a4-6cfcbaead5d2",
    "a071a713-a6a1-4b4c-bb3f-45d9fba7a08c",
}

s1_crabs_pitchers = {
    "97dfc1f6-ac94-4cdc-b0d5-1cb9f8984aa5",
    "f2a27a7e-bf04-4d31-86f5-16bfa3addbe7",
    "1ffb1153-909d-44c7-9df1-6ed3a9a45bbd",
    "d0d7b8fe-bad8-481f-978e-cb659304ed49",
    "f70dd57b-55c4-4a62-a5ea-7cc4bf9d8ac1",
}

s1_tigers_pitchers = {
    "9abe02fb-2b5a-432f-b0af-176be6bd62cf",
    "b082ca6e-eb11-4eab-8d6a-30f8be522ec4",
    "2720559e-9173-4042-aaa0-d3852b72ab2e",
    "7aeb8e0b-f6fb-4a9e-bba2-335dada5f0a3",
    "b3e512df-c411-4100-9544-0ceadddb28cf"
}

s1_hitting_rerolls = {
    "5ff66eae-7111-4e3b-a9b8-a9579165b0a5",
    "2e86de11-a2dd-4b28-b5fe-f4d0c38cd20b",
    "80de2b05-e0d4-4d33-9297-9951b2b5c950",
    "70ccff1e-6b53-40e2-8844-0a28621cb33e"
}

s1_pitching_rerolls = {
    "f2a27a7e-bf04-4d31-86f5-16bfa3addbe7"  # hi winnie :)
}

hitting_stats = ["buoyancy", "patheticism", "musclitude", "divinity",
                 "moxie", "thwackability", "martyrdom", "tragicness"]

baserunning_stats = ["baseThirst", "laserlikeness", "groundFriction",
                     "continuation", "indulgence"]

pitching_stats = ["shakespearianism", "suppression", "unthwackability",
                  "coldness", "overpowerment", "ruthlessness", ]

defense_stats = ["omniscience", "tenaciousness", "watchfulness",
                 "anticapitalism", "chasiness"]


def boost(player, stats, amount):
    for attr in stats:
        if attr == 'tragicness' and (player[attr] == 0.1 or player[attr] == 0):
            continue
        if player[attr] == 0.99 or player[attr] == 0.01:
            # Then it was floored/capped, and there's no way to get what it was
            # before
            player[attr] = None
        elif attr in {'patheticism', 'tragicness'}:
            player[attr] += amount
        else:
            player[attr] -= amount


def adjust(player_full):
    player_full = copy.copy(player_full)
    player = player_full['data']
    if player_full['entityId'] in s1_steaks_hitters:
        boost(player, hitting_stats, 0.1)

    if player_full['entityId'] in s1_crabs_hitters:
        boost(player, hitting_stats, 0.06)
        boost(player, baserunning_stats, 0.06)
        boost(player, defense_stats, 0.06)

    if player_full['entityId'] in s1_crabs_pitchers:
        boost(player, pitching_stats, 0.06)
        boost(player, defense_stats, 0.06)

    if player_full['entityId'] in s1_tigers_pitchers:
        boost(player, pitching_stats, 0.1)

    if player_full['entityId'] in s1_hitting_rerolls:
        mark_unknown(player, hitting_stats)

    if player_full['entityId'] in s1_pitching_rerolls:
        mark_unknown(player, pitching_stats)

    # JT, hitting max
    if player_full['entityId'] == '083d09d4-7ed3-4100-b021-8fbe30dd43e8':
        mark_unknown(player, hitting_stats)

    # Dot, pitching max
    if player_full['entityId'] == '338694b7-6256-4724-86b6-3884299a5d9e':
        mark_unknown(player, pitching_stats)

    # These players was born without cinnamon, then died before being recorded
    # by chron, then assigned cinnamon while dead, then made visible to chron.
    # As a result their first recorded player objects have cinnamon, but their
    # generations don't. We need to delete cinnamon from their player objects
    # for them to be matched up.
    if player_full[
        'entityId'] in jaylen_hotdogfingers_memorial_cinnamon_peanut_allergy_and_fate_problems_list:
        del player['cinnamon']
        del player['peanutAllergy']
        del player['fate']

    # SCORES was generated as part of an election and boosted during the same
    # election
    if player_full['entityId'] == "be18d363-752d-4e4a-b06b-1a7e4641400b":
        boost(player, chain(hitting_stats, baserunning_stats,
                            pitching_stats, defense_stats), 0.02)

    return player_full


def mark_unknown(player, stats):
    for attr in stats:
        player[attr] = None


def main():
    players_oldest = load_players_oldest_records(exclude_initial=False)

    total_found = 0
    total_synced = 0
    for player in players_oldest:
        name = player['data']['name']

        if player['entityId'] in clones:
            print(f"Not searching for clone {name}")
            continue

        if player['entityId'] in explained_failures:
            print(F"Expected failure: {name}. "
                  F"Reason: {explained_failures[player['entityId']]}")
            continue

        adjusted_player = adjust(player)

        try:
            walkers = list(rng_walker_for_birth(adjusted_player))
        except RngMatcherError as e:
            print(f"{name} could not be derived: {e}")
        else:
            print(f"{name} found")
            total_found += 1
            for walker in walkers:
                # If adjusted thwackability is None it means the player's thwack
                # was rerolled before the first value chronicler captured, and
                # we can't use it to verify
                if adjusted_player['data']['thwackability'] is not None:
                    assert abs(
                        player['data']['thwackability'] - walker[0]) < 1e-12

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
