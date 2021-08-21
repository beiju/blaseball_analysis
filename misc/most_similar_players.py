from argparse import ArgumentParser

from blaseball_mike.models import Player
from requests import HTTPError

overpowerment_weight = .14
ruthlessness_weight = .46
unthwackability_weight = .40

divinity_weight = .21
martyrdom_weight = .07
moxie_weight = .09
musclitude_weight = .04
inv_pathetecism_weight = .17
thwackability_weight = .35
ground_friction_weight = .06


def compare(player_id):
    all_players = Player.load_all()
    target_player = all_players[player_id]

    def weighted_difference_wobabr(player):
        return (
                divinity_weight * abs(
            player.divinity - target_player.divinity - buff()) +
                martyrdom_weight * abs(
            player.martyrdom - target_player.martyrdom - buff()) +
                moxie_weight * abs(
            player.moxie - target_player.moxie - buff()) +
                musclitude_weight * abs(
            player.musclitude - target_player.musclitude - buff()) +
                inv_pathetecism_weight * abs(
            (1 - player.patheticism) - (
                    1 - target_player.patheticism) - buff()) +
                thwackability_weight * abs(
            player.thwackability - target_player.thwackability - buff()) +
                ground_friction_weight * abs(
            player.ground_friction - target_player.ground_friction - buff())
        )

    def weighted_difference_erpr(player):
        return (
                overpowerment_weight * abs(
            player.overpowerment - target_player.overpowerment - buff()) +
                ruthlessness_weight * abs(
            player.ruthlessness - target_player.ruthlessness - buff()) +
                unthwackability_weight * abs(
            player.unthwackability - target_player.unthwackability - buff())
        )

    def buff():
        return 0

    all_batters = (player for player in all_players.values()
                   if is_league_player(player))
    best_matches = sorted(all_batters, key=weighted_difference_erpr)

    n_printed = 0
    for player in best_matches:
        if player in player.league_team.rotation:
            print(player.name, weighted_difference_erpr(player))
            n_printed += 1
            if n_printed > 10:
                break


def is_league_player(player):
    try:
        return player.league_team and player in player.league_team.rotation
    except (ValueError, HTTPError):
        return False


def main():
    parser = ArgumentParser()
    parser.add_argument('player_id')

    args = parser.parse_args()

    compare(args.player_id)


if __name__ == '__main__':
    main()
