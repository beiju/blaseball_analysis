import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from plot_utils import error_bounds

attempts_col = 'num_events'
successes_col = 'num_tunnels'
# attempts_col = 'num_homers'
# successes_col = 'num_oops'
attribute = 'by_team'


def error_bounds_pd(data):
    return error_bounds(data[successes_col], data[attempts_col])

def main():
    data = pd.read_csv(f"tunnels_{attribute}.csv")

    errors = data.apply(error_bounds_pd, axis='columns')

    fig, ax = plt.subplots(1)
    ax.bar(np.arange(len(errors)),
           data[successes_col] / data[attempts_col],
           tick_label=data["nickname"],
           yerr=np.array(errors.to_list()).T,
           ecolor="lightgrey")
    # ax.errorbar(data[attribute],
    #             data[successes_col] / data[attempts_col],
    #             yerr=np.array(errors.to_list()).T,
    #             ecolor="lightgrey")
    ax.set_xlabel(attribute.title())
    # ax.set_ylabel("Went for the alley oop")
    # ax.set_ylabel("Slammed it down")
    ax.set_ylabel("Pitcher entered the Tunnels")
    # ax.set_ylim(0, 0.4)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    # ax.set_title("Alley oop attempts vs. home-run-hitter's " + attribute)
    # ax.set_title("Tunnels rate vs. defending pitcher's " + attribute)
    ax.set_title("Tunnels rate by team")

    plt.show()


if __name__ == '__main__':
    main()
