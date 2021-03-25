import json


def main():
    with open("bets.json", 'rb') as f:
        bets = json.load(f)

    for bet in bets:
        print(bet['metadata']['toast'])
    pass


if __name__ == '__main__':
    main()
