from nd import rng


class RngGame:
    def __init__(self, *rng_args, **rng_kwargs):
        self.next_update = 0
        self.rng = rng.Rng(*rng_args, **rng_kwargs)
