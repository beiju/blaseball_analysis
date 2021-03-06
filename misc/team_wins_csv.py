import pandas as pd
import requests

TEAM_IDS = [
    "b72f3061-f573-40d7-832a-5ad475bd7909",  # Lovers
    "878c1bf6-0d21-4659-bfee-916c8314d69c",  # Tacos
    "b024e975-1c4a-4575-8936-a3754a08806a",  # Steaks
    "adc5b394-8f76-416d-9ce9-813706877b84",  # Breath Mints
    "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16",  # Firefighters
    "bfd38797-8404-4b38-8b82-341da28b1f83",  # Shoe Thieves
    "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e",  # Flowers
    "979aee4a-6d80-4863-bf1c-ee1a78e06024",  # Fridays
    "7966eb04-efcc-499b-8f03-d13916330531",  # Magic
    "36569151-a2fb-43c1-9df7-2df512424c82",  # Millennials
    "8d87c468-699a-47a8-b40d-cfb73a5660ad",  # Crabs
    "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7",  # Pies
    "f02aeae2-5e6a-4098-9842-02d2273f25c7",  # Sunbeams
    "57ec08cc-0411-4643-b304-0e80dbc15ac7",  # Wild Wings
    "747b8e4a-7e50-4638-a973-ea7950a3e739",  # Tigers
    "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff",  # Moist Talkers
    "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5",  # Spies
    "b63be8c2-576a-4d6e-8daf-814f8bcea96f",  # Dale
    "105bc3ff-1320-4e37-8ef0-8d595cb95dd0",  # Garages
    "a37f9158-7f82-46bc-908c-c9e2dda7c33b",  # Jazz Hands
    "c73b705c-40ad-4633-a6ed-d357ee2e2bcf",  # Lift
    "bb4a9de5-c924-4923-a0cb-9d1445f1ee5d",  # Worms
    "46358869-dce9-4a01-bfba-ac24fc56f57e",  # Mechanics
    "d9f89a8a-c563-493e-9d64-78e4f9a55d4a",  # Georgias
    "2e22beba-8e36-42ba-a8bf-975683c52b5f",  # Queens
    "b47df036-3aa4-4b98-8e9e-fe1d3ff1894b",  # Queens (wait one of these must be the paws)
]


def main():
    seasons = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=season").json()
    standingses = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=standings").json()
    standings_dict = {st['entityId']: st['data'] for st in standingses['items']}

    # Season 2 bad :(
    standings_s2 = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=standings&id=2049b677-d869-472e-a25d-d9d6a094a547&at=2020-08-08T04:34:32.691Z").json()
    standings_dict[standings_s2['items'][0]['entityId']] = standings_s2['items'][0]['data']

    beta_seasons = sorted(
        (season['data']['seasonNumber'], standings_dict[season['data']['standings']]['wins'])
        for season in seasons['items']
        if season['data']['league'] == 'd8545021-e9fc-48a3-af74-48685950a183'
    )

    teams = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=team&at=2021-06-26T00:00:00Z&id=" + ",".join(TEAM_IDS)).json()
    teams_dict = {team['entityId']: team['data']['fullName'] for team in teams['items']}

    data = {
        season_n: {
            teams_dict[team]: team_wins.get(team, float('nan')) for team in TEAM_IDS
            if team in teams_dict
        } for (season_n, team_wins) in beta_seasons
    }

    for team in TEAM_IDS:
        if team not in teams_dict:
            print("Not outputting data for", team, "(unknown as of start of s24)")

    dataframe = pd.DataFrame(data)
    dataframe.to_csv("team_wins.csv")


if __name__ == '__main__':
    main()
