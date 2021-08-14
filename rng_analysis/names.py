from math import floor, ceil

import requests
from tqdm import tqdm

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError


def main():
    first_name_pool, first_name_pool_size = prehistory_pool_size('first_names')
    last_name_pool, last_name_pool_size = prehistory_pool_size('last_names')

    players_oldest = load_players_oldest_records(exclude_initial=True)

    max_player_name_len = max(len(p['data']['name']) for p in players_oldest)
    for player in tqdm(players_oldest):
        name = player['data']['name']

        try:
            walker = rng_walker_for_birth(player['data'])
        except RngMatcherError as e:
            pass
            # print(player['data']['name'], "could not be derived:", e)
        else:
            assert player['data']['thwackability'] == walker[0]
            l


def player_oldest_record(player):
    return requests.get(
        f"https://api.sibr.dev/chronicler/v2/versions?type=player&id={player['data']['id']}&sort=asc&count=1").json()[
        'items'][0]


def prehistory_pool_size(filename):
    pairs = []
    with open(f'/home/will/Downloads/{filename}.txt', 'r', encoding='utf-8',
              errors='ignore') as f:
        for line in f.readlines():
            (value, name) = line.split(maxsplit=1)
            pairs.append((float(value), name))

    pairs.sort()

    buckets = []
    names_in_order = []
    prev_name = None
    for value, name in pairs:
        if name != prev_name:
            buckets.append([])
            prev_name = name

        names_in_order.append(name)
        buckets[-1].append(float(value))

    bucket_size_lower_bound, bucket_size_lower_bound_name_index = max(
        (max(values) - min(values), i) for i, values in enumerate(buckets)
    )
    bucket_size_lower_bound_name = names_in_order[
        bucket_size_lower_bound_name_index]
    bucket_size_upper_bound, bucket_size_upper_bound_name_index = min(
        (min(buckets[i + 2]) - max(values), i) for i, values in
        enumerate(buckets[:-2])
    )
    bucket_size_upper_bound_name = names_in_order[
        bucket_size_upper_bound_name_index]

    if bucket_size_lower_bound == 0:
        bucket_size_lower_bound = 1 / 10000
        print("Couldn't find upper bound, assuming 10k")
    bounds = (1 / bucket_size_upper_bound, 1 / bucket_size_lower_bound)

    actual_size = None
    actual_namelist = None
    for size in range(floor(bounds[0]), ceil(bounds[1])):
        potential_namelist = {}

        conflict = False
        for value, name in pairs:
            position = floor(value * size)
            if position in potential_namelist and potential_namelist[
                position] != name:
                conflict = True
                break

            potential_namelist[position] = name

        if not conflict:
            assert actual_size is None
            actual_size = size
            actual_namelist = potential_namelist

    assert actual_size is not None
    assert actual_namelist is not None

    return actual_size, actual_namelist


if __name__ == '__main__':
    main()
