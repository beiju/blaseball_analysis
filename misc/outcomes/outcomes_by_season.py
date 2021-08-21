import pandas as pd


def main():
    data = pd.read_csv(f"outcomes_all.csv")

    pivot = data.pivot_table(values='count', index='season',
                             columns='event_type', aggfunc='first',
                             fill_value=0)

    pivot.to_csv("outcomes_pivoted_all.csv")


if __name__ == '__main__':
    main()
