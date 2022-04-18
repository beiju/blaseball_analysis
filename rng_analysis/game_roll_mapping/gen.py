from .data import *
from .rng import *


def roll_stats(r, cinnamon=False):
    stats = {}
    stats["thwackability"] = r.next()
    thwack_state = r.get_state()

    for stat in [x for x in stat_order[1:] if x != "cinnamon"]:
        stats[stat] = r.next()

    if cinnamon:
        stats["cinnamon"] = r.next()

    return stats, thwack_state


def generate_player(
    r: Rng,
    roll_name=True,
    roll_cinnamon=False,
    roll_peanuts=False,
    roll_interviews=False,
):
    first_name_roll, last_name_roll = (
        (r.next(), r.next()) if roll_name else (None, None)
    )

    stats, thwack_state = roll_stats(r, cinnamon=roll_cinnamon)

    soul_roll = r.next()
    allergy_roll, fate_roll = (r.next(), r.next()) if roll_peanuts else (None, None)
    ritual_roll, blood_roll, coffee_roll = (
        (r.next(), r.next(), r.next()) if roll_interviews else (None, None, None)
    )

    return dict(
        **stats,
        soul=soul_roll and to_soul(soul_roll),
        peanutAllergy=allergy_roll and to_allergy(allergy_roll),
        fate=fate_roll and to_fate(fate_roll),
        ritual=ritual_roll and to_ritual(ritual_roll),
        blood=blood_roll and to_blood(blood_roll),
        coffee=coffee_roll and to_coffee(coffee_roll),
        rolls=dict(
            firstName=first_name_roll,
            lastName=last_name_roll,
            soul=soul_roll,
            peanutAllergy=allergy_roll,
            fate=fate_roll,
            ritual=ritual_roll,
            blood=blood_roll,
            coffee=coffee_roll,
        ),
        state=dict(s0=thwack_state[0], s1=thwack_state[1], offset=thwack_state[2])
    )
