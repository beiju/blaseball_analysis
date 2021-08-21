import json
import re
from collections import defaultdict
from itertools import chain

import matplotlib.pyplot as plt
from blaseball_mike import chronicler, models, utils

parties_json_name = "parties_data.json"

player_name_cache = {}


def main():
    try:
        with open(parties_json_name, "r") as f:
            data = json.load(f)
            parties_by_myst, parties_by_vibe = data["myst"], data["vibe"]
    except FileNotFoundError:
        parties_by_myst, parties_by_vibe = get_data_from_blaseball()
        with open(parties_json_name, "w") as f:
            json.dump({"myst": parties_by_myst, "vibe": parties_by_vibe}, f)

    for data, name in [(parties_by_myst, "Myst"), (parties_by_vibe, "Vibes")]:
        fig, ax = plt.subplots(1, 1, figsize=[8, 6])

        ax.hist(x=[float(k) for k in data.keys()], weights=data.values(), bins=10)
        ax.set_title(f"Parties by {name}")
        ax.set_ylabel("Number of parties")
        ax.set_xlabel(name)

    plt.tight_layout()
    plt.show()


def get_data_from_blaseball():
    parties_by_myst = defaultdict(lambda: 0)
    parties_by_vibe = defaultdict(lambda: 0)
    party_re = re.compile(r"(.*) is Partying!")
    for season in range(14, 20):
        print("Processing season", season)

        games_by_day = defaultdict(lambda: [])
        print("Querying games")
        for g in chronicler.get_games(season):
            games_by_day[g["data"]["day"]].append(g["data"])
        print("Crunching numbers")

        # Cache this season's players for lookup
        player_name_cache.clear()
        for player in models.Player.load_all_by_gameday(season, day=1).values():
            if player.name in player_name_cache:
                # Then there's multiple of them. Can't cache this way.
                player_name_cache[player.name] = None
            else:
                player_name_cache[player.name] = player

        for day in sorted(games_by_day.keys()):
            if day >= 99:
                # Don't process postseason games
                break
            games = games_by_day[day]

            assert len(games) == 12
            for game in games:
                for outcome in game["outcomes"]:
                    if (match := party_re.match(outcome)) is not None:
                        print("Finding", match.group(1))
                        player = find_player_in_game(match.group(1), game)

                        if player is not None:
                            parties_by_vibe[player.get_vibe(day + 1)] += 1

                        stadium = models.Stadium.load_by_gameday(
                            game["stadiumId"], season, day + 1)

                        parties_by_myst[stadium.mysticism] += 1
    return parties_by_myst, parties_by_vibe


def find_player_in_game(name, game):
    # First try them in the cache
    try:
        player = player_name_cache[name]
        if player is not None and (
                player.team_id == game["homeTeam"] or
                player.team_id == game["awayTeam"]):
            return player
    except KeyError:
        pass

    print("Falling back to day-specific search")

    found_player = None
    for team_id in (game["homeTeam"], game["awayTeam"]):
        team = models.Team.load_at_time(
            team_id,
            # load when next gameday starts, which should be
            # equivalent to when this gameday ends
            utils.get_gameday_start_time(game["season"] + 1, game["day"] + 2))

        for player in chain(team.lineup, team.rotation):
            if player.name == name:
                if found_player is None:
                    found_player = player
                else:
                    print("Found multiple players named", name)
                    return None

    if found_player is None:
        print("Couldn't find any players named", name)

    return found_player


if __name__ == '__main__':
    main()
