from math import floor, ceil


def main():

    pairs = []
    prev_value = None
    anteprev_value = None
    for filename in ['stuff', 'dropbears', 'frogs']:
        with open(f'/home/will/Downloads/{filename}.txt', 'r', encoding='utf-8',
                  errors='ignore') as f:
            for line in f.readlines():
                if filename == 'stuff':
                    (value, name) = line.split(maxsplit=1)
                else:
                    (value, _, _, name) = line.split(maxsplit=3)
                    name = name.replace('stat=', '')

                if '/thwackability' in name:
                    name = name.replace('/thwackability', '')
                    name = name.replace('\n', '')
                    assert prev_value is not None
                    assert anteprev_value is not None
                    pairs.append((float(prev_value), name))

                anteprev_value = prev_value
                prev_value = value

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
    bucket_size_lower_bound_name = names_in_order[bucket_size_lower_bound_name_index]
    bucket_size_upper_bound, bucket_size_upper_bound_name_index = min(
        (min(buckets[i + 2]) - max(values), i) for i, values in enumerate(buckets[:-2])
    )
    bucket_size_upper_bound_name = names_in_order[bucket_size_upper_bound_name_index]

    if bucket_size_lower_bound == 0:
        bucket_size_lower_bound = 1/10000
        print("Couldn't find upper bound, assuming 10k")
    bounds = (1 / bucket_size_upper_bound, 1 / bucket_size_lower_bound)
    print(bounds)

    for size in range(floor(bounds[0]), ceil(bounds[1])):
        potential_namelist = {}

        conflict = False
        for value, name in pairs:
            position = floor(value * size)
            if position in potential_namelist and potential_namelist[position] != name:
                conflict = True
                break

            potential_namelist[position] = name

        if not conflict:
            print("Possible size: ", size)

            # for i in range(size):
            #     if i in potential_namelist:
            #         print(i, potential_namelist[i])
            #     else:
            #         print(i, '-')


if __name__ == '__main__':
    main()
