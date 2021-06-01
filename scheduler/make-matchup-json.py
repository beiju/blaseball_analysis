import json
from collections import defaultdict

from blaseball_mike import models
from tqdm import tqdm

season = 13  # one indexed


def main():
    days = defaultdict(lambda: [])

    for day in tqdm(range(1, 100, 3), unit="days"):
        for game_id in models.Game.load_by_season(season, day=day):
            game = models.Game.load_by_id(game_id)
            days[day].append((game.home_team.id, game.away_team.id))

    with open(f"season-{season}-matchups.json", "w") as f:
        json.dump(days, f)


if __name__ == '__main__':
    main()
