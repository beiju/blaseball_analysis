"""
Using this file:

Call the rng_walker_for_birth function with the player data object (in the
format returned by chron) of a newly birthed player. It returns an iterator of
RngWalker objects if successful or throws an RngMatcherError if not. Every
RngWalker in this iterator represents a possible state that could've generated
the player you gave. If there's only one, then the values it gives can be
trusted, otherwise we don't know which is the true state. In addition to
checking the iterator size you can use the `synced` property of any RngWalker
to determine whether the values are trustworthy.

The main (only) use of an RngWalker is to subscript it to get an RNG value. See
RngWalker.__getitem__ for more. RngWalkers returned from rng_walker_for_birth
are "anchored" on the player's thwackability and positive values go forward in
time. So walker[0] will give you the thwack value, walker[-1] the last name
value, walker[-2] the first name value, walker[1] the moxie, and so on.
"""

import random
import struct
from copy import copy
from itertools import islice
from math import floor
from typing import List

import numpy as np
import z3

MASK = 0xFFFFFFFFFFFFFFFF
RNG_MATCHING_WINDOW = 5
BLOCK_SIZE = 64

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

"""
Order:
first name
last name
thwackability
moxie
divinity
musclitude
patheticism
buoyancy
baseThirst
laserlikeness
groundFriction
continuation
indulgence
martyrdom
tragicness
shakespearianism
suppression
unthwackability
coldness
overpowerment
ruthlessness
omniscience
tenaciousness
watchfulness
anticapitalism
chasiness
pressurization
cinnamon, if player has 'cinnamon' field
soul = floor(rand()*8+2)
allergy = rand() < 0.5, if player has 'peanutAllergy' field
fate = floor(rand()*100), if player has 'fate' field
ritual (value unknown), if s12 or later
blood = floor(rand()*13), if s12 or later
coffee = floor(rand()*13), if s12 or later
"""


class RngMatcherError(RuntimeError):
    pass


class RngMatcherNoSolution(RngMatcherError):
    pass


class RngMatcherMultipleSolutions(RngMatcherError):
    pass


class RngWalker:
    def __init__(self, state, offset, synced):
        self.block0_s0, self.block1_s1 = state
        self.block_to_reference_offset = offset
        self.synced = synced

        self.blocks = {}

    def __getitem__(self, i):
        """
        Return the RNG value at an offset of i from wherever this RngWalker is
        anchored (usually the player's thwackability). Positive i moves forward
        in time.

        This caches every value it sees, so it's not suitable for iterating huge
        amounts of the RNG. If you want to do that you'll need to make a new
        function that is suitable.
        """

        i_relative_to_block = i + self.block_to_reference_offset

        block_num = floor(i_relative_to_block / BLOCK_SIZE)

        if block_num in self.blocks:
            block = self.blocks[block_num]
        else:
            # This could go faster if you found the closest block to start
            # from, but the current speed is fast enough for me.
            block_s0, block_s1 = step_directionally(self.block0_s0,
                                                    self.block1_s1,
                                                    block_num * BLOCK_SIZE)

            block = generate_block(block_s0, block_s1)
            self.blocks[block_num] = block

        i_within_block = i_relative_to_block - block_num * BLOCK_SIZE
        return block[i_within_block]


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
        if input is None:
            raise RngMatcherError("Can't match on missing values")

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


def generate_numbers(s0: int, s1: int):
    while True:
        block = []
        for _ in range(BLOCK_SIZE):
            s0, s1 = xs128p(s0, s1)
            block.append(to_double(s0))
        block = block[::-1]
        yield from block


def generate_block(s0, s1):
    block = []
    for _ in range(BLOCK_SIZE):
        s0, s1 = xs128p(s0, s1)
        block.append(to_double(s0))
    block = block[::-1]
    return block


def step_forwards(s0, s1, amount):
    for _ in range(amount):
        s0, s1 = xs128p(s0, s1)
    return s0, s1


def step_backwards(s0, s1, amount):
    for _ in range(amount):
        s0, s1 = xs128p_backward(s0, s1)
    return s0, s1


def step_directionally(s0, s1, amount):
    if amount < 0:
        return step_backwards(s0, s1, -amount)
    return step_forwards(s0, s1, amount)


def rng_state_for_values(values: List[float]) -> (int, int):
    values = copy(values)
    while len(values) >= 2:
        try:
            return
        except RngMatcherError:
            values.pop()

    raise RngMatcherNoSolution("Solver found no unique solutions")


def attribute_matches(generated, expected):
    if expected is None:
        return True

    return abs(expected - generated) < 1e-12


def player_size_after_thwack(player_full):
    player = player_full['data']

    return (len(attrs_ordered) +
            ('cinnamon' in player) +
            1 +  # Soul
            ('peanutAllergy' in player) +
            ('fate' in player) +
            (player_full['validFrom'] > '2021') * 3)


def validate_rng_for_player(generator, player_full, mismatches):
    player = player_full['data']

    # First, all attributes
    for attr, generated_value in zip(attrs_ordered, generator):
        if (not attribute_matches(generated_value, player[attr]) and
                not (attr == 'tragicness' and
                     (player[attr] == 0 or player[attr] == 0.1))):
            mismatches.append(attr)
            return False

    # If the player has cinnamon, it was generated after the other attrs
    if 'cinnamon' in player:
        if not attribute_matches(next(generator), player['cinnamon']):
            mismatches.append('cinnamon')
            return False

    if player['soul'] != int(next(generator) * 8 + 2):
        mismatches.append('soul')
        return False

    if 'peanutAllergy' in player:
        if player['peanutAllergy'] != (next(generator) < 0.5):
            mismatches.append('allergy')
            return False

    if 'fate' in player:
        if player['fate'] != int(next(generator) * 100):
            mismatches.append('fate')
            return False

    # Players from before the first grand siesta have blood and coffee fields,
    # but they're always 0 at generation. After the siesta blood and coffee
    # are generated randomly with player generation.
    if player_full['validFrom'] > '2021':  # Yeah, this comparison works
        # Don't yet have a ritual database, but need to consume the value
        next(generator)

        if player['blood'] != int(next(generator) * 13):
            mismatches.append('blood')
            return False

        if player['coffee'] != int(next(generator) * 13):
            mismatches.append('coffee')
            return False

    return True


def grouper(n, iterable):
    args = [iter(iterable)] * n
    return zip(*args)


def rng_walker_for_birth(player_full):
    player = player_full['data']
    values = [player[attr] for attr in attrs_ordered]

    initial_s0, initial_s1 = None, None
    initial_offset = None
    for i in range(len(values) - RNG_MATCHING_WINDOW):
        try:
            initial_s0, initial_s1 = find_state(
                values[i:i + RNG_MATCHING_WINDOW])
            initial_offset = i
            break
        except RngMatcherError:
            pass

    if initial_s0 is None or initial_s1 is None:
        raise RngMatcherNoSolution("Solver found no unique solutions")

    initial_s0, initial_s1 = step_backwards(initial_s0, initial_s1,
                                            128 - initial_offset)
    advance_generator_by = 64 - initial_offset

    sync_to = None
    for i, val in enumerate(values):
        if val is not None:
            sync_to = i
            break

    # Find all offsets that work
    valid_offsets = []
    mismatches = []
    for offset in range(64):
        s0, s1 = step_backwards(initial_s0, initial_s1, offset)

        generator = generate_numbers(s0, s1)
        sync_iterations = None
        for i, generated in enumerate(islice(generator,
                                             advance_generator_by + sync_to,
                                             advance_generator_by + sync_to + 128)):
            if abs(generated - values[sync_to]) < 1e-12:
                # Synced!
                sync_iterations = i
                break

        if sync_iterations is None:
            mismatches.append('sync')
            continue

        generator = islice(generate_numbers(s0, s1),
                           advance_generator_by + sync_iterations,
                           None)
        if validate_rng_for_player(generator, player_full, mismatches):
            valid_offsets.append(
                (offset, advance_generator_by + sync_iterations))

    if len(valid_offsets) == 0:
        print(f"Mismatches ({len(mismatches)}):", mismatches)
        raise RngMatcherNoSolution("Couldn't find any valid offsets")

    for offset, sync_iterations in valid_offsets:
        yield RngWalker(step_backwards(initial_s0, initial_s1, offset),
                        sync_iterations, len(valid_offsets) == 1)
