from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain

import pandas as pd
from blaseball_mike import eventually, models
from tqdm import tqdm


def main():
    load_data("chomps_graph_data2.csv")


def zero_defaultdict():
    return defaultdict(lambda: 0)


@dataclass
class Category:
    total: defaultdict = field(default_factory=zero_defaultdict)
    with_soul: defaultdict = field(default_factory=zero_defaultdict)
    on_soul: defaultdict = field(default_factory=zero_defaultdict)
    leadoff_s24: defaultdict = field(default_factory=zero_defaultdict)

    def add_one(self, team_id: str, on_soul: bool, with_soul: bool,
                leadoff_s24: bool):
        self.total[team_id] += 1
        if on_soul:
            self.on_soul[team_id] += 1
        if with_soul:
            self.with_soul[team_id] += 1
        if leadoff_s24:
            self.leadoff_s24[team_id] += 1

    def as_dataframe(self, colname: str):
        return pd.DataFrame.from_dict(self.total, orient='index', dtype=int,
                                      columns=[colname]) \
            .join(
            pd.DataFrame.from_dict(self.on_soul, orient='index', dtype=int,
                                   columns=[f"{colname}_on_soul"]), how='outer') \
            .join(
            pd.DataFrame.from_dict(self.with_soul, orient='index', dtype=int,
                                   columns=[f"{colname}_with_soul"]),
            how='outer') \
            .join(
            pd.DataFrame.from_dict(self.leadoff_s24, orient='index', dtype=int,
                                   columns=[f"{colname}_leadoff_s24"]),
            how='outer')


def load_data(filename):
    try:
        return pd.read_csv(filename, index_col=0)
    except FileNotFoundError:
        pass

    events = eventually.search(cache_time=None, limit=-1, query={
        "type": 67
    })

    real_attacks = Category()
    defended_item = Category()
    defended_cannons = Category()
    defended_detective = Category()
    defended_chair = Category()

    for event in tqdm(events, total=972):
        if len(event["playerTags"]) == 1:
            player_id = event["playerTags"][0]
        elif len(event["playerTags"]) == 2:
            player_id = event["playerTags"][0]
            defender = models.Player.load_one_at_time(event["playerTags"][1],
                                                      event["created"])
            # Make sure the victim is the first id
            assert (
                # Steel chair
                    ("STEELED " + defender.player_name.upper()) in event[
                "description"] or
                    # Detective
                    (defender.player_name.upper() in event[
                        "description"] and "A CONSUMER!" in event[
                         "description"])
            )
        else:
            raise RuntimeError("Event with no player")
        player = models.Player.load_one_at_time(player_id, event["created"])
        team_id = player.league_team.id
        team = models.Team.load_at_time(team_id, event["created"])

        on_soul = player_is_soul(player)
        with_soul = team_has_soul(team, event["created"])
        leadoff_s24 = event["season"] == 23 and player_id == team.lineup[0].id

        if "SALMON CANNONS FIRE" in event["description"]:
            defended_cannons.add_one(team_id, on_soul, with_soul, leadoff_s24)
        elif "DEFENDS" in event["description"]:
            defended_item.add_one(team_id, on_soul, with_soul, leadoff_s24)
        elif "COUNTERED WITH THE" in event["description"]:
            defended_chair.add_one(team_id, on_soul, with_soul, leadoff_s24)
        elif "A CONSUMER!" in event["description"]:
            defended_detective.add_one(team_id, on_soul, with_soul, leadoff_s24)
        else:
            real_attacks.add_one(team_id, on_soul, with_soul, leadoff_s24)

    data = real_attacks.as_dataframe("real_attacks") \
        .join(defended_cannons.as_dataframe("defended_cannons"), how='outer') \
        .join(defended_item.as_dataframe("defended_item"), how='outer') \
        .join(defended_chair.as_dataframe("defended_chair"), how='outer') \
        .join(defended_detective.as_dataframe("defended_detective"),
              how='outer') \
        .fillna(0)

    data.to_csv(filename)

    return data


def player_is_soul(player):
    return (
            player.id == "a1628d97-16ca-4a75-b8df-569bae02bef9" or
            any(
                item.id == "04749f19-e782-40e2-9077-e79baa6236f6" or item.id == "34848297-a781-4a0a-9176-62d22364190c"
                for item in player.items)
    )


def team_has_soul(team: models.Team, date: str):
    # hilariously inefficient but hey, it works
    for player_at_wrong_time in chain(team.lineup, team.rotation):
        player = models.Player.load_one_at_time(player_at_wrong_time.id, date)
        if player_is_soul(player):
            return True

    return False


if __name__ == '__main__':
    main()
