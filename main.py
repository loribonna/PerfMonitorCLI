import json
import sys
import time
import os
import signal

from gpu_stats import get_gpu_state
from gui import pretty_print_data
from libstats import get_all_stats as lib_stats
import argparse

CLR_PRINTS = 10


def signal_handler(sig, frame):
    os.system("CLS")
    sys.exit(0)


def main(resfresh_time=2):
    signal.signal(signal.SIGINT, signal_handler)

    os.system('conda activate torch')
    if sys.platform != "win32":
        print("ONLY WINDOWS SUPPORTED")
        exit(1)

    os.system("CLS")

    stats, loading_time = lib_stats()  # get_all_stats()

    with open("out.json", "w") as f:
        # f.write(json.dump(stats, indent=4))
        json.dump(stats, f, indent=4)

    p_index = 0
    while 1:
        t = time.time()
        stats, loading_time = lib_stats()  # get_all_stats()
        gpu_state, gpu_load_time = get_gpu_state()

        if p_index > CLR_PRINTS:
            p_index = 0
            os.system("CLS")

        pretty_print_data(stats, gpu_state, loading_time, gpu_load_time, t,
                          final_line=f"Press Ctrl+C to exit. Refreshing every {resfresh_time} seconds")
        time.sleep(resfresh_time)
        p_index += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Windows Performance Monitor CLI')
    parser.add_argument(
        '-t', '--time', help='Refresh every -t seconds.', type=int, default=2)

    args = parser.parse_args()
    main(args.time)
