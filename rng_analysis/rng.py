import struct
from typing import Tuple

# from . import attr_map

MASK = 0xFFFFFFFFFFFFFFFF

def reverse17(val):
    return val ^ (val >> 17) ^ (val >> 34) ^ (val >> 51)

def reverse23(val):
    return (val ^ (val << 23) ^ (val << 46)) & MASK

def xs128p(state):
    s1 = state[0] & MASK
    s0 = state[1] & MASK
    s1 ^= (s1 << 23) & MASK
    s1 ^= (s1 >> 17) & MASK
    s1 ^= s0 & MASK
    s1 ^= (s0 >> 26) & MASK 
    state0 = state[1] & MASK
    state1 = s1 & MASK
    return state0, state1

def xs128p_backward(state):
    prev_state1 = state[0]
    prev_state0 = state[1] ^ (state[0] >> 26)
    prev_state0 = prev_state0 ^ state[0]
    prev_state0 = reverse17(prev_state0)
    prev_state0 = reverse23(prev_state0)
    return prev_state0, prev_state1

def to_double(out):
    double_bits = ((out & MASK) >> 12) | 0x3FF0000000000000
    return struct.unpack('d', struct.pack('<Q', double_bits))[0] - 1

def state_str(s0, s1, offset):
    return "({}, {})+{:<2}".format(s0, s1, offset)

def dbg_str(s0, s1, offset, note=None):
    state = state_str(s0, s1, offset)
    val = to_double(s0)
    return "s={:<47}  val={:<22} {}".format(state, val, note or "")

def to_soul(val):
    return int(val * 8 + 2)

def to_fate(val):
    return int(val * 100)

def to_allergy(val):
    return val < 0.5

def to_ritual(val):
    return int(val * 310)

def to_blood(val):
    return int(val * 13)

def to_coffee(val):
    return int(val * 13)

class Rng(object):
    state: Tuple[int, int]
    offset: int

    def __init__(self, state: Tuple[int, int], offset: int):
        self.state = state
        self.offset = offset

        self.distance_from_start = 0

    def __getitem__(self, i):
        self.step(i - self.distance_from_start)
        return self.value()

    def get_state(self) -> Tuple[int, int, int]:
        return self.state[0], self.state[1], self.offset

    def get_state_str(self) -> str:
        return state_str(self.state[0], self.state[1], self.offset)

    # def dbg(self) -> str:
    #     val = self.value()
    #
    #     match = attr_map.match_attr(val)
    #     stat_str = attr_map.match_str(match) if match else None
    #
    #     return "s={:<47}  val={:<22} {}".format(self.get_state_str(), val, stat_str)

    def value(self) -> float:
        return to_double(self.state[0])

    def next(self) -> float:
        self.step(1)
        return self.value()

    def prev(self) -> float:
        self.step(-1)
        return self.value()

    def step_raw(self, amount=1):
        if amount > 0:
            for _ in range(amount):
                self.state = xs128p(self.state)
        else:
            for _ in range(-amount):
                self.state = xs128p_backward(self.state)

    def step(self, steps=1, debug_block_boundaries=False):
        self.offset -= steps
        self.distance_from_start += steps

        while self.offset < 0:
            if debug_block_boundaries:
                print("-----")
            self.step_raw(128)
            self.offset += 64

        while self.offset >= 64:
            if debug_block_boundaries:
                print("-----")
            self.step_raw(-128)
            self.offset -= 64

        self.step_raw(-steps)
