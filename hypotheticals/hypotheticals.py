from argparse import ArgumentParser

from blaseball_mike import chronicler, database, models
from blaseball_mike.session import session, check_network_response


def get_events_from_datablase(s, game_id):
    return check_network_response(s.get("https://api.blaseball-reference.com/v1/events", params={
        "gameId": game_id,
        "baseRunners": True,
    }))['results']


def hypothetical_game(team, game_id, args, s):
    print(f"Running hypothetical on game {game_id}")
    events = get_events_from_datablase(s, game_id)
    for event in events:
        pass


def hypothetical_season(team, args):
    print(f"Running hypothetical on {team.full_name} for season {args.season}")
    s = session(expiry=None)
    for game_id in models.Game.load_by_season(args.season, team_id=team.id):
        hypothetical_game(team, game_id, args, s)


def main(args):
    team = models.Team.load_by_name(args.team)
    hypothetical_season(team, args)


if __name__ == '__main__':
    parser = ArgumentParser("Blaseball Hypotheticals")
    # TODO: Add support for running a hypothetical on a whole season
    parser.add_argument('--team', required=True, help="Team whose hypothetical to run")
    parser.add_argument('--season', type=int, required=True, help="Season whose hypothetical to run")

    adjustments = parser.add_argument_group('adjustments', "Adjustments")

    main(parser.parse_args())
