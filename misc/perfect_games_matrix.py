import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup
from matplotlib import gridspec

TEAM_NAMES = {name: i for i, name in enumerate([
    "San Francisco Lovers",
    "LA Unlimited Tacos",
    "Dallas Steaks",
    "Kansas City Breath Mints",
    "Chicago Firefighters",
    "Charleston Shoe Thieves",
    "Boston Flowers",
    "Hawai'i Fridays",
    "Yellowstone Magic",
    "New York Millennials",
    "Baltimore Crabs",
    "Philly Pies",
    "Hellmouth Sunbeams",
    "Mexico City Wild Wings",
    "Hades Tigers",
    "Canada Moist Talkers",
    "Houston Spies",
    "Miami Dale",
    "Seattle Garages",
    "Breckenridge Jazz Hands",
    "Tokyo Lift",
    "Ohio Worms",
    "Core Mechanics",
    "Atlantis Georgias",
])}


def main():
    page = requests.get("https://www.blaseball.wiki/w/Perfect_game")
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find("table", class_="wikitable")

    matrix = np.zeros((len(TEAM_NAMES), len(TEAM_NAMES)), dtype=int)
    for tr in table.findAll('tr')[1:]:
        season_td, player_td, perfectrator_team_td, score_td, victim_team_td, \
        strikeout_td = tr.findAll('td')
        matrix[TEAM_NAMES[perfectrator_team_td.text],
               TEAM_NAMES[victim_team_td.text]] += 1

    indices, names = zip(*enumerate(TEAM_NAMES))

    fig = plt.figure(figsize=(13, 16))
    gs = gridspec.GridSpec(2, 1, height_ratios=[5, 1])
    matrix_ax = plt.subplot(gs[0])
    graph_ax = plt.subplot(gs[1])

    im = matrix_ax.imshow(matrix)
    matrix_ax.set_xticks(indices)
    matrix_ax.set_xticklabels(names)
    matrix_ax.set_xlabel("Sufferer")
    matrix_ax.set_yticks(indices)
    matrix_ax.set_yticklabels(names)
    matrix_ax.set_ylabel("Perfectrator")

    # Rotate the tick labels and set their alignment.
    plt.setp(matrix_ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in indices:
        for j in indices:
            if matrix[i, j] != 0:
                color = "b" if matrix[i, j] == 2 else "w"
                text = matrix_ax.text(j, i, matrix[i, j],
                                      ha="center", va="center", color=color)

    matrix_ax.hlines(np.array(indices[1:]) - 0.5, -0.5, len(indices) - 0.5,
                     color='#666')
    matrix_ax.vlines(np.array(indices[1:]) - 0.5, -0.5, len(indices) - 0.5,
                     color='#666')

    matrix_ax.set_title("Perfect James")

    graph_ax.bar(indices, matrix.sum(axis=1), width=1, color='g', )
    graph_ax.bar(indices, -matrix.sum(axis=0), width=1, color='r')
    graph_ax.plot(indices, matrix.sum(axis=1) - matrix.sum(axis=0),
                  color='k', linestyle='--', linewidth=3)
    graph_ax.set_xticks(indices)
    graph_ax.set_xticklabels(names)
    plt.setp(graph_ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")
    graph_ax.set_title("Perfect Games by Team")
    plt.legend(["Net", "Perfect games earned", "Perfect games suffered"],
               loc="lower center", bbox_to_anchor=(0.5, -1), ncol=3)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.15)
    plt.show()


if __name__ == '__main__':
    main()
