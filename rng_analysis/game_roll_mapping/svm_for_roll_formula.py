from glob import glob

import numpy as np
import pandas as pd
from sklearn.svm import LinearSVC


def main():
    files = glob("game_*.csv")
    df = pd.concat((pd.read_csv(f) for f in files))

    # Get rid of all entries that don't have a value for the roll
    df = df[~df['pitch_in_strike_zone_roll'].isnull()]

    # Only on pitches in/out of the strike zone
    df = df[df['pitch_in_strike_zone_roll'] > 0.35 * (1 + df['pitcher.ruthlessness'])]

    # Traj doesn't have enough variety. Filter to only batters with traj of 0.1
    # df = df[df['batter.tragicness'] == 0.1]

    # Get rid of fouls
    df = df[df['event_type'] != "EventType.Foul"]
    df = df[df['event_type'] != "EventType.FieldersChoice"]

    df_szknown = df[(df['event_type'] == "EventType.StrikeLooking") |
                    (df['event_type'] == "EventType.Ball")]
    assert (
            (df_szknown['pitch_in_strike_zone_roll'] > 0.35 * (
                1 + df_szknown['pitcher.ruthlessness'])) ^
            (df_szknown['event_type'] == "EventType.StrikeLooking")).all()
    # df = df[(df['event_type'] == "EventType.StrikeLooking") |
    #         (df['event_type'] == "EventType.StrikeSwinging")]

    batter_attrs = [col for col in df if col.startswith('batter.')]
    pitcher_attrs = [col for col in df if col.startswith('pitcher.')]

    # samples = df[['pitch_in_strike_zone_roll', 'pitcher.ruthlessness', 'pitcher.unthwackability']]
    samples = df[['batter_swings_roll', "batter.moxie", "batter.thwackability", "batter.vibes", "pitcher.vibes", 'pitcher.coldness']]
    # samples = df[['batter_swings_roll', *batter_attrs, 'pitcher.coldness', 'pitcher.vibes']]
    # samples = df[['batter_swings_roll', *batter_attrs, *pitcher_attrs]]
    in_strike_zone = df['event_type'] == "EventType.StrikeLooking"

    batter_swung = (
            (df['event_type'] == 'EventType.StrikeSwinging') |
            (df['event_type'] == 'EventType.Foul') |
            (df['event_type'] == 'EventType.GroundOut') |
            (df['event_type'] == 'EventType.HomeRun') |
            (df['event_type'] == 'EventType.Single') |
            (df['event_type'] == 'EventType.Double') |
            (df['event_type'] == 'EventType.Triple') |
            (df['event_type'] == 'EventType.FieldersChoice') |
            (df['event_type'] == 'EventType.DoublePlay') |
            (df['event_type'] == 'EventType.Sacrifice')
    )

    X = np.array(samples)
    y = ~np.array(batter_swung)
    clf = LinearSVC(verbose=True, tol=1e-10, penalty='l1', dual=False, max_iter=1e8, C=0.1)
    fit = clf.fit(X, y)

    y_pred = clf.predict(X)
    # y_pred = df['batter_swings_roll'] > 0.45 - 0.25 * df['batter.moxie']

    n_errors = (y_pred ^ y).sum()
    n_samples = y.shape[0]
    print(f"Error: {n_errors / n_samples:.03} ({n_errors}/{n_samples})")
    for category in df['event_type'].unique():
        print(category, np.average(y_pred[df['event_type'] == category]))

    print((df['batter_swings_roll'] - (0.45 - 0.25 * df['batter.moxie']))[y_pred ^ y])
    print((df['event_type'])[y_pred ^ y])

    coeff = pd.Series(clf.coef_.squeeze(), samples.columns)
    coeff.sort_values(inplace=True, key=abs, ascending=False)
    print("\nCoefficients:\n" + str(coeff))
    print("Intercept:", clf.intercept_)

    print("\nNormalized:\n" + str(coeff / -coeff['batter_swings_roll']))
    print("Intercept:", clf.intercept_ / -coeff['batter_swings_roll'])


if __name__ == '__main__':
    main()
