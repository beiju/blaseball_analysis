import requests
from tqdm import tqdm

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


def main():
    players_oldest = load_players_oldest_records(exclude_initial=True)

    max_player_name_len = max(len(p['data']['name']) for p in players_oldest)
    for player in tqdm(players_oldest):
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
            lowest_of_knowns, lowest_of_knowns_i = min(
                [(at_3, 3), (at_4, 4), (at_5, 5), (at_98, 98)])
            tqdm.write(
                f"{spaces}{name} lowest of 3, 4, 5, 98: {lowest_of_knowns:.5f} at {lowest_of_knowns_i}, lowest overall: {lowest_roll:.5f} at {lowest_roll_i}{unsynced}")


if __name__ == '__main__':
    main()