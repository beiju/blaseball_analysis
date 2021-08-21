import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.linalg


def main():
    df = pd.read_csv("hit_rate.csv")

    data = df[['unthwck', 'omni', 'hit_rate']].to_numpy()
    W = np.diag(np.sqrt(df['contact']))

    # regular grid covering the domain of the data
    X, Y = np.meshgrid(np.arange(0, 2.1, 0.1))
    XX = X.flatten()
    YY = Y.flatten()

    # best-fit linear plane
    A = np.c_[data[:, 0], data[:, 1], np.ones(data.shape[0])]
    C, residual, _, _ = scipy.linalg.lstsq(W @ A, W @ data[:, 2])  # coefficients

    # evaluate it on grid
    Z = C[0] * X + C[1] * Y + C[2]

    # or expressed using matrix/vector product
    # Z = np.dot(np.c_[XX, YY, np.ones(XX.shape)], C).reshape(X.shape)

    print(f"Hit rate ~= {C[0]:.5f} * unthwack + {C[1]:.5f} * omni + {C[2]:.5f}")

    display_data = np.repeat(data, df['contact'], axis=0)

    # This needs the data after the .repeat but before adding noise
    r2 = 1 - residual / (display_data[:, 2].size * display_data[:, 2].var())
    print("R^2:", r2)

    # Add noise to the rounded metrics so the dots aren't all overlapping
    display_data[:, :2] += (np.random.random(
        (display_data.shape[0], 2)) - 0.5) * 0.001

    # Apparently matplotlib doesn't like 1 billion data points
    display_data = display_data[np.random.choice(display_data.shape[0], 10000, replace=False)]

    # plot points and fitted surface
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, alpha=0.2)
    ax.scatter(display_data[:, 0], display_data[:, 1], display_data[:, 2],
               c='r', s=10)
    plt.xlabel('unthwack')
    plt.ylabel('omni')
    ax.set_zlabel('hit rate')
    # ax.axis('equal')
    ax.axis('tight')
    plt.show()

    # fig = plt.figure(figsize=(12, 9))
    # ax = Axes3D(fig)
    #
    # y = df['unthwck']
    # x = df['omni']
    # z = df['hit_rate']
    # ax.scatter(x, y, z,)
    #
    # ax.legend()
    #
    # plt.show()


if __name__ == '__main__':
    main()
