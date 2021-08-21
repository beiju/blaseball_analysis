import json
import os
import re
from argparse import ArgumentParser
from urllib.request import urlretrieve

import matplotlib.pyplot as plt
import numpy as np
from blaseball_mike import chronicler, models
from tqdm import tqdm


def download_games(season=18):
    games = chronicler.get_games(season=season)
    for i, game in enumerate(tqdm(games)):
        game_url = f"https://api.sibr.dev/chronicler/v1/games/updates?game={game['gameId']}&count=1000"
        team_folder_path = f"data-s{season}/{game['data']['homeTeamName']}"
        os.makedirs(team_folder_path, exist_ok=True)
        game_file_path = f"{team_folder_path}/{i}.json"
        urlretrieve(game_url, game_file_path)


runners_scored_re = re.compile(r'^(.+) (?:scores!|advances on the sacrifice\.|steals fourth base!)', flags=re.MULTILINE)
out_without_reaching_re = re.compile(
    r'hit a (?:ground |fly)out|strikes out (?:looking|swinging)|swings \d times to strike out willingly')
out_at_base_re = re.compile(
    r'^(.+) (?:out at (?:first|second|third|fourth) base\.|gets caught stealing)|A murder of Crows ambush (.+)!$',
    flags=re.MULTILINE)

# TODO: Separate special from flavor
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
    "The Birds circle...\nThe Birds pecked ",
    "  Perks up.",
    "The Community Chest Opens!",
    "A shimmering Crate descends.",
    "Smithy beckons to ",
    "The Black Hole swallows the Runs and ",
    "Sun 2 set a Win upon the ",
    "Incoming Shadow Fax...",
    " Echoed ",  # uh oh, this one is vulnerable to the Scores Baserunner problem
    " is homesick.",
    " is happy to be home.",
    " chugs a Third Wave of Coffee!",
    "The Echo Chamber traps a wave",
    " loves Peanuts.",
    " misses Peanuts.",
    "Reality flickers. Things look different ...",
    "Reverberations are at unsafe levels!",
    "Reverberations are at high levels!",
    " tastes the infinite!",
    "SALMON CANNONS FIRE",
    " are Late to the Party",
    " go Undersea. They're now Overperforming!",
    "The Peanut Mister activates!",
}


class Outcome(object):
    all = []

    def __init__(self, name):
        self.name = name
        self.batter_occurrences = [0 for _ in range(7)]
        self.pitcher_occurrences = [0 for _ in range(7)]

        Outcome.all.append(self)

    def bin(self, vibe):
        if vibe < -0.8:
            return 6  # Honestly Terrible
        if vibe < -0.4:
            return 5  # Far Less Than Ideal
        if vibe < -0.1:
            return 4  # Less Than Ideal
        if vibe < 0.1:
            return 3  # Neutral
        if vibe < 0.4:
            return 2  # Quality
        if vibe < 0.8:
            return 1  # Excellent
        return 0  # Most Excellent

    def add(self, day, batter, pitcher):
        batter_vibe = batter.get_vibe(day)
        if batter_vibe is not None:  # Ghosts from before vibes, apparently
            self.batter_occurrences[self.bin(batter_vibe)] += 1

        pitcher_vibe = pitcher.get_vibe(day)
        if pitcher_vibe is not None:  # Ghosts from before vibes, apparently
            self.pitcher_occurrences[self.bin(pitcher_vibe)] += 1

        if self != any_outcome:
            any_outcome.add(day, batter, pitcher)


any_outcome = Outcome("Any")
ball = Outcome("Ball")
strike_looking = Outcome("Strike, looking")
strike_swinging = Outcome("Strike, swinging")
strike_flinching = Outcome("Strike, flinching")
strike_thinking = Outcome("Strike, thinking")
foul = Outcome("Foul")
ground_out = Outcome("Ground out")
flyout = Outcome("Flyout")
single = Outcome("Single")
double = Outcome("Double")
triple = Outcome("Triple")
homer = Outcome("Home run")
stolen_base = Outcome("Stolen base")
grind_rail = Outcome("Grind rail")
caught_stealing = Outcome("Caught stealing")
fielders_choice = Outcome("Fielders choice")
double_play = Outcome("Double play")
special = Outcome("Special")
flavor = Outcome("Flavor")


def get_batter(update):
    if update['topOfInning']:
        return update['awayBatter']
    else:
        return update['homeBatter']


def get_pitcher(update):
    if update['topOfInning']:
        return update['awayPitcher']
    else:
        return update['homePitcher']


def tally_season(season=18):
    filenames = []
    for root, dirs, files in os.walk(f"data-s{season}", topdown=False):
        for name in files:
            filenames.append(os.path.join(root, name))

    # For testing
    # filenames = filenames[:]

    for name in tqdm(filenames):
        tally_game(name)

    for outcome in Outcome.all:
        plot(outcome)


def tally_game(game_path):
    with open(game_path, 'r') as events_file:
        events = json.load(events_file)

    state = GameState()
    for update in events['data']:
        state.consume_update(update['data'])


class GameState(object):
    def __init__(self):
        self.pitcher = None
        self.batter = None

    def consume_update(self, update):
        if update['phase'] == 0:
            # print("Game created")
            pass
        elif update['phase'] == 1:
            # print("Game start")
            pass
        elif update['phase'] == 2:
            # print("Inning start")
            pass
        elif update['phase'] == 5:
            # print("Batter up (pre-s10)")
            self.consume_game_event(update)
        elif update['phase'] == 6:
            # Game event
            self.consume_game_event(update)
        elif update['phase'] == 3:
            # Game event that ends the top half-inning
            self.consume_game_event(update)
        elif update['phase'] == 7:
            # Game event that ends the game. Don't process it because it breaks assertions
            self.consume_game_event(update)
        else:
            raise RuntimeError("Unknown phase: " + str(update['phase']))

    def consume_game_event(self, update):
        if get_batter(update) is not None:
            self.batter = models.Player.load_one(get_batter(update))
        if get_pitcher(update) is not None:
            self.pitcher = models.Player.load_one(get_pitcher(update))

        if update['lastUpdate'].startswith("Top of "):
            # print("Half-inning start")
            pass
        elif update['lastUpdate'].startswith("Bottom of "):
            # print("Half-inning start")
            pass
        elif " batting for the " in update['lastUpdate']:
            # print("Batter up")
            pass
        elif "Strike, swinging" in update['lastUpdate'] or "Strikes, swinging" in update['lastUpdate']:
            strike_swinging.add(update['day'], self.batter, self.pitcher)
        elif "Strike, looking" in update['lastUpdate'] or "Strikes, looking" in update['lastUpdate']:
            strike_looking.add(update['day'], self.batter, self.pitcher)
        elif "Strike, flinching" in update['lastUpdate'] or "Strikes, flinching" in update['lastUpdate']:
            strike_flinching.add(update['day'], self.batter, self.pitcher)
        elif " hit a ground out to " in update['lastUpdate'] or " scores on the sacrifice." in update['lastUpdate']:
            ground_out.add(update['day'], self.pitcher, self.batter)
        elif " hit a flyout to " in update['lastUpdate'] or " hit a sacrifice fly." in update['lastUpdate']:
            flyout.add(update['day'], self.pitcher, self.batter)
        elif " strikes out " in update['lastUpdate']:
            if "swinging" in update['lastUpdate']:
                strike_swinging.add(update['day'], self.batter, self.pitcher)
            elif "looking" in update['lastUpdate']:
                strike_looking.add(update['day'], self.batter, self.pitcher)
            elif "thinking" in update['lastUpdate']:
                strike_thinking.add(update['day'], self.batter, self.pitcher)
            else:
                raise RuntimeError("What kind of strikeout is this")
        elif "Foul Ball." in update['lastUpdate'] or "Foul Balls." in update['lastUpdate']:
            foul.add(update['day'], self.batter, self.pitcher)
        elif update['lastUpdate'].startswith("Ball.") or "\nBall. " in update['lastUpdate']:
            ball.add(update['day'], self.batter, self.pitcher)
        elif " draws a walk." in update['lastUpdate']:
            ball.add(update['day'], self.batter, self.pitcher)
        elif " home run!" in update['lastUpdate']:
            homer.add(update['day'], self.batter, self.pitcher)
        elif " hits a Single!" in update['lastUpdate']:
            single.add(update['day'], self.batter, self.pitcher)
        elif " hits a Double!" in update['lastUpdate']:
            double.add(update['day'], self.batter, self.pitcher)
        elif " hits a Triple!" in update['lastUpdate']:
            triple.add(update['day'], self.batter, self.pitcher)
        elif "Baserunners are swept from play" in update['lastUpdate']:
            special.add(update['day'], self.batter, self.pitcher)
        elif " steals " in update['lastUpdate'] and " base!" in update['lastUpdate']:
            stolen_base.add(update['day'], self.batter, self.pitcher)
        elif "reaches on fielder's choice." in update['lastUpdate']:
            fielders_choice.add(update['day'], self.batter, self.pitcher)
        elif "hit into a double play!" in update['lastUpdate']:
            double_play.add(update['day'], self.batter, self.pitcher)
        elif " gets caught stealing " in update['lastUpdate']:
            caught_stealing.add(update['day'], self.batter, self.pitcher)
        elif "throws a Mild pitch!\nBall," in update['lastUpdate']:
            special.add(update['day'], self.batter, self.pitcher)
        elif " is Elsewhere.." in update['lastUpdate'] or " is Shelled and cannot escape" in update['lastUpdate']:
            pass
        elif " hits a grand slam!" in update['lastUpdate']:
            homer.add(update['day'], self.batter, self.pitcher)
        elif "They run to safety, resulting in an out." in update['lastUpdate']:
            special.add(update['day'], self.batter, self.pitcher)
        elif "walks to first base." in update['lastUpdate']:  # Love blood
            special.add(update['day'], self.batter, self.pitcher)
        elif " times to strike out willingly!" in update['lastUpdate']:  # Love blood
            special.add(update['day'], self.batter, self.pitcher)
        elif (any(event in update['lastUpdate'] for event in flavor_events) or
              re.match(r"^\d+ Birds$", update['lastUpdate'])):
            if self.batter is not None and self.pitcher is not None:
                flavor.add(update['day'], self.batter, self.pitcher)
        elif (f"{update['homeTeamNickname']} {update['homeScore']}" in update['lastUpdate'] and
              f"{update['awayTeamNickname']} {update['awayScore']}" in update['lastUpdate']):
            # print("Game over")
            pass
        elif " hops on the Grind Rail" in update['lastUpdate']:
            grind_rail.add(update['day'], self.batter, self.pitcher)
        elif (" enters the Secret Base" in update['lastUpdate'] or
              " exits the Secret Base" in update['lastUpdate']):
            special.add(update['day'], self.batter, self.pitcher)
        elif (" is Poured Over with a" in update['lastUpdate'] or
              " is Beaned by a" in update['lastUpdate']):
            special.add(update['day'], self.batter, self.pitcher)
        elif " Perks up" in update['lastUpdate']:
            pass
        elif (" Over Under, On" in update['lastUpdate'] or
              " Over Under, Off" in update['lastUpdate'] or
              " Under Over, On" in update['lastUpdate'] or
              " Under Over, Off" in update['lastUpdate']):
            pass
        elif "CONSUMERS ATTACK" in update['lastUpdate']:
            special.add(update['day'], self.batter, self.pitcher)
        elif update['lastUpdate'] == "":
            # print("Empty update")
            pass
        else:
            raise RuntimeError("Unknown gameId update")


def plot(outcome):
    fig, [pax, bax] = plt.subplots(1, 2, figsize=[10, 6])
    fig.suptitle(outcome.name)

    labels = ["Most Excellent", "Excellent", "Quality", "Neutral",
              "Less Than Ideal", "Far Less Than Ideal", "Honestly Terrible"]

    bin_locs = list(range(len(labels)))

    ppct = [a / b for (a, b) in zip(outcome.pitcher_occurrences, any_outcome.pitcher_occurrences)]
    pax.bar(bin_locs, ppct, tick_label=labels)
    pax.set_title("Pitcher")
    pax.set_ylabel("Occurrences")
    pax.set_xlabel("Vibe")

    bpct = [a / b for (a, b) in zip(outcome.batter_occurrences, any_outcome.batter_occurrences)]
    bax.bar(bin_locs, bpct, tick_label=labels)
    bax.set_title("Batter")
    bax.set_xlabel("Vibe")

    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--download', action='store_true')

    args = parser.parse_args()

    if args.download:
        download_games()
    else:
        tally_season()
