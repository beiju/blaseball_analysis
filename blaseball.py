import matplotlib.pyplot as plt
from dateutil import parser
from dateutil.tz import gettz, tzutc

tzinfos = {"PST": gettz("America/Los Angeles"), "BST": gettz("Europe/London")}


def main():
    blaseball1 = parser.parse("Monday, July 20, 2020 at 9am PST", tzinfos=tzinfos).astimezone(tzutc())
    blaseball2 = parser.parse("10/20/2020 11:02 AM BST", tzinfos=tzinfos).astimezone(tzutc())
    blaseball0 = parser.parse("June 2, 2023 at 4:51 PM BST", tzinfos=tzinfos).astimezone(tzutc())

    x = [blaseball1, blaseball2, blaseball0]
    y = [1, 2]

    figsize_denom = 2
    fig, ax = plt.subplots(figsize=[16 / figsize_denom, 9 / figsize_denom])

    ax.stairs(y, x)
    ax.set_xticks(x, [t.strftime("%Y-%m-%d %H:%M:%S") for t in x], rotation=15, ha="right")
    ax.set_yticks([0, 1, 2])
    ax.set_ylabel("blaseball")
    ax.set_xlabel("time")
    ax.set_title("blaseball")

    plt.tight_layout()

    plt.show()


if __name__ == '__main__':
    main()
