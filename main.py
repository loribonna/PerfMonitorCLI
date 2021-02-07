import json
import sys

from gui import pretty_print_data
from utils import get_all_stats


def main():
    if sys.platform != "win32":
        print("ONLY WINDOWS SUPPORTED")
        exit(1)

    stats = get_all_stats()

    with open("out.json", "w") as f:
        # f.write(json.dump(stats, indent=4))
        json.dump(stats, f, indent=4)

    pretty_print_data(stats)


if __name__ == '__main__':
    main()
