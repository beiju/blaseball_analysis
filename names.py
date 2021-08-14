import json
from math import floor, ceil
from typing import List

import requests
from tqdm import tqdm

from rng_matcher import rng_walker_for_birth, RngMatcherError

replacements = {'Sixpack Dogwalker', 'Greer Gwiffin', 'Case Sports',
                'Yrjö Kerfuffle', 'Cannonball Sports', 'Jomgy Rolsenthal',
                'Bonk Jokes', 'Rai Spliff', 'Steph Weeks', 'Tiana Cash',
                "Rylan O'Lantern", 'Allan Kranch', 'Frasier Shmurmgle',
                'Scoobert Toast', 'Evelton McBlase', 'Eduardo Woodman',
                'Usurper Violet', 'Alx Keming', 'Zippy DeShields',
                'Khulan Sagaba', 'Goobie Ballson', 'Lachlan Shelton',
                'Zeruel Kramer', 'Frankie Incarnate', 'Lenjamin Zhuge',
                'Kennedy Meh', 'Ryuji Ngozi', 'Steals Mondegreen',
                'Kurt Crueller', 'Sebastian Woodman', 'Sandie Turner',
                'Inez Owens', 'Salih Ultrabass', 'Loubert Ji-Eun',
                'Juice Collins', 'Emmett Owens', 'Charlatan Seabright',
                'Atlas Jonbois', 'Norris Firestar', 'Alston Cerveza',
                'Clarinet McCormick', 'Kline Greenlemon', 'Hiroto Cerna',
                'Quack Enjoyable', 'Nandy Fantastic', 'Blood Hamburger',
                'Commissioner Vapor', 'Sutton Bishop', 'Jaxon Buckley',
                'Geepa Beanpot', 'Lancelot Kane', 'Stew Briggs',
                'Scarlet Caster', 'Will Statter Jr', "Gunther O'Brian",
                'Roscoe Sundae', 'Pannonica Oko', 'Lenny Spruce',
                'Sixpack Santiago', 'Trinity Smaht', 'Alexander Horne',
                'Donna Milicic', 'Lucien Patchwork', 'Finn James',
                'Backpatch Rolsenthal', 'Adelaide Judochop', 'Yulia Skitter',
                'Nickname Yamashita', 'Dudley Mueller', 'Anathema Elemefayo',
                'Tai Beanbag', 'Jasper Blather', 'Combs Estes',
                'Vernon Shotwell', 'Gallup Crueller', 'Millipede Aqualuft',
                'Pudge Nakatamo', 'Bobbin Moss', 'Jon Halifax',
                'Dervin Gorczyca', 'Paula Turnip', 'Orion Ultrabass',
                'August Sky', 'Clove Ji-Eun', 'Kaj Statter Jr',
                'Gloria Bugsnax', 'Yusef Puddles', 'Kevelyn Jeff',
                'Jon Tumblehome', 'Trinity Roche', 'Beans McBlase',
                'Sandford Garner', 'Ziwa Mueller', 'Caligula Lotus',
                'Kiki Familia', 'Riley Firewall', 'Ruffian Scrobbles',
                'Hotbox Sato', 'Rat Batson', 'Marion Shriffle', 'Annie Roland',
                'Basilio Fig', 'Vito Kravitz', 'Silvaire Roadhouse',
                'Scouse Bedazzle', 'Fitzgerald Blackburn', 'Mummy Melcon',
                'Carmelo Plums', 'Gita Sparrow', 'Bennett Bluesky',
                'Mikan Hammer', 'Hendricks Rangel', 'Randy Dennis',
                'Paula Mason', 'Holden Stanton', 'Felix Garbage', 'Marco Stink',
                'Halexandrey Walton', 'Collins Melon', 'Cory Twelve',
                'Simon Haley', 'Thomas Kirby', 'York Silk', 'Nic Winkler',
                'Hendricks Richardson', 'Murray Pony', 'Dan Holloway'}


def main():
    # replacement_names = set(
    #     re.search('[Rr]eplaced by (.*?)(:?$| The Instability|\.)', line).group(
    #         1) for
    #     line in replacements.splitlines() if 'incinerated instead!' not in line)
    first_name_pool, first_name_pool_size = prehistory_pool_size('first_names')
    last_name_pool, last_name_pool_size = prehistory_pool_size('last_names')

    try:
        with open('players_baby_grand_oldest.json', 'r') as f:
            players_oldest = json.load(f)
    except FileNotFoundError:
        with open('players_baby_grand.json', 'r') as f:
            players: List[dict] = json.load(f)['items']

        players_oldest = [player_oldest_record(p) for p in players]
        players_oldest.sort(key=lambda item: item['validFrom'])

        with open('players_baby_grand_oldest.json', 'w') as f:
            json.dump(players_oldest, f)

    max_player_name_len = max(len(p['data']['name']) for p in players_oldest)
    for player in tqdm([p for p in players_oldest if
                        p['validFrom'] != '2020-07-29T08:12:22.438Z']):
        name = player['data']['name']

        if name not in replacements:
            continue

        try:
            walker = rng_walker_for_birth(player['data'])
        except RngMatcherError as e:
            pass
            # print(player['data']['name'], "could not be derived:", e)
        else:
            assert player['data']['thwackability'] == walker[0]
            lowest_roll, lowest_roll_i = min((walker[i], i) for i in range(200))
            spaces = " " * (max_player_name_len - len(name))
            unsynced = ""
            if not walker.synced:
                unsynced = " (not synced)"
            at_3 = walker[3]
            at_4 = walker[4]
            at_5 = walker[5]
            at_98 = walker[98]
            lowest_of_knowns, lowest_of_knowns_i = min([(at_3, 3), (at_4, 4), (at_5, 5), (at_98, 98)])
            tqdm.write(f"{spaces}{name} lowest of 3, 4, 5, 98: {lowest_of_knowns:.5f} at {lowest_of_knowns_i}, lowest overall: {lowest_roll:.5f} at {lowest_roll_i}{unsynced}")


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
