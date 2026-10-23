"""System and Ableton Live install checks."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Optional

import psutil

from afr.boost import detect_p_cores, find_ableton_live_process

ABLETON_CANDIDATES = [
    Path(r"C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe"),
    Path(r"C:\ProgramData\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe"),
    Path(r"C:\Program Files\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe"),
    Path(r"C:\Program Files\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe"),
]


def find_ableton_install() -> Optional[Path]:
    for path in ABLETON_CANDIDATES:
        if path.exists():
            return path
    # Fallback: scan ProgramData\Ableton for Live * Suite.exe
    root = Path(r"C:\ProgramData\Ableton")
    if root.is_dir():
        for exe in root.rglob("Ableton Live *.exe"):
            name = exe.name.lower()
            if "suite" in name or "standard" in name or "intro" in name:
                if "addons" not in name and "index" not in name:
                    return exe
    return None


def run_check() -> int:
    print("\n=== Ableton Fast Render - System Check ===\n")

    print("CPU")
    logical = psutil.cpu_count(logical=True)
    physical = psutil.cpu_count(logical=False)
    print(f"  Logical cores : {logical}")
    print(f"  Physical cores: {physical}")
    print(f"  Processor     : {platform.processor() or 'n/a'}")
    p_cores = detect_p_cores()
    print(f"  P-core guess  : {p_cores[0]}-{p_cores[-1]} ({len(p_cores)} logical)")

    ram = psutil.virtual_memory()
    print("\nRAM")
    print(f"  Total         : {ram.total / (1024 ** 3):.1f} GB")
    print(f"  Available     : {ram.available / (1024 ** 3):.1f} GB")

    install = find_ableton_install()
    print("\nAbleton install")
    if install:
        print(f"  Found         : {install}")
    else:
        print("  NOT FOUND — set path manually or install Live Suite")
        return 1

    proc = find_ableton_live_process()
    print("\nRunning Live process")
    if proc:
        try:
            aff = proc.cpu_affinity()
            prio = proc.nice()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            aff, prio = "?", "?"
        print(f"  PID           : {proc.pid}")
        print(f"  Name          : {proc.name()}")
        try:
            print(f"  Exe           : {proc.exe()}")
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        print(f"  Affinity      : {aff}")
        print(f"  Priority      : {prio}")
    else:
        print("  Not running (start Ableton Live before 'afr boost')")

    print("\n=== Check OK ===\n")
    return 0
