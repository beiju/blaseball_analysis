import json

import matplotlib.pyplot as plt
import numpy as np
from dateutil.parser import isoparse


def main():
    with open('pies-win-data.json', 'rb') as f:
        data = json.load(f)

    first_date = None
    odds = []
    times = []
    for item in data["items"]:
        date = isoparse(item["validFrom"])
        if first_date is None:
            first_date = date
        for record in item["data"]:
            if record["teamId"] == "76d3489f-c7c4-4cb9-9c58-b1e1bab062d1":
                odds.append(record["odds"])
                times.append((date - first_date).total_seconds() / 3600)

    x = times
    y = odds
    coefficients = np.polyfit(x, y, 2)

    poly = np.poly1d(coefficients)

    new_x = np.linspace(0, 480)

    new_y = poly(new_x)

    plt.plot(np.array(x) + 7, y, "o", new_x + 7, new_y)
    plt.axhline(1)

    plt.xlim(0, 450)
    plt.ylim(0, 1.1)
    plt.title("Scientific analysis of the philly pies")
    plt.xlabel("Day")
    plt.ylabel("Pies win")
    plt.show()


if __name__ == '__main__':
    main()
