# DEPRECATED: check out [NVITOP](https://github.com/XuehaiPan/nvitop) instead for better support and functionality across platforms

# Performance monitor CLI for Windows
Parse and display performance counter from `psutil` and `nvidia-smi`.

Minimum height:
- If GPU: 17 + #CPUs/2
- Else: 9 + #CPUs/2

Unfortunately, temperature reading for CPU is not available.

## Requires
- `psutil`: load CPU+MEM stats.
- `termcolor`: color stuff.
- `xmltodict`: parse `nvidia-smi` output during GPU stats load.

### Parameters:
- `-t` or `--time`: Change default refresh time to `t` seconds (default: 2).
- `-d` or `--disable_gpu`: Disable GPU stats load and display.
- `-c` or `--disable_cpu`: Clear screen every `c` prints (default: 5).

## Run standalone
- Install `requirements.txt`
- Run with: `python main.py`
