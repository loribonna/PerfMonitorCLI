import os
import shutil
from time import time
from typing import Tuple

import termcolor


def color_perc_str(val: int, format_str: str = None):
    if format_str is None:
        format_str = "{}"
    s = f"{format_str.format(val)}"

    if float(val) < 50:
        return termcolor.colored(s, 'green')
    if float(val) < 80:
        return termcolor.colored(s, 'yellow')
    return termcolor.colored(s, 'red')


def perc_usage_bar(current_usage: float, length: int, max_usage: float, low_usage=0.5, mid_usage=0.8, ext=""):
    if current_usage >= max_usage or current_usage < 0:
        current_usage = max_usage
    p_str_len = 15
    usable_len = length - 2 - p_str_len

    usage_perc = current_usage / max_usage
    color = "green" if usage_perc < low_usage else "yellow" if usage_perc < mid_usage else "red"
    usage_str = "{:.1f}%".format(usage_perc * 100)

    s_internal = ("█" * round(usable_len * usage_perc)) + \
        ("-" * round(usable_len * (1 - usage_perc)))
    s_internal = termcolor.colored(s_internal[:round(len(s_internal) * low_usage)], "green") + \
        termcolor.colored(s_internal[round(len(s_internal) * low_usage):round(len(s_internal) * mid_usage)],
                          "yellow") + \
        termcolor.colored(
            s_internal[round(len(s_internal) * mid_usage):], "red")

    p_str = termcolor.colored(usage_str, color)  # type: str
    return "{} [{}]".format((p_str + ext).rjust(p_str_len), s_internal)


def raw_usage_bar(current_usage: float, length: int, max_usage: float, low_usage=0.5, mid_usage=0.8, ext="", pad_start=0):
    if current_usage >= max_usage or current_usage < 0:
        current_usage = max_usage
    p_len = 25
    usable_len = length - 2 - (p_len-pad_start)

    usage_perc = current_usage / max_usage
    color = "green" if usage_perc < low_usage else "yellow" if usage_perc < mid_usage else "red"
    usage_str = "{:.2f} / {:.2f}".format(current_usage, max_usage)

    s_internal = ("█" * int(usable_len * usage_perc)) + \
        ("-" * int(usable_len * (1 - usage_perc)))

    s_internal = termcolor.colored(s_internal[:round(len(s_internal) * low_usage)], "green") + \
        termcolor.colored(s_internal[round(len(s_internal) * low_usage):round(len(s_internal) * mid_usage)],
                          "yellow") + \
        termcolor.colored(
            s_internal[round(len(s_internal) * mid_usage):], "red")

    return "[{}] {}".format(s_internal, termcolor.colored(usage_str + ext, color).rjust(25))


def print_cpu_stats(data: dict, out_str: str, cols: int) -> Tuple[str, int]:
    out_str += "\nCPU STATS\n"

    # CPU STATS
    temp_info = data["Temperatura"]
    cpu_time = data["% Tempo processore"]
    combined_info = " Total:  " + \
        perc_usage_bar(float(cpu_time['_Total']), cols // 2 - 9, 100)
    combined_info += " - Temperature: {}".format(
        temp_info) if temp_info is not None else ""
    out_str += combined_info + "\n\n"
    cpu_usage = ""
    rows = 0
    for cpu_i in range(len(cpu_time.keys()) - 1):
        base_s = f" Core {cpu_i + 1}: "
        s = perc_usage_bar(cpu_time[cpu_i], cols // 2 - 9, 100)

        cpu_usage += base_s + s
        if cpu_i % 2 == 1:
            cpu_usage += "\n"
            rows += 1
    return out_str + cpu_usage + "\n", 6 + rows


def print_mem_stats(data: dict, gpu_state: dict, out_str: str, cols: int, n_lines: int) -> Tuple[str, int]:
    # MEM STATS
    ram_unit = "GB" if data["Byte disponibili"] > 1024 else "MB"
    swap_unit = "GB" if data["Byte vincolati"] > 1024 else "MB"

    avail_ram = data["Byte disponibili"] / \
        1024 if data["Byte disponibili"] > 1024 else data["Byte disponibili"]
    tot_ram = data["Totale MB"] / \
        1024 if data["Totale MB"] > 1024 else data["Totale MB"]
    swap_mem = data["Byte vincolati"] / \
        1024 if data["Byte vincolati"] > 1024 else data["Byte vincolati"]

    tot_swap = data["Limite memoria vincolata"] if data["Limite memoria vincolata"] < 1024 else \
        data["Limite memoria vincolata"] / 1024 if data["Limite memoria vincolata"] < (1024 ** 2) else \
        data["Limite memoria vincolata"] / (1024 ** 2) if data["Limite memoria vincolata"] < (1024 ** 3) else \
        data["Limite memoria vincolata"] / (1024 ** 3)

    out_str += "\nMEM STATS\n"
    out_str += " RAM:  " + raw_usage_bar(tot_ram - avail_ram, cols // 2 - 7, tot_ram, ext=" " + ram_unit) + \
               " <" + "{:.2f}".format(avail_ram).rjust(5) + \
        " {} available>".format(ram_unit) + "\n"
    out_str += " SWAP: " + raw_usage_bar(swap_mem, cols // 2 - 7, tot_swap, ext=" " + swap_unit) + \
               " <" + "{:.2f}".format(swap_mem).rjust(5) + \
        " {} available>".format(swap_unit) + "\n"
    out_str += " GPU:  " + raw_usage_bar(float(gpu_state['used_mem'].split()[0])/1024, cols // 2 - 17, float(gpu_state['total_mem'].split(
    )[0])/1024, ext=" GB", pad_start=10) + " <" + "{:.2f}".format(float(gpu_state['free_mem'].split()[0])/1024).rjust(5) + " GB available>" + "\n"

    input_sec = data["Input pagine/sec"]
    output_sec = data["Output pagine/sec"]
    faults_sec = data["Errori di pagina/sec"]
    write_sec = data["Scritture pagine/sec"]
    read_sec = data["Letture pagine/sec"]

    if faults_sec is not None:
        out_str += "\n Page faults: {:.2f} /s | Pages read from disk: {:.2f} /s | Pages write on disk: {:.2f} /s\n".format(
            faults_sec, input_sec, output_sec)
        out_str += "\n Load on disk: READS {:.2f} /s | WRITES {:.2f} /s\n".format(
            read_sec, write_sec)
        n_lines += 9
    else:
        n_lines += 5

    return out_str, n_lines


def print_gpu_stats(stat: dict, out_str: str, cols: int, n_lines: int) -> Tuple[str, int]:
    out_str += "\nGPU STATS\n"
    out_str += " Compute engine: " + \
        perc_usage_bar(float(stat['gpu_usage'].split()[
                       0]), cols // 2 - 17, 100) + "\n"
    out_str += " Encoder:        " + \
        perc_usage_bar(float(stat['encoder_usage'].split()[
                       0]), cols // 2 - 17, 100) + "\n"
    out_str += " Decoder:        " + \
        perc_usage_bar(float(stat['decoder_usage'].split()[
                       0]), cols // 2 - 17, 100) + "\n"
    out_str += " Memory Bus:     " + \
        perc_usage_bar(float(stat['memory_usage'].split()[
                       0]), cols // 2 - 17, 100) + "\n"

    temp = float(stat['temperature'].split()[0])
    max_temp = float(stat['max_temp'].split()[0])
    slow_temp = float(stat['slow_temp'].split()[0])

    temp_perc = temp / max_temp
    temp_color = "green" if temp_perc < 0.6 else "yellow" if temp_perc < 0.8 else "red"

    out_str += " Current temperature: " + termcolor.colored(f"{temp} C",
                                                            temp_color) + f" <Max: {max_temp} C | Slowing down at: {slow_temp} C>\n"

    return out_str, n_lines + 5


def pretty_print_data(data: dict, gpu_state: dict, loading_time: float, gpu_load_time: float,
                      start_time: float) -> None:
    rows, cols = get_terminal_size()
    rows, cols = int(rows), int(cols)

    out_str = "\r"

    out_str, n_lines = print_cpu_stats(data, out_str, cols)
    out_str, n_lines = print_mem_stats(data, gpu_state, out_str, cols, n_lines)
    out_str, n_lines = print_gpu_stats(gpu_state, out_str, cols, n_lines)

    out_str += "\n" * (rows - n_lines - 3)
    out_str += "System info loading time: {:.2f} ms | GPU info loading time: {:.2f} ms | Processing time: {:5.2f} ms\n".format(
        loading_time * 1000, gpu_load_time * 1000, ((time() - start_time) - (loading_time + gpu_load_time)) * 1000)

    print(out_str, end="")
    print("\033[F"*rows, end="")


def get_terminal_size():
    """Return the terminal size in rows and columns."""
    term_size = shutil.get_terminal_size()
    return int(term_size.lines), int(term_size.columns)
