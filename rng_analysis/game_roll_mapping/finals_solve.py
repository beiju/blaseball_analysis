from nd import data, rng

timestamp = "2020-08-09T00:25:00Z"
teams = data.get_teams(timestamp)
players = data.get_players(timestamp)
by_name = {p["name"]: p for p in players.values()}

player_indices = {}
for t in teams.values():
    for i, l in enumerate(t["lineup"]):
        p = players[l]
        player_indices[p["name"]] = i


def bird_check(bird):
    roll = r.next()
    if (roll < 0.05) != bird:
        print("ERROR @ {}: WRONG BIRDS".format(r.get_state_str()))


def swing_threshold(batter_moxie):
    return 0.5 + batter_moxie * -0.3


def strike_threshold(pitcher_ruth):
    return 0.35 + pitcher_ruth * 0.35


def strike_swing_check(pitcher, batter, outcome):
    strike_roll = r.next()
    swing_roll = r.next()

    pitcher_ruth = by_name[pitcher]["ruthlessness"]
    batter_moxie = by_name[batter]["moxie"]

    strike_pred = strike_roll < strike_threshold(pitcher_ruth)
    swing_pred = swing_roll < swing_threshold(batter_moxie)

    if outcome in ["b"] and strike_pred:
        print(
            "ERROR @ {}: rolled {}, too low for ball".format(
                r.get_state_str(), strike_roll
            )
        )

    if outcome in ["sl"] and not strike_pred:
        print(
            "ERROR @ {}: rolled {}, too high for strike looking".format(
                r.get_state_str(), strike_roll
            )
        )

    return strike_roll, swing_roll


def runner_check(has_runner):
    if has_runner:
        r.next()


def sl(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "sl")


def ss(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "ss")
    contact = r.next()

    batter_path = by_name[batter]["patheticism"]
    # print("path={:.05f} roll={:.05f} outcome=ss".format(batter_path, contact))


def ball(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "b")


def advance_check(advance):
    if advance:
        advance_roll = r.next()


def foul(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_roll, swing_roll = strike_swing_check(pitcher, batter, "f")
    contact = r.next()
    fair = r.next()

    batter_path = by_name[batter]["patheticism"]
    if contact > 0.5:
        print(
            "path={:.05f} swing_roll={:.05f} outcome=f".format(batter_path,
                                                               swing_roll)
        )

    batter_musc = by_name[batter]["musclitude"]
    if fair > 0.32:
        print(
            "warn @ {}: rolled high fair on foul ({}) with musc {:.03f}".format(
                r.get_state_str(), fair, batter_musc
            )
        )


def ground_out(pitcher, batter, out_to, runner=False, inning_ending=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "go")
    contact = r.next()
    fair = r.next()
    r.next()
    r.next()
    r.next()
    r.next()

    fielder = r.next()

    if not inning_ending:
        advance_check(runner)

    if int(fielder * 9) != player_indices[out_to]:
        print(
            "ERROR @ {}: ground out rolled {}, wrong fielder".format(
                r.get_state_str(), fielder
            )
        )


def flyout(pitcher, batter, out_to, runner=False, inning_ending=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "fo")
    contact = r.next()
    fair = r.next()
    r.next()
    r.next()
    fielder = r.next()
    r.next()

    if int(fielder * 9) != player_indices[out_to]:
        print(
            "ERROR @ {}: flyout rolled {}, wrong fielder".format(
                r.get_state_str(), fielder
            )
        )

    if not inning_ending:
        advance_check(runner)


def bird():
    bird_check(True)
    r.next()
    r.next()


def solo_homer(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "h")
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()


def two_run_homer(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "h")
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()


def single(pitcher, batter, runner=False, is_on_third=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "h")
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()

    if not is_on_third:
        advance_check(runner)


def double(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "h")
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()


def triple(pitcher, batter, runner=False):
    bird_check(False)
    r.next()
    runner_check(runner)
    strike_swing_check(pitcher, batter, "h")
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()
    r.next()


def base_steal(pitcher, runner):
    bird_check(False)
    r.next()
    steal_roll = r.next()
    steal_success = r.next()


r = rng.Rng((2009851709471025379, 7904764474545764681), 7)
r.step(-1)

# top of 1
sl("Theodore Cervantes", "Fish Summer")
foul("Theodore Cervantes", "Fish Summer")
bird()
ball("Theodore Cervantes", "Fish Summer")
solo_homer("Theodore Cervantes", "Fish Summer")

ss("Theodore Cervantes", "Paula Turnip")
ball("Theodore Cervantes", "Paula Turnip")
sl("Theodore Cervantes", "Paula Turnip")
ball("Theodore Cervantes", "Paula Turnip")
ball("Theodore Cervantes", "Paula Turnip")
ground_out("Theodore Cervantes", "Paula Turnip", "Sandie Turner")

foul("Theodore Cervantes", "Jessica Telephone")
sl("Theodore Cervantes", "Jessica Telephone")
single("Theodore Cervantes", "Jessica Telephone")

ss("Theodore Cervantes", "Alyssa Harrell", runner=True)
sl("Theodore Cervantes", "Alyssa Harrell", runner=True)
single("Theodore Cervantes", "Alyssa Harrell", runner=True)

single("Theodore Cervantes", "Peanutiel Duffy", runner=True)

r.step(15)  # fc? 14 or 15

sl("Theodore Cervantes", "Ren Morin", runner=True)
sl("Theodore Cervantes", "Ren Morin", runner=True)
ground_out(
    "Theodore Cervantes",
    "Ren Morin",
    "Dominic Marijuana",
    runner=True,
    inning_ending=True,
)

# bottom of 1
ss("Nagomi Meng", "Dominic Marijuana")
foul("Nagomi Meng", "Dominic Marijuana")
ground_out("Nagomi Meng", "Dominic Marijuana", "Paula Turnip")

sl("Nagomi Meng", "Mclaughlin Scorpler")
ball("Nagomi Meng", "Mclaughlin Scorpler")
bird()
ball("Nagomi Meng", "Mclaughlin Scorpler")
ball("Nagomi Meng", "Mclaughlin Scorpler")
flyout("Nagomi Meng", "Mclaughlin Scorpler", "Jessica Telephone")

foul("Nagomi Meng", "Conrad Vaughan")
foul("Nagomi Meng", "Conrad Vaughan")
foul("Nagomi Meng", "Conrad Vaughan")
ball("Nagomi Meng", "Conrad Vaughan")
ball("Nagomi Meng", "Conrad Vaughan")
ground_out("Nagomi Meng", "Conrad Vaughan", "Fish Summer")

# top of 2
sl("Theodore Cervantes", "Zion Aliciakeyes")
bird()
ss("Theodore Cervantes", "Zion Aliciakeyes")
ground_out("Nagomi Meng", "Zion Aliciakeyes", "Mclaughlin Scorpler")

ball("Theodore Cervantes", "Randy Castillo")
ss("Theodore Cervantes", "Randy Castillo")
ss("Theodore Cervantes", "Randy Castillo")
ball("Theodore Cervantes", "Randy Castillo")
ball("Theodore Cervantes", "Randy Castillo")
ball("Theodore Cervantes", "Randy Castillo")

flyout("Theodore Cervantes", "Fish Summer", "Mclaughlin Scorpler", runner=True)

ball("Theodore Cervantes", "Paula Turnip", runner=True)
single("Theodore Cervantes", "Paula Turnip", runner=True)

foul("Theodore Cervantes", "Jessica Telephone", runner=True)
bird()
ball("Theodore Cervantes", "Jessica Telephone", runner=True)
ground_out(
    "Theodore Cervantes",
    "Jessica Telephone",
    "Winnie Mccall",
    runner=True,
    inning_ending=True,
)

# bottom of 2
ball("Nagomi Meng", "Thomas Dracaena")
ball("Nagomi Meng", "Thomas Dracaena")
ball("Nagomi Meng", "Thomas Dracaena")
ground_out("Nagomi Meng", "Thomas Dracaena", "Moody Cookbook")

sl("Nagomi Meng", "Schneider Bendie")
ball("Nagomi Meng", "Schneider Bendie")
ss("Nagomi Meng", "Schneider Bendie")
sl("Nagomi Meng", "Schneider Bendie")
ground_out("Nagomi Meng", "Schneider Bendie", "Jessica Telephone")

ground_out("Nagomi Meng", "Wesley Dudley", "Randy Castillo")

# top of 3
flyout("Theodore Cervantes", "Alyssa Harrell", "Thomas Dracaena")

bird()
triple("Theodore Cervantes", "Peanutiel Duffy")

ground_out("Theodore Cervantes", "Moody Cookbook", "Thomas Dracaena",
           runner=True)

single("Theodore Cervantes", "Ren Morin", runner=True)

flyout(
    "Theodore Cervantes",
    "Zion Aliciakeyes",
    "Winnie Mccall",
    runner=True,
    inning_ending=True,
)

# bottom of 3
ball("Nagomi Meng", "Richardson Games")
ball("Nagomi Meng", "Richardson Games")
ss("Nagomi Meng", "Richardson Games")
sl("Nagomi Meng", "Richardson Games")
ground_out("Nagomi Meng", "Richardson Games", "Jessica Telephone")

ball("Nagomi Meng", "Winnie Mccall")
sl("Nagomi Meng", "Winnie Mccall")
sl("Nagomi Meng", "Winnie Mccall")
ball("Nagomi Meng", "Winnie Mccall")
ground_out("Nagomi Meng", "Winnie Mccall", "Peanutiel Duffy")

bird()
sl("Nagomi Meng", "Sandie Turner")
ground_out("Nagomi Meng", "Sandie Turner", "Randy Castillo", inning_ending=True)

# top of 4
ss("Theodore Cervantes", "Zion Aliciakeyes")
foul("Theodore Cervantes", "Zion Aliciakeyes")
ss("Theodore Cervantes", "Zion Aliciakeyes")

ball("Theodore Cervantes", "Randy Castillo")
sl("Theodore Cervantes", "Randy Castillo")
bird()
ball("Theodore Cervantes", "Randy Castillo")
foul("Theodore Cervantes", "Randy Castillo")
bird()
sl("Theodore Cervantes", "Randy Castillo")

flyout("Theodore Cervantes", "Fish Summer", "Conrad Vaughan",
       inning_ending=True)

# bottom of 4
sl("Nagomi Meng", "Dominic Marijuana")
ball("Nagomi Meng", "Dominic Marijuana")
foul("Nagomi Meng", "Dominic Marijuana")
foul("Nagomi Meng", "Dominic Marijuana")
ball("Nagomi Meng", "Dominic Marijuana")
ball("Nagomi Meng", "Dominic Marijuana")
solo_homer("Nagomi Meng", "Dominic Marijuana")

ss("Nagomi Meng", "Mclaughlin Scorpler")
sl("Nagomi Meng", "Mclaughlin Scorpler")
ball("Nagomi Meng", "Mclaughlin Scorpler")
ss("Nagomi Meng", "Mclaughlin Scorpler")
ground_out("Nagomi Meng", "Mclaughlin Scorpler", "Peanutiel Duffy")

ground_out("Nagomi Meng", "Conrad Vaughan", "Alyssa Harrell")

bird()
ball("Nagomi Meng", "Thomas Dracaena")
bird()
ball("Nagomi Meng", "Thomas Dracaena")
ball("Nagomi Meng", "Thomas Dracaena")
bird()
ground_out("Nagomi Meng", "Thomas Dracaena", "Jessica Telephone",
           inning_ending=True)

# top of 5
sl("Theodore Cervantes", "Fish Summer")
sl("Theodore Cervantes", "Fish Summer")
ball("Theodore Cervantes", "Fish Summer")
foul("Theodore Cervantes", "Fish Summer")
ball("Theodore Cervantes", "Fish Summer")
ss("Theodore Cervantes", "Fish Summer")

ground_out("Theodore Cervantes", "Paula Turnip", "Schneider Bendie")

sl("Theodore Cervantes", "Jessica Telephone")
ball("Theodore Cervantes", "Jessica Telephone")
single("Theodore Cervantes", "Jessica Telephone")

flyout(
    "Theodore Cervantes",
    "Alyssa Harrell",
    "Mclaughlin Scorpler",
    runner=True,
    inning_ending=True,
)

# bottom of 5
sl("Nagomi Meng", "Schneider Bendie")
ball("Nagomi Meng", "Schneider Bendie")
bird()
bird()
ground_out("Nagomi Meng", "Schneider Bendie", "Randy Castillo")

ball("Nagomi Meng", "Wesley Dudley")
ground_out("Nagomi Meng", "Wesley Dudley", "Fish Summer")

ball("Nagomi Meng", "Richardson Games")
sl("Nagomi Meng", "Richardson Games")
ball("Nagomi Meng", "Richardson Games")
ball("Nagomi Meng", "Richardson Games")
ball("Nagomi Meng", "Richardson Games")

flyout(
    "Nagomi Meng", "Winnie Mccall", "Peanutiel Duffy", runner=True,
    inning_ending=True
)

# top of 6
ball("Theodore Cervantes", "Peanutiel Duffy")
ball("Theodore Cervantes", "Peanutiel Duffy")
bird()
ss("Theodore Cervantes", "Peanutiel Duffy")
sl("Theodore Cervantes", "Peanutiel Duffy")
ground_out("Theodore Cervantes", "Peanutiel Duffy", "Schneider Bendie")

bird()
foul("Theodore Cervantes", "Moody Cookbook")
sl("Theodore Cervantes", "Moody Cookbook")
sl("Theodore Cervantes", "Moody Cookbook")

ss("Theodore Cervantes", "Ren Morin")
ball("Theodore Cervantes", "Ren Morin")
ball("Theodore Cervantes", "Ren Morin")
ball("Theodore Cervantes", "Ren Morin")
ball("Theodore Cervantes", "Ren Morin")

sl("Theodore Cervantes", "Zion Aliciakeyes", runner=True)
ss("Theodore Cervantes", "Zion Aliciakeyes", runner=True)
foul("Theodore Cervantes", "Zion Aliciakeyes", runner=True)
sl("Theodore Cervantes", "Zion Aliciakeyes", runner=True)

# bottom of 6
flyout("Nagomi Meng", "Winnie Mccall", "Peanutiel Duffy")

ball("Nagomi Meng", "Sandie Turner")
ball("Nagomi Meng", "Sandie Turner")
ball("Nagomi Meng", "Sandie Turner")
ss("Nagomi Meng", "Sandie Turner")
flyout("Nagomi Meng", "Sandie Turner", "Jessica Telephone")

ground_out("Nagomi Meng", "Dominic Marijuana", "Moody Cookbook",
           inning_ending=True)

# top of 7
foul("Theodore Cervantes", "Randy Castillo")
ground_out("Theodore Cervantes", "Randy Castillo", "Conrad Vaughan")

ground_out("Theodore Cervantes", "Fish Summer", "Dominic Marijuana")

ss("Theodore Cervantes", "Paula Turnip")
ss("Theodore Cervantes", "Paula Turnip")
solo_homer("Theodore Cervantes", "Paula Turnip")

sl("Theodore Cervantes", "Jessica Telephone")
solo_homer("Theodore Cervantes", "Jessica Telephone")

sl("Theodore Cervantes", "Alyssa Harrell")
ground_out(
    "Theodore Cervantes", "Alyssa Harrell", "Thomas Dracaena",
    inning_ending=True
)

# bottom of 7
sl("Nagomi Meng", "Mclaughlin Scorpler")
sl("Nagomi Meng", "Mclaughlin Scorpler")
ball("Nagomi Meng", "Mclaughlin Scorpler")
ground_out("Nagomi Meng", "Mclaughlin Scorpler", "Fish Summer")

foul("Nagomi Meng", "Conrad Vaughan")
ground_out("Nagomi Meng", "Conrad Vaughan", "Jessica Telephone")

single("Nagomi Meng", "Thomas Dracaena")

foul("Nagomi Meng", "Schneider Bendie", runner=True)
foul("Nagomi Meng", "Schneider Bendie", runner=True)
ball("Nagomi Meng", "Schneider Bendie", runner=True)
sl("Nagomi Meng", "Schneider Bendie", runner=True)
ball("Nagomi Meng", "Schneider Bendie", runner=True)
ground_out(
    "Nagomi Meng", "Schneider Bendie", "Ren Morin", runner=True,
    inning_ending=True
)

# top of 8
ball("Theodore Cervantes", "Peanutiel Duffy")
ball("Theodore Cervantes", "Peanutiel Duffy")
ground_out("Theodore Cervantes", "Peanutiel Duffy", "Schneider Bendie")

sl("Theodore Cervantes", "Moody Cookbook")
ball("Theodore Cervantes", "Moody Cookbook")
ground_out("Theodore Cervantes", "Moody Cookbook", "Winnie Mccall")

sl("Theodore Cervantes", "Ren Morin")
ss("Theodore Cervantes", "Ren Morin")
bird()
sl("Theodore Cervantes", "Ren Morin")

# bottom of 8
flyout("Nagomi Meng", "Wesley Dudley", "Zion Aliciakeyes")

ball("Nagomi Meng", "Richardson Games")
single("Nagomi Meng", "Richardson Games")

bird()
ball("Nagomi Meng", "Winnie Mccall", runner=True)
ss("Nagomi Meng", "Winnie Mccall", runner=True)
bird()
ball("Nagomi Meng", "Winnie Mccall", runner=True)
foul("Nagomi Meng", "Winnie Mccall", runner=True)
ball("Nagomi Meng", "Winnie Mccall", runner=True)
ball("Nagomi Meng", "Winnie Mccall", runner=True)

r.step(
    14)  # sandie turner fc, runner on first and second, definitely exactly 14

bird()
ground_out(
    "Nagomi Meng", "Dominic Marijuana", "Fish Summer", runner=True,
    inning_ending=True
)

# top of 9
foul("Theodore Cervantes", "Zion Aliciakeyes")
bird()
bird()
ground_out("Theodore Cervantes", "Zion Aliciakeyes", "Richardson Games")

foul("Theodore Cervantes", "Randy Castillo")
foul("Theodore Cervantes", "Randy Castillo")
ball("Theodore Cervantes", "Randy Castillo")
ball("Theodore Cervantes", "Randy Castillo")
bird()
double("Theodore Cervantes", "Randy Castillo")

bird()
base_steal("Theodore Cervantes", "Randy Castillo")
triple("Theodore Cervantes", "Fish Summer", runner=True)

ball("Theodore Cervantes", "Paula Turnip", runner=True)
ss("Theodore Cervantes", "Paula Turnip", runner=True)
sl("Theodore Cervantes", "Paula Turnip", runner=True)
foul("Theodore Cervantes", "Paula Turnip", runner=True)
single("Theodore Cervantes", "Paula Turnip", runner=True, is_on_third=True)

sl("Theodore Cervantes", "Jessica Telephone", runner=True)
ball("Theodore Cervantes", "Jessica Telephone", runner=True)
ball("Theodore Cervantes", "Jessica Telephone", runner=True)

r.step(14)  # more fc. 14/15?

flyout(
    "Theodore Cervantes",
    "Alyssa Harrell",
    "Wesley Dudley",
    runner=True,
    inning_ending=True,
)

# bottom of 9
ground_out("Nagomi Meng", "Mclaughlin Scorpler", "Fish Summer")

foul("Nagomi Meng", "Conrad Vaughan")
bird()
flyout("Nagomi Meng", "Conrad Vaughan", "Moody Cookbook")

ground_out("Nagomi Meng", "Thomas Dracaena", "Jessica Telephone",
           inning_ending=True)

# game over!
