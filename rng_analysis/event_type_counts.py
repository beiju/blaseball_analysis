from rng_analysis.load_fragments import load_fragments


def main():
    fragments = load_fragments('data/all_stats8.txt')

    differences = []
    # Skip fragment 1, that's s1 generation and not useful
    for fragment in fragments[1:]:
        prev_event = fragment.events[0]
        for event in fragment.events[1:]:
            # Simultaneous records are not useful
            if prev_event.timestamp != event.timestamp:
                differences.append((prev_event, event))
            prev_event = event

    differences.sort(key=lambda pair: pair[0].timestamp - pair[1].timestamp)
    pass


if __name__ == '__main__':
    main()
