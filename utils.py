import multiprocessing
import os
import re
import subprocess
from io import StringIO
from typing import List

import pandas as pd

STATS = {
    "cpu": {
        "info": [
            "\\Informazioni processore(*)\\% limite prestazioni",
            "\\Informazioni processore(*)\\% frequenza massima",
            "\\Informazioni processore(*)\\Frequenza processore",
            "\\Informazioni processore(*)\\% Tempo processore",
        ],
        "perf": [
            "\\Processore(*)\\% Tempo processore",
            "\\Processore(*)\\% Tempo utente",
            "\\Processore(*)\\% Tempo privilegiato",
            # "\\Processo(*)\\% Tempo processore"
        ],
        "temp": [
            "\\Informazioni zona termica(*)\\Motivi limitazione",
            "\\Informazioni zona termica(*)\\Temperatura"
        ]
    },
    "disk": {
        "stats": [
            "\Disco fisico(*)\% Tempo disco",
            "\Disco fisico(*)\Byte scritti su disco/sec",
            "\Disco fisico(*)\Byte letti da disco/sec"
        ]
    },
    "mem": {
        "stats": [
            "\Memoria\Byte disponibili",
            "\Memoria\Byte vincolati",
            "\Memoria\Scritture pagine/sec",
            "\Memoria\Letture pagine/sec",
            "\Memoria\Output pagine/sec",
            "\Memoria\Input pagine/sec",
            "\Memoria\Errori di pagina/sec",
            "\Memoria\Limite memoria vincolata",
            "\Memoria nodo NUMA(*)\Totale MB"  # NOT NUMA AWARE
        ]
    },
    "network": {
        "stats": [
            "\Scheda di rete(*)\Totale byte/sec",
            "\Scheda di rete(*)\Byte ricevuti/sec",
            "\Scheda di rete(*)\Byte inviati/sec",
            "\Interfaccia di rete(*)\Byte inviati/sec",
            "\Interfaccia di rete(*)\Byte ricevuti/sec",
            "\Interfaccia di rete(*)\Larghezza di banda corrente"
        ]
    },
    "system": {
        "stats": [
            "\Sistema\Processi",
            "\Sistema\Thread"
        ]
    }
}

CORECOUNT = multiprocessing.cpu_count()
DISKRE = re.compile(r"^.*\((?P<disknumber>\d*)\ (?P<diskname>\w):\)$")
GENERIC_GROUP_RE = re.compile(r"^.*\((.*)\).*$")
IFACERE = re.compile(r"^.*\((?P<ifacename>.*)\)$")

flatten = lambda t: [item for sublist in t for item in sublist]


def get_stats(counters: List[str], file_name=None) -> pd.Series:
    if file_name is None or not os.path.exists(file_name):
        file_name = file_name if file_name is not None else "tmp"
        with open('{}.txt'.format(file_name), "w") as f:
            f.write("\n".join(counters))

    data = run(f"typeperf -cf .\\{file_name}.txt -sc 1")
    df = pd.read_csv(StringIO(data), sep=",").iloc[:1]

    df.rename(columns=lambda s: "\\".join(s.split("\\")[3:]) if "\\\\" in s else s, inplace=True)
    return df


def run(command: str) -> str:
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    result = p.communicate()
    return result[0].decode('utf8', "ignore")


def filter_data(data: pd.Series, names: List[str]) -> pd.Series:
    indexes = [ind.replace(k.group(1), "*") if (k := GENERIC_GROUP_RE.search(ind)) is not None else ind for ind in
               data.index]

    filter_data_indexes = [i for i, f in enumerate(indexes) if "\\" + f in names]
    data = data.iloc[filter_data_indexes]

    return data


def get_temp(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['cpu']['temp'], "cpu_temp").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['cpu']['temp'])

    data.rename(index=lambda s: s.split("\\")[-1] if "\\" in s else s, inplace=True)

    data["Temperatura"] -= 273  # to Celsius

    return data.to_dict()


def get_system_info(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['system']['stats'], "sys_info").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['system']['stats'])

    return data.rename(index=lambda x: x.split('\\')[-1]).astype(int).to_dict()


def get_disk_info(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['disk']['stats'], "disk_info").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['disk']['stats'])

    keys = [f.split("\\")[-1] for f in STATS['disk']['stats']]
    drives = list(set([k.groups(0) for f in data.index if (k := DISKRE.match(f.split('\\')[0])) is not None]))

    df = pd.DataFrame(columns=keys, index=[d[1] for d in drives] + ["_Total"])
    for index in range(len(drives) + 1):
        for k in keys:
            if index == len(drives):  # TOTAL
                if k.startswith("%"):
                    df.loc["_Total", k] = "{:.2f} %".format(data["Disco fisico(_Total)\\{}".format(k)])
                elif k.lower().startswith("byte"):
                    v = data["Disco fisico(_Total)\\{}".format(k)]
                    s = "B/s" if v < 1024 else "KB/s" if v < (1024 ** 2) else "MB/s"
                    v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2)
                    df.loc["_Total", k] = "{:.2f} {}".format(v, s)
                else:
                    df.loc["_Total", k] = data["Disco fisico(_Total)\\{}".format(k)]
            else:
                drive = drives[index]
                if k.startswith("%"):
                    df.loc[drive[1], k] = "{:.2f} %".format(
                        data["Disco fisico({} {}:)\\{}".format(drive[0], drive[1], k)])
                elif k.lower().startswith("byte"):
                    v = data["Disco fisico({} {}:)\\{}".format(drive[0], drive[1], k)]
                    s = "B/s" if v < 1024 else "KB/s" if v < (1024 ** 2) else "MB/s"
                    v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2)
                    df.loc[drive[1], k] = "{:.2f} {}".format(v, s)
                else:
                    df.loc[drive[1], k] = data["Disco fisico({} {}:)\\{}".format(drive[0], drive[1], k)]

    return df.to_dict()


def get_net_info(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['network']['stats'], "net_info").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['network']['stats'])

    net_ifaces = list(set([
        IFACERE.match(f.split("\\")[0]).group(1)
        for f in data.index if f.lower().startswith("interfaccia di rete")
    ]))

    filter_data_indexes = [i for i, f in enumerate(data.index) if
                           IFACERE.match(f.split("\\")[0]).group(1) in net_ifaces]
    data = data.iloc[filter_data_indexes]

    d = {iface: {} for iface in net_ifaces}
    for key in data.index:
        iface = IFACERE.match(key.split("\\")[0]).group(1)
        name = key.split('\\')[-1]
        v = data[key]

        if name.endswith('/sec'):
            if "byte" in name.lower():
                s = "B/s" if v < 1024 else "KB/s" if v < (1024 ** 2) else "MB/s"
                v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2)
            else:
                s = "*/s"

            d[iface][name] = "{:.2f} {}".format(v, s)
        elif name.lower() == "larghezza di banda corrente" or name.lower().startswith('byte'):
            s = "B" if v < 1024 else "KB" if v < (1024 ** 2) else "MB" if v < (1024 ** 3) else "GB"
            v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2) if v < (1024 ** 3) else v / (
                    1024 ** 3)
            d[iface][name] = "{:.2f} {}".format(v, s)
        else:
            d[iface][name] = v

    return d


def get_mem_info(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['mem']['stats'], "mem_info").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['mem']['stats'])

    d = {}
    for key in data.index:
        name = key.split('\\')[-1]
        v = data[key]
        if name.lower().startswith('byte'):
            d[name] = v / (1024 ** 2)
        else:
            d[name] = v

        # if name.lower().startswith('byte'):
        #     s = "B" if v < 1024 else "KB" if v < (1024 ** 2) else "MB" if v < (1024 ** 3) else "GB"
        #     v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2) if v < (1024 ** 3) else v / (
        #             1024 ** 3)
        #     d[name] = "{:.2f} {}".format(v, s)
        # elif name.lower().endswith('/sec'):
        #     s = "B/s" if v < 1024 else "KB/s" if v < (1024 ** 2) else "MB/s"
        #     v = v if v < 1024 else v / 1024 if v < (1024 ** 2) else v / (1024 ** 2)
        #     d[name] = "{:.2f} {}".format(v, s)
        # else:
        #     d[name] = v

    return d


def get_cpu_info(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['cpu']['info'], "cpu_info").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['cpu']['info'])

    keys = [f.split("\\")[-1] for f in STATS['cpu']['info']]

    df = pd.DataFrame(columns=keys, index=[*range(CORECOUNT), "_Total"])
    for c in range(CORECOUNT + 1):  # account for _total
        for k in keys:
            l = c
            if c == CORECOUNT:
                l = "_Total"
            try:
                df.loc[l, k] = data["Informazioni processore(0,{})\\{}".format(l, k)]
            except:
                try:
                    df.loc[l, k] = data["Informazioni processore({})\\{}".format(l, k)]
                except:
                    pass

    return df.to_dict()


def get_cpu_perf(data_override=None) -> dict:
    if data_override is None:
        data = get_stats(STATS['cpu']['perf'], "cpu_perf").iloc[0, 1:]
    else:
        data = filter_data(data_override, STATS['cpu']['perf'])

    keys = [f.split("\\")[-1] for f in STATS['cpu']['perf']]

    df = pd.DataFrame(columns=keys, index=[*range(CORECOUNT), "_Total"])
    for c in range(CORECOUNT + 1):  # account for _total
        for k in keys:
            l = c
            if c == CORECOUNT:
                l = "_Total"
            try:
                df.loc[l, k] = "{:.2f}".format(data["Processore({})\\{}".format(l, k)])
            except:
                df.loc[l, k] = "0.00"

    return df.to_dict()


def get_all_stats() -> dict:
    allnames = flatten([d for v in STATS.values() for d in v.values()])
    data = get_stats(allnames, "all_stats").iloc[0, 1:]

    temp = get_temp(data)
    info = get_cpu_info(data)
    perf = get_cpu_perf(data)
    disk_info = get_disk_info(data)
    mem_info = get_mem_info(data)
    net_info = get_net_info(data)
    sys_info = get_system_info(data)

    return {**info, **temp, **perf, **disk_info, **mem_info, **net_info, **sys_info}
