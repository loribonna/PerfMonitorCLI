import sys
import os
from utils import run
import struct
from ctypes import windll, create_string_buffer
import shutil


class bcolors:
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    CYAN = "\033[1;36m"
    GREEN = "\033[0;32m"
    RESET = "\033[0;0m"
    BOLD = "\033[;1m"
    ORANGE = '\033[43m'
    RESET = '\033[0m'


def add_line(s: str, line: str, cols: int):
    s += line + (cols - len(line) - 1) * " " + "\n"
    return s


def color_perc_str(val: int, format_str: str = None):
    if format_str is None:
        format_str = "{}"

    if float(val) < 50:
        return f"{bcolors.GREEN} {format_str.format(val)}"
    if float(val) < 80:
        return f"{bcolors.ORANGE} {format_str.format(val)}"
    return f"{bcolors.RED} {format_str.format(val)}"


def pretty_print_data(data: dict) -> None:
    rows, cols = get_terminal_size()
    rows, cols = int(rows), int(cols)

    out_str = add_line("\nCPU STATS", "", cols)

    # CPU STATS
    temp_info = data["Temperatura"]
    cpu_time = data["% Tempo processore"]
    temp_color = bcolors.GREEN if temp_info < 60 else bcolors.ORANGE if temp_info < 80 else bcolors.RED
    combined_info = color_perc_str(cpu_time["_Total"], "Total: {}% | ") + " Temperature: {}{} C{}".format(temp_color,
                                                                                                          temp_info,
                                                                                                          bcolors.RESET)

    out_str = add_line(out_str, combined_info + bcolors.RESET, cols)
    cpu_usage = f"{bcolors.ORANGE}"
    for cpu_i in range(len(cpu_time.keys()) - 1):
        if cpu_i == len(cpu_time.keys()) - 2:
            cpu_usage += color_perc_str(cpu_time[cpu_i], "Core " + str(cpu_i) + ": {}%")
        else:
            cpu_usage += color_perc_str(cpu_time[cpu_i], "Core " + str(cpu_i) + ": {}% " + bcolors.RESET + "| ")
    out_str = add_line(out_str, cpu_usage + bcolors.RESET, cols)
    n_lines = 5

    # MEM STATS

    # "Byte disponibili": "6.53 GB",
    # "Byte vincolati": "17.51 GB",
    # "Scritture pagine/sec": "0.00 B/s",
    # "Letture pagine/sec": "0.00 B/s",
    # "Input pagine/sec": "0.00 B/s",
    # "Totale MB": 16338.0

    avail_ram = "{:.2f} GB".format(data["Byte disponibili"] / 1024) if data["Byte disponibili"] > 1024 \
        else "{:.2f} MB".format(data["Byte disponibili"])
    tot_ram = "{:.2f} GB".format(data["Totale MB"] / 1024) if data["Totale MB"] > 1024 \
        else "{:.2f} MB".format(data["Totale MB"])
    swap_mem = "{:.2f} GB".format(data["Byte vincolati"] / 1024) if data["Byte vincolati"] > 1024 \
        else "{:.2f} MB".format(data["Byte vincolati"])
    ram_color = bcolors.GREEN if data["Byte disponibili"] < data["Totale MB"] * 0.5 else \
        bcolors.ORANGE if data["Byte disponibili"] < data["Totale MB"] * 0.8 else bcolors.RED
    tot_swap = "{:.2f} B".format(data["Limite memoria vincolata"]) if data["Limite memoria vincolata"] < 1024 \
        else "{:.2f} KB".format(data["Limite memoria vincolata"]/1024) if data["Limite memoria vincolata"] < (1024**2) \
        else "{:.2f} MB".format(data["Limite memoria vincolata"]/(1024**2)) if data["Limite memoria vincolata"] < (1024**3) \
        else "{:.2f} GB".format(data["Limite memoria vincolata"]/(1024**3))

    out_str = add_line(out_str, "", cols)
    out_str = add_line(out_str, "MEM STATS\n", cols)
    out_str = add_line(out_str, " Available RAM: {}{} {}of {}".format(ram_color, avail_ram, bcolors.RESET, tot_ram),
                       cols)
    out_str = add_line(out_str, " Total SWAP: {} of {}".format(swap_mem, tot_swap), cols)

    input_sec = data["Input pagine/sec"]
    output_sec = data["Output pagine/sec"]
    faults_sec = data["Errori di pagina/sec"]
    write_sec = data["Scritture pagine/sec"]
    read_sec = data["Letture pagine/sec"]

    out_str = add_line(out_str,
                       "\n Page faults: {:.2f} /s | Pages read from disk: {:.2f} /s | Pages write on disk: {:.2f} /s".format(
                           faults_sec, input_sec, output_sec), cols)
    out_str = add_line(out_str, " Load on disk: READS {:.2f} /s | WRITES {:.2f} /s".format(read_sec, write_sec), cols)
    n_lines += 8

    #

    out_str += "\n" * (rows - n_lines - 1)
    print(out_str)


def get_terminal_size():
    """Return the terminal size in rows and columns."""
    term_size = shutil.get_terminal_size()
    return int(term_size.lines), int(term_size.columns)
