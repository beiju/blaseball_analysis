from datetime import datetime
from typing import List, Tuple, Union, Optional

from dateutil.parser import parse as parse_date
from lark import Lark, Transformer


class Entry:
    def __init__(self,
                 pos: int,
                 state: Tuple[Tuple[int, int], int],
                 name: Union[str, Tuple[str, str]],
                 timestamp: Optional[datetime] = None):
        self.pos = pos
        self.state = state
        try:
            (self.name, self.type) = name
        except ValueError:
            self.name = name
            self.type = None
        self.timestamp = timestamp


class Fragment:
    def __init__(self, aligned: bool, anchors: List[Entry],
                 events: List[Entry]):
        self.aligned = aligned
        self.anchors = anchors
        self.events = events


# noinspection PyMethodMayBeStatic
class FragmentsTransformer(Transformer):
    def true(self, _):
        return True

    def false(self, _):
        return False

    def fragments(self, node):
        return node

    def fragment(self, node):
        assert len(node) == 3
        return Fragment(*node)

    def anchors(self, node):
        # This function does do something -- it unwraps from a parser type to a
        # python type
        return node

    def events(self, node):
        return node

    def anchor_entry(self, node):
        return Entry(*node)

    def event_entry(self, node):
        return Entry(*node)

    def pos(self, node):
        assert len(node) == 1
        return int(node[0].value)

    def state(self, node):
        assert len(node) == 3
        return ((int(node[0].value), int(node[1].value)),
                int(node[2].value))

    def name_any(self, node):
        assert len(node) == 1
        return node[0].value

    def name_roll(self, node):
        assert len(node) == 2
        return node[0].value, node[1].value

    def timestamp(self, node):
        assert len(node) == 1
        return parse_date(node[0].value)


def load_fragments(filename: str):
    parser = Lark(open('fragments_file_parser.lark', 'r'),
                  start='fragments', debug=True)
    with open(filename, 'r') as f:
        fragments_raw = parser.parse(f.read())

    return FragmentsTransformer().transform(fragments_raw)
