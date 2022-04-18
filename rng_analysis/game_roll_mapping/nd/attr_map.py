import csv

def load_attrs():
    attr_map = {}
    with open("all_attrs.csv", newline="", encoding="utf-8") as f:
        for player_id, player_name, attr_name, attr_value, timestamp in csv.reader(f):
            attr_value = float(attr_value)
            if attr_value in attr_map:
                continue

            attr_map[attr_value] = (player_id, player_name, attr_name, timestamp)
    return attr_map


attr_map = load_attrs()

def match_attr(val):
    return attr_map.get(val)

def match_any(vals):
    earliest = None
    for val in vals:
        if type(val) != float:
            continue

        match = match_attr(val)
        if match:
            if not earliest or earliest[3] > match[3]:
                earliest = match
    return earliest

def match_first(vals):
    for val in vals:
        if type(val) != float:
            continue

        match = match_attr(val)
        if match:
            return match

def match_str(match):
    if not match:
        return None
    _, player_name, stat_name, timestamp = match
    day = timestamp[:len("YYYY-MM-DD")]
    return "[{}/{}] @ {}".format(player_name, stat_name, day)