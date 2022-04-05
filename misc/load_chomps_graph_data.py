from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain

import matplotlib.patches as mpatches
import pandas as pd
from blaseball_mike import eventually, models
from matplotlib import pyplot as plt
from tqdm import tqdm

TEAMS = [
    ("bb4a9de5-c924-4923-a0cb-9d1445f1ee5d", "Worms"),
    ("8d87c468-699a-47a8-b40d-cfb73a5660ad", "Crabs"),
    ("36569151-a2fb-43c1-9df7-2df512424c82", "Millennials"),
    ("3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e", "Flowers"),
    ("9debc64f-74b7-4ae1-a4d6-fce0144b6ea5", "Spies"),
    ("f02aeae2-5e6a-4098-9842-02d2273f25c7", "Sunbeams"),
    ("747b8e4a-7e50-4638-a973-ea7950a3e739", "Tigers"),
    ("7966eb04-efcc-499b-8f03-d13916330531", "Magic"),
    ("46358869-dce9-4a01-bfba-ac24fc56f57e", "Mechanics"),
    ("878c1bf6-0d21-4659-bfee-916c8314d69c", "Tacos"),
    ("b024e975-1c4a-4575-8936-a3754a08806a", "Steaks"),
    ("bfd38797-8404-4b38-8b82-341da28b1f83", "Shoe Thieves"),
    ("b63be8c2-576a-4d6e-8daf-814f8bcea96f", "Dale"),
    ("105bc3ff-1320-4e37-8ef0-8d595cb95dd0", "Garages"),
    ("23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7", "Pies"),
    ("d9f89a8a-c563-493e-9d64-78e4f9a55d4a", "Georgias"),
    ("ca3f1c8c-c025-4d8e-8eef-5be6accbeb16", "Firefighters"),
    ("eb67ae5e-c4bf-46ca-bbbc-425cd34182ff", "Moist Talkers"),
    ("a37f9158-7f82-46bc-908c-c9e2dda7c33b", "Jazz Hands"),
    ("c73b705c-40ad-4633-a6ed-d357ee2e2bcf", "Lift"),
    ("2e22beba-8e36-42ba-a8bf-975683c52b5f", "Queens"),
    ("b72f3061-f573-40d7-832a-5ad475bd7909", "Lovers"),
    ("adc5b394-8f76-416d-9ce9-813706877b84", "Breath Mints"),
    ("979aee4a-6d80-4863-bf1c-ee1a78e06024", "Fridays"),
    ("57ec08cc-0411-4643-b304-0e80dbc15ac7", "Wild Wings"),
    ("b47df036-3aa4-4b98-8e9e-fe1d3ff1894b", "Paws"),
]


def main():
    data = load_data("chomps_graph_data2.csv")

    def plot_group(name: str, color: str, bottom, label):
        no_soul = data[name] - data[f"{name}_with_soul"]
        ax.bar(team_names, no_soul, bottom=bottom,
               color=color, edgecolor="black", label=label)
        if bottom is None:
            bottom = no_soul
        else:
            bottom += no_soul

        with_soul = data[f"{name}_with_soul"] - data[f"{name}_on_soul"]
        ax.bar(team_names, with_soul, bottom=bottom,
               color=color, edgecolor="black", hatch="//")
        bottom += with_soul

        return bottom

    team_ids, team_names = zip(*TEAMS)

    # get data in the right order
    data = data.reindex(team_ids)

    fig, ax = plt.subplots(1, 1, figsize=(16, 9))

    bottom = plot_group("real_attacks", "#e41a1c", None, "Chomp")
    bottom = plot_group("defended_item", "#4daf4a", bottom, "Defended: Item")
    bottom = plot_group("defended_chair", "#984ea3", bottom,
                        "Defended: Steel Chair")
    bottom = plot_group("defended_detective", "#ff7f00", bottom,
                        "Defended: Detective")
    bottom = plot_group("defended_cannons", "#377eb8", bottom,
                        "Expelled (Salmon Cannons)")

    ax.set_ylim(0, 60)

    plt.setp(ax.get_xticklabels(), rotation=-25, ha="left",
             rotation_mode="anchor")

    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]
    handles.append(
        mpatches.Patch(facecolor="#fff", hatch="//", edgecolor="black"))
    labels.append("On same team as\nChorby Soul/Chorby's Soul")
    legend = ax.legend(handles, labels, fontsize='x-large')
    legend.legendHandles[-1].set_y(9)

    fig.suptitle("Consumer Attacks by Team", fontsize="xx-large")
    ax.set_title("Excluding attacks on Chorby Soul")

    fig.tight_layout()

    plt.show()


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
