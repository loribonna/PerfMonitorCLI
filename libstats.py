from typing import Tuple
from time import time
import psutil

#     "disk": {
#         "stats": [
#             "\Disco fisico(*)\% Tempo disco",
#             "\Disco fisico(*)\Byte scritti su disco/sec",
#             "\Disco fisico(*)\Byte letti da disco/sec"
#         ]
#     },
#     "network": {
#         "stats": [
#             "\Scheda di rete(*)\Totale byte/sec",
#             "\Scheda di rete(*)\Byte ricevuti/sec",
#             "\Scheda di rete(*)\Byte inviati/sec",
#             "\Interfaccia di rete(*)\Byte inviati/sec",
#             "\Interfaccia di rete(*)\Byte ricevuti/sec",
#             "\Interfaccia di rete(*)\Larghezza di banda corrente"
#         ]
#     },
#     "system": {
#         "stats": [
#             "\Sistema\Processi",
#             "\Sistema\Thread"
#         ]
#     }

INIT = False


def get_cpu_stats() -> dict:
    global INIT

    if not INIT:
        psutil.cpu_percent(interval=0.1)
        psutil.cpu_percent(percpu=True, interval=0.1)

        INIT = True

    n_cores = psutil.cpu_count(logical=True)
    t_freq_c, t_freq_min, t_freq_max = psutil.cpu_freq()
    cpu_perc = psutil.cpu_percent(percpu=True, interval=0.0)
    t_cpu_perc = psutil.cpu_percent(interval=0.0)

    return {
        "% limite prestazioni": {"_Total": 100.},
        "% frequenza massima": {**{i: 100. for i in range(n_cores)}, **{"_Total": 100.}},
        "Frequenza processore": {"_Total": t_freq_c / t_freq_max},
        "% Tempo processore": {**{i: cpu_perc[i] for i in range(n_cores)}, **{"_Total": t_cpu_perc}},
        "Temperatura": None
    }


def get_mem_stats() -> dict:
    total_mem, avail_mem, _, _, _ = psutil.virtual_memory()
    total_swap, used_swap, _, _, sin, sout = psutil.swap_memory()

    return {
        "Byte disponibili": avail_mem / (1024 * 1024),
        "Totale MB": total_mem / (1024 * 1024),
        "Byte vincolati": used_swap / (1024 * 1024),
        "Limite memoria vincolata": total_swap / (1024 * 1024),
        "Input pagine/sec": None,
        "Output pagine/sec": None,
        "Errori di pagina/sec": None,
        "Scritture pagine/sec": None,
        "Letture pagine/sec": None
    }


def get_all_stats() -> Tuple[dict, float]:
    t = time()
    cpu_stats = get_cpu_stats()
    mem_stats = get_mem_stats()

    return {**cpu_stats, **mem_stats}, time() - t
