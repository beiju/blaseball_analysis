import json
from argparse import ArgumentParser
from collections import defaultdict
from itertools import groupby
from os import path
from urllib.request import urlretrieve

from blaseball_mike import chronicler

CLAB = '8d87c468-699a-47a8-b40d-cfb73a5660ad'


def download_games():
    games = chronicler.get_games(season=13, team_ids=['8d87c468-699a-47a8-b40d-cfb73a5660ad'])
    for i, game in enumerate(games):
        if i != 24:
            continue
        game_url = f"https://api.sibr.dev/chronicler/v1/games/updates?game={game['gameId']}&count=1000"
        game_file_path = f"data/{i}.json"
        urlretrieve(game_url, game_file_path)
        print("Downloaded game", i)


class GameState(object):
    # Events that don't change any of the game state that I track
    flavor_events = {
        "A desolate peanutty wind blows.",
        "Peanut fragments rustle on the infield.",
        "A solitary peanut rolls onto the field. Nobody cares.",
        "The faint crunch of a shell underfoot",
        "The sour smell of rancid peanuts on the wind",
        "The Birds circle ... but they don't find what they're looking for.",
        "swallowed a stray peanut and had an allergic reaction!",
        "has returned from Elsewhere",
        "They became Magmatic!",
        "The Blooddrain gurgled!",
        "They are now Triple Threats!",
        "is now Reverberating wildly!",
        "is Partying!",
        " has been cured of their peanut allergy!",
    }

    number_of_bases = 4  # Someone can update this for fifth base if they want

    def __init__(self):
        self.inning = 0
        self.top_of_inning = True
        self.balls = 0
        self.strikes = 0
        self.outs = 0
        self.runners_on = [0 for _ in range(GameState.number_of_bases)]

        self.runs_home = 0
        self.runs_away = 0

        self.home_team = None  # Will be set once we get a game
        self.away_team = None  # Will be set once we get a game

    def consume(self, update):
        self.home_team = update['homeTeam']
        self.away_team = update['awayTeam']
        if update['phase'] == 0:
            print("Game created")
        elif update['phase'] == 1:
            print("Game start")
        elif update['phase'] == 2:
            print("Inning start")
        elif update['phase'] == 6:
            # Game event
            self.consume_game_event(update)
        elif update['phase'] == 3:
            # Game event that ends the top half-inning
            self.consume_game_event(update)
            print("Half-inning end", update['lastUpdate'])
            self.reset_half_inning()
        elif update['phase'] == 7:
            # Game event that ends the game. Don't process it because it breaks assertions
            print("Half-inning end and game end", update['lastUpdate'])
            assert self.runs_away == update['awayScore']
            assert self.runs_home == update['homeScore']
        else:
            raise RuntimeError("Unknown phase: " + str(update['phase']))

    def reset_at_bat(self):
        self.balls = 0
        self.strikes = 0

    def reset_half_inning(self):
        self.reset_at_bat()
        self.clear_bases()
        self.outs = 0

    def consume_game_event(self, update):
        print(update['lastUpdate'])

        assert update['inning'] == self.inning
        assert update['topOfInning'] == self.top_of_inning

        if update['inning'] != self.inning or update['topOfInning'] != self.top_of_inning:
            # Then the real half-inning kept going while the simulated one stopped. skip this update
            if update['topOfInning']:
                print("Skipping update at top of inning", update['inning'] + 1)
            else:
                print("Skipping update at top of inning", update['inning'] + 1)

            return

        if update['lastUpdate'].startswith("Top of "):
            print("Half-inning start")
        elif update['lastUpdate'].startswith("Bottom of "):
            print("Half-inning start")
        elif " batting for the " in update['lastUpdate']:
            print("Batter up")
        elif update['lastUpdate'].startswith("Strike, "):
            self.strike(update)
        elif " hit a ground out to " in update['lastUpdate']:
            self.out(update)
        elif " hit a flyout to " in update['lastUpdate']:
            self.out(update)
        elif " strikes out " in update['lastUpdate']:
            self.strike(update)
        elif update['lastUpdate'].startswith("Foul Ball."):
            self.foul(update)
        elif update['lastUpdate'].startswith("Ball."):
            self.ball(update)
        elif " draws a walk." in update['lastUpdate']:
            self.ball(update)
        elif " home run!" in update['lastUpdate']:
            self.home_run(update)
        elif " hits a Single!" in update['lastUpdate']:
            self.hit(update)
        elif " hits a Double!" in update['lastUpdate']:
            self.hit(update)
        elif " hits a Triple!" in update['lastUpdate']:
            self.hit(update)
        elif "Baserunners are swept from play" in update['lastUpdate']:
            self.clear_bases()
        elif " steals " in update['lastUpdate'] and " base!" in update['lastUpdate']:
            self.steal(update)
        elif update['lastUpdate'].endswith("reaches on fielder's choice."):
            # For scoring purposes I don't THINK it matters who replaced whom
            self.out(update)
        elif "hit into a double play!" in update['lastUpdate']:
            self.out(update, 2)
        elif " gets caught stealing " in update['lastUpdate']:
            self.caught_stealing(update)
        elif "throws a Mild pitch!\nBall," in update['lastUpdate']:
            self.ball(update)
        elif " is Elsewhere.." in update['lastUpdate'] or " is Shelled and cannot escape " in update['lastUpdate']:
            print("Player skip")
        elif update['lastUpdate'].endswith(" hits a grand slam!"):
            self.home_run(update)
        elif "They run to safety, resulting in an out." in update['lastUpdate']:
            self.out(update)
        elif "walks to first base." in update['lastUpdate']:  # Love blood
            self.walk(update)
        elif "swings 4 times to strike out willingly!" in update['lastUpdate']:  # Love blood
            self.out(update)
        elif any(event in update['lastUpdate'] for event in GameState.flavor_events):
            print("Flavor event")
        else:
            raise RuntimeError("Unknown game update")

        assert update['halfInningOuts'] == self.outs
        assert update['atBatStrikes'] == self.strikes

        assert sum(r for r in self.runners_on) == len(update['basesOccupied'])
        # Goddamn blaseball making me do epsilon comparisons on number of runs
        assert abs(update['homeScore'] - self.runs_home) < 1e-6
        assert abs(update['awayScore'] - self.runs_away) < 1e-6

        print(f"{self.runs_away:.1f}-{self.runs_home:.1f}")

    def advance_half_inning(self):
        if self.top_of_inning:
            self.top_of_inning = False
        else:
            self.top_of_inning = True
            self.inning += 1

        self.reset_half_inning()

    def strike(self, update):
        print("Strike")
        self.strikes += 1

        max_strikes = update['awayStrikes'] if update['topOfInning'] else update['homeStrikes']
        # if update['topOfInning'] and self.away_team == CLAB or not update['topOfInning'] and self.home_team == CLAB:
        #     max_strikes -= 1

        assert self.strikes <= max_strikes

        if self.strikes == max_strikes:
            self.out(update)

            # Handle Triple Threat runs
            if abs(update['awayScore'] - self.runs_away + 0.3) < 1e-6:
                # Away got triple threatted
                self.runs_away -= 0.3
            elif abs(update['homeScore'] - self.runs_home + 0.3) < 1e-6:
                # Home got triple threatted
                self.runs_home -= 0.3

    def out(self, update, num_out=1, without_reset=False):
        if without_reset:
            print("Out (without ending the at-bat)")
        else:
            print("Out")
        self.outs += num_out
        if not without_reset:
            self.reset_at_bat()

        max_outs = update['awayOuts'] if update['topOfInning'] else update['homeOuts']
        assert self.outs <= max_outs

        # Runners can move and score on the sacrifice
        runner_change = self.move_runners(update)

        runners_scored = (update['lastUpdate'].count(" advances on the sacrifice.") +
                          update['lastUpdate'].count(" scores!"))
        self.score_runs(runners_scored, update)

        if self.outs == max_outs:
            self.advance_half_inning()
            return True
        else:
            assert runner_change == 1 - runners_scored - num_out
            return False

    def foul(self, update):
        print("Foul")
        max_strikes = update['awayStrikes'] if update['topOfInning'] else update['homeStrikes']
        assert self.strikes <= max_strikes

        if self.strikes + 1 < max_strikes:
            self.strike(update)

    def ball(self, update):
        print("Ball")
        self.balls += 1

        max_balls = update['awayBalls'] if update['topOfInning'] else update['homeBalls']
        assert self.balls <= max_balls

        if self.balls == max_balls:
            self.walk(update)

        if "Runners advance on the pathetic play!" in update['lastUpdate']:
            runners_changed = self.move_runners(update)
            runners_scored = update['lastUpdate'].count(" scores!")
            assert runners_changed == -runners_scored

            self.score_runs(runners_scored, update)

    def walk(self, update):
        print("Simulating Walk as a Hit")
        self.hit(update)

    def home_run(self, update):
        print("Home run")
        runs_scored = 1  # Starts with 1 for the batter
        for i, runners in enumerate(self.runners_on):
            runs_scored += runners
        self.clear_bases()

        self.score_runs(runs_scored, update)
        self.reset_at_bat()

    def score_runs(self, runs_scored, update):
        if update['topOfInning']:
            self.runs_away += runs_scored
        else:
            self.runs_home += runs_scored

    def hit(self, update):
        print("Hit")

        runners_changed = self.move_runners(update)

        runners_out = update['lastUpdate'].count(" out at ")
        runners_scored = update['lastUpdate'].count(" scores!")

        # Make sure that the change in runners, except for the addition of the hitter, matches the number of runners
        # out + number of runners home
        assert runners_changed == 1 - runners_out - runners_scored

        for _ in range(runners_out):
            self.out(update)

        self.score_runs(runners_scored, update)
        self.reset_at_bat()

    def move_runners(self, update):
        runner_change = 0
        for i, runners in enumerate(self.runners_on):
            new_runners = update['basesOccupied'].count(i)
            runner_change += new_runners - runners
            self.runners_on[i] = new_runners

        return runner_change

    def clear_bases(self):
        for i, _ in enumerate(self.runners_on):
            self.runners_on[i] = 0

    def steal(self, update):
        print("Steal")
        runner_change = self.move_runners(update)

        # This won't be right with Fifth Base but eh
        if update['lastUpdate'].endswith(" steals fourth base!"):
            self.score_runs(1, update)
            assert runner_change == -1
        else:
            assert runner_change == 0

    def caught_stealing(self, update):
        print("Caught stealing")
        runner_change = self.move_runners(update)
        inning_ended = self.out(update, without_reset=True)
        assert inning_ended or runner_change == -1

    # Not necessarily the opposite of is_clab_bad! If a game would have continued under
    # the simulated circumstances, the simulation cannot continue and so stops it at a tie.
    # In that case, clab is neither good nor bad.
    def is_clab_good(self):
        if self.home_team == CLAB:
            return self.runs_home > self.runs_away
        elif self.away_team == CLAB:
            return self.runs_home < self.runs_away

        raise RuntimeError("Clab not found!")

    # Not necessarily the opposite of is_clab_good! See comment over is_clab_good.
    def is_clab_bad(self):
        if self.home_team == CLAB:
            return self.runs_home < self.runs_away
        elif self.away_team == CLAB:
            return self.runs_home > self.runs_away

        raise RuntimeError("Clab not found!")


def simulate_season():
    clab_good_games = 0
    clab_bad_games = 0
    for i in range(99):
        if i == 24:
            # Chronicle broke for this game so the data does not exist. We scored 0 runs, though, so clab good is not
            # likely under most circumstances
            clab_bad_games += 1
            continue

        events_file_path = f"data/{i}.json"
        if not path.exists(events_file_path):
            print("Season over")
            break

        with open(events_file_path, 'r') as events_file:
            events = json.load(events_file)

        state = GameState()

        for event in events['data']:
            state.consume(event['data'])

        if state.is_clab_good():
            clab_good_games += 1
        if state.is_clab_bad():
            clab_bad_games += 1

    print("CLAB GOOD:", clab_good_games, "CLAB BAD:", clab_bad_games)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--download', action='store_true')

    args = parser.parse_args()

    if args.download:
        download_games()
    else:
        simulate_season()
