import json
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from blaseball_mike import eventually, models, chronicler, utils
from dateutil.parser import parse

from util.plot_utils import error_bounds

EVENT_TYPES = {
    4,  # Stolen base
    5,  # Walk
    6,  # Strikeout
    7,  # Flyout
    8,  # Ground out
    9,  # Home run
    10,  # Hit (single/double/triple)
    13,  # Strike (not including Foul Balls)
    14,  # Ball
    15,  # Foul Ball
    22,  # Hit by pitch
    27,  # Mild pitch
    62,  # Flood
    63,  # Salmon swim upstream
    65,  # Entering the Secret Base
    66,  # Exiting the Secret Base
    67,  # Consumers attack
    70,  # Grind Rail
}


def find_player_team(event, player_id=None):
    """
    Find the team object associated with a player id in an event
    :param dict event: Eventually event
    :param str|None player_id: One of the players in event['playerTags'], or
        None to use the first player.
    :return models.Team:
    """
    if player_id is None:
        player_id = event['playerTags'][0]

    for team_id in event['teamTags']:
        team = models.Team.load_at_time(team_id, event['created'])
        if (any(player.id == player_id for player in team.rotation) or
                any(player.id == player_id for player in team.lineup)):
            return team

    raise RuntimeError("Couldn't find player's team")


def main():
    num_attacks_per_level, num_events_per_level = get_attack_rate()

    levels = sorted(num_events_per_level.keys(), key=int)
    rate = [num_attacks_per_level[level] / num_events_per_level[level] for level
            in levels]
    errors = [
        error_bounds(num_attacks_per_level[level], num_events_per_level[level])
        for level in levels]

    fig, ax = plt.subplots(1)
    ax.errorbar(levels,
                rate,
                yerr=np.array(errors).T,
                ecolor="lightgrey")
    ax.set_xlabel("Level")
    ax.set_ylabel("Consumer Attack Rate")
    # ax.set_ylim(0, 0.4)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title("Consumer attack rate by level")

    plt.show()


def get_attack_rate():
    try:
        with open('consumer_attack_rate.json', 'r') as f:
            attack_rate = json.load(f)
            num_events_per_level = attack_rate["num_events_per_level"]
            num_attacks_per_level = attack_rate["num_attacks_per_level"]

    except FileNotFoundError:
        num_events_per_level, num_attacks_per_level = load_attack_rate()

        with open('consumer_attack_rate.json', 'w') as f:
            json.dump({
                "num_events_per_level": num_events_per_level,
                "num_attacks_per_level": num_attacks_per_level,
            }, f)

    return (defaultdict(int, num_attacks_per_level),
            defaultdict(int, num_events_per_level))


def load_attack_rate():
    updates_for_team = get_updates_for_team()
    num_events_per_level = defaultdict(lambda: 0)
    num_attacks_per_level = defaultdict(lambda: 0)

    def get_update_time(team_update):
        return parse(team_update['firstSeen'])

    update_times_for_team = {
        team_id: [get_update_time(update) for update in updates]
        for team_id, updates in updates_for_team.items()
    }
    next_print = datetime.now()
    query = {
        'season_min': 14,  # First consumer attack was in season 14
        # 'type': "_or_".join((str(i) for i in RNG_EVENT_TYPES))
    }
    for event in eventually.search(query=query, limit=-1):
        if event['type'] not in EVENT_TYPES:
            continue

        event_time = parse(event['created'])
        for team_id in event['teamTags']:

            i = bisect_left(update_times_for_team[team_id], event_time)
            team_data = updates_for_team[team_id][i - 1]['data']
            level = team_data['level']

            if level is not None:
                num_events_per_level[level] += 1

                if 'CONSUMER' in event['description'] and (
                        event['playerTags'][0] in team_data['rotation'] or
                        event['playerTags'][0] in team_data['lineup']
                ):
                    num_attacks_per_level[level] += 1

        if next_print < datetime.now():
            print("Season", event['season'], "day", event['day'])
            next_print = datetime.now() + timedelta(seconds=5)

    return num_events_per_level, num_attacks_per_level


def get_updates_for_team():
    try:
        with open('../team_updates.json', 'r') as f:
            updates_for_team = json.load(f)
    except FileNotFoundError:
        updates_for_team = load_updates_for_team(updates_for_team)

        with open('../team_updates.json', 'w') as f:
            json.dump(updates_for_team, f)
    return updates_for_team


def load_updates_for_team(updates_for_team):
    teams = models.League.load().teams
    team_updates = chronicler.get_team_updates(
        ids=list(teams.keys()),
        after=utils.get_gameday_start_time(12, 1),
        lazy=True
    )
    updates_for_team = defaultdict(lambda: [])
    for i, update in enumerate(team_updates):
        updates_for_team[update['teamId']].append(update)

        if i % 100 == 0:
            print(i)
    return updates_for_team


if __name__ == '__main__':
    main()
