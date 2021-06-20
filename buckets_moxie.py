import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from ebcic import ebcic

attempts_col = 'num_oops'
successes_col = 'num_successful'
# attempts_col = 'num_homers'
# successes_col = 'num_oops'
attribute = 'moxie'


def error_bounds(data):
    p = ebcic.Params(
        k=data[successes_col],
        n=data[attempts_col],
        confi_perc=95,
    )

    lower, upper = ebcic.exact(p)
    percent = data[successes_col] / data[attempts_col]
    return (
        percent - upper,
        lower - percent
    )


def main():
    data = pd.read_csv(f"hoop_success_{attribute}.csv")

    errors = data.apply(error_bounds, axis='columns')

    fig, ax = plt.subplots(1)
    ax.errorbar(data[attribute],
                data[successes_col] / data[attempts_col],
                yerr=np.array(errors.to_list()).T,
                ecolor="lightgrey")
    ax.set_xlabel(attribute.title())
    # ax.set_ylabel("Went for the alley oop")
    ax.set_ylabel("Slammed it down")
    # ax.set_ylim(0, 0.4)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    # ax.set_title("Alley oop attempts vs. home-run-hitter's " + attribute)
    ax.set_title("Alley oop success rate vs. alley-ooper's " + attribute)

    plt.show()


if __name__ == '__main__':
    main()
