import z3, json, struct, requests, random

MASK = 0xFFFFFFFFFFFFFFFF

def reverse17(val):
    return val ^ (val >> 17) ^ (val >> 34) ^ (val >> 51)

def reverse23(val):
    return (val ^ (val << 23) ^ (val << 46)) & MASK

def xs128p(state0, state1):
    s1 = state0 & MASK
    s0 = state1 & MASK
    s1 ^= (s1 << 23) & MASK
    s1 ^= (s1 >> 17) & MASK
    s1 ^= s0 & MASK
    s1 ^= (s0 >> 26) & MASK 
    state0 = state1 & MASK
    state1 = s1 & MASK
    return state0, state1

def xs128p_backward(state0, state1):
    prev_state1 = state0
    prev_state0 = state1 ^ (state0 >> 26)
    prev_state0 = prev_state0 ^ state0
    prev_state0 = reverse17(prev_state0)
    prev_state0 = reverse23(prev_state0)
    return prev_state0, prev_state1

def z3_xs128p(sym_state0, sym_state1):
    s1 = sym_state0 
    s0 = sym_state1 
    s1 ^= (s1 << 23)
    s1 ^= z3.LShR(s1, 17)
    s1 ^= s0
    s1 ^= z3.LShR(s0, 26) 
    sym_state0 = sym_state1
    sym_state1 = s1
    return sym_state0, sym_state1

def z3_mantissa_eq(slvr, sym_state0, mantissa):
    condition = z3.Bool('c%d' % int(mantissa * random.random()))
    impl = z3.Implies(condition, (z3.LShR(sym_state0, 12)) == (int(mantissa)))
    slvr.add(impl)
    return [condition]

def z3_mantissa_range(slvr, sym_state0, lo, hi):
    conds = []

    if lo:
        condition_lo = z3.Bool('c%d' % int(hi * random.random()))
        impl_lo = z3.Implies(condition_lo, (z3.LShR(sym_state0, 12)) > (int(lo)))
        slvr.add(impl_lo)
        conds.append(condition_lo)

    if hi:
        condition_hi = z3.Bool('c%d' % int(hi * random.random()))
        impl_hi = z3.Implies(condition_hi, (z3.LShR(sym_state0, 12)) < (int(hi)))
        slvr.add(impl_hi)
        conds.append(condition_hi)

    return conds

def soul_range(soul):
    return (soul - 2) / 8, (soul - 1) / 8

def fate_range(fate):
    return fate / 100, (fate + 1) / 100

def allergy_range(allergy):
    return (0, 0.5) if allergy else (0.5, 1)

def blood_range(blood):
    return blood / 13, (blood + 1) / 13

def coffee_range(coffee):
    return coffee / 13, (coffee + 1) / 13

def get_mantissa(val):
    if val == 1.0:
        return MASK >> 12
    return struct.unpack('<Q', struct.pack('d', val + 1))[0] & (MASK >> 12)

def to_double(out):
    double_bits = ((out & MASK) >> 12) | 0x3FF0000000000000
    return struct.unpack('d', struct.pack('<Q', double_bits))[0] - 1

def solve(knowns):
    ostate0, ostate1 = z3.BitVecs('ostate0 ostate1', 64)
    sym_state0 = ostate0
    sym_state1 = ostate1
    slvr = z3.Solver()
    conditions = []

    for known in knowns[::-1]:
        sym_state0, sym_state1 = z3_xs128p(sym_state0, sym_state1)

        if type(known) == float:
            mantissa = get_mantissa(known)
            conditions += z3_mantissa_eq(slvr, sym_state0, mantissa)
        elif type(known) == tuple:
            lo, hi = known
            conditions += z3_mantissa_range(slvr, sym_state0, get_mantissa(lo), get_mantissa(hi))

    if slvr.check(conditions) == z3.sat:
        m = slvr.model()
        s0 = m[ostate0].as_long()
        s1 = m[ostate1].as_long()
        slvr.add(z3.Or(ostate0 != m[ostate0], ostate1 != m[ostate1]))
        if slvr.check(conditions) == z3.sat:
            print('not specific enough :(')
            return None
        return s0, s1
    return None

def generate_block(s0, s1, size=64):
    block = []
    for _ in range(size):
        last_s0, last_s1 = s0, s1
        s0, s1 = xs128p(s0, s1)
        block.append((last_s0, last_s1, to_double(s0)))
    block = block[::-1]
    return s0, s1, block

def generate_numbers(s0, s1, offset=0):
    if offset:
        s0, s1, block = generate_block(s0, s1, 64 - offset)
        yield from block

    while True:
        s0, s1, block = generate_block(s0, s1)
        yield from block

def step_backwards(s0, s1, amount):
    for _ in range(amount):
        s0, s1 = xs128p_backward(s0, s1)
    return s0, s1

def get_first_player_data(id): 
    versions = requests.get("https://api.sibr.dev/chronicler/v2/versions?type=player&id={}&count=1&order=asc".format(id)).json()
    return versions["items"][0]["data"]

def generate_statmap(players):
    statmap = {}
    for player in players:
        for k, v in player.items():
            if type(v) == float:
                statmap[v] = "{}/{}".format(player["name"], k)
    return statmap

def get_statmap(time):
    players = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=player&at={}&count=2000".format(time)).json()
    players = [p["data"] for p in players["items"]]
    return generate_statmap(players)

def print_val(s0, s1, val, statmap=None):
    stat = (statmap or {}).get(val)
    print("val={:<22} s0={:<20} s1={:<20} stat={}".format(val, s0, s1, stat))


team_order = [
    "b72f3061-f573-40d7-832a-5ad475bd7909", # Lovers
    "878c1bf6-0d21-4659-bfee-916c8314d69c", # Tacos
    "b024e975-1c4a-4575-8936-a3754a08806a", # Steaks
    "adc5b394-8f76-416d-9ce9-813706877b84", # Breath Mints
    "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16", # Firefighters
    "bfd38797-8404-4b38-8b82-341da28b1f83", # Shoe Thieves
    "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e", # Flowers
    "979aee4a-6d80-4863-bf1c-ee1a78e06024", # Fridays
    "7966eb04-efcc-499b-8f03-d13916330531", # Magic
    "36569151-a2fb-43c1-9df7-2df512424c82", # Millennials
    "8d87c468-699a-47a8-b40d-cfb73a5660ad", # Crabs
    "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7", # Pies
    "f02aeae2-5e6a-4098-9842-02d2273f25c7", # Sunbeams
    "57ec08cc-0411-4643-b304-0e80dbc15ac7", # Wild Wings
    "747b8e4a-7e50-4638-a973-ea7950a3e739", # Tigers
    "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff", # Moist Talkers
    "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5", # Spies
    "b63be8c2-576a-4d6e-8daf-814f8bcea96f", # Dale
    "105bc3ff-1320-4e37-8ef0-8d595cb95dd0", # Garages
    "a37f9158-7f82-46bc-908c-c9e2dda7c33b", # Jazz Hands
]

stat_order = [
    "thwackability",
    "moxie",
    "divinity",
    "musclitude",
    "patheticism",
    "buoyancy",
    "baseThirst",
    "laserlikeness",
    "groundFriction",
    "continuation",
    "indulgence",
    "tragicness",
    "shakespearianism",
    "suppression",
    "unthwackability",
    "coldness",
    "overpowerment",
    "ruthlessness",
    "omniscience",
    "tenaciousness",
    "watchfulness",
    "anticapitalism",
    "chasiness",
    "pressurization",
    # "cinnamon"
]

def find_player(player):
    window_size = 4
    for i in range(len(stat_order) - window_size + 1):
        stat_window = stat_order[i:i+window_size]
        values = [player[s] for s in stat_window]
        result = solve(values)
        if result:
            return result


def get_teams(at):
    teams = requests.get("https://api.sibr.dev/chronicler/v2/entities?type=team&at={}".format(at)).json()
    by_id = {t["entityId"]: t["data"] for t in teams["items"]}
    return [by_id[t] for t in team_order]

def load_oldest():
    with open("players_baby_grand_oldest.json", encoding="utf-8") as f:
        data = json.load(f)
        return {p["entityId"]: p["data"] for p in data}

def dump_around(s0, s1, statmap=None, blocks=3, offset=0):
    s0, s1 = step_backwards(s0, s1, 64 * blocks + offset)
    for _ in range(blocks * 2):
        s0, s1, block = generate_block(s0, s1)
        for vs0, vs1, val in block:
            print_val(vs0, vs1, val, statmap=statmap)