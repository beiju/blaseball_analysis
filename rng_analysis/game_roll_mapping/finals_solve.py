from nd import data, rng

timestamp = "2020-08-09T00:25:00Z"
teams = data.get_teams(timestamp)
players = data.get_players(timestamp)
by_name = {p["name"]: p for p in players.values()}




event_info = []

first_unknown_vals = []
hit_vals = []
third_unknown_vals = []
categories = []

player_indices = {}
for t in teams.values():
    for i, l in enumerate(t["lineup"]):
        p = players[l]
        player_indices[p["name"]] = i


weather = "birds"










def ss(pitcher, batter, runner=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "ss")
    contact = r.next()

    batter_path = by_name[batter]["patheticism"]
    # print("path={:.05f} roll={:.05f} outcome=ss".format(batter_path, contact))

    event_info.append(EventInfo(
        event_type=EventType.StrikeSwinging,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact
    ))

def advance_check(advance):
    if advance:
        advance_roll = r.next()


def foul(pitcher, batter, runner=False):


def ground_out(pitcher, batter, out_to, runner=False, inning_ending=False, is_on_third=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "go")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()
    r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('ground out')

    fielder = r.next()

    if not inning_ending:
        advance_check(runner)

        if is_on_third:
            r.next()  # rgsots check??

    if int(fielder * 9) != player_indices[out_to]:
        print(
            "ERROR @ {}: ground out rolled {}, wrong fielder".format(
                r.get_state_str(), fielder
            )
        )

    event_info.append(EventInfo(
        event_type=EventType.GroundOut,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit,
        three_val=three
    ))


def flyout(pitcher, batter, out_to, runner=False, inning_ending=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "fo")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    fielder = r.next()
    r.next()  # not gonna call this three bc it's after the fielder roll

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    categories.append('flyout')

    if int(fielder * 9) != player_indices[out_to]:
        print(
            "ERROR @ {}: flyout rolled {}, wrong fielder".format(
                r.get_state_str(), fielder
            )
        )

    if not inning_ending:
        advance_check(runner)

    event_info.append(EventInfo(
        event_type=EventType.GroundOut,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def bird():


def solo_homer(pitcher, batter, runner=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "h")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('homer')

    event_info.append(EventInfo(
        event_type=EventType.HomeRun,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def two_run_homer(pitcher, batter, runner=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "h")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('homer')

    event_info.append(EventInfo(
        event_type=EventType.HomeRun,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def single(pitcher, batter, runner=False, is_on_third=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "h")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()
    r.next()
    r.next()
    r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('single')
    if hit > 0.5:
        print("Here")

    if not is_on_third:
        advance_check(runner)

    event_info.append(EventInfo(
        event_type=EventType.Single,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def double(pitcher, batter, runner=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "h")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()
    r.next()
    r.next()
    r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('double')

    event_info.append(EventInfo(
        event_type=EventType.Double,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def triple(pitcher, batter, runner=False):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal = runner_check(runner)
    strike, swing = strike_swing_check(pitcher, batter, "h")
    contact = r.next()
    fair = r.next()
    one = r.next()
    hit = r.next()
    three = r.next()
    r.next()
    r.next()
    r.next()

    first_unknown_vals.append(one)
    hit_vals.append(hit)
    third_unknown_vals.append(three)
    categories.append('double')

    event_info.append(EventInfo(
        event_type=EventType.Triple,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=runner,
        steal_val=steal,
        strike_zone_val=strike,
        pitcher_ruth=by_name[pitcher]["ruthlessness"],
        batter_path=by_name[batter]["patheticism"],
        batter_moxie=by_name[batter]["moxie"],
        swing_val=swing,
        contact_val=contact,
        foul_val=fair,
        one_val=one,
        hit_val=hit
    ))


def base_steal(pitcher, runner):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal_roll = r.next()
    steal_success = r.next()

    event_info.append(EventInfo(
        event_type=EventType.Steal,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=True,
        steal_val=steal_roll,
    ))


def caught_stealing(pitcher, runner):
    weather_roll = weather_check(False)
    mystery = r.next()
    steal_roll = r.next()
    steal_success = r.next()
    r.next()  # ???
    r.next()  # ???
    # this is probably wrong somehow

    event_info.append(EventInfo(
        event_type=EventType.Steal,
        weather_val=weather_roll,
        mystery_val=mystery,
        has_runner=True,
        steal_val=steal_roll,
    ))


r = rng.Rng((2009851709471025379, 7904764474545764681), 8)
r.step(-3)

print("First game:")
print(r.next())
print(r.next())
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
           runner=True, is_on_third=True)

single("Theodore Cervantes", "Ren Morin", runner=True, is_on_third=True)

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
# game over!
print("Second game")
print(r.next())
print(r.next())

# top of 1
ball("Patty Fox", "Fish Summer")
foul("Patty Fox", "Fish Summer")
foul("Patty Fox", "Fish Summer")
ground_out("Patty Fox", "Fish Summer", "Sandie Turner")

triple("Patty Fox", "Paula Turnip")

foul("Patty Fox", "Jessica Telephone", runner=True)
ball("Patty Fox", "Jessica Telephone", runner=True)
foul("Patty Fox", "Jessica Telephone", runner=True)

bird()

r.step(7)  # ?????

ball("Patty Fox", "Jessica Telephone", runner=True)
sl("Patty Fox", "Jessica Telephone", runner=True)

foul("Patty Fox", "Alyssa Harrell", runner=True)
sl("Patty Fox", "Alyssa Harrell", runner=True)
ground_out(
    "Patty Fox",
    "Alyssa Harrell",
    "Mclaughlin Scorpler",
    runner=True,
    inning_ending=True,
)

# bottom of 1
bird()
sl("Yazmin Mason", "Dominic Marijuana")
ss("Yazmin Mason", "Dominic Marijuana")
ball("Yazmin Mason", "Dominic Marijuana")
ball("Yazmin Mason", "Dominic Marijuana")
ball("Yazmin Mason", "Dominic Marijuana")
ss("Yazmin Mason", "Dominic Marijuana")
ground_out("Yazmin Mason", "Dominic Marijuana", "Fish Summer")

ball("Yazmin Mason", "Mclaughlin Scorpler")
ball("Yazmin Mason", "Mclaughlin Scorpler")
ss("Yazmin Mason", "Mclaughlin Scorpler")
ball("Yazmin Mason", "Mclaughlin Scorpler")
ball("Yazmin Mason", "Mclaughlin Scorpler")

ball("Yazmin Mason", "Conrad Vaughan", runner=True)
single("Yazmin Mason", "Conrad Vaughan", runner=True)

foul("Yazmin Mason", "Thomas Dracaena", runner=True)
solo_homer("Yazmin Mason", "Thomas Dracaena", runner=True)  # 3-run lol

bird()
ball("Yazmin Mason", "Schneider Bendie")
ss("Yazmin Mason", "Schneider Bendie")
ground_out("Yazmin Mason", "Schneider Bendie", "Paula Turnip")

sl("Yazmin Mason", "Wesley Dudley")
single("Yazmin Mason", "Wesley Dudley")

ball("Yazmin Mason", "Richardson Games", runner=True)
sl("Yazmin Mason", "Richardson Games", runner=True)
ball("Yazmin Mason", "Richardson Games", runner=True)
ball("Yazmin Mason", "Richardson Games", runner=True)
ball("Yazmin Mason", "Richardson Games", runner=True)

ground_out(
    "Yazmin Mason", "Winnie Mccall", "Zion Aliciakeyes", runner=True, inning_ending=True
)

# top of 2
ball("Patty Fox", "Peanutiel Duffy")
triple("Patty Fox", "Peanutiel Duffy")

ball("Patty Fox", "Moody Cookbook", runner=True)
ss("Patty Fox", "Moody Cookbook", runner=True)
foul("Patty Fox", "Moody Cookbook", runner=True)
ball("Patty Fox", "Moody Cookbook", runner=True)
ground_out("Patty Fox", "Moody Cookbook", "Winnie Mccall", runner=True)
r.step(1)  # why is this needed? it's not because there's a runner on third

ss("Patty Fox", "Ren Morin", runner=True)
bird()
ss("Patty Fox", "Ren Morin", runner=True)
sl("Patty Fox", "Ren Morin", runner=True)

foul("Patty Fox", "Zion Aliciakeyes", runner=True)
sl("Patty Fox", "Zion Aliciakeyes", runner=True)
flyout(
    "Patty Fox", "Zion Aliciakeyes", "Winnie Mccall", runner=True, inning_ending=True
)

# bottom of 2
bird()
bird()
ball("Yazmin Mason", "Sandie Turner")
foul("Yazmin Mason", "Sandie Turner")
flyout("Yazmin Mason", "Sandie Turner", "Zion Aliciakeyes")

foul("Yazmin Mason", "Dominic Marijuana")
ball("Yazmin Mason", "Dominic Marijuana")
ball("Yazmin Mason", "Dominic Marijuana")
single("Yazmin Mason", "Dominic Marijuana")

ground_out("Yazmin Mason", "Mclaughlin Scorpler", "Alyssa Harrell", runner=True)

ss("Yazmin Mason", "Conrad Vaughan", runner=True)
caught_stealing("Yazmin Mason", "Dominic Marijuana")

# top of 3
ball("Patty Fox", "Zion Aliciakeyes")
ss("Patty Fox", "Zion Aliciakeyes")
sl("Patty Fox", "Zion Aliciakeyes")
sl("Patty Fox", "Zion Aliciakeyes")

bird()
single("Patty Fox", "Randy Castillo")

bird()
ball("Patty Fox", "Fish Summer", runner=True)
foul("Patty Fox", "Fish Summer", runner=True)
ball("Patty Fox", "Fish Summer", runner=True)
ball("Patty Fox", "Fish Summer", runner=True)
flyout("Patty Fox", "Fish Summer", "Dominic Marijuana", runner=True)

foul("Patty Fox", "Paula Turnip", runner=True)
single("Patty Fox", "Paula Turnip", runner=True)

foul("Patty Fox", "Jessica Telephone", runner=True)
ball("Patty Fox", "Jessica Telephone", runner=True)
single("Patty Fox", "Jessica Telephone", runner=True)
r.next()  # runner on first and second, might be two advancement rolls?

sl("Patty Fox", "Alyssa Harrell", runner=True)
foul("Patty Fox", "Alyssa Harrell", runner=True)
ground_out(
    "Patty Fox", "Alyssa Harrell", "Sandie Turner", runner=True, inning_ending=True
)

# bottom of 3
single("Yazmin Mason", "Conrad Vaughan")

r.step(14)  # fc?

ball("Yazmin Mason", "Schneider Bendie", runner=True)
foul("Yazmin Mason", "Schneider Bendie", runner=True)

r.step(14)  # dp?

# top of 4
ground_out("Patty Fox", "Peanutiel Duffy", "Winnie Mccall")

sl("Patty Fox", "Moody Cookbook")
sl("Patty Fox", "Moody Cookbook")
foul("Patty Fox", "Moody Cookbook")
ball("Patty Fox", "Moody Cookbook")
bird()
ground_out("Patty Fox", "Moody Cookbook", "Sandie Turner")

foul("Patty Fox", "Ren Morin")
ground_out("Patty Fox", "Ren Morin", "Winnie Mccall", inning_ending=True)

# bottom of 4
ground_out("Yazmin Mason", "Schneider Bendie", "Ren Morin")

ball("Yazmin Mason", "Wesley Dudley")
foul("Yazmin Mason", "Wesley Dudley")
ball("Yazmin Mason", "Wesley Dudley")
flyout("Yazmin Mason", "Wesley Dudley", "Jessica Telephone")

bird()
flyout("Yazmin Mason", "Richardson Games", "Paula Turnip", inning_ending=True)

# top of 5
sl("Patty Fox", "Zion Aliciakeyes")
ground_out("Patty Fox", "Zion Aliciakeyes", "Sandie Turner")

single("Patty Fox", "Randy Castillo")

bird()
ball("Patty Fox", "Fish Summer", runner=True)
sl("Patty Fox", "Fish Summer", runner=True)
sl("Patty Fox", "Fish Summer", runner=True)
sl("Patty Fox", "Fish Summer", runner=True)

foul("Patty Fox", "Paula Turnip", runner=True)
ss("Patty Fox", "Paula Turnip", runner=True)
foul("Patty Fox", "Paula Turnip", runner=True)
sl("Patty Fox", "Paula Turnip", runner=True)

# bottom of 5
ball("Yazmin Mason", "Richardson Games")
ball("Yazmin Mason", "Richardson Games")
ball("Yazmin Mason", "Richardson Games")
ball("Yazmin Mason", "Richardson Games")

sl("Yazmin Mason", "Winnie Mccall", runner=True)
foul("Yazmin Mason", "Winnie Mccall", runner=True)
sl("Yazmin Mason", "Winnie Mccall", runner=True)
ground_out("Yazmin Mason", "Winnie Mccall", "Randy Castillo", runner=True)

caught_stealing("Yazmin Mason", "Richardson Games")
sl("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
foul("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
flyout("Yazmin Mason", "Sandie Turner", "Fish Summer", inning_ending=True)

# top of 6
ground_out("Patty Fox", "Jessica Telephone", "Winnie Mccall")

ss("Patty Fox", "Alyssa Harrell")
flyout("Patty Fox", "Alyssa Harrell", "Winnie Mccall")

single("Patty Fox", "Peanutiel Duffy")

sl("Patty Fox", "Moody Cookbook", runner=True)
ball("Patty Fox", "Moody Cookbook", runner=True)
bird()
ball("Patty Fox", "Moody Cookbook", runner=True)
ball("Patty Fox", "Moody Cookbook", runner=True)
foul("Patty Fox", "Moody Cookbook", runner=True)
two_run_homer("Patty Fox", "Moody Cookbook", runner=True)

foul("Patty Fox", "Ren Morin")
ball("Patty Fox", "Ren Morin")
ball("Patty Fox", "Ren Morin")
ball("Patty Fox", "Ren Morin")
double("Patty Fox", "Ren Morin")

sl("Patty Fox", "Zion Aliciakeyes", runner=True)
ground_out(
    "Patty Fox", "Zion Aliciakeyes", "Conrad Vaughan", runner=True, inning_ending=True
)

# bottom of 6
ball("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
flyout("Yazmin Mason", "Sandie Turner", "Jessica Telephone")

single("Yazmin Mason", "Dominic Marijuana")

single("Yazmin Mason", "Mclaughlin Scorpler", runner=True)

ball("Yazmin Mason", "Conrad Vaughan", runner=True)
ball("Yazmin Mason", "Conrad Vaughan", runner=True)
sl("Yazmin Mason", "Conrad Vaughan", runner=True)
ball("Yazmin Mason", "Conrad Vaughan", runner=True)
sl("Yazmin Mason", "Conrad Vaughan", runner=True)
bird()
ss("Yazmin Mason", "Conrad Vaughan", runner=True)
ball("Yazmin Mason", "Conrad Vaughan", runner=True)

r.step(14)  # fc?

foul("Yazmin Mason", "Schneider Bendie", runner=True)
ball("Yazmin Mason", "Schneider Bendie", runner=True)
foul("Yazmin Mason", "Schneider Bendie", runner=True)
triple("Yazmin Mason", "Schneider Bendie", runner=True)

foul("Yazmin Mason", "Wesley Dudley", runner=True)
single("Yazmin Mason", "Wesley Dudley", runner=True, is_on_third=True)

ball("Yazmin Mason", "Richardson Games", runner=True)
sl("Yazmin Mason", "Richardson Games", runner=True)
ground_out(
    "Yazmin Mason", "Richardson Games", "Fish Summer", runner=True, inning_ending=True
)

# top of 7
ground_out("Patty Fox", "Randy Castillo", "Sandie Turner")

sl("Patty Fox", "Fish Summer")
single("Patty Fox", "Fish Summer")

sl("Patty Fox", "Paula Turnip", runner=True)
r.step(14)  # dp?

# bottom of 7
sl("Yazmin Mason", "Winnie Mccall")
ss("Yazmin Mason", "Winnie Mccall")
sl("Yazmin Mason", "Winnie Mccall")
ss("Yazmin Mason", "Winnie Mccall")

foul("Yazmin Mason", "Sandie Turner")
sl("Yazmin Mason", "Sandie Turner")
sl("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
foul("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
foul("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")
ball("Yazmin Mason", "Sandie Turner")

bird()
ball("Yazmin Mason", "Dominic Marijuana", runner=True)
two_run_homer("Yazmin Mason", "Dominic Marijuana", runner=True)

ground_out("Yazmin Mason", "Mclaughlin Scorpler", "Ren Morin")

bird()
ball("Yazmin Mason", "Conrad Vaughan")
foul("Yazmin Mason", "Conrad Vaughan")
bird()
ball("Yazmin Mason", "Conrad Vaughan")
single("Yazmin Mason", "Conrad Vaughan")

ball("Yazmin Mason", "Thomas Dracaena", runner=True)
ss("Yazmin Mason", "Thomas Dracaena", runner=True)
ball("Yazmin Mason", "Thomas Dracaena", runner=True)
ground_out(
    "Yazmin Mason",
    "Thomas Dracaena",
    "Peanutiel Duffy",
    runner=True,
    inning_ending=True,
)

# top of 8
bird()
sl("Patty Fox", "Paula Turnip")
ground_out("Patty Fox", "Paula Turnip", "Schneider Bendie")

flyout("Patty Fox", "Jessica Telephone", "Winnie Mccall")

ss("Patty Fox", "Alyssa Harrell")
sl("Patty Fox", "Alyssa Harrell")
ball("Patty Fox", "Alyssa Harrell")
ball("Patty Fox", "Alyssa Harrell")
ground_out("Patty Fox", "Alyssa Harrell", "Dominic Marijuana", inning_ending=True)

# bottom of 8
foul("Yazmin Mason", "Schneider Bendie")
double("Yazmin Mason", "Schneider Bendie")

flyout("Yazmin Mason", "Wesley Dudley", "Moody Cookbook", runner=True)

ball("Yazmin Mason", "Richardson Games", runner=True)
r.step(14)  # schneider bendie scores on the sacrifice

ball("Yazmin Mason", "Winnie Mccall")
ground_out("Yazmin Mason", "Winnie Mccall", "Alyssa Harrell", inning_ending=True)

# top of 9
ground_out("Patty Fox", "Peanutiel Duffy", "Schneider Bendie")

foul("Patty Fox", "Moody Cookbook")
ball("Patty Fox", "Moody Cookbook")
foul("Patty Fox", "Moody Cookbook")
single("Patty Fox", "Moody Cookbook")

single("Patty Fox", "Ren Morin", runner=True)
foul("Patty Fox", "Zion Aliciakeyes", runner=True)
r.step(14)  # dp?
# game over

# day 113?
# r.step(2)
print("Third game")
print(r.next())
print(r.next())

weather = "peanuts"
foul("Fynn Doyle", "Fish Summer")
ball("Fynn Doyle", "Fish Summer")
ball("Fynn Doyle", "Fish Summer")
sl("Fynn Doyle", "Fish Summer")
ball("Fynn Doyle", "Fish Summer")
flyout("Fynn Doyle", "Fish Summer", "Richardson Games")

ball("Fynn Doyle", "Paula Turnip")
ss("Fynn Doyle", "Paula Turnip")
ball("Fynn Doyle", "Paula Turnip")
ball("Fynn Doyle", "Paula Turnip")
ground_out("Fynn Doyle", "Paula Turnip", "Conrad Vaughan")

ball("Fynn Doyle", "Jessica Telephone")
single("Fynn Doyle", "Jessica Telephone")

ball("Fynn Doyle", "Alyssa Harrell", runner=True)
ground_out(
    "Fynn Doyle", "Alyssa Harrell", "Sandie Turner", runner=True, inning_ending=True
)

# bottom of 1
ball("Hiroto Wilcox", "Dominic Marijuana")
foul("Hiroto Wilcox", "Dominic Marijuana")
foul("Hiroto Wilcox", "Dominic Marijuana")
double("Hiroto Wilcox", "Dominic Marijuana")

sl("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)
sl("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)
base_steal("Hiroto Wilcox", "Dominic Marijuana")
ball("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)
sl("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)
ball("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)
ss("Hiroto Wilcox", "Mclaughlin Scorpler", runner=True)

ss("Hiroto Wilcox", "Conrad Vaughan", runner=True)
sl("Hiroto Wilcox", "Conrad Vaughan", runner=True)
r.step(14)  # sac. 14 or 15

sl("Hiroto Wilcox", "Thomas Dracaena")
ss("Hiroto Wilcox", "Thomas Dracaena")
ss("Hiroto Wilcox", "Thomas Dracaena")
ground_out("Hiroto Wilcox", "Thomas Dracaena", "Alyssa Harrell", inning_ending=True)

# top of 2
single("Fynn Doyle", "Peanutiel Duffy")

ss("Fynn Doyle", "Moody Cookbook", runner=True)
ss("Fynn Doyle", "Moody Cookbook", runner=True)
ball("Fynn Doyle", "Moody Cookbook", runner=True)
foul("Fynn Doyle", "Moody Cookbook", runner=True)
ball("Fynn Doyle", "Moody Cookbook", runner=True)
foul("Fynn Doyle", "Moody Cookbook", runner=True)
sl("Fynn Doyle", "Moody Cookbook", runner=True)

r.step(14)  # dp

# bottom of 2
flyout("Hiroto Wilcox", "Schneider Bendie", "Fish Summer")

sl("Hiroto Wilcox", "Wesley Dudley")
foul("Hiroto Wilcox", "Wesley Dudley")
single("Hiroto Wilcox", "Wesley Dudley")

ball("Hiroto Wilcox", "Richardson Games", runner=True)
sl("Hiroto Wilcox", "Richardson Games", runner=True)
ball("Hiroto Wilcox", "Richardson Games", runner=True)
ss("Hiroto Wilcox", "Richardson Games", runner=True)
ball("Hiroto Wilcox", "Richardson Games", runner=True)
r.step(14)  # fc

ground_out(
    "Hiroto Wilcox",
    "Winnie Mccall",
    "Zion Aliciakeyes",
    runner=True,
    inning_ending=True,
)

import matplotlib.pyplot as plt
import pandas as pd

data = pd.DataFrame(event_info).reset_index()
data['event_type'] = data['event_type'].apply(lambda x: x.name).astype(
    'category')

color_map = {
    'Weather': "black",
    # 'StrikeLooking': "orange",
    'StrikeLooking': "red",
    'StrikeSwinging': "blue",
    'Ball': "red",
    'Foul': "blue",
    # 'Foul': "purple",
    'GroundOut': "green",
    'FlyOut': "yellow",
    'Single': "darkgreen",
    'Double': "darkred",
    'Triple': "darkblue",
    'HomeRun': "darkorange",
    'Steal': "grey",
    'CaughtStealing': "darkgrey",
}

fig, ax = plt.subplots(figsize=(12, 8))
gdata = data.groupby('event_type')
for key, group in gdata:
    if key in {"StrikeLooking", "StrikeSwinging", "Ball", "Foul"}:
        # (group['pitcher_ruth'] == data.iloc[0]['pitcher_ruth']) &
        plot_group = group[(group['strike_zone_val'] < 0.35 + group['pitcher_ruth'] * 0.35)]  #[group['strike_zone_val'] < 0.35 + group['pitcher_ruth'] * 0.35]
        plot_group.plot(ax=ax, kind='scatter', x='batter_path', y='swing_val', label=key, color=color_map[key])

plt.savefig("output.png")