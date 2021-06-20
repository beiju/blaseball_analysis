from argparse import ArgumentParser
import random

from blaseball_mike.models import Player

overpowerment_weight = .14
ruthlessness_weight = .46
unthwackability_weight = .40


def compare(player_id):
    all_players = Player.load_all()
    target_player = all_players[player_id]

    def weighted_difference(player):
        return sum(
            overpowerment_weight * abs(
                player.overpowerment - target_player.overpowerment - buff()) +
            ruthlessness_weight * abs(
                player.ruthlessness - target_player.ruthlessness - buff()) +
            unthwackability_weight * abs(
                player.unthwackability - target_player.unthwackability - buff())
            for _ in range(1000)
        ) / 1000

    def buff():
        return 0

    best_matches = sorted(all_players.values(), key=weighted_difference)[:10]

    for player in best_matches:
        print(player.name, weighted_difference(player))


def main():
    parser = ArgumentParser()
    parser.add_argument('player_id')

    args = parser.parse_args()

    compare(args.player_id)


if __name__ == '__main__':
    main()
