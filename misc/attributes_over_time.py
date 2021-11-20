import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation
from tqdm import tqdm

ATTRS = ['divinity', 'thwackability', 'moxie',
         'musclitude', 'patheticism', 'martyrdom', 'tragicness', 'buoyancy',
         'unthwackability', 'ruthlessness', 'overpowerment', 'shakespearianism',
         'suppression', 'laserlikeness', 'continuation', 'base_thirst',
         'indulgence', 'ground_friction', 'omniscience', 'tenaciousness',
         'watchfulness', 'anticapitalism', 'chasiness']

TEAM_IDS = list(reversed([
    "b72f3061-f573-40d7-832a-5ad475bd7909",  # Lovers
    "878c1bf6-0d21-4659-bfee-916c8314d69c",  # Tacos
    "b024e975-1c4a-4575-8936-a3754a08806a",  # Steaks
    "adc5b394-8f76-416d-9ce9-813706877b84",  # Breath Mints
    "ca3f1c8c-c025-4d8e-8eef-5be6accbeb16",  # Firefighters
    "bfd38797-8404-4b38-8b82-341da28b1f83",  # Shoe Thieves
    "3f8bbb15-61c0-4e3f-8e4a-907a5fb1565e",  # Flowers
    "979aee4a-6d80-4863-bf1c-ee1a78e06024",  # Fridays
    "7966eb04-efcc-499b-8f03-d13916330531",  # Magic
    "36569151-a2fb-43c1-9df7-2df512424c82",  # Millennials
    "8d87c468-699a-47a8-b40d-cfb73a5660ad",  # Crabs
    "23e4cbc1-e9cd-47fa-a35b-bfa06f726cb7",  # Pies
    "f02aeae2-5e6a-4098-9842-02d2273f25c7",  # Sunbeams
    "57ec08cc-0411-4643-b304-0e80dbc15ac7",  # Wild Wings
    "747b8e4a-7e50-4638-a973-ea7950a3e739",  # Tigers
    "eb67ae5e-c4bf-46ca-bbbc-425cd34182ff",  # Moist Talkers
    "9debc64f-74b7-4ae1-a4d6-fce0144b6ea5",  # Spies
    "b63be8c2-576a-4d6e-8daf-814f8bcea96f",  # Dale
    "105bc3ff-1320-4e37-8ef0-8d595cb95dd0",  # Garages
    "a37f9158-7f82-46bc-908c-c9e2dda7c33b",  # Jazz Hands
    "c73b705c-40ad-4633-a6ed-d357ee2e2bcf",  # Lift
    "bb4a9de5-c924-4923-a0cb-9d1445f1ee5d",  # Worms
    "46358869-dce9-4a01-bfba-ac24fc56f57e",  # Mechanics
    "d9f89a8a-c563-493e-9d64-78e4f9a55d4a",  # Georgias
    "2e22beba-8e36-42ba-a8bf-975683c52b5f",  # Queens
    "b47df036-3aa4-4b98-8e9e-fe1d3ff1894b",  # Queens
]))


def main():
    data = pd.read_csv('attributes_over_time.csv')

    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_axes([0.2, 0.025, 0.6, 0.9])

    prev_labels = [tid for tid in TEAM_IDS]

    zeros = np.zeros(len(TEAM_IDS), dtype=np.float64)
    bar_artists = [
        (attr, ax.barh(prev_labels, zeros, label=attr, left=zeros))
        for attr in ATTRS
    ]

    ax.set_title("Attributes over time")
    ax.set_xlim((0, 21))

    ax.legend(bbox_to_anchor=(1.25, 1))
    title_artist = ax.text(0.5, 0.975, "asdfasfdasdf",
                           bbox={'facecolor': 'w', 'alpha': 0.5, 'pad': 5},
                           transform=ax.transAxes, ha="center")

    def get_blitted_artists():
        return [
            *[patch
              for _, artist in bar_artists
              for patch in artist.patches],
            title_artist
        ]

    def func(frame_data):
        nonlocal prev_labels
        (season, day), rows = frame_data

        title_artist.set_text(f"Season {season + 1} Day {day + 1}")

        offsets = [0] * len(TEAM_IDS)
        for attr, bar_artist in bar_artists:
            for i, patch in enumerate(bar_artist.patches):
                width = rows[attr].get(TEAM_IDS[i], 0)
                patch.set_width(width)
                patch.set_x(offsets[i])
                offsets[i] += width

        labels = [
            rows['full_name'].get(team_id, "")
            for team_id in TEAM_IDS
        ]
        if labels != prev_labels:
            ax.set_yticklabels(labels)
            # Force a non-blit draw because blit doesn't update tick labels
            plt.draw()
            prev_labels = labels

        return get_blitted_artists()

    groups = data.set_index('team_id').groupby(['season', 'day'])
    frame_iter = tqdm(iter(groups), total=len(groups), unit='frame')
    ani = FuncAnimation(fig, func, frames=frame_iter,
                        init_func=get_blitted_artists, blit=True, interval=1)

    ani.save("attributes_over_time.mp4", fps=30)


if __name__ == '__main__':
    main()
