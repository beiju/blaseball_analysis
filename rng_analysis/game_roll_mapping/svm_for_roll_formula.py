from glob import glob

import numpy as np
import pandas as pd
from sklearn.svm import LinearSVC


def main():
    files = glob("game_*.csv")
    df = pd.concat((pd.read_csv(f) for f in files))

    # Get rid of all entries that don't have a value for the roll
    df = df[~df['pitch_in_strike_zone_roll'].isnull()]

    # Traj doesn't have enough variety. Filter to only batters with traj of 0.1
    df = df[df['batter.tragicness'] == 0.1]

    # df = df[(df['event_type'] == "EventType.StrikeLooking") |
    #         (df['event_type'] == "EventType.Ball")]

    batter_attrs = [col for col in df if col.startswith('batter.')]
    pitcher_attrs = [col for col in df if col.startswith('pitcher.')]

    # samples = df[['pitch_in_strike_zone_roll', 'pitcher.ruthlessness', 'pitcher.unthwackability']]
    samples = df[['batter_swings_roll', 'batter.moxie']]
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
    clf = LinearSVC(verbose=True, tol=0.05, penalty='l1', dual=False, max_iter=1e5)
    fit = clf.fit(X, y)

    n_errors = (clf.predict(X) ^ y).sum()
    n_samples = y.shape[0]
    print(f"Error: {n_errors / n_samples:.03} ({n_errors}/{n_samples})")

    coeff = pd.Series(clf.coef_.squeeze(), samples.columns)
    coeff.sort_values(inplace=True, key=abs, ascending=False)
    print("\nCoefficients:\n" + str(coeff))
    print("Intercept:", clf.intercept_)

    print("\nNormalized:\n" + str(coeff / -coeff['batter_swings_roll']))
    print("Intercept:", clf.intercept_ / -coeff['batter_swings_roll'])


if __name__ == '__main__':
    main()
