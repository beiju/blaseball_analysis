import json
from typing import List

import requests

VERSIONS_BASE = "https://api.sibr.dev/chronicler/v2/versions"


def player_oldest_record(player):
    id_ = player['data']['id']
    url = f"{VERSIONS_BASE}?type=player&sort=asc&count=1&id={id_}"
    return requests.get(url).json()['items'][0]


def load_players_oldest_records(exclude_initial=False):
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

    if exclude_initial:
        return [p for p in players_oldest if
                p['validFrom'] != '2020-07-29T08:12:22.438Z']

    return players_oldest
