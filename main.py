import json
import re
from argparse import ArgumentParser
from os import path
from urllib.request import urlretrieve

import matplotlib.pyplot as plt
import numpy as np
from blaseball_mike import chronicler
from matplotlib import colors

CLAB = '8d87c468-699a-47a8-b40d-cfb73a5660ad'

num_games = 99


def download_games():
    games = chronicler.get_games(season=10, team_ids=['8d87c468-699a-47a8-b40d-cfb73a5660ad'])
    for i, game in enumerate(games):
        game_url = f"https://api.sibr.dev/chronicler/v1/games/updates?game={game['gameId']}&count=1000"
        game_file_path = f"data-s10/{i}.json"
        urlretrieve(game_url, game_file_path)
        print("Downloaded gameId", i)


runners_scored_re = re.compile(r'^(.+) (?:scores!|advances on the sacrifice\.|steals fourth base!)', flags=re.MULTILINE)
out_without_reaching_re = re.compile(
    r'hit a (?:ground |fly)out|strikes out (?:looking|swinging)|swings \d times to strike out willingly')
out_at_base_re = re.compile(
    r'^(.+) (?:out at (?:first|second|third|fourth) base\.|gets caught stealing)|A murder of Crows ambush (.+)!$',
    flags=re.MULTILINE)


crab_hits_onto_base = 0
crab_hits_into_hr = 0
crab_hits_into_outs = 0
crab_hits_into_fc = 0
crab_fouls = 0
crab_walks = 0

crab_strikeouts_swinging = 0
crab_strikeouts_looking = 0

opponent_hits_onto_base = 0
opponent_hits_into_hr = 0
opponent_hits_into_outs = 0
opponent_hits_into_fc = 0
opponent_fouls = 0
opponent_walks = 0

opponent_strikeouts_swinging = 0
opponent_strikeouts_looking = 0

def is_crab(update):
    if update['topOfInning']:
        return update['awayTeam'] != CLAB
    else:
        return update['homeTeam'] != CLAB


class GameState(object):
    # Events that don't change any of the gameId state that I track
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
        "BIRD NOISES",
        "The Shame Pit activates!",
        "These birds hate Blaseball!",
        "Rogue Umpire incinerated ",
        "Don't feed the birds",
        "Have you ever seen this many birds?",
        "The birds are mad at you. You specifically. You know who you are.",
        "The birds are after the children...",
        "The Electricity zaps a strike away!",
        "Several birds are pecking...",
        "Game over.",
        "Oh dear Gods...",
        "Where did these birds come from?",
        "What are we gonna do with all these birds?",
        "This is too many birds.",
        "There's just too many birds!",
        "They're clearing feathers off the field...",
        "The birds are very loud!",
        "I hardly think a few birds are going to bring about the end of the world.",
        "The birds continue to stare.",
        "The birds are paralyzed! They can't move!",
        "Do these birds have souls?",
    }

    number_of_bases = 4  # Someone can update this for fifth base if they want

    def __init__(self, optimistic=True):
        self.optimistic = optimistic
        
        self.inning = 0
        self.top_of_inning = True
        self.balls = 0
        self.strikes = 0
        self.outs = 0
        self.runners_on = [0 for _ in range(GameState.number_of_bases)]

        self.runs_home = 0
        self.runs_away = 0

        self.home_team = None  # Will be set once we get a gameId
        self.away_team = None  # Will be set once we get a gameId

        self.borrowed_time = False
        self.reached_on_borrowed_time = []  # Intentionally a list, not a set, because of Kennedy Loser
        self.potentially_out_by_scoring_during_borrowed_time = []
        self.current_batter = None
        self.runs_by_reaching_on_borrowed_time = 0
        self.runs_scored_on_borrowed_time = 0
        self.double_borrowed_runs = 0
        self.recoverable_runs = 0

        self.player_id_to_name = {}
        self.baserunners_prev = []

    def consume(self, update):
        self.home_team = update['homeTeam']
        self.away_team = update['awayTeam']
        if update['phase'] == 0:
            print("Game created")
        elif update['phase'] == 1:
            print("Game start")
        elif update['phase'] == 2:
            print("Inning start")
        elif update['phase'] == 5:
            print("Batter up (pre-s10)")
            self.consume_game_event(update)
        elif update['phase'] == 6:
            # Game event
            self.consume_game_event(update)
        elif update['phase'] == 3:
            # Game event that ends the top half-inning
            self.consume_game_event(update)
            print("Half-inning end", update['lastUpdate'])
            self.reset_half_inning()
        elif update['phase'] == 7:
            # Game event that ends the gameId. Don't process it because it breaks assertions
            print("Half-inning end and gameId end", update['lastUpdate'])
            assert self.runs_away == update['awayScore']
            assert self.runs_home == update['homeScore']
        else:
            raise RuntimeError("Unknown phase: " + str(update['phase']))

    def reset_at_bat(self):
        self.balls = 0
        self.strikes = 0
        self.borrowed_time = False

    def reset_half_inning(self):
        self.reset_at_bat()
        self.clear_bases()
        self.outs = 0
        self.reached_on_borrowed_time = []
        self.potentially_out_by_scoring_during_borrowed_time = []
        self.borrowed_time = False

    def consume_game_event(self, update):
        global crab_hits_onto_base, crab_hits_into_fc, crab_hits_into_hr, crab_hits_into_outs, crab_fouls, crab_walks
        global crab_strikeouts_swinging, crab_strikeouts_looking
        global opponent_hits_onto_base, opponent_hits_into_fc, opponent_hits_into_hr, opponent_hits_into_outs
        global opponent_fouls, opponent_walks, opponent_strikeouts_swinging, opponent_strikeouts_looking

        print(update['lastUpdate'])

        # assert update['inning'] == self.inning
        # assert update['topOfInning'] == self.top_of_inning

        # if update['inning'] != self.inning or update['topOfInning'] != self.top_of_inning:
        #     # Then the real half-inning kept going while the simulated one stopped. skip this update
        #     if update['topOfInning']:
        #         print("Skipping update at top of inning", update['inning'] + 1)
        #     else:
        #         print("Skipping update at top of inning", update['inning'] + 1)
        #
        #     return

        if self.borrowed_time:
            print("BORROWED TIME: ", end='')

        if update['lastUpdate'].startswith("Top of "):
            print("Half-inning start")
        elif update['lastUpdate'].startswith("Bottom of "):
            print("Half-inning start")
        elif " batting for the " in update['lastUpdate']:
            self.current_batter = update['lastUpdate'][:update['lastUpdate'].index(" batting for the")]
            batter_id = update['awayBatter'] if update['topOfInning'] else update['homeBatter']
            self.player_id_to_name[batter_id] = self.current_batter
            print("Batter up")
        elif update['lastUpdate'].startswith("Strike, "):
            self.strike(update)
        elif " hit a ground out to " in update['lastUpdate'] or " scores on the sacrifice." in update['lastUpdate']:
            self.out(update)
            crab_hits_into_outs += is_crab(update)
            opponent_hits_into_outs += not is_crab(update)
        elif " hit a flyout to " in update['lastUpdate'] or " hit a sacrifice fly." in update['lastUpdate']:
            self.out(update)
            crab_hits_into_outs += is_crab(update)
            opponent_hits_into_outs += not is_crab(update)
        elif " strikes out " in update['lastUpdate']:
            self.strike(update)
            if "swinging" in update['lastUpdate']:
                crab_strikeouts_swinging += is_crab(update)
                opponent_strikeouts_swinging += not is_crab(update)
            elif "looking" in update['lastUpdate']:
                crab_strikeouts_looking += is_crab(update)
                opponent_strikeouts_looking += not is_crab(update)
            else:
                raise RuntimeError("What kind of strikeout is this")
        elif update['lastUpdate'].startswith("Foul Ball."):
            self.foul(update)
            crab_fouls += is_crab(update)
            opponent_fouls += not is_crab(update)
        elif update['lastUpdate'].startswith("Ball."):
            self.ball(update)
        elif " draws a walk." in update['lastUpdate']:
            self.ball(update)
            crab_walks += is_crab(update)
            opponent_walks += not is_crab(update)
        elif " home run!" in update['lastUpdate']:
            self.home_run(update)
            crab_hits_into_hr += is_crab(update)
            opponent_hits_into_hr += not is_crab(update)
        elif (" hits a Single!" in update['lastUpdate'] or " hits a Double!" in update['lastUpdate'] or
              " hits a Triple!" in update['lastUpdate'] or " hits a Quadruple!" in update['lastUpdate']):
            self.hit(update)
            crab_hits_onto_base += is_crab(update)
            opponent_hits_onto_base += not is_crab(update)
        elif "Baserunners are swept from play" in update['lastUpdate']:
            self.clear_bases()
        elif " steals " in update['lastUpdate'] and " base!" in update['lastUpdate']:
            self.steal(update)
        elif "reaches on fielder's choice." in update['lastUpdate']:
            # For scoring purposes I don't THINK it matters who replaced whom
            self.out(update)
            crab_hits_into_fc += is_crab(update)
            opponent_hits_into_fc += not is_crab(update)
        elif "hit into a double play!" in update['lastUpdate']:
            self.out(update, 2)
            crab_hits_into_outs += is_crab(update)
            opponent_hits_into_outs += not is_crab(update)
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
        elif " times to strike out willingly!" in update['lastUpdate']:  # Love blood
            self.out(update)
        elif any(event in update['lastUpdate'] for event in GameState.flavor_events) or re.match(r"^\d+ Birds$", update['lastUpdate']):
            print("Flavor event")
        else:
            raise RuntimeError("Unknown gameId update")

        self.baserunners_prev = update['baseRunners']

        # assert update['halfInningOuts'] == self.outs
        # assert update['atBatStrikes'] == self.strikes

        # assert sum(r for r in self.runners_on) == len(update['basesOccupied'])
        # # Goddamn blaseball making me do epsilon comparisons on number of runs
        # assert abs(update['homeScore'] - self.runs_home) < 1e-6
        # assert abs(update['awayScore'] - self.runs_away) < 1e-6

        away_str = "{0:.1f}".format(self.runs_away).rstrip('0').rstrip('.')
        home_str = "{0:.1f}".format(self.runs_home).rstrip('0').rstrip('.')
        print(
            f"{self.outs} outs, {self.strikes} strikes, {self.balls} balls, {sum(self.runners_on)} on, score {away_str}-{home_str}")

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
        if update['topOfInning'] and self.away_team == CLAB or not update['topOfInning'] and self.home_team == CLAB:
            self.borrowed_time = self.strikes == max_strikes - 1

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

        if out_without_reaching_re.search(update['lastUpdate']) is None:
            runners_out = out_at_base_re.findall(update['lastUpdate'])
            if "hit into a double play!" in update['lastUpdate']:
                # Find the runner who got out. The gameId doesn't tell us.
                runners_out.append(self.player_id_to_name[
                                       [player for player in self.baserunners_prev if
                                        player not in update['baseRunners']][0]])
                assert len(runners_out) == num_out - 1
            else:
                # assert len(runners_out) == num_out
                pass
            for runnertup in runners_out:
                if isinstance(runnertup, tuple):
                    runner = runnertup[0] if runnertup[0] != '' else runnertup[1]
                else:
                    runner = runnertup
                assert runner != ''
                try:
                    self.reached_on_borrowed_time.remove(runner)
                except ValueError:
                    pass

                try:
                    self.potentially_out_by_scoring_during_borrowed_time.remove(runner)
                except ValueError:
                    pass

        self.outs += num_out
        if not without_reset:
            self.reset_at_bat()

        if 'awayOuts' in update:
            max_outs = update['awayOuts'] if update['topOfInning'] else update['homeOuts']
        else:
            max_outs = 3
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
            # assert runner_change == 1 - runners_scored - num_out
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

        if 'awayBalls' in update:
            max_balls = update['awayBalls'] if update['topOfInning'] else update['homeBalls']
        else:
            max_balls = 4
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

        self.score_runs(runs_scored, update)
        self.clear_bases()
        self.reset_at_bat()

    def score_runs(self, runs_scored, update):
        runs_by_reaching_on_borrowed_time = 0
        if "home run!" in update['lastUpdate'] or "grand slam!" in update['lastUpdate']:
            runners_who_scored = [self.player_id_to_name[player_id] for player_id in self.baserunners_prev]
            # During a home run, all batters who reached on borrowed time (and are still on) score
            runs_by_reaching_on_borrowed_time += len(self.reached_on_borrowed_time)
            self.reached_on_borrowed_time = []
        else:
            runners_who_scored = runners_scored_re.findall(update['lastUpdate'])
            assert len(runners_who_scored) == runs_scored
            for runner in runners_who_scored:
                if runner in self.reached_on_borrowed_time:
                    runs_by_reaching_on_borrowed_time += 1
                    self.reached_on_borrowed_time.remove(runner)

        self.runs_by_reaching_on_borrowed_time += runs_by_reaching_on_borrowed_time

        if update['topOfInning']:
            self.runs_away += runs_scored
        else:
            self.runs_home += runs_scored

        if self.borrowed_time or self.outs_without_borrowed_time() >= 3:
            self.runs_scored_on_borrowed_time += runs_scored
            self.potentially_out_by_scoring_during_borrowed_time.extend(runners_who_scored)

            self.double_borrowed_runs += runs_by_reaching_on_borrowed_time

            # An run is *recoverable* if it was scored during borrowed time, but there's more time in the inning
            # to make it up. This happens if there would be 1 or 0 outs without 4th strike -- as soon as you
            # enter borrowed time with 2 outs on the board, you would never get any more time if not for 4th strike.
            # However, runs scored by reaching on borrowed time can't be recovered like this, since the player wasn't
            # there in the first place.
            if self.outs_without_borrowed_time() < 2:
                self.recoverable_runs += runs_scored - runs_by_reaching_on_borrowed_time

    def outs_without_borrowed_time(self):
        result = self.outs + len(self.reached_on_borrowed_time)
        # Any run scored during borrowed time could've been an out instead (by Caught Stealing, if nothing else)
        if not self.optimistic:
            result += len(self.potentially_out_by_scoring_during_borrowed_time)
        return result

    def hit(self, update):
        print("Hit")

        if self.borrowed_time:
            self.reached_on_borrowed_time.append(self.current_batter)
            print(self.current_batter, "reached on borrowed time")

        runners_changed = self.move_runners(update)

        runners_out = update['lastUpdate'].count(" out at ")
        runners_scored = update['lastUpdate'].count(" scores!")

        # Make sure that the change in runners, except for the addition of the hitter, matches the number of runners
        # out + number of runners home
        # assert runners_changed == 1 - runners_out - runners_scored

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
        self.reached_on_borrowed_time = []

    def steal(self, update):
        print("Steal")
        runner_change = self.move_runners(update)

        # This won't be right with Fifth Base but eh
        if update['lastUpdate'].endswith(" steals fourth base!"):
            self.score_runs(1, update)
            # assert runner_change == -1
        else:
            assert runner_change == 0

    def caught_stealing(self, update):
        print("Caught stealing")
        runner_change = self.move_runners(update)
        inning_ended = self.out(update, without_reset=True)
        assert inning_ended or runner_change == -1

    # Not necessarily the opposite of is_clab_bad! If a gameId would have continued under
    # the simulated circumstances, the simulation cannot continue and so stops it at a tie.
    # In that case, clab is neither good nor bad.
    def is_clab_good(self, adjust_runs=True, adjust_runs_optimist=True):
        return self.crab_runs(adjust_runs, adjust_runs_optimist) > self.not_crab_runs()

    # Not necessarily the opposite of is_clab_good! See comment over is_clab_good.
    def is_clab_bad(self, adjust_runs=True, adjust_runs_optimist=True):
        return self.crab_runs(adjust_runs, adjust_runs_optimist) < self.not_crab_runs()

    def crab_runs(self, adjust_runs=True, adjust_runs_optimist=True):
        run_adjustment = 0
        if adjust_runs:
            run_adjustment = (self.runs_scored_on_borrowed_time +
                              self.runs_by_reaching_on_borrowed_time -
                              self.double_borrowed_runs)
            if adjust_runs_optimist:
                run_adjustment -= self.recoverable_runs

        if self.home_team == CLAB:
            return self.runs_home - run_adjustment
        elif self.away_team == CLAB:
            return self.runs_away - run_adjustment

        raise RuntimeError("Clab not found!")

    def not_crab_runs(self):
        if self.home_team == CLAB:
            return self.runs_away
        elif self.away_team == CLAB:
            return self.runs_home

        raise RuntimeError("Clab not found!")


def simulate_season():
    games_won_optimist, games_won_pessimist = 0, 0
    games_lost_optimist, games_lost_pessimist = 0, 0
    runs_total = 0
    runs_scored_on_borrowed_time = 0
    runs_by_reaching_on_borrowed_time = 0
    double_borrowed_runs = 0
    recoverable_runs = 0

    crab_score = []
    crab_score_adjusted_optimist = []
    crab_score_adjusted_pessimist = []
    opponent_score = []

    crab_strikes_flinching = 0
    crab_strikes_looking = 0
    crab_strikes_swinging = 0

    opponent_strikes_flinching = 0
    opponent_strikes_looking = 0
    opponent_strikes_swinging = 0
    for i in range(num_games):
        if i == 24:
            # Chronicle broke for this gameId so the data does not exist. We scored 0 runs, though, so clab good is not
            # likely under most circumstances
            games_lost_optimist += 1

            crab_score.append(0)
            crab_score_adjusted_optimist.append(0)
            crab_score_adjusted_pessimist.append(0)
            opponent_score.append(1)

            continue

        events_file_path = f"data/{i}.json"
        if not path.exists(events_file_path):
            print("Season over")
            break

        with open(events_file_path, 'r') as events_file:
            events = json.load(events_file)

        optimist_state = GameState(optimistic=True)
        pessimist_state = GameState(optimistic=False)

        for event in events['data']:
            e = event['data']
            optimist_state.consume(e)
            pessimist_state.consume(e)

            if "Strike, flinching" in e['lastUpdate']:
                crab_strikes_flinching += is_crab(e)
                opponent_strikes_flinching += not is_crab(e)
            elif "Strike, looking" in e['lastUpdate']:
                crab_strikes_looking += is_crab(e)
                opponent_strikes_looking += not is_crab(e)
            elif "Strike, swinging" in e['lastUpdate']:
                crab_strikes_swinging += is_crab(e)
                opponent_strikes_swinging += not is_crab(e)

        if optimist_state.is_clab_good(adjust_runs=True, adjust_runs_optimist=True):
            games_won_optimist += 1
        if optimist_state.is_clab_bad(adjust_runs=True, adjust_runs_optimist=True):
            games_lost_optimist += 1
            
        if pessimist_state.is_clab_good(adjust_runs=True, adjust_runs_optimist=False):
            games_won_pessimist += 1
        if pessimist_state.is_clab_bad(adjust_runs=True, adjust_runs_optimist=False):
            games_lost_pessimist += 1

        crab_score.append(optimist_state.crab_runs(adjust_runs=False))
        crab_score_adjusted_optimist.append(optimist_state.crab_runs(adjust_runs=True, adjust_runs_optimist=True))
        crab_score_adjusted_pessimist.append(pessimist_state.crab_runs(adjust_runs=True, adjust_runs_optimist=False))
        opponent_score.append(optimist_state.not_crab_runs())

        state = optimist_state
        runs_scored_on_borrowed_time += state.runs_scored_on_borrowed_time
        runs_by_reaching_on_borrowed_time += state.runs_by_reaching_on_borrowed_time
        double_borrowed_runs += state.double_borrowed_runs
        recoverable_runs += state.recoverable_runs
        runs_total += state.crab_runs()

    unknown_games_optimist = num_games - (games_won_optimist + games_lost_optimist)
    print(f"OPTIMIST: {games_won_optimist}-{games_lost_optimist} ({unknown_games_optimist} unknown)")
    unknown_games_pessimist = num_games - (games_won_pessimist + games_lost_pessimist)
    print(f"PESSIMIST: {games_won_pessimist}-{games_lost_pessimist} ({unknown_games_pessimist} unknown)")
    print(runs_total, "runs scored after adjustment")
    print(runs_scored_on_borrowed_time, "runs scored during borrowed time")
    print(runs_by_reaching_on_borrowed_time, "runs scored by players who reached the base because of borrowed time")
    print(double_borrowed_runs, "runs scored during borrowed time by players who reached the base because of borrowed "
                                "time (i.e. overlap between the previous two categories)")
    print(recoverable_runs, "runs scored during borrowed time which could still have been scored later in the inning")

    plot(np.array(crab_score), np.array(crab_score_adjusted_optimist), np.array(crab_score_adjusted_pessimist),
         np.array(opponent_score))


def plot(crab_score, crab_score_adjusted, crab_score_adjusted_pessimist, opponent_score):
    # matplotlib.style.use('ggplot')

    x = list(range(1, num_games + 1))

    # crab_score /= opponent_score
    # crab_score_adjusted /= opponent_score
    # crab_score_adjusted_pessimist /= opponent_score
    # opponent_score /= opponent_score

    labels = ["Crab (actual)", "Crab without 4th strike (optimist)", "Crab without 4th strike (pessimist)", "Not Crab"]

    fig, ax = plt.subplots(figsize=[34, 6])
    ax.bar(x, crab_score - crab_score_adjusted,
           bottom=crab_score_adjusted,
           width=0.4, align='edge', color=colors.to_rgba('tab:red', 0.2), edgecolor='tab:red', hatch='///')
    ax.bar(x, crab_score_adjusted - crab_score_adjusted_pessimist,
           bottom=crab_score_adjusted_pessimist,
           width=0.4, align='edge', color=colors.to_rgba('tab:red', 0.5), edgecolor='tab:red', hatch='xxx')
    ax.bar(x, crab_score_adjusted_pessimist, width=0.4, align='edge', color='tab:red', edgecolor='tab:red')
    ax.bar(x, opponent_score, width=-0.4, align='edge', color=colors.to_rgba('tab:blue', 0.8), edgecolor='tab:blue')
    ax.legend(labels, loc="upper right")
    ax.set_title("Crab")
    ax.set_xlabel("Game")
    ax.set_ylabel("Score")
    ax.set_xlim(0, 100)
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--download', action='store_true')

    args = parser.parse_args()

    if args.download:
        download_games()
    else:
        simulate_season()
