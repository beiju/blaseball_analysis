from collections import defaultdict
from itertools import count

import pandas as pd
from blaseball_mike import utils, chronicler
from tqdm import tqdm

TEAM_IDS = "bb4a9de5-c924-4923-a0cb-9d1445f1ee5d," \
           "8d87c468-699a-47a8-b40d-cfb73a5660ad," \
           "36569151-a2fb-43c1-9df7-2df512424c82," \
           "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e," \
           "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5," \
           "f02aeae2-5e6a-4098-9842-02d2273f25c7," \
           "747b8e4a-7e50-4638-a973-ea7950a3e739," \
           "7966eb04-efcc-499b-8f03-d13916330531," \
           "46358869-dce9-4a01-bfba-ac24fc56f57e," \
           "878c1bf6-0d21-4659-bfee-916c8314d69c," \
           "b024e975-1c4a-4575-8936-a3754a08806a," \
           "bfd38797-8404-4b38-8b82-341da28b1f83," \
           "b63be8c2-576a-4d6e-8daf-814f8bcea96f," \
           "105bc3ff-1320-4e37-8ef0-8d595cb95dd0," \
           "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7," \
           "d9f89a8a-c563-493e-9d64-78e4f9a55d4a," \
           "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16," \
           "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff," \
           "a37f9158-7f82-46bc-908c-c9e2dda7c33b," \
           "c73b705c-40ad-4633-a6ed-d357ee2e2bcf," \
           "2e22beba-8e36-42ba-a8bf-975683c52b5f," \
           "b72f3061-f573-40d7-832a-5ad475bd7909," \
           "adc5b394-8f76-416d-9ce9-813706877b84," \
           "979aee4a-6d80-4863-bf1c-ee1a78e06024," \
           "57ec08cc-0411-4643-b304-0e80dbc15ac7," \
           "b47df036-3aa4-4b98-8e9e-fe1d3ff1894b "


def start_time_of_each_day():
    days = 0
    for season in range(14, 25):
        first_day = 1
        if season == 14:
            first_day = 28

        for day in count(first_day):
            time = utils.get_gameday_start_time(season, day)
            if time is None:
                # Last day
                print(day - 1, "days in season", season)
                break
            yield time, season

    print(days, "total days with consumers")


normal_levels = {
    0: "safe",  # 0D
    1: "safe",  # 1D
    2: "safe",  # 2D
    3: "safe",  # 3D
    4: "safe",  # C
    5: "danger1",  # Low A
    6: "danger2",  # High A
    7: "danger3",  # AA
    8: "danger4",  # AAA
    9: "danger5",  # AAAA
    10: "danger6",  # AAAAA
    11: "danger7",  # Beyond AAAAA
}

s24_levels = {
    0: "danger5",  # 0D
    1: "danger4",  # 1D
    2: "danger3",  # 2D
    3: "danger2",  # 3D
    4: "danger1",  # C
    5: "safe",  # Low A
    6: "safe",  # High A
    7: "safe",  # AA
    8: "safe",  # AAA
    9: "safe",  # AAAA
    10: "safe",  # AAAAA
    11: "safe",  # Beyond AAAAA
}

def main():
    days_at_level = {
        "safe": defaultdict(lambda: 0),
        "danger1": defaultdict(lambda: 0),
        "danger2": defaultdict(lambda: 0),
        "danger3": defaultdict(lambda: 0),
        "danger4": defaultdict(lambda: 0),
        "danger5": defaultdict(lambda: 0),
        "danger6": defaultdict(lambda: 0),
        "danger7": defaultdict(lambda: 0),
    }

    for time, season in tqdm(start_time_of_each_day(), total=1231):
        teams = chronicler.get_entities("team", TEAM_IDS, time, cache_time=None)
        for team in teams:
            if season == 24:
                danger = s24_levels[team["data"]["level"]]
            else:
                danger = normal_levels[team["data"]["level"]]

            days_at_level[danger][team["entityId"]] += 1

    data = pd.DataFrame.from_dict(days_at_level).fillna(0)
    data.to_csv("days_at_level.csv")


if __name__ == '__main__':
    main()
