from blaseball_mike import models
import matplotlib.pyplot as plt


def main():
    print("Loading league...", end="")
    league = models.League.load()
    print(" Done")

    fig, ax = plt.subplots(figsize=(10, 6))

    ruth, unthwck, colors = [], [], []
    for team in league.teams.values():
        ruth.append(
            sum(p.ruthlessness for p in team.rotation) / len(team.rotation))
        unthwck.append(
            sum(p.unthwackability for p in team.rotation) / len(team.rotation))
        colors.append(team.main_color)

        print(team.full_name, ruth[-1], unthwck[-1])


    ax.scatter(ruth, unthwck, c=colors, s=200)
    ax.set_title('Pitchers', fontsize=15)
    ax.set_xlabel('Average Ruthlessness')
    ax.set_ylabel('Average Unthwackability')
    plt.show()


if __name__ == '__main__':
    main()
