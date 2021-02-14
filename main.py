import json
import sys

from gpu_stats import get_gpu_state
from gui import pretty_print_data
from utils import get_all_stats
import time
from libstats import get_all_stats as lib_stats


def main():
    if sys.platform != "win32":
        print("ONLY WINDOWS SUPPORTED")
        exit(1)

    stats, loading_time = lib_stats()  # get_all_stats()

    with open("out.json", "w") as f:
        # f.write(json.dump(stats, indent=4))
        json.dump(stats, f, indent=4)

    while 1:
        t = time.time()
        stats, loading_time = lib_stats()  # get_all_stats()
        gpu_state, gpu_load_time = get_gpu_state()

        pretty_print_data(stats, gpu_state, loading_time, gpu_load_time, t)
        time.sleep(1)


if __name__ == '__main__':
    main()
