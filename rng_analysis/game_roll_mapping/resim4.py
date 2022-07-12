import itertools
import math
from dataclasses import dataclass
from typing import List

import json
import os
import pandas as pd
import requests

from nd import rng


@dataclass
class RollLog:
    event_type: str
    roll: float
    passed: bool

    batter_name: str
    batter_buoyancy: float
    batter_divinity: float
    batter_martyrdom: float
    batter_moxie: float
    batter_musclitude: float
    batter_patheticism: float
    batter_thwackability: float
    batter_tragicness: float

    pitcher_name: str
    pitcher_ruthlessness: float
    pitcher_overpowerment: float
    pitcher_unthwackability: float
    pitcher_shakespearianism: float
    pitcher_suppression: float
    pitcher_coldness: float

    # on a lark
    pitcher_chasiness: float

    defense_avg_anticapitalism: float
    defense_avg_chasiness: float
    defense_avg_omniscience: float
    defense_avg_tenaciousness: float
    defense_avg_watchfulness: float

    ballpark_grandiosity: float
    ballpark_fortification: float
    ballpark_obtuseness: float
    ballpark_ominousness: float
    ballpark_inconvenience: float
    ballpark_viscosity: float
    ballpark_forwardness: float
    ballpark_mysticism: float
    ballpark_elongation: float

    batting_team_hype: float
    pitching_team_hype: float

    batter_vibes: float
    pitcher_vibes: float

strike_roll_log: List[RollLog] = []

cache = {}
def get_cached(key, url):
    key = key.replace(":", "_")
    if key in cache:
        return cache[key]

    path = os.path.join("cache", key + ".json")
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = requests.get(url).json()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    cache[key] = data
    return data


cached_plays = {}
def get_game(game_id):
    resp = get_cached("game_updates_{}".format(game_id), "https://api.sibr.dev/chronicler/v1/games/updates?count=2000&game={}&started=true".format(game_id))
    return resp["data"]

def get_game_update(game_id, play):
    if (game_id, play + 1) in cached_plays:
        return cached_plays[(game_id, play + 1)]

    game_data = get_game(game_id)
    for update in game_data:
        cached_plays[(game_id, update["data"]["playCount"])] = update["data"]

    return cached_plays.get((game_id, play + 1))

def get_team_states(timestamp):
    # Hack around timing problems
    if timestamp == '2021-05-22T15:26:45.984Z':
        timestamp = '2021-05-22T15:27:45.984Z'
    key = "teams_at_{}".format(timestamp)
    resp = get_cached(key, "https://api.sibr.dev/chronicler/v2/entities?type=team&at={}&count=1000".format(timestamp))
    return {e["entityId"]: e["data"] for e in resp["items"]}

def get_player_states(timestamp):
    key = "players_at_{}".format(timestamp)
    resp = get_cached(key, "https://api.sibr.dev/chronicler/v2/entities?type=player&at={}&count=1000".format(timestamp))
    return {e["entityId"]: e["data"] for e in resp["items"]}

def get_stadium_states(timestamp):
    key = "stadiums_at_{}".format(timestamp)
    resp = get_cached(key, "https://api.sibr.dev/chronicler/v2/entities?type=stadium&at={}&count=1000".format(timestamp))
    return {e["entityId"]: e["data"] for e in resp["items"]}

def get_feed_between(start, end):
    key = "feed_range_{}_{}".format(start, end)
    resp = get_cached(key, "https://api.sibr.dev/eventually/v2/events?after={}&before={}&sortorder=asc&limit=10000".format(start, end))
    return resp

def get_game_feed(game_id):
    key = "feed_game_{}".format(game_id)
    resp = get_cached(key, "https://api.blaseball.com/database/feed/game?id={}&sort=1".format(game_id))
    return resp

def get_mods(player):
    return player["permAttr"] + player["seasAttr"] + player["weekAttr"] + player["gameAttr"] + player.get("itemAttr", [])

def advance_bases(occupied, amount, up_to=4):
    occupied = [b+(amount if b < up_to else 0) for b in occupied]
    return [b for b in occupied if b < 3]

def make_base_map(update):
    bases = {}
    for i, pos in enumerate(update["basesOccupied"]):
        bases[pos] = update["baseRunners"][i]
    return bases

def force_advance(bases, start_at=0):
    new_bases = {}
    for i in range(start_at, 5):
        if i in bases:
            new_bases[i+1] = bases[i]
    return new_bases

def calculate_advances(bases_before, bases_after, bases_hit):
    # this code sucks so much. i hate runner advances. they're nasty
    # (and i'm not even really using it)
    bases = dict(bases_before)
    for i in range(bases_hit):
        bases = force_advance(bases, i)

    if bases_hit > 0:
        # ignore the batter
        for i in range(bases_hit):
            if i in bases_after:
                del bases_after[i]
        # and anyone past home. todo for fifth base lmao
        for base in range(3, 6):
            if base in bases:
                del bases[base]

    third_scored = len(bases_after) < len(bases)

    rolls = []
    occupied = sorted(bases.keys(), reverse=True)
    for runner in occupied:
        player = bases[runner]

        is_eligible = runner+1 not in bases
        if is_eligible:
            if runner == 2:
                did_advance = third_scored 
            else:
                did_advance = runner+1 in bases_after

            rolls.append((player, runner, did_advance))
            if did_advance:
                bases[runner+1] = bases[runner]
                del bases[runner]
    
    return rolls

def get_base_stolen(evt):
    desc = evt["description"]
    if "caught stealing" not in desc and "steals" not in desc:
        return -1

    if " second base" in desc:
        return 1
    if " third base" in desc:
        return 2
    if " fourth base" in desc:
        return 3
    return -1

# r = rng.Rng((790234539889214562, 14669156679034209477), 37) # s15 d82
# r = rng.Rng((737438775242349698, 12659490749958512437), 34) # s15 d83
# r = rng.Rng((11494868936943868267, 12502013663339465217), 16) # s16 d62
# r = rng.Rng((32620635765425914, 14279845229920010793), 47) # s19 d117
# r = rng.Rng((7899190525681891322, 8317887830822397138), 0) # s19 d117 later
# r = rng.Rng((465289181973838067, 3894280709857786711), 52) # s20 d84
# r = rng.Rng((60387313066966576, 7846820719416832276), 7) # s18 d32
# r = rng.Rng((188808254737127897, 13838365250427127983), 40) # s17 d92
# r = rng.Rng((2069524830621846891, 18003550220282697058), 61) # s17 d95
# r = rng.Rng((928416491203753528, 10350433993036381887), 20) # s17 d99
# r = rng.Rng((12683473301718976932, 5919031430033858668), 41) # s18 d51
# r = rng.Rng((636277877949988771, 3881154616169282314), 39) # s19 d82
r = rng.Rng((530316401040218212, 2247554972408709593), 11) # s19 d108 (original offset was 10 but this fixes stuff?)
# r = rng.Rng((613184461950222513, 10038836234213281742), 27) # s19 d100
# r = rng.Rng((522387208750378249, 13668660566350785158), 43) # s19 d105
# r = rng.Rng((936786078422383288, 10820197941868927543), 39) # s19 d102
# r = rng.Rng((85494335616218333, 7724238040931076749), 0) # s14 d86
# r = rng.Rng((2650715360711910019, 17245520577082755476), 17)
# r = rng.Rng((1316743807472851669, 17772626344277621807), 49) # s14 d92
# r = rng.Rng((16943380630585140239, 11517173126754224871), 12) # s15 d109
# r = rng.Rng((868006547431101664, 11091279837865964336), 43) # s16 d36
# r = rng.Rng((15890928721722172301, 8423737649996255823), 17) # s16 d89
# r = rng.Rng((417042252713188880, 1562738339095492067), 33) # s16 d96
# r = rng.Rng((736756854816003500, 8529369898167953346), 23) # s16 d93
# r = rng.Rng((736756854816003500, 8529369898167953346), 23) # s16 d93
# r = rng.Rng((676118450426903180, 6352083664653818018), 13) # s15 d89
# r = rng.Rng((13057216834274731221, 13021821994170632805), 63) # s15 d101
# r = rng.Rng((10191579601830159046, 6807026445923622412), 41) # s15 d104
# r = rng.Rng((16300910589699054409, 765138142953410791), 52) # s15 d39
r.step(-9)

def try_damage(player):
    if "items" not in player:
        return False

    mods = get_mods(player)
    if "CAREFUL" in mods:
        print("careful, not damaging item")
        return False

    # if len(player["items"]) == 0:
        # need a better way to check for pre-s16 so i just comment this out lol
        # return False

    healths = [i["health"] for i in player["items"]]
    print("item: {} {}".format(player["name"], healths))

    # i had a bunch of code here to check health but it seems like none of it is necessary so
    damage_roll = r.next()
    print("item damage", damage_roll)
    
    # known success: 0.00021365522484551036
    # known failure: 0.0009537498046980897
    if damage_roll < 0.00025:
        print("!!! successful damage, roll for item?", r.next())

    return False

# min_stamp = "2021-05-23T00:17:09.809Z"
# max_stamp = "2021-05-23T00:27:55.616257Z"
# min_stamp, max_stamp = ("2021-05-23T00:01:00.809Z", "2021-05-23T00:29:55.616257Z") # s19 d117
# min_stamp, max_stamp = ("2021-05-23T00:27:05.809Z", "2021-05-23T00:30:55.616257Z") # s19 d117 later
# min_stamp, max_stamp = ("2021-03-19T12:38:03.293Z", "2021-03-19T12:50:03.293Z") # s14 d92
# min_stamp, max_stamp = ("2021-04-07T06:31:39.431Z", "2021-04-07T06:34:41.431Z") # s15 d39
# min_stamp, max_stamp = ("2021-04-09T09:32:57.120Z", "2021-04-09T09:35:09.120Z") # s15 d89
# min_stamp, max_stamp = ("2021-04-09T23:25:37Z", "2021-04-09T23:30:44Z") # s15 d101
# min_stamp, max_stamp = ("2021-04-10T02:28:50.307Z", "2021-04-10T02:35:53.307Z") # s15 d104
# min_stamp, max_stamp = ("2021-04-16T11:35:38.169Z", "2021-04-16T11:39:40.169Z") # s16 d89
# min_stamp, max_stamp = ("2021-04-16T18:28:25.094Z", "2021-04-16T18:35:27.094Z") # s16 d96
# min_stamp, max_stamp = ("2021-04-14T04:27:44.098Z", "2021-04-14T05:10:30.072Z") # s16 d36
# min_stamp, max_stamp = ("2021-04-16T15:31:52.587Z", "2021-04-16T15:35:56.587Z") # s16 d93
# min_stamp, max_stamp = ("2021-04-10T17:23:00.667Z", "2021-04-10T21:25:01.667Z") # s15 d109
# min_stamp, max_stamp = ("2021-06-18T04:39:23.809Z", "2021-06-18T04:43:09.809Z") # s20 d84
# min_stamp, max_stamp = ("2021-05-12T00:28:14.172Z", "2021-05-12T00:35:16.172Z") # s20 d84
# min_stamp, max_stamp = ("2021-03-19T06:35:08.525966Z", "2021-03-19T06:45:26.969973Z") # s14 d86
# min_stamp, max_stamp = ("2021-04-15T07:29:55.193Z", "2021-04-15T07:40:56.193Z") # s16 d62
# min_stamp, max_stamp = ("2021-04-09T02:32:30.909Z", "2021-04-09T02:40:30.909Z") # s16 d82
# min_stamp, max_stamp = ("2021-04-09T03:30:55.768Z", "2021-04-09T03:35:57.768Z") # s15 d83
# min_stamp, max_stamp = ("2021-04-23T12:43:47.668Z", "2021-04-23T12:47:50.668Z") # s17 d92
# min_stamp, max_stamp = ("2021-04-23T15:46:45.291Z", "2021-04-23T15:50:47.291Z") # s17 d95
# min_stamp, max_stamp = ("2021-04-23T19:32:02.539Z", "2021-04-23T19:35:04.539Z") # s17 d99
# min_stamp, max_stamp = ("2021-05-12T19:32:35.372783Z", "2021-05-12T19:50:43.372783Z") # s18 d51
# min_stamp, max_stamp = ("2021-05-21T02:34:20.217Z", "2021-05-21T02:40:23.217Z") # s19 d82
min_stamp, max_stamp = ("2021-05-22T15:26:45.984Z", "2021-05-23T00:35:48.984Z") # s19 d108
# min_stamp, max_stamp = ("2021-05-21T21:09:20.000Z", "2021-05-22T03:35:20.116Z") # s19 d100
# min_stamp, max_stamp = ("2021-05-22T02:13:50.500Z", "2021-05-22T03:03:20.116Z") # s19 d105
# min_stamp, max_stamp = ("2021-05-21T23:02:32.000Z", "2021-05-21T23:30:32.004Z") # s19 d102
# game_id = "6d5cadef-7192-42f1-a1df-3e61df152e1a" # s14 d86
# game_id = "a22b8277-bcac-456d-9d48-8aca72fedf3c" # s20 d84
# game_id = "f7ad7826-ca6e-49c2-818e-190408b046fe" # s19 d117
# game_id = "f85ba1ab-8163-40f5-bf99-ec1ef9fc183a" # s16 d62
# game_id = "819fcb8d-e4e2-4129-b05c-70ae436f4f86" # s16 d82
# game_id = "6d12517b-04e7-4344-a214-4bd642f234d5" # s16 d83
# game_id = "7cf6d0c5-2a3d-466e-aded-77f7e9b20ea1" # s14 d92
# game_id = "56239efb-de49-4a15-b376-9f535c34a7d4" # s15 d109
# game_id = "b6349183-2afc-4de1-89a2-519538a41c0f" # s16 d93
# game_id = "9e281f6c-01ff-42cc-8c8a-3ac6972086cc" # s16 d89
# game_id = "ae567408-7cb0-4523-aa86-9a12c1fa063c" # s16 d36
# game_id = "a78706e6-79dc-4d4c-85a6-4a7a333df5f2" # s15 d101
# game_id = "4e927f04-c58f-4657-99d3-c8a9597d4c77" # s15 d104
# game_id = "6bcc142b-0886-4dc5-8686-dcd63d7248df" # s15 d89
# game_id = "927dc1be-53c8-4a9f-a308-1b04692ecaf7" # s15 d39
# min_stamp, max_stamp = ("2021-05-20T07:41:13.809Z", "2021-05-20T07:47:09.809Z")

timestamp = min_stamp

teams = get_team_states(timestamp)
players = get_player_states(timestamp)
stadiums = get_stadium_states(timestamp)

events = get_feed_between(min_stamp, max_stamp)
fetched_for_days = set()


def calculate_vibes(player, day):
    frequency = 6 + round(10 * player['buoyancy'])
    phase = math.pi * ((2 / frequency) * day + 0.5)

    range = 0.5 * (player['pressurization'] + player['cinnamon'])
    return (range * math.sin(phase)) - (0.5 * player['pressurization']) + (0.5 * player['cinnamon'])

seen_mods = set()
def make_roll_log(event_type: str, roll: float, passed: bool):
    batter_multiplier = 1
    for mod in itertools.chain(batter_mods, batting_team_mods):
        seen_mods.add(mod)
        if mod == 'OVERPERFORMING':
            batter_multiplier += 0.2
        elif mod == 'UNDERPERFORMING':
            batter_multiplier -= 0.2
        elif mod == 'GROWTH':
            batter_multiplier += 0.05
        elif mod == 'HIGH_PRESSURE':
            # checks for flooding weather and baserunners
            if update["weather"] == 18 and len(update['baseRunners']) > 0:
                batter_multiplier += 0.25
        elif mod == 'TRAVELING':
            if update["topOfInning"]:
                batter_multiplier += 0.05

    pitcher_multiplier = 1
    for mod in itertools.chain(pitcher_mods, pitching_team_mods):
        seen_mods.add(mod)
        if mod == 'OVERPERFORMING':
            pitcher_multiplier += 0.2
        elif mod == 'UNDERPERFORMING':
            pitcher_multiplier -= 0.2
        elif mod == 'GROWTH':
            pitcher_multiplier += 0.05
        elif mod == 'TRAVELING':
            if not update["topOfInning"]:
                pitcher_multiplier += 0.05

    return RollLog(
        event_type=event_type,
        roll=roll,
        passed=passed,

        batter_name=batter["name"],
        batter_buoyancy=batter["buoyancy"] * batter_multiplier,
        batter_divinity=batter["divinity"] * batter_multiplier,
        batter_martyrdom=batter["martyrdom"] * batter_multiplier,
        batter_moxie=batter["moxie"] * batter_multiplier,
        batter_musclitude=batter["musclitude"] * batter_multiplier,
        batter_patheticism=batter["patheticism"] * batter_multiplier,
        batter_thwackability=batter["thwackability"] * batter_multiplier,
        batter_tragicness=batter["tragicness"] * batter_multiplier,

        pitcher_name=pitcher["name"],
        pitcher_ruthlessness=pitcher["ruthlessness"] * pitcher_multiplier,
        pitcher_overpowerment=pitcher["overpowerment"] * pitcher_multiplier,
        pitcher_unthwackability=pitcher["unthwackability"] * pitcher_multiplier,
        pitcher_shakespearianism=pitcher["shakespearianism"] * pitcher_multiplier,
        pitcher_suppression=pitcher["suppression"] * pitcher_multiplier,
        pitcher_coldness=pitcher["coldness"] * pitcher_multiplier,
        pitcher_chasiness=pitcher["chasiness"] * pitcher_multiplier,

        defense_avg_anticapitalism=sum(
            players[pid]['anticapitalism'] for pid in batting_team['lineup']) / len(
            batting_team['lineup']),
        defense_avg_chasiness=sum(
            players[pid]['chasiness'] for pid in batting_team['lineup']) / len(
            batting_team['lineup']),
        defense_avg_omniscience=sum(
            players[pid]['omniscience'] for pid in batting_team['lineup']) / len(
            batting_team['lineup']),
        defense_avg_tenaciousness=sum(
            players[pid]['tenaciousness'] for pid in batting_team['lineup']) / len(
            batting_team['lineup']),
        defense_avg_watchfulness=sum(
            players[pid]['watchfulness'] for pid in batting_team['lineup']) / len(
            batting_team['lineup']),

        ballpark_grandiosity=stadium["grandiosity"],
        ballpark_fortification=stadium["fortification"],
        ballpark_obtuseness=stadium["obtuseness"],
        ballpark_ominousness=stadium["ominousness"],
        ballpark_inconvenience=stadium["inconvenience"],
        ballpark_viscosity=stadium["viscosity"],
        ballpark_forwardness=stadium["forwardness"],
        ballpark_mysticism=stadium["mysticism"],
        ballpark_elongation=stadium["elongation"],

        batting_team_hype=stadium["hype"] if not update["topOfInning"] else 0,
        pitching_team_hype=stadium["hype"] if update["topOfInning"] else 0,

        batter_vibes=calculate_vibes(batter, update["day"]),
        pitcher_vibes=calculate_vibes(pitcher, update["day"]),
    )


for event in events:
    if not event["metadata"] or "play" not in event["metadata"]:
        print("unknown event", event)
        continue

    play = event["metadata"]["play"]
    if event["metadata"]["subPlay"] != -1:
        print("=== EXTRA:", event["type"], event["description"], event["metadata"])
        if event["type"] == 106:
            player_id = event["playerTags"][0]
            players[player_id]["permAttr"].append(event["metadata"]["mod"])
        if event["type"] == 107:
            player_id = event["playerTags"][0]
            players[player_id]["permAttr"].remove(event["metadata"]["mod"])
        if event["type"] == 146:
            if event["playerTags"]:
                # Then it's added to the player
                player_id = event["playerTags"][0]
                players[player_id]["permAttr"].append(event["metadata"]["mod"])
            else:
                # Then it's added to the team
                team_id = event["teamTags"][0]
                teams[team_id]["permAttr"].append(event["metadata"]["mod"])
        continue
    if event["created"] == "2021-05-22T02:13:50.540Z":
        print("the shoe thieves have a blood type :)")
        teams["bfd38797-8404-4b38-8b82-341da28b1f83"]["permAttr"].append("ELECTRIC")

    game_id = event["gameTags"][0]
    if event["type"] == 1:
        # probably actually rolled on postseason weather gen but putting them here is easier
        print("play ball!", r.next())
        print("play ball!", r.next())
        print("play ball!", r.next())

        # i'm sure there's a logic to this somewhere
        if game_id == "ca16e900-aee9-42b7-abf7-7eff848fb462":
            print("CORRECTION: start of game", r.step(-1))

        if game_id == "5af576a9-adaf-40dc-80a7-4ec652396780":
            # ??????
            print("CORRECTION: start of game", r.step(11))

        if game_id == "a8ce708b-c8be-4eb2-a129-c2e1cdca0b18":
            # this game is reverb weather, psychoacoustics roll maybe?
            print("CORRECTION: start of game", r.step(1))

        if game_id == "f4b476c8-9664-472e-acb7-1ff88b901425":
            print("CORRECTION: start of game", r.step(1))


        timestamp = event["created"]
        print("new game, refetching...")

        if event["day"] not in fetched_for_days:
            teams = get_team_states(timestamp)
            players = get_player_states(timestamp)
            stadiums = get_stadium_states(timestamp)
            fetched_for_days.add(event["day"])
        continue
    if event["type"] == 54:
        print("incin, refetching")
        if event["created"] == "2021-05-22T01:20:43.576Z":
            # special casing this so we get a post-incin player list
            teams = get_team_states("2021-05-22T01:22:43.576Z")
            players = get_player_states("2021-05-22T01:22:43.576Z")


    update = get_game_update(game_id, play-1)
    next_update = get_game_update(game_id, play)
    if not update or not next_update:
        print("couldn't find update for", game_id, "play #", play)
        continue

    batting_team_id = update["awayTeam"] if update["topOfInning"] else update["homeTeam"]
    batting_team = teams[batting_team_id]
    batting_team_mods = get_mods(batting_team)

    pitching_team_id = update["homeTeam"] if update["topOfInning"] else update["awayTeam"]
    pitching_team = teams[pitching_team_id]
    pitching_team_mods = get_mods(pitching_team)

    batter_id = update["awayBatter"] if update["topOfInning"] else update["homeBatter"]
    if not batter_id:
        batter_id = next_update["awayBatter"] if next_update["topOfInning"] else next_update["homeBatter"]
    batter = players.get(batter_id)
    batter_mods = get_mods(batter) if batter else []
    flinch_eligible = "FLINCH" in batter_mods and update["atBatStrikes"] == 0
    zero_eligible = "0" in batting_team_mods and update["atBatStrikes"] == 0 and update["atBatBalls"] == 0

    pitcher_id = update["homePitcher"] if update["topOfInning"] else update["awayPitcher"]
    pitcher = players.get(pitcher_id)
    pitcher_mods = get_mods(pitcher) if pitcher else []

    stadium = stadiums[update["stadiumId"]]
    stadium_mods = stadium["mods"]

    ty = event["type"]

    print()
    print("=====", event["created"], event["gameTags"][0])
    print("=====", ty, event["description"].replace("\n", " "))

    if ty == 11:
        print("end of game")
        continue

    if ty == 28:
        print("skipping outing", update["inning"])

        if update["inning"] == 2:
            home_pitcher = players[update["homePitcher"]]
            away_pitcher = players[update["awayPitcher"]]

            print("home pitcher mods:", home_pitcher["permAttr"])
            print("away pitcher mods:", away_pitcher["permAttr"])
            if "TRIPLE_THREAT" in away_pitcher["permAttr"]:
                print("roll for away pitcher triple threat removal?", r.next())
            if "TRIPLE_THREAT" in home_pitcher["permAttr"]:
                print("roll for home pitcher triple threat removal?", r.next())

        continue
    elif ty in [2, 63]:
        print("skipping top-of")

        if update["weather"] == 19 and next_update["inning"] > 0 and not update["topOfInning"]:
            last_play = get_game_update(game_id, play-3)
            # only roll salmon if the last inning had any scores, but also we have to dig into game history to find this
            # how does the sim do it? no idea. i'm cheating.
            print("salmon state", last_play["topInningScore"], last_play["bottomInningScore"], last_play["halfInningScore"], last_play["newInningPhase"])
            if last_play["topInningScore"] or last_play["bottomInningScore"]:
                print("salmon proc", r.next())

                if ty == 63:
                    print("something salmon related", r.next())
                    print("something salmon related", r.next())
                    print("something salmon related", r.next())
                    print("something salmon related", r.next())

        continue
    elif ty == 198:
        print("a blood type", r.next())
        continue
    elif ty in [21, 91, 182]:
        print("skipping pregame messages")
        continue
    elif ty == 193:
        print("item generation? no idea how many rolls this is")
        r.step(13)
        continue

    # don't know when this interrupts either
    if ty in [85, 86]:
        print("skipping under/over")
        continue


    # stuff that runs before batterup
    did_elsewhere_return = False
    for player_id in batting_team["lineup"] + batting_team["rotation"]:
        player = players[player_id]
        player_mods = player["permAttr"] + player["seasAttr"] + player["weekAttr"] + player["gameAttr"] + player.get("itemAttr", [])

        if "ELSEWHERE" in player_mods:
            print("elsewhere:", r.next()) # elsewhere check
            
            if ty == 84 and player["name"] in event["description"]:
                should_scatter = False
                if "days" in event["description"]:
                    elsewhere_time = int(event["description"].split("after ")[1].split(" days")[0])
                    should_scatter = elsewhere_time >= 18
                if "season" in event["description"]:
                    should_scatter = True

                if should_scatter:
                    for letter in player["name"]:
                        # might need to skip dashes instead of spaces?
                        if letter not in [" ", "-"]:
                            print("scatter letter {}?".format(letter), r.next())
                            print("scatter letter {}?".format(letter), r.next())
                did_elsewhere_return = True
                continue

        if "SCATTERED" in player_mods:
            unscatter_roll = r.next()
            print("scattered:", unscatter_roll) # unscatter check

            # todo: figure out threshold better idk
            # if unscatter_roll < 5e-08:
            # should happen at least on 2021-05-22T16:29:13.234Z  
            if unscatter_roll < 0.00025:
                print("letter?", r.next(), player["name"])
                
                # lol. (just to make fielder selection work through unscatters)
                if player["name"] == "Burke Go-zale-":
                    player["name"] = "Burke Gonzale-"
                if player["name"] == "St-w Bri--s":
                    player["name"] = "St-w Brig-s"
    if did_elsewhere_return:
        continue

    if ty == 84:
        print("skipping elsewhere return")
        continue
    if ty == 23:
        print("skipping elsewhere")
        continue
    if ty == 12:
        print("skipping batter-up")
        print("pitcher ruth={:.05f}".format(pitcher["ruthlessness"]))
        if "HAUNTED" in batter_mods:
            print("haunted", r.next())
        if "is Inhabiting" in event["description"]:
            print("haunted", r.next())
            print("haunted selection", r.next())
            # might be more here
        continue

    
    if ty == 67:
        # consumer escape
        print("consumers:", r.next())
        print("player:", r.next())
        for _ in range(25):
            print("stat:", r.next())
        continue

    if update["weather"] == 18:
        # flooding
        # there should be a roll here but it doesn't look like it's needed
        pass
    elif update["weather"] == 19:
        # salmon
        pass
    elif update["weather"] == 9:
        # blooddrain
        print("blooddrain?", r.next())
        pass
    elif update["weather"] == 1:
        # sun 2
        pass
    elif update["weather"] == 12:
        # feedback
        print("???:", r.next())
        print("???:", r.next())

        # this seems like it's needed
        if "PSYCHOACOUSTICS" in stadium_mods:
            print("psychoacoustics:", r.next())

    elif update["weather"] == 13:
        # reverb
        print("reverb:", r.next())
        # print("???:", r.next())
        # print("???:", r.next())
    elif update["weather"] == 16:
        # coffee 2
        print("coffee 2?:", r.next())

        if ty == 37:
            # no idea if there are actually three, i'm just guessing
            print("coffee roll:", r.next())
            print("coffee roll:", r.next())
            print("coffee roll:", r.next())
            continue

    elif update["weather"] == 11:
        # birds
        print("birds:", r.next())

        if ty == 33:
            print("skipping bird message")
            continue
    elif update["weather"] == 10:
        # peanuts
        print("peanuts:", r.next())
        if ty == 73:
            print("message:", r.next())
            continue

        print("???:", r.next())
    elif update["weather"] == 8:
        # glitter
        print("glitter:", r.next())
    elif update["weather"] == 7:
        print("eclipse:", r.next())

        for player_id in pitching_team["lineup"] + [batter_id]:
            player = players[player_id]
            is_fire_eater = "FIRE_EATER" in player["permAttr"] or "FIRE_EATER" in player["itemAttr"] 
            if is_fire_eater and "ELSEWHERE" not in player["permAttr"]:
                print("fire eater?", r.next(), player["name"])
                break

        if ty == 55:
            print("skipping fire eater", r.next())
            continue

        if ty == 54:
            print("incin at", r.get_state_str())
            print("misc incin roll?", r.next()) # probably position/slot
            print("misc incin roll?", r.next())
            print("first name", r.next())
            print("last name", r.next())
            for _ in range(26):
                print("stat", r.next())
            print("soul", r.next())
            print("allergy", r.next())
            print("fate", r.next())
            print("ritual", r.next())
            print("blood", r.next())
            print("coffee", r.next())

            # don't know if these are needed, this is a weird area
            print("???", r.next())
            print("???", r.next())
            print("???", r.next())
            continue
    elif update["weather"] == 14:
        # black hole
        pass
    else:
        print("weather is", update["weather"])

    mystery = r.next()
    print("mystery:", mystery)
    if mystery < 0.0052:
        # this exception has 0.0048, might be influenced by ballpark myst or sth?
        if event["created"] != "2021-05-22T18:09:44.057Z":
            print("!!! weird roll?", mystery, r.next())

    if ty == 62:
        # flooding proc
        print("flooding:", r.next())
        print("found flooding at", r.get_state_str())
        for runner in update["baseRunners"]:
            print("sweep?", r.next())
        print("filthiness", r.next())
        continue

    # this is definitely after the mystery roll above. the others might be too?
    if update["weather"] in [20, 21]:
        # polarity
        print("polarity?", r.next())

        if ty == 64:
            print("skipping polarity")
            continue

    if "PEANUT_MISTER" in stadium_mods:
        proc = r.next()
        print("peanut mister:", proc)

        if ty == 72:
            # idk
            print("mister target?", r.next())
            for _ in range(2):
                print("?????", r.next())

            continue

        # this happens sometimes with regular rolls
        # i think it just throws out the proc if the target isn't allergic?
        # idk if this is even necessary, hence it not actually doing the roll but warning instead
        if proc < 0.0023:
            print("!!! peanut mister target selection?")


    # todo: does this go before or after weather?
    if batting_team["level"] >= 5:
        print("consumers:", r.next())
    if pitching_team["level"] >= 5:
        print("consumers:", r.next())


    if ty == 24:
        # party escape
        print("party:", r.next())
        print("position?", r.next())
        print("player?", r.next())
        r.step(1)
        print("party shakes position:", r.get_state_str())
        r.step(-1)

        for _ in range(25):
            print("stat:", r.next())
        continue

    if "PARTY_TIME" in batting_team_mods:
        print("party:", r.next())
    if "PARTY_TIME" in pitching_team_mods:
        print("party:", r.next())



    secret_base_enter_eligible = 1 in update["basesOccupied"] and not update["secretBaserunner"]
    secret_base_exit_eligible = 1 not in update["basesOccupied"] and update["secretBaserunner"]
    secret_base_wrong_side = False
    if update["secretBaserunner"]:
        secret_runner = players[update["secretBaserunner"]]
        if secret_runner["leagueTeamId"] != batting_team_id:
            print("can't exit secret base on wrong team")
            secret_base_exit_eligible = False # lol
            secret_base_wrong_side = True

    attractor_eligible = not update["secretBaserunner"] and 1 not in update["basesOccupied"]
    if 1 in update["basesOccupied"] and update["secretBaserunner"] and secret_base_wrong_side:
        print("special attractor case", attractor_eligible)
    print("???:", r.next())

    if "SECRET_BASE" in stadium_mods:
        # exit is before other mods but not enter? idk but it works
        # (except not, if i'm having to add alignment rolls. something else is going on idk)
        if secret_base_exit_eligible:
            print("secret base (exit):", r.next())
        if ty == 66:
            print("skipping secret base exit")
            
            if event["created"] == "2021-05-22T01:04:18.200Z":
                print("exit alignment", r.next())
            if event["created"] == "2021-05-22T02:07:33.383Z":
                print("exit alignment", r.next())
            continue

    if "SMITHY" in stadium_mods:
        print("smithy:", r.next())

        if ty == 195:
            # probably player + item
            print("skipping smithy", r.next())
            print("skipping smithy", r.next())
            continue

    if ty == 191:
        print("found shadow fax at", r.get_state_str())
        for _ in range(25):
            print("stat:", r.next())
        continue

    league_mods = ["uhhh", "yeah i'm just hardcoding these"]
    if (update["season"], update["day"]) > (18, 71):
        league_mods.append("SECRET_TUNNELS")

    if "SECRET_TUNNELS" in league_mods:
        print("tunnels:", r.next())
        pass

    if "SECRET_BASE" in stadium_mods:
        if attractor_eligible:
            print("secret base (attract):", r.next())
        if secret_base_enter_eligible:
            print("secret base (enter):", r.next())
        if ty == 65:
            print("skipping secret base enter")

            if event["created"] == "2021-05-22T01:01:47.344Z":
                print("enter align", r.next())
            continue


    grind_rail_eligible = 0 in update["basesOccupied"] and 2 not in update["basesOccupied"]
    if "GRIND_RAIL" in stadium_mods:
        if grind_rail_eligible:
            print("grind rail?", r.next())

        if ty == 70:
            print("found grind rail at {}, skipping".format(r.get_state_str()))

            # probably have this in the wrong spot in the pitch
            if event["created"] == "2021-05-22T20:24:38.028Z":
                print("align?", r.next())
            if event["created"] == "2021-05-22T03:01:11.578Z":
                print("align?", r.next())
            
            runner_idx = update["basesOccupied"].index(0)
            runner_id = update["baseRunners"][runner_idx]
            runner = players[runner_id]

            print("trick 1 name:", r.next())
            score1 = r.next()
            lo1 = runner["pressurization"] * 200
            hi1 = runner["cinnamon"] * 1500 + 500
            print("trick 1 score:", score1, "({})".format(int((hi1-lo1) * score1 + lo1)))
            print("trick 1 success:", r.next())

            if "lose their balance and bail" not in event["description"]:
                print("trick 2 name:", r.next())
                lo2 = runner["pressurization"] * 500
                hi2 = runner["cinnamon"] * 3000 + 1000
                score2 = r.next()
                print("trick 2 score:", score2, "({})".format(int((hi2-lo2) * score2 + lo2)))
                print("trick 2 success:", r.next())

            continue

    if 0 in update["basesOccupied"]:
        if 2 not in update["basesOccupied"]:
            if "GRIND_RAIL" in stadium_mods:
                print("extra grind rail roll?", r.next())
    if 1 in update["basesOccupied"]:
        if "SECRET_BASE" in stadium_mods:
            # no idea why these are needed. this is very weird
            if secret_base_enter_eligible or secret_base_exit_eligible or attractor_eligible:
                print("extra secret base roll?", r.next(), secret_base_enter_eligible, secret_base_exit_eligible, attractor_eligible)

    # might need to get moved into the weather block depending on roll order
    if update["weather"] == 18:
        # only in flooding??
        if len(update["basesOccupied"]) > 0:
            print("extra flooding roll?", r.next())

    for base in update["basesOccupied"]:
        if base + 1 not in update["basesOccupied"]:
            print("steal:", r.next())

            if base + 1 == get_base_stolen(event):
                print("steal success?", r.next())
                break

        if update["basesOccupied"] == [2, 2]:
            # don't roll twice when holding hands
            break

    if ty == 4:
        if "third base" in event["description"]:
            runner_idx = update["basesOccupied"].index(1)
        elif "second base" in event["description"]:
            runner_idx = update["basesOccupied"].index(0)
        elif "fourth base" in event["description"]:
            runner_idx = update["basesOccupied"].index(2)
        runner_id = update["baseRunners"][runner_idx]
        runner = players[runner_id]

        if "caught stealing" in event["description"]:
            print("extra cs roll (fielder selection?)", r.next())

        # might need to damage selected fielder instead if caught stealing, idk
        try_damage(runner)

        if event["created"] == "2021-05-21T22:15:15.277Z":
            # might be a roll order issue, this could proc before tunnels and/or secret base?
            print(" - !!! CORRECTION: -1?")
            r.step(-1)
        continue


    print("base states:", update["basesOccupied"], game_id[:8], update["topOfInning"])

    if "FIERY" in pitching_team_mods:
        # unsure if only eligible with 0/1 strikes
        if update["atBatStrikes"] < 2:
            print("double strike?", r.next())

    print("(pitcher mods: {})".format(pitcher_mods))
    print("(batter mods: {})".format(batter_mods))
    print("(stadium mods: {})".format(stadium_mods))

    # this entire pile is a mess and i'm sure there's a good reason for it
    if event["created"] == "2021-05-21T22:19:06.352Z":
        print(" - !!! CORRECTION: weird spot")
        r.step(-3)

    if event["created"] == "2021-05-22T01:21:03.792Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:21:13.755Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:21:18.792Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:21:24.008Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:21:28.840Z":
        print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:21:33.992Z":
        # low mystery roll here so that might "self correct"
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:21:39.108Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:22:39.418Z":
        # misaligned secret base exit somehow (previous out too short?)
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:22:59.779Z":
        # without this the double "should" be a triple so the error is probably in the single before?
        print("CORRECTION: something", r.next())


    if event["created"] == "2021-05-22T01:23:09.598Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:14.641Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:19.678Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:29.720Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:39.538Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:39.787Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:50.105Z":
        # print("CORRECTION: something", r.next())
        # starts being weird here
        pass
    if event["created"] == "2021-05-22T01:23:54.418Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:23:59.921Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:25:35.533Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:25:45.693Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:25:55.666Z":
        # print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:26:00.236Z":
        print("CORRECTION: something", r.next())
        pass
    if event["created"] == "2021-05-22T01:26:05.613Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:26:10.746Z":
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        pass 
    if event["created"] == "2021-05-22T01:27:36.320Z":
        # this doesn't make sense w/ the secret base exit and the triple earlier?
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:27:55.828Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:28:01.471Z":
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:28:11.512Z":
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:28:16.560Z":
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:30:57.536Z":
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
    if event["created"] == "2021-05-22T01:31:17.665Z":
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())
        print("CORRECTION: something", r.next())

    if event["created"] == "2021-05-22T02:19:22.126Z":
        print("CORRECTION: idk", r.step(-1))


    if update["basesOccupied"] == [0] and game_id == "2eaeeaee-bf12-4181-97e2-a7c293e250b8":
        if event["created"] >= "2021-05-22T01:23:09.598Z" and event["created"] < "2021-05-22T01:29:47.096Z":
            print("CORRECTION: extra base roll??", r.next())

    if event["created"] == "2021-05-22T16:19:51.612Z":
        # there's a very low roll in the item damage block. either the ??? flyout roll lands in that spot
        # (and item rolls happen after that), or the order is wrong, it should land on King Weatherman
        # ...and it's skipping because all their items are broken already
        print("CORRECTION: weird item roll?", r.step(-1))


    # is this before or after mild?
    if "ELECTRIC" in batting_team_mods and update["atBatStrikes"] > 0:
        print("electric:", r.next())

        if ty == 25:
            # successful zap, cancel
            continue

    if update["weather"] == 11:
        # birds
        if update["atBatStrikes"] == 0:
            print("bird ambush?", r.next())

        if ty == 34:
            print("skipping ambush", r.next())
            continue

    print("mild?", r.next())
    if ty == 27:
        # no idea what this roll is. damage?
        print("skipping mild proc", r.next())
        continue
    
    # don't know when in the pitch this interrupts. seems to be about here
    if ty == 31:
        print("skipping sun 2 proc")
        continue


    if "0" in batting_team_mods:
        if update["atBatBalls"] == 0 and update["atBatStrikes"] == 0:
            print("!!! 0 blood potentially messing things up here")


    if "LOVE" in batting_team_mods or "LOVE" in pitching_team_mods:
        if update["atBatBalls"] == 0 and update["atBatStrikes"] == 0:
            print("charm?", r.next())

            if " charmed " in event["description"]:
                # skipping charm proc
                for _ in range(3):
                    print("charm success?", r.next())
                continue
            if " charms " in event["description"]:
                for _ in range(4):
                    print("charm success?", r.next())
                continue


    if ty in [5, 14, 27]:  # Walk, Ball, Mild pitch (in order)
        # ball/walk
        strike_roll = r.next()
        strike_roll_log.append(make_roll_log('Ball', strike_roll, False))

        print("strike:", strike_roll, "(batter {}, pitcher {})".format(batter["name"], pitcher["name"]))
        if "ACIDIC" in pitching_team_mods:
            print("acidic:", r.next())

        if strike_roll < 0.75:
            print("!!! too low strike roll?", r.get_state_str())

        if not flinch_eligible and not zero_eligible:
            print("swing:", r.next())

        if ty == 5: # walk
            if "BASE_INSTINCTS" in batting_team_mods:
                print("base instincts:", r.next())

            try_damage(batter) # should be only on walk

        # lol
        if ty != 5 or True:
            try_damage(pitcher) # should be only on non-walk. or should it? i think it shouldn't


    elif ty in [7, 8]:
        print("strike:", r.next())
        if "ACIDIC" in pitching_team_mods:
            print("acidic:", r.next())

        print("swing:", r.next())
        print("contact:", r.next())
        print("foul:", r.next())

        if ty == 8:
            # ground out
            for _ in range(4):
                print("???:", r.next())
        else:
            # flyout
            for _ in range(2):
                print("???:", r.next())

        eligible_fielders = []
        fielder_idx = None
        fielder_obj = None
        for fielder_id in pitching_team["lineup"]:
            fielder = players[fielder_id]
            if "ELSEWHERE" in fielder["permAttr"]:
                continue

            if fielder["name"] in event["description"]:
                fielder_idx = len(eligible_fielders)
                fielder_obj = fielder
            eligible_fielders.append(fielder)
        
        fielder_roll = r.next()
        fielder_roll_idx = int(fielder_roll * len(eligible_fielders))
        print("fielder:", fielder_roll, "({}/{})".format(fielder_roll_idx, len(eligible_fielders)), "expected", fielder_idx, "({:.03f}-{:.03f})".format((fielder_idx or 0) / len(eligible_fielders), ((fielder_idx or 0) + 1) / len(eligible_fielders)))
        if fielder_roll_idx != fielder_idx and fielder_idx is not None and "fielder's choice" not in event["description"]:
            print("!!! incorrect fielder")

        matching = []
        r2 = rng.Rng(r.state, r.offset)
        check_range = 50
        r2.step(-check_range)
        for i in range(check_range * 2):
            val = r2.next()
            if int(val * len(eligible_fielders)) == fielder_idx:
                matching.append(i - check_range + 1)
        print("!!! expected {}, found {}, matching offsets {}".format(fielder_idx, fielder_roll_idx, matching))


        try_damage(batter)
        try_damage(pitcher)
        if fielder_obj:
            try_damage(fielder_obj)

        if "hit into a double play!" in event["description"]:
            for _ in range(2):
                print("dp?:", r.next(), update["halfInningOuts"])

            if "scores!" in event["description"]:
                print("scoring dp?", r.next()) # might be adv roll or sth?
                print("scoring dp?", r.next())
            elif 2 in update["basesOccupied"]:
                # this might need one roll too
                print("non-scoring dp with runner on second?")

        elif "reaches on fielder's choice" in event["description"]:
            # not confident in these at all, fcs seem to be a consistent length
            # but i can't tell if it's 1 or 2, lmao. and all the extra rolls might just be other misalignments in the games i found them

            for _ in range(1):
                print("fc?:", r.next())
            if 1 in update["basesOccupied"]:
                print("fc runner?:", r.next())

            if 2 in update["basesOccupied"] and "scores!" in event["description"]:
                print("sac?:", r.next())
                print("sac?:", r.next())
                pass
        else:

            if ty == 8:
                # ground out
                for _ in range(0):
                    print("???:", r.next())
            else:
                # flyout
                for _ in range(1):
                    print("???:", r.next())


            # i gave up on out advancement logic i'm just gonna do this and find the logic later
            if update["halfInningOuts"] < 2:
                bases_before = make_base_map(update)
                bases_after = make_base_map(next_update)
                print("OUT BASE STATE: {} -> {}".format(update["basesOccupied"], next_update["basesOccupied"]))

                if ty == 7:
                    # flyout
                    extras = {
                        (tuple(), tuple()): 0,
                        ((0,), (0,)): 1,
                        ((0,), (1,)): 2,
                        ((1,), (1,)): 1,
                        ((1,), (2,)): 2,
                        ((2,), (2,)): 1,
                        ((2,0), (0,)): 4,
                        ((2,0), (2,0)): 1,
                        ((2,1), (2,1)): 3,
                        ((1,0), (1,0)): 1,
                        ((1,0), (2,0)): 2,
                        ((2,1,0), (1,0)): 4,
                        ((2,1), (2,)): 5,
                        ((2,), tuple()): 3
                    }
                    
                    rolls = extras[(tuple(update["basesOccupied"]), tuple(next_update["basesOccupied"]))]
                    for _ in range(rolls):
                        print("extras:", r.next())
                else:
                    # ground out
                    extras = {
                        (tuple(), tuple()): 0,
                        ((0,), (1,)): 4,
                        ((1,), (1,)): 2,
                        ((1,), (2,)): 3,
                        ((2,), tuple()): 4,
                        ((2,), (2,)): 2,
                        ((2,0), (0,)): 6,
                        ((2, 1), (2,)): 6,

                        # ...holding hands?
                        ((2, 1), (2, 2)): 4
                    }
                    
                    rolls = extras[(tuple(update["basesOccupied"]), tuple(next_update["basesOccupied"]))]
                    for _ in range(rolls):
                        print("extras:", r.next())


    elif ty in [6, 13]:
        # strike swinging/looking
        strike_roll = r.next()
        print("strike:", strike_roll, "(batter {}, pitcher {})".format(batter["name"], pitcher["name"]))
        if "ACIDIC" in pitching_team_mods:
            print("acidic:", r.next())

        if not flinch_eligible:
            print("swing:", r.next())

        if ", swinging." in event["description"] or "strikes out swinging." in event["description"]:
            print("contact:", r.next())
        else:
            strike_roll_log.append(make_roll_log('StrikeLooking', strike_roll, True))
            if strike_roll > 0.85:
                print("!!! too high strike roll?", strike_roll)

        try_damage(pitcher)

    elif ty in [9]:
        # home run
        if "MAGMATIC" not in batter_mods:
            print("strike:", r.next())
            if "ACIDIC" in pitching_team_mods:
                print("acidic:", r.next())

            print("swing:", r.next())
            print("contact:", r.next())
            print("foul:", r.next())
            print("???:", r.next())
            print("???:", r.next())
            print("hr:", r.next())
        else:
            print("magmatic roll?", r.next())

        try_damage(batter)

        if "BIG_BUCKET" in stadium_mods:
            # same deal
            print("big buckets?", r.next(), "moxie=", batter["moxie"])

        # order here is weird. might need to shuffle
        if "HOOPS" in stadium_mods:
            # bucket proc seems to exclude hoop proc
            if "lands in a Big Bucket" not in event["description"]:
                print("hoops?", r.next(), "continuation=", batter["continuation"])


        if "went up for the alley oop" in event["description"]:
            print("hoops success?", r.next())

        if "AIR_BALLOONS" in stadium_mods:
            print("pop?", r.next())
            if "was struck and popped!" in event["description"]:
                bird_roll = r.next()
                bird_count = int(bird_roll * 6) + 2
                print("birds:", bird_roll, "({})".format(bird_count))

        for runner_id in update["baseRunners"]:
            runner = players[runner_id]
            try_damage(runner)

    elif ty in [10]:
        # base hit
        bases_hit = 0
        if "hits a Single" in event["description"]:
            bases_hit = 1
        elif "hits a Double" in event["description"]:
            bases_hit = 2
        elif "hits a Triple" in event["description"]:
            bases_hit = 3

        print("strike:", r.next())
        if "ACIDIC" in pitching_team_mods:
            print("acidic:", r.next())

        print("swing:", r.next())
        print("contact:", r.next())
        print("foul:", r.next())

        for _ in range(6):
            print("???:", r.next())

        try_damage(batter)
        try_damage(pitcher)

        bases_before = make_base_map(update)
        bases_after = make_base_map(next_update)

        calculated_roll = 0

        damaged = set()
        # forced advance
        for base, runner_id in zip(update["basesOccupied"], update["baseRunners"]):
            runner = players[runner_id]
            print("damage on adv:", runner["name"])
            try_damage(runner)
            damaged.add(runner_id)


        for runner_id, base, roll_outcome in calculate_advances(bases_before, bases_after, bases_hit):
            print("adv?", base, r.next(), roll_outcome)
            # we might need to damage these additionally if they successfully advance
            # but they should all have gotten damage from the forced advance earlier, so hell if i know

        # damage on score, even if they already got damage earlier
        for runner_id in update["baseRunners"]:
            if runner_id not in next_update["baseRunners"]:
                runner = players[runner_id]
                print("no damage on score:", runner["name"])
                try_damage(runner)

                damaged.add(runner_id)
                if runner_id in damaged:
                    print("double damage on", runner["name"])

        # i should just make a lookup table here too because clearly some of this isn't right
        corrections = {
            "2021-05-21T21:21:43.556Z": -1, # somewhere around this area?
            "2021-05-21T22:13:19.915Z": -1, # double, [1] -> [1]
            # "2021-05-21T22:13:39.928Z": -1, # double, [1] -> [1]
            "2021-05-21T22:16:30.693Z": -1, # triple, [] -> []
            "2021-05-22T00:11:39.769Z": -1, # single, [2] -> [0]
            "2021-05-22T01:01:37.246Z": -1, # single, [0] -> [1]
        }
        if event["created"] in corrections:
            amount = corrections[event["created"]]
            print("=== CORRECTION: stepping by {}".format(amount))
            r.step(amount)

        if len(update["basesOccupied"]) > 0:
            print("HIT BASE STATE: {} / {} -> {}".format(bases_hit, update["basesOccupied"], next_update["basesOccupied"]))

    elif ty in [15]:
        # foul
        print("strike:", r.next())
        if "ACIDIC" in pitching_team_mods:
            print("acidic:", r.next())

        print("swing:", r.next())
        print("contact:", r.next())

        foul_roll = r.next()
        print("foul:", foul_roll)
        if foul_roll > 0.5:
            print("!!! too high foul?")

        # we know the order of this
        try_damage(pitcher)
        try_damage(batter)

        if "O_NO" in batting_team_mods and update["atBatStrikes"] == 2 and update["atBatBalls"] == 0:
            print("!!! 0 no blood potentially messing things up here")

    else:
        print("!!! unknown type", ty)

    is_at_bat_end = ty in [5, 6, 7, 8, 9, 10]
    # rolls even on inning ending?
    if is_at_bat_end and "REVERBERATING" in batter_mods:
        if event["created"] not in ["2021-05-21T23:06:43.070Z"]:
            print("reverb?", r.next(), update["halfInningOuts"])
        else:
            print("NOT reverbing")

strike_roll_df = pd.DataFrame(strike_roll_log)
strike_roll_df.to_csv(f"roll_data/{min_stamp}-strikes.csv")

print(seen_mods)