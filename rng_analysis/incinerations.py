from itertools import cycle, islice

from rng_analysis.util import load_players_oldest_records
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


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


def main():
    players_oldest = load_players_oldest_records(exclude_initial=True)

    total_synced = 0
    max_player_name_len = max(len(p['data']['name']) for p in players_oldest)
    for player in players_oldest:
        name = player['data']['name']

        if name not in replacements:
            continue

        try:
            walkers = rng_walker_for_birth(player)
        except RngMatcherError as e:
            print(f"{player['data']['name']} could not be derived: {e}")
        else:
            spaces = " " * (max_player_name_len - len(name))
            lowest_lowest_of_knowns = None
            lowest_lowest_of_knowns_i = None
            lowest_lowest_roll = None
            lowest_lowest_roll_i = None

            synced = ""
            for walker in walkers:
                assert player['data']['thwackability'] == walker[0]
                lowest_roll, lowest_roll_i = min(
                    (walker[-i], i) for i in range(200))
                if not walker.synced:
                    synced = " (inferred)"
                else:
                    total_synced += 1
                at_99 = walker[-99]
                at_98 = walker[-98]
                at_5 = walker[-5]
                at_4 = walker[-4]
                at_3 = walker[-3]

                lowest_of_knowns, lowest_of_knowns_i = min(
                    [(at_3, 3), (at_4, 4), (at_5, 5), (at_98, 98), (at_99, 99)])

                if lowest_lowest_of_knowns is None or \
                        lowest_of_knowns < lowest_lowest_of_knowns:
                    lowest_lowest_of_knowns = lowest_of_knowns
                    lowest_lowest_of_knowns_i = lowest_of_knowns_i
                    lowest_lowest_roll = lowest_roll
                    lowest_lowest_roll_i = lowest_roll_i

            print(f"{spaces}{name} lowest of 3, 4, 5, 98, 99: "
                  f"{lowest_lowest_of_knowns:.5f} at "
                  f"{lowest_lowest_of_knowns_i:>2}, lowest within 200: "
                  f"{lowest_lowest_roll:.5f} at "
                  f"{lowest_lowest_roll_i:>2}{synced}")

    print(total_synced)


def connect_replacements(players_oldest):
    plums = None
    kiki = None
    fraiser = None
    quack = None
    beans = None
    cory = None
    melon = None
    for player in players_oldest:
        if player['data']['name'] == 'Carmelo Plums':
            plums = player
        if player['data']['name'] == 'Kiki Familia':
            kiki = player
        if player['data']['name'] == 'Frasier Shmurmgle':
            fraiser = player
        if player['data']['name'] == 'Quack Enjoyable':
            quack = player
        if player['data']['name'] == 'Beans McBlase':
            beans = player
        if player['data']['name'] == 'Cory Twelve':
            cory = player
        if player['data']['name'] == 'Collins Melon':
            melon = player
        if player['data']['name'] == 'Trinity Smaht':
            trin = player
        if player['data']['name'] == 'Jon Halifax':
            jon = player
        if player['data']['name'] == 'Zeruel Kramer':
            ze = player
        if player['data']['name'] == 'Trinity Roche':
            trint = player
        if player['data']['name'] == 'Morrow Doyle':
            morrow = player
    walkers = list(rng_walker_for_birth(trint))
    for walker in walkers:
        walker[0]
        for i, num in enumerate(walker.cached_generator):
            if num == ze['data']['thwackability']:
                print("Found ze from trin in", i, "rolls")
                return

            if i % 1000 == 0:
                print("Tested", i, "rolls")


if __name__ == '__main__':
    main()
