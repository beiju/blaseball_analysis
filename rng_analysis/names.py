from math import floor, ceil

from tqdm import tqdm
import matplotlib.pyplot as plt

from rng_analysis.util import load_players_oldest_records
from rng_matcher import rng_walker_for_birth, RngMatcherError


def main():
    first_name_pool_size, first_name_pool = s1_pool_size('first_names')
    last_name_pool_size, last_name_pool = s1_pool_size('last_names')

    players_oldest = load_players_oldest_records(exclude_initial=True)

    prev_first = first_name_pool_size
    prev_last = last_name_pool_size
    first_sizes = [first_name_pool_size]
    last_sizes = [last_name_pool_size]
    for player in tqdm(players_oldest):
        name = player['data']['name']

        first_name_map = {name: pos for pos, name in first_name_pool.items()}
        last_name_map = {name: pos for pos, name in last_name_pool.items()}

        try:
            walker = rng_walker_for_birth(player['data'])
        except RngMatcherError as e:
            pass
            # print(player['data']['name'], "could not be derived:", e)
        else:
            if not walker.synced:
                continue

            assert player['data']['thwackability'] == walker[0]
            first_name_val = walker[2]
            last_name_val = walker[1]

            segments = name.split()
            if len(segments) != 2:
                # Uhhhhhhhhhhhhhh
                continue

            actual_first, actual_last = segments
            try:
                first_pos = first_name_map[actual_first]
            except KeyError:
                first_sizes.append(float('nan'))
            else:
                first_size = first_pos / first_name_val
                first_sizes.append(first_size)

                if first_size < first_name_pool_size:
                    breakpoint()
                prev_first = first_size

            if actual_last not in ['Melon']:
                try:
                    last_pos = last_name_map[actual_last]
                except KeyError:
                    last_sizes.append(float('nan'))
                else:
                    last_size = last_pos / last_name_val
                    last_sizes.append(last_size)

                    if last_size < last_name_pool_size:
                        breakpoint()
                    prev_last = last_size

            pass

    fig, (first_ax, last_ax) = plt.subplots(2)
    first_ax.scatter(range(len(first_sizes)), first_sizes)
    first_ax.set_title("First name pool size")
    last_ax.scatter(range(len(last_sizes)), last_sizes)
    last_ax.set_title("Last name pool size")

    plt.show()


def s1_pool_size(filename) -> (int, dict):
    pairs = []
    with open(f'/home/will/Downloads/{filename}.txt', 'r', encoding='utf-8',
              errors='ignore') as f:
        for line in f.readlines():
            (value, name) = line.split(maxsplit=1)
            name = name.replace('\n', '')
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
