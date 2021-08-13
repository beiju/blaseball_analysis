import pandas as pd

from blaseball_mike.models import Team
from blaseball_mike.utils import get_gameday_start_time
from matplotlib import pyplot as plt


def plot():
    data = pd.read_csv("navigation_with_edensity.csv")
    hole_x = -10 - data['X']
    hole_y = -10 - data['Y']
    norm = (hole_x ** 2 + hole_y ** 2) ** 0.5

    hole_x /= norm
    hole_y /= norm

    data['at_wall'] = ~((-1 < data['X']) & (data['X'] < 1) &
                        (-1 < data['Y']) & (data['Y'] < 1))

    data['hits_wall'] = data.groupby('ID')['at_wall'].shift(-1)

    velocities = data.groupby('ID')[['X', 'Y']].diff(axis=0).shift(-1)
    velocities[data['hits_wall'] == True] = float('nan')

    corrected_vel_x = velocities['X'] - hole_x * data.groupby('ID')[
        'edensity'].shift(-2) * 0.00002
    corrected_vel_y = velocities['Y'] - hole_y * data.groupby('ID')[
        'edensity'].shift(-2) * 0.00002

    corrected_speed = (corrected_vel_x ** 2 + corrected_vel_y ** 2) ** 0.5

    data['corrected_speed'] = corrected_speed
    data['speed'] = (velocities['X'] ** 2 + velocities['Y'] ** 2) ** 0.5

    clean_data = data[
        (-1 < data['X']) & (data['X'] < 1) &
        (-1 < data['Y']) & (data['Y'] < 1) &
        (data['corrected_speed'] > 0) &
        (data['edensity'] != 0)
        ]

    fig, ax = plt.subplots(1)
    ax.scatter(clean_data['Day'], clean_data['speed'], label='Speed')
    ax.scatter(clean_data['Day'], clean_data['corrected_speed'],
               label='Speed minus pull')
    ax.set_xlabel('Day')
    ax.set_ylabel('Speed')
    ax.legend()
    plt.show()


def compute():
    data = pd.read_csv("navigation.csv")

    data = data[data['Day'] > 57]

    def get_edensity(row):
        print("Fetching", row['Name'], "on day", row['Day'])
        time = get_gameday_start_time(season=24, day=row['Day'])
        team = Team.load_at_time(row['ID'], time)

        if team is None:
            return float('nan')

        return team.e_density

    data['edensity'] = data.apply(get_edensity, axis='columns')

    data.to_csv("navigation_with_edensity.csv")


if __name__ == '__main__':
    plot()
