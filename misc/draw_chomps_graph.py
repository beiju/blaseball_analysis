from collections import defaultdict

import matplotlib.patches as mpatches
import pandas as pd
from matplotlib import pyplot as plt

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

leadoff_hitter_victims = [
    "8d87c468-699a-47a8-b40d-cfb73a5660ad",
    "7966eb04-efcc-499b-8f03-d13916330531",
    "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16",
    "36569151-a2fb-43c1-9df7-2df512424c82",
]


def main():
    data = load_data("chomps_graph_data2.csv")

    team_ids, team_names = zip(*TEAMS)

    # get data in the right order
    data = data.reindex(team_ids)

    def plot_group(name: str, color: str, bottom, label):
        # there's probably a better way to do this
        leadoff_s24 = data[f"{name}_leadoff_s24"] * 0
        leadoff_s24.loc[leadoff_hitter_victims] = data[f"{name}_leadoff_s24"].loc[leadoff_hitter_victims]
        ax.bar(team_names, leadoff_s24, bottom=bottom,
               color=color, edgecolor="#0008", hatch="xxx")
        if bottom is None:
            bottom = leadoff_s24
        else:
            bottom += leadoff_s24

        no_soul = data[name] - data[f"{name}_with_soul"] - leadoff_s24
        ax.bar(team_names, no_soul, bottom=bottom,
               color=color, edgecolor="#0008", label=label)
        bottom += no_soul

        with_soul = data[f"{name}_with_soul"]
        ax.bar(team_names, with_soul, bottom=bottom,
               color=color, edgecolor="#0008", hatch="///")
        bottom += with_soul

        return bottom

    fig = plt.figure(constrained_layout=True, figsize=(16, 9))
    gs = fig.add_gridspec(2, 27, height_ratios=(6, 1),
                          width_ratios=[0.2] + ([1] * 26))
    ax = fig.add_subplot(gs[0, :])
    pie_axes = [fig.add_subplot(gs[1, i + 1]) for i in range(26)]

    bottom = plot_group("real_attacks", "#e41a1c", None, "Chomp")
    bottom = plot_group("defended_item", "#4daf4a", bottom, "Defended: Item")
    bottom = plot_group("defended_chair", "#984ea3", bottom,
                        "Defended: Steel Chair")
    bottom = plot_group("defended_detective", "#ff7f00", bottom,
                        "Defended: Detective")
    bottom = plot_group("defended_cannons", "#377eb8", bottom,
                        "Expelled (Salmon Cannons)")

    ax.set_ylim(0, 200)
    ax.set_xlim(-0.6, len(team_ids) - 0.4)

    plt.setp(ax.get_xticklabels(), rotation=-25, ha="left",
             rotation_mode="anchor")

    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]
    handles.append(
        mpatches.Patch(facecolor="#fff", hatch="///", edgecolor="black"))
    labels.append("On same team as\nChorby Soul/Chorby's Soul")
    handles.append(
        mpatches.Patch(facecolor="#fff", hatch="xxx", edgecolor="black"))
    labels.append("S24 leadoff hitter effect")
    legend = ax.legend(handles, labels, fontsize='x-large')
    legend.legendHandles[-2].set_y(9)

    fig.suptitle("Consumer Attacks by Team", fontsize="xx-large")
    ax.set_title("Including attacks on Chorby Soul and Chorby's Soul")

    # Hijacking the xlabel as a title for the pie chart
    ax.set_xlabel("Games spent at each dangerous Credit Rating",
                  fontsize="xx-large", labelpad=20)

    pie_data = pd.read_csv("days_at_level.csv", index_col=0)
    pie_data.drop(columns=['safe'], inplace=True)

    pie_colors = [
        "#fdbb84",
        "#fc8d59",
        "#ef6548",
        "#d7301f",
        "#b30000",
        "#7f0000",
        "#000"
    ]
    max_days = pie_data.max().max()
    for i, pie_ax in enumerate(pie_axes):
        pie_ax.axis("off")
        pie_ax.bar(pie_data.columns, pie_data.loc[team_ids[i]].array,
                   width=1.0, color=pie_colors)
        # pie_ax.add_patch(
        #     mpatches.Rectangle((-0.5, 0), 12, max_days,
        #                        linewidth=0.5, edgecolor='k', facecolor='none')
        # )

        pie_ax.set_ylim(-max_days * 1, max_days * 1.05)

    fig.legend(
        [mpatches.Patch(facecolor=color, edgecolor="black") for color in
         pie_colors],
        ["Low A*", "High A*", "AA*", "AAA*", "AAAA*", "AAAAA*", "Beyond AAAAA"],
        loc="lower center", ncol=len(pie_colors), fontsize="large"
    )
    fig.text(0.95, .02, "* or season 24 equivalent", ha='right')
    fig.text(0.05, .02, "visualization by beiju", ha='left', color="#0006")

    # fig.tight_layout()

    plt.savefig("chomps_with_soul.png", dpi=300, )
    # plt.show()


def zero_defaultdict():
    return defaultdict(lambda: 0)


def load_data(filename):
    return pd.read_csv(filename, index_col=0)


if __name__ == '__main__':
    main()
