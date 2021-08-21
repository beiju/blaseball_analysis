import numpy as np
from matplotlib import pyplot as plt
import matplotlib.ticker as plticker
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = mpl.rcParams['figure.dpi'] * 2

base_cost = 1


def shift(arr, num, fill_value=np.nan):
    result = np.empty_like(arr)
    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result[:] = arr
    return result


def main():
    coins_spent_forcing = np.arange(0, 35)
    coins_to_defend = np.zeros_like(coins_spent_forcing)
    renos_earned = np.zeros_like(coins_spent_forcing)

    fig, ax = plt.subplots(1, figsize=(3, 8))
    ax.set_aspect('equal', adjustable='box')

    cumulative_reno_cost = 0
    next_reno_cost = base_cost
    for reno_number in range(1, 10):
        cumulative_reno_cost += next_reno_cost
        next_reno_cost = 3 * next_reno_cost
        coins_spent_defending = coins_spent_forcing * reno_number

        total_coins = coins_spent_forcing + coins_spent_defending
        mask = (cumulative_reno_cost <= total_coins) & (
                total_coins < cumulative_reno_cost + next_reno_cost)
        coins_to_defend[mask] = coins_spent_defending[mask]
        renos_earned[mask] = reno_number

    # ax.plot([0, coins_spent_forcing[0]], [0, coins_to_defend[0]], label=0)
    for reno_number in np.unique(renos_earned):
        mask = renos_earned == reno_number
        mask = mask | shift(mask, -1, fill_value=False)
        ax.plot(coins_spent_forcing[mask], coins_to_defend[mask],
                label=str(reno_number))

    ax.set_xlabel("Coins spent on one reno (millions)")
    ax.set_xlim(left=0, right=30)
    ax.set_ylabel("Coins required to outspend (millions)")
    ax.set_ylim(bottom=0)
    ax.set_title("Avoiding a reno is expensive")
    ax.legend(title="Num earned")

    loc = plticker.MultipleLocator(
        base=10)  # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)
    ax.yaxis.set_major_locator(loc)

    plt.tight_layout()
    plt.show()

    pass


if __name__ == '__main__':
    main()
