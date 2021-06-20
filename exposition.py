import pickle
from collections import defaultdict
from datetime import timedelta

import blaseball_mike.chronicler.v1 as chron_v1
import blaseball_mike.chronicler.v2 as chron
import matplotlib.pyplot as plt
import mip

# all seasons, days 1-indexed

GATHER = True  # set to True to gather imPositions from chronicler
SEASONS = [20]
COLORS = {
    "Breath Mints": "#509e77",
    "Crabs": "#cd7672",
    "Dale": "#8877ee",
    "Firefighters": "#ff4230",
    "Flowers": "#cc66dd",
    "Fridays": "#04a321",
    "Garages": "#3f88fd",
    "Georgias": "#339991",
    "Jazz Hands": "#6b95b1",
    "Lift": "#f032c9",
    "Lovers": "#dd6699",
    "Magic": "#f94965",
    "Mechanics": "#998800",
    "Millennials": "#aa77aa",
    "Moist Talkers": "#009bc2",
    "Pies": "#339991",
    "Shoe Thieves": "#6388c8",
    "Spies": "#9980ba",
    "Steaks": "#b2838d",
    "Sunbeams": "#aa8855",
    "Tacos": "#aa66ee",
    "Tigers": "#f05d14",
    "Wild Wings": "#cc7733",
    "Worms": "#aa8877",
    "Noodle": "#ffbe00",
}

data = {}

if GATHER:
    for season in SEASONS:
        days = chron_v1.time_season(season)[0]["days"]
        teams = defaultdict(list)
        stadiums = defaultdict(list)
        team_ids = [
            "105bc3ff-1320-4e37-8ef0-8d595cb95dd0",
            "d9f89a8a-c563-493e-9d64-78e4f9a55d4a",
            "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16",
            "c73b705c-40ad-4633-a6ed-d357ee2e2bcf",
            "bfd38797-8404-4b38-8b82-341da28b1f83",
            "bb4a9de5-c924-4923-a0cb-9d1445f1ee5d",
            "b72f3061-f573-40d7-832a-5ad475bd7909",
            "b63be8c2-576a-4d6e-8daf-814f8bcea96f",
            "b024e975-1c4a-4575-8936-a3754a08806a",
            "adc5b394-8f76-416d-9ce9-813706877b84",
            "a37f9158-7f82-46bc-908c-c9e2dda7c33b",
            "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5",
            "979aee4a-6d80-4863-bf1c-ee1a78e06024",
            "8d87c468-699a-47a8-b40d-cfb73a5660ad",
            "878c1bf6-0d21-4659-bfee-916c8314d69c",
            "7966eb04-efcc-499b-8f03-d13916330531",
            "747b8e4a-7e50-4638-a973-ea7950a3e739",
            "57ec08cc-0411-4643-b304-0e80dbc15ac7",
            "46358869-dce9-4a01-bfba-ac24fc56f57e",
            "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e",
            "36569151-a2fb-43c1-9df7-2df512424c82",
            "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff",
            "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7",
            "f02aeae2-5e6a-4098-9842-02d2273f25c7",
        ]
        for day in range(1, days + 1):
            day=99
            day = chron_v1.time_map(season=season, day=day)[-1]
            time = day["startTime"]
            stadium_ids = []
            for team in chron.get_entities(
                "team", id_=team_ids, at=time + timedelta(minutes=5)
            ):
                stadium_ids.append(team["data"]["stadium"])
                teams[team["entityId"]].append(team["data"])
            for stadium in chron.get_entities(
                "stadium", id_=stadium_ids, at=time + timedelta(minutes=5)
            ):
                stadiums[stadium["entityId"]].append(stadium["data"])
            print(day)
        data[season] = {
            'teams': list(teams.values()),
            'stadiums': list(stadiums.values()),
        }
    pickle.dump(data, open("teams_s20", "wb"))

data = pickle.load(open("teams_s20", "rb"))

teams = data[20]['teams']  # TODO more seasons
stadiums = data[20]['stadiums']  # TODO more seasons

fig, ax = plt.subplots()

values = {}
xs = list(range(2, len(teams[0]) + 1))
for team in teams:
    ys = []
    nickname = team[0]["nickname"]
    pos = 0
    vel = 0
    for i in range(1, len(team)):
        day = i + 1
        pos_new = team[i]["imPosition"][0]
        vel_new = pos_new - pos
        target = vel_new / 0.55 - vel + pos
        pos = pos_new
        vel = vel_new
        # hack to disable capping
        if day in range(5) and nickname == "Spies":
            target = 1
        if day in range(5) and nickname == "Mechanics":
            target = -1
        ys.append(target)
    values[nickname] = ys

# find scale
scales = []
for i in range(len(xs)):
    min_error = float("inf")
    best_scale = 0
    for scale in range(20, 60):
        error = 0
        for team in values:
            x = scale * values[team][i]
            error += abs(x - round(x))
        if error < min_error:
            best_scale = scale
            min_error = error
    scales.append(best_scale)


def maybe_round(x):
    if abs(x - round(x)) < 0.00000005:
        return round(x)
    return x


m = mip.Model()
m.emphasis = 1  # 1 = feasibility emphasis

card_var = m.add_var(var_type=mip.INTEGER)
level_var = m.add_var(var_type=mip.INTEGER)
lineup_len_var = m.add_var(var_type=mip.INTEGER)
shadows_len_var = m.add_var(var_type=mip.INTEGER)
game_attr_len_var = m.add_var(var_type=mip.INTEGER)
perm_attr_len_var = m.add_var(var_type=mip.INTEGER)
rotation_len_var = m.add_var(var_type=mip.INTEGER)
evolution_var = m.add_var(var_type=mip.INTEGER)
championships_var = m.add_var(var_type=mip.INTEGER)
underchampionships_var = m.add_var(var_type=mip.INTEGER)
stadium_mods_len_var = m.add_var(var_type=mip.INTEGER)
model_var = m.add_var(var_type=mip.INTEGER)
reno_log_len_var = m.add_var(var_type=mip.INTEGER)
weather_len_var = m.add_var(var_type=mip.INTEGER)

for team_by_day, stadium_by_day in zip(teams, stadiums):
    for i, (team, stadium, scale) in enumerate(zip(team_by_day, stadium_by_day, scales)):
        day = i + 2
        value = (values[team['nickname']][i] + 1) / 2 * scale
        if day >= 25:  # mechs moved down 1
            value -= 1
        value = maybe_round(value)

        print()

# apply scale
changes = defaultdict(list)
for team in sorted(values):
    ys = []
    color = COLORS[team]
    for i, (y, scale) in enumerate(zip(values[team], scales)):
        day = i + 2
        value = (y + 1) / 2 * scale
        if day >= 25:  # mechs moved down 1
            value -= 1
        ys.append(value)
    print(team, [maybe_round(y) for y in ys])
    ys = [maybe_round(y) for y in ys]

    if team == "Sunbeams":  # hack
        for i in range(2, 5):
            ys[i] = 29

    for i in range(1, len(ys)):
        day = i + 2
        if ys[i] != ys[i - 1]:
            delta = ys[i] - ys[i - 1]
            if delta < 0:
                delta = str(delta)
            else:
                delta = "+" + str(delta)
            changes[day].append(f"{team}: {delta}")

    if [ys[0]] * len(ys) != ys:  # don't plot teams that don't change
        plt.plot(xs, ys, c=color, zorder=1)
        plt.scatter(xs, ys, c=color, zorder=2)

print("scales:", scales)

for day in sorted(changes):
    print(f"day {day-1}->{day}")
    for i in changes[day]:
        print("  " + i)
    print()

plt.title(f"imPosition[0] targets, integerized")
plt.xlabel("day")
plt.ylabel(f"target")
plt.grid(axis="y")
plt.show()
