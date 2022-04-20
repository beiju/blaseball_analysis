import requests

from nd import rng, data


def match_bird_message(msg):
    msgs = [
        "There's just too many birds!",
        "The birds are very loud!",
        "Several birds are pecking...",
        "The birds are paralyzed! They can't move!",
        "The birds continue to stare.",
        "Where did these birds come from?",
        "They're clearing feathers off the field...",
        "This is too many birds.",
        "I hardly think a few birds are going to bring about the end of the world.",
        "The birds are after the children...",
        "Do these birds have souls?",
        "BIRD NOISES",
        "These birds hate Blaseball!",
        "Have you ever seen this many birds?",
        "What are we gonna do with all these birds?",
        "Oh dear Gods...",
        "Don't feed the birds",
        "The birds are mad at you. You specifically. You know who you are.",
    ]
    return msg in msgs or msg.endswith(" Birds")
        

def advance_bases(occupied, amount):
    occupied = [b+amount for b in occupied]
    return [b for b in occupied if b < 3]

class Sim():
    def __init__(self, rng) -> None:
        self.rng = rng
        self.bases = []
        self.runners = []
        self.outs = 0
        self.weather = "birds"

    def set_pitcher(self, pitcher):
        self.pitcher = pitcher

    def set_batter(self, batter):
        self.batter = batter

    def pre_pitch(self):
        weather_roll = self.rng.next()
        if self.weather == "birds" and weather_roll < 0.05:
            print("ERROR: too many birds")

        self.rng.next()

        if self.bases:
            # steal check
            steal_check = self.rng.next()

            runner = self.runners[0]
            thirst = runner["baseThirst"]
            # if steal_check < 0.05:
            #     print("steal check: {}, thirst {}".format(steal_check, thirst))

    def roll_strike(self):
        strike_roll = self.rng.next()
        strike_threshold = 0.35 + self.pitcher["ruthlessness"] * 0.35
        # print("strike roll {:.05f}, thres {:.05f} for pitcher {}".format(strike_roll, strike_threshold, self.pitcher["name"]))
        return strike_roll < strike_threshold

    def assert_strike(self, expected_is_strike):
        actual_is_strike = self.roll_strike()
        if actual_is_strike != expected_is_strike:
            print("ERROR: expected strike {}, found {}".format(expected_is_strike, actual_is_strike))
        return actual_is_strike

    def assert_contact(self, is_strike):
        contact_roll = self.rng.next()
        # todo

    def roll_baserunner_advance(self):
        for runner in self.bases:
            if runner != 2:
                self.rng.next()


    def assert_fielder(self, expected_index):
        fielder_roll = self.rng.next()
        rolled_index = int(fielder_roll * 9)
        if rolled_index != expected_index:
            print("ERROR: rolled wrong fielder: {}".format(fielder_roll))

    def roll_swing(self, is_strike, known_outcome):
        # self.rng.step(-1)
        # strike_roll = self.rng.next()

        swing_roll = self.rng.next()
        if is_strike:
            if known_outcome == "no" and swing_roll < 0.6:
                print("ERROR: swing roll unreasonably low for strike ({:.05f})".format(swing_roll))

            if known_outcome == "yes" and swing_roll > 0.75:
                print("ERROR: swing roll unreasonably high for strike ({:.05f})".format(swing_roll))
        else:
            if known_outcome == "no" and swing_roll < 0.2:
                print("ERROR: swing roll unreasonably low for ball ({:.05f})".format(swing_roll))

            if known_outcome == "yes" and swing_roll > 0.6:
                print("ERROR: swing roll unreasonably high for ball ({:.05f})".format(swing_roll))
        
        # print(repr((swing_roll, strike_roll, is_strike, self.batter, self.pitcher, known_outcome)) + ",")

    def strike_swinging(self):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.rng.next()

    def strike_looking(self):
        self.pre_pitch()
        is_strike = self.assert_strike(True)
        self.roll_swing(is_strike, "no")

    def ball(self):
        self.pre_pitch()
        is_strike = self.assert_strike(False)
        self.roll_swing(is_strike, "no")

    def foul(self):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.rng.next()
        foul_roll = self.rng.next()
        if foul_roll > 0.37:
            print("ERROR: foul roll unreasonably high")

    def ground_out(self, fielder_index):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.assert_contact(is_strike)
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()

        self.assert_fielder(fielder_index)

        if self.outs < 2:
            # print(self.outs, self.bases, self.rng.get_state_str())
            for runner in self.bases:
                self.rng.next()

                if runner == 2:
                    self.rng.next() # sac fly roll?


    def flyout(self, fielder_index):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.assert_contact(is_strike)
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.assert_fielder(fielder_index)
        self.rng.next()

        if self.outs < 2:
            for runner in self.bases:
                self.rng.next()

    def home_run(self):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.assert_contact(is_strike)
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()

    def base_hit(self, hit_bases, bases_after):
        self.pre_pitch()
        is_strike = self.roll_strike()
        self.roll_swing(is_strike, "yes")
        self.assert_contact(is_strike)
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()
        self.rng.next()

        # advance by hit type
        bases = advance_bases(self.bases, hit_bases)

        # roll for runner advancement
        if len(bases) == 1:
            self.rng.next()
        elif len(bases) == 2:
            # guaranteed advancement
            self.rng.next()

            # super special edge case for singles only
            # effectively asking "did anyone score on a single from second"
            if bases_after != [2, 1, 0]:
                # ...because after advancing every baserunner (incl second->third)
                # the runner now on third advanced to home, freeing up third base
                # for the new, super special, bonus advancement roll from second->third
                self.rng.next()

            # i'm sure there's a fun way to do this for 3+ bases but, lol, lmao

    def fielders_choice(self):
        self.pre_pitch()
        self.rng.step(11)

    def double_play(self):
        self.pre_pitch()
        self.rng.step(11)

    def base_steal(self):
        self.pre_pitch()
        self.rng.next() # steal success maybe

    def caught_stealing(self):
        self.pre_pitch()
        self.rng.next() # steal success maybe

        # unsure why this should matter but ???it fits data??
        if len(self.bases) == 1:
            self.rng.next()
            self.rng.next()


    def sac_fly(self):
        self.pre_pitch()
        self.rng.step(11) # ???

    def sac_score(self):
        self.pre_pitch()
        self.rng.step(9) # ???

    def birds(self):
        weather_roll = self.rng.next()
        if weather_roll > 0.05:
            print("ERROR: not enough birds")

        self.rng.next()
        self.rng.next()

    def incineration(self):
        incin_roll = self.rng.next()
        if incin_roll > 0.001:
            print("ERROR: incin roll too high?")
        # name, stats, info, location
        self.rng.step(2 + 26 + 3 + 2)

def update_sim_state(sim, state, players):
    sim.bases = state["basesOccupied"]
    sim.runners = [players[p] for p in state["baseRunners"]]
    sim.outs = state["halfInningOuts"]

    batter = state["awayBatter"] if state["topOfInning"] else state["homeBatter"]
    pitcher = state["homePitcher"] if state["topOfInning"] else state["awayPitcher"]

    if batter:
        sim.set_batter(players[batter])
    if pitcher:
        sim.set_pitcher(players[pitcher])

def resim_games(rng, game_ids, skips={}, start_at="2020-01-01T00:00:00Z", pull_data_at=None):
    sims = {}

    updates = []
    for game_id in game_ids:
        game_updates = requests.get("https://api.sibr.dev/chronicler/v1/games/updates?count=2000&game={}&started=true&after={}".format(game_id, start_at)).json()
        updates += enumerate(game_updates["data"])

        game = game_updates["data"][0]["data"]
        sim = Sim(rng)
        sim.weather = {11: "birds"}.get(game["weather"])
        sims[game_id] = sim

    updates = sorted(updates, key=lambda x: (x[1]["timestamp"][:19], x[1]["gameId"]))

    timestamp = pull_data_at if pull_data_at else updates[0][1]["timestamp"]
    teams = data.get_teams(timestamp)
    players = data.get_players(timestamp)

    player_indices = {}
    for t in teams.values():
        for i, id in enumerate(t["lineup"]):
            player_indices[players[id]["name"]] = i

    for i, u in updates:
        state = u["data"]
        sim = sims[u["gameId"]]
        short_id = u["gameId"][:8]


        msg = state["lastUpdate"]

        skips_key = (short_id, i)
        if skips_key in skips:
            sim.rng.step(skips[skips_key])
            # print("STEPPING RNG BY {}".format(skips[skips_key]))

        if i == 0:
            update_sim_state(sim, state, players)

        sim.rng.step(1)
        print("{} {} {:>3} {} - {}".format(u["timestamp"][14:19], short_id, i, sim.rng.state[0], msg))
        sim.rng.step(-1)

        if "Strike, looking" in msg or "strikes out looking." in msg:
            sim.strike_looking()
        elif "Strike, swinging" in msg or "struck out swinging." in msg:
            sim.strike_swinging()
        elif "Foul Ball." in msg:
            sim.foul()
        elif "Ball." in msg or "draws a walk." in msg:
            sim.ball()
        elif "hits a solo home run" in msg or "hits a 2-run home run" in msg or "hits a 3-run home run" in msg:
            sim.home_run()
        elif "hit a ground out to" in msg:
            fielder_name = msg.split(" to ")[1].strip(".")
            sim.ground_out(player_indices[fielder_name])
        elif "hit a flyout to" in msg:
            fielder_name = msg.split(" to ")[1].strip(".")
            sim.flyout(player_indices[fielder_name])
        elif "hits a Single" in msg:
            sim.base_hit(1, state["basesOccupied"])
        elif "hits a Double" in msg:
            sim.base_hit(2, state["basesOccupied"])
        elif "hits a Triple" in msg:
            sim.base_hit(3, state["basesOccupied"])
        elif "reaches on fielder's choice" in msg:
            sim.fielders_choice()
        elif "hit into a double play" in msg:
            sim.double_play()
        elif "steals" in msg:
            sim.base_steal()
        elif "gets caught stealing" in msg:
            sim.caught_stealing()
        elif "scores on the sacrifice" in msg:
            sim.sac_fly()
        elif "tags up and scores" in msg:
            sim.sac_score()
        elif "Rogue Umpire incinerated" in msg:
            sim.incineration()
        elif match_bird_message(msg):
            sim.birds()
        elif "batting for the" in msg or "Game over." in msg or "batting." in msg or "Play ball!" in msg:
            # flavor, skip
            pass
        else:
            print("===UNK" , msg)

        update_sim_state(sim, state, players)


r = rng.Rng((5533805311492506700, 15692468723559200702), 48)
r.step(-1)

resim_games(r, ["5bb9abd8-96a1-4edf-9fce-1c227f79bd1a", "8f6ca425-6bc0-493f-99d8-3fc145e265a9"], {
    ("5bb9abd8", 28): 6, # foul
    ("5bb9abd8", 37): 2, # ground out advancement i haven't worked out the proper logic for
    ("8f6ca425", 64): 6, # foul
    ("8f6ca425", 98): 6, # foul
    ("8f6ca425", 140): -1, # flyout advancement (in 5b game) - we roll 2 for advancement but first fails so second isn't eligible
}, "2020-08-08T21:14:03Z")

r = rng.Rng((6293080272763260934, 11654195519702723052), 60)
r.step(-1)

resim_games(r, ["aa1b7fde-f077-4e4b-825f-0d1538d02822"], {
    ("aa1b7fde", 15): 7, # foul+runner
    ("aa1b7fde", 231): 12, # 2x foul
}, pull_data_at="2020-08-09T00:30:03Z")

r.step(2)
resim_games(r, ["ea55d541-1abe-4a02-8cd8-f62d1392226b"], {
    ("ea55d541", 4): 18 # hey remember that time fish summer hit four foul balls in a row
})

r.step(2)
resim_games(r, ["731e7e33-4cd3-47de-b9fe-850d7131c4d6"], {
    ("731e7e33", 14): 7, # foul+runner where we dropped the event
})

r.step(2)
resim_games(r, ["b38e0917-43da-470c-a7bb-5712368a2492"])