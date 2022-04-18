import json
import requests

# Lawful Good -> Chaotic Good -> Lawful Evil -> Chaotic Evil
team_order = [
    "b72f3061-f573-40d7-832a-5ad475bd7909", # Lovers
    "878c1bf6-0d21-4659-bfee-916c8314d69c", # Tacos
    "b024e975-1c4a-4575-8936-a3754a08806a", # Steaks
    "adc5b394-8f76-416d-9ce9-813706877b84", # Breath Mints
    "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16", # Firefighters
    "bfd38797-8404-4b38-8b82-341da28b1f83", # Shoe Thieves
    "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e", # Flowers
    "979aee4a-6d80-4863-bf1c-ee1a78e06024", # Fridays
    "7966eb04-efcc-499b-8f03-d13916330531", # Magic
    "36569151-a2fb-43c1-9df7-2df512424c82", # Millennials
    "8d87c468-699a-47a8-b40d-cfb73a5660ad", # Crabs
    "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7", # Pies
    "f02aeae2-5e6a-4098-9842-02d2273f25c7", # Sunbeams
    "57ec08cc-0411-4643-b304-0e80dbc15ac7", # Wild Wings
    "747b8e4a-7e50-4638-a973-ea7950a3e739", # Tigers
    "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff", # Moist Talkers
    "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5", # Spies
    "b63be8c2-576a-4d6e-8daf-814f8bcea96f", # Dale
    "105bc3ff-1320-4e37-8ef0-8d595cb95dd0", # Garages
    "a37f9158-7f82-46bc-908c-c9e2dda7c33b", # Jazz Hands
]

# Order of generation
stat_order = [
    "thwackability",
    "moxie",
    "divinity",
    "musclitude",
    "patheticism",
    "buoyancy",
    "baseThirst",
    "laserlikeness",
    "groundFriction",
    "continuation",
    "indulgence",
    "martyrdom",
    "tragicness",
    "shakespearianism",
    "suppression",
    "unthwackability",
    "coldness",
    "overpowerment",
    "ruthlessness",
    "omniscience",
    "tenaciousness",
    "watchfulness",
    "anticapitalism",
    "chasiness",
    "pressurization",
    "cinnamon"
]

batting_block = "tragicness buoyancy thwackability moxie divinity musclitude patheticism martyrdom".split()
pitching_block = "shakespearianism suppression unthwackability coldness overpowerment ruthlessness".split()
baserunning_block = "baseThirst laserlikeness groundFriction continuation indulgence".split()
defense_block = "omniscience tenaciousness watchfulness anticapitalism chasiness".split()

blood_types = ["A", "AAA", "AA", "Acidic", "Basic", "O", "O No", "H₂O", "Electric", "Love", "Fire", "Psychic", "Grass"]
coffee_styles = ["Black", "Light & Sweet", "Macchiato", "Cream & Sugar", "Cold Brew", "Flat White", "Americano", "Espresso", "Heavy Foam", "Latte", "Decaf", "Milk Substitute", "Plenty of Sugar", "Anything"]

def get_teams(at):
    teams = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=team&at={}".format(at)).json()
    return {t["entityId"]: t["data"] for t in teams["items"]}

def get_players(at):
    players = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=player&at={}".format(at)).json()
    return {t["entityId"]: t["data"] for t in players["items"]}

def get_team_roster(team):
    return team["lineup"] + team["rotation"] + team.get("shadows", []) + team.get("bench", []) + team.get("bullpen", [])

def get_team_order(at):
    sim = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=sim&at={}".format(at)).json()

    subleagues = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=subleague&at={}".format(at)).json()
    subleagues = {d["entityId"]: d["data"] for d in subleagues["items"]}

    divisions = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=division&at={}".format(at)).json()
    divisions = {d["entityId"]: d["data"] for d in divisions["items"]}

    league_id = sim["items"][0]["data"]["league"]
    league = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=league&at={}&id={}".format(at, league_id)).json()

    team_ids = []
    for subleague_id in league["items"][0]["data"]["subleagues"]:
        subleague = subleagues[subleague_id]
        for division_id in subleague["divisions"]:
            division = divisions[division_id]
            for team_id in division["teams"]:
                team_ids.append(team_id)
    return team_ids

def load_oldest():
    with open("players_baby_grand_oldest.json", encoding="utf-8") as f:
        data = json.load(f)
        return {p["entityId"]: p["data"] for p in data}
