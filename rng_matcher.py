"""
Using this file:

Call the rng_walker_for_birth function with the player data object (in the
format returned by chron) of a newly birthed player. It returns an RngWalker
object if successful or throws an RngMatcherError if not. An RngWalker will
be returned even if the RNG position could not be synced (ask sibr what this
means). Values derived from an unsynced walker are untrustworthy. You can use
the `synced` property of an RngWalker to determine whether the values are
trustworthy.

The main use of an RngWalker is to subscript it to get an RNG value. See
RngWalker.__getitem__ for more.
"""


import random
import struct
from copy import copy
from itertools import islice
from typing import List

import z3

MASK = 0xFFFFFFFFFFFFFFFF

attrs_ordered = [
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
    "martyrdom",
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
    # "cinnamon"  # Not present in early players
]


class RngMatcherError(RuntimeError):
    pass


class RngMatcherNoSolution(RngMatcherError):
    pass


class RngMatcherMultipleSolutions(RngMatcherError):
    pass


# Symbolic execution of xs128p
def sym_xs128p(slvr, sym_state0, sym_state1, generated):
    s1 = sym_state0
    s0 = sym_state1
    s1 ^= (s1 << 23)
    s1 ^= z3.LShR(s1, 17)
    s1 ^= s0
    s1 ^= z3.LShR(s0, 26)
    sym_state0 = sym_state1
    sym_state1 = s1
    calc = sym_state0

    condition = z3.Bool('c%d' % int(generated * random.random()))
    impl = z3.Implies(condition, z3.LShR(calc, 12) == int(generated))

    slvr.add(impl)
    return sym_state0, sym_state1, [condition]


def find_state(inputs):
    knowns = []
    for input in inputs[::-1]:
        recovered = struct.unpack('<Q', struct.pack('d', input + 1))[0] & (
                MASK >> 12)
        knowns.append(recovered)

    ostate0, ostate1 = z3.BitVecs('ostate0 ostate1', 64)
    sym_state0 = ostate0
    sym_state1 = ostate1
    slvr = z3.Solver()
    conditions = []

    # run symbolic xorshift128+ algorithm for three iterations
    # using the recovered numbers as constraints
    for known in knowns:
        sym_state0, sym_state1, ret_conditions = sym_xs128p(slvr, sym_state0,
                                                            sym_state1, known)
        conditions += ret_conditions

    if slvr.check(conditions) == z3.sat:
        # get a solved state
        m = slvr.model()
        s0 = m[ostate0].as_long()
        s1 = m[ostate1].as_long()
        slvr.add(z3.Or(ostate0 != m[ostate0], ostate1 != m[ostate1]))
        if slvr.check(conditions) == z3.sat:
            raise RngMatcherMultipleSolutions("Solver found multiple solutions")
        return s0, s1

    raise RngMatcherNoSolution("Solver found no solutions")


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


def to_double(out):
    double_bits = ((out & MASK) >> 12) | 0x3FF0000000000000
    return struct.unpack('d', struct.pack('<Q', double_bits))[0] - 1


def find_fk_stat(player, value):
    for k, v in player.items():
        if v == value:
            return k


def find_fk_stat_deep(players, value):
    for player in players:
        stat = find_fk_stat(player, value)
        if stat:
            return "{}/{}".format(player["name"], stat)


def generate_numbers(s0: int, s1: int):
    while True:
        block = []
        for _ in range(64):
            last_s0, last_s1 = s0, s1
            s0, s1 = xs128p(s0, s1)
            block.append((last_s0, last_s1, to_double(s0)))
        block = block[::-1]
        yield from block


def print_val(players, s0, s1, val):
    print("{}\ts0={}\ts1={}\tstat={}".format(val, s0, s1,
                                             find_fk_stat_deep(players, val)))


def step_backwards(s0, s1, amount):
    for _ in range(amount):
        s0, s1 = xs128p_backward(s0, s1)
    return s0, s1


def rng_state_for_values(values: List[float]) -> (int, int):
    values = copy(values)
    while len(values) >= 2:
        try:
            return find_state(values)
        except RngMatcherError:
            values.pop()

    raise RngMatcherNoSolution("Solver found no unique solutions")


class RngWalker:
    def __init__(self, state, sync_iterations, synced):
        self.start_s0, self.start_s1 = state
        self.sync_iterations = sync_iterations
        self.synced = synced

    def __getitem__(self, i):
        """
        Return the RNG value at an offset of i from the player's thwackability.
        Note that positive i moves backwards in time (so i=1 should return the
        last name value, i=2 the first name value, etc). This is a load-bearing
        bug.

        This function is really inefficient. Hilariously inefficient. You
        probably want to save the values you get in variables rather than
        calling it twice. Or just write the function better.
        """
        target = self.sync_iterations - i
        s0, s1 = self.start_s0, self.start_s1
        while target < 0:
            s0, s1 = step_backwards(s0, s1, 64)
            target += 64

        generator = generate_numbers(s0, s1)
        for _ in zip(generator, range(target)):
            pass

        _, _, value = next(generator)
        return value


def rng_walker_for_values(values: List[float]):
    initial_s0, initial_s1 = rng_state_for_values(values[:5])

    # Find all offsets that work
    valid_offsets = []
    for offset in range(64):
        s0, s1 = step_backwards(initial_s0, initial_s1, offset)

        generator = generate_numbers(s0, s1)
        sync_iterations = None
        for i, (_, _, generated) in enumerate(islice(generator, 128)):
            if generated == values[0]:
                # Synced!
                sync_iterations = i
                break

        if sync_iterations is None:
            raise RngMatcherNoSolution("Failed to sync RNG")

        for i, (expected, (_, _, actual)) in enumerate(zip(values[1:], generator)):
            if expected != actual:
                # print("Offset", offset, "breaks at item", i, expected, '!=', actual)
                break
        else:
            # print("Offset", offset, "works")
            valid_offsets.append((offset, sync_iterations))

    if len(valid_offsets) == 0:
        raise RngMatcherNoSolution("Couldn't find any valid offsets")

    offset, sync_iterations = valid_offsets[0]
    return RngWalker(step_backwards(initial_s0, initial_s1, offset),
                     sync_iterations - 1, len(valid_offsets) == 1)


def rng_walker_for_birth(player):
    values = [player[attr] for attr in attrs_ordered]
    return rng_walker_for_values(values)
