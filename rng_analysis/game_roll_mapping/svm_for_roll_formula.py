from glob import glob

import numpy as np
import pandas as pd
from sklearn.svm import LinearSVC


def main():
    files = glob("game_*.csv")
    df = pd.concat((pd.read_csv(f) for f in files))

    # Get rid of all entries that don't have a value for the roll
    df = df[~df['pitch_in_strike_zone_roll'].isnull()]

    df = df[(df['event_type'] == "EventType.StrikeLooking") |
            (df['event_type'] == "EventType.Ball")]

    batter_attrs = [col for col in df if col.startswith('batter.')]
    pitcher_attrs = [col for col in df if col.startswith('pitcher.')]

    samples = df[['pitch_in_strike_zone_roll', 'pitcher.ruthlessness', 'pitcher.unthwackability']]
    # samples = df[['pitch_in_strike_zone_roll', 'batter.thwackability', 'batter.moxie', 'batter.divinity',
    #               'batter.musclitude', 'batter.patheticism', 'batter.buoyancy', 'batter.baseThirst',
    #               'batter.laserlikeness', 'batter.groundFriction', 'batter.continuation',
    #               'batter.indulgence', 'batter.martyrdom', 'batter.tragicness']]
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
    y = ~np.array(in_strike_zone)
    clf = LinearSVC(verbose=True)
    fit = clf.fit(X, y)

    print("Perfect fit: ", not (clf.predict(X) ^ y).all())

    coeff = pd.Series(clf.coef_.squeeze(), samples.columns)
    print("\nCoefficients:\n" + str(coeff))

    print("\nNormalized:\n" + str(coeff / coeff['pitch_in_strike_zone_roll']))


if __name__ == '__main__':
    main()
