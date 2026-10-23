"""Boost / reset Ableton Live process (affinity, priority, timer, power)."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from typing import Optional

import psutil

HIGH_PRIORITY_CLASS = 0x00000080
NORMAL_PRIORITY_CLASS = 0x00000020
PROCESS_ALL_ACCESS = 0x1F0FFF

# Names / path fragments that are NOT the Live DAW process
_EXCLUDE_SUBSTRINGS = (
    "addons",
    "add-ons",
    "index",
    "web connector",
    "webconnector",
    "crash",
    "helper",
)



def detect_p_cores() -> list[int]:
    """Best-effort P-core logical indices on hybrid Intel.

    Prefer first N logical CPUs (Windows usually lists P-cores first).
    Fallback: all logical CPUs.
    """
    logical = psutil.cpu_count(logical=True) or 1
    physical = psutil.cpu_count(logical=False) or logical
    if logical > physical and physical >= 4:
        if logical >= 16:
            n = min(8, physical, logical)
            return list(range(n))
        return list(range(min(physical, logical)))
    return list(range(logical))


def _is_ableton_live_process(name: str, exe: Optional[str]) -> bool:
    """Match Ableton Live DAW only — never AddOns / Index / Web Connector."""
    n = (name or "").lower()
    e = (exe or "").lower()
    combined = f"{n} {e}"

    for bad in _EXCLUDE_SUBSTRINGS:
        if bad in combined:
            return False

    # Require "ableton" and "live" in name or path
    has_ableton = "ableton" in n or "ableton" in e
    has_live = "live" in n or ("\\live " in e) or ("/live " in e) or "live " in e
    if not (has_ableton and has_live):
        return False

    # Prefer Suite / Standard / Intro / Lite exe names
    if any(x in combined for x in ("suite", "standard", "intro", "lite", "beta")):
        return True

    # Name like "Ableton Live 12 Suite" without path
    if "ableton" in n and "live" in n:
        return True

    return False


def find_ableton_live_process() -> Optional[psutil.Process]:
    """Return the main Ableton Live process, or None."""
    candidates: list[psutil.Process] = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            info = proc.info
            name = info.get("name") or ""
            exe = info.get("exe") or ""
            if _is_ableton_live_process(name, exe):
                candidates.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not candidates:
        return None

    # Prefer process whose exe path contains Program\Ableton Live
    for proc in candidates:
        try:
            exe = (proc.exe() or "").lower()
            if "\\program\\" in exe and "ableton live" in exe:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Prefer highest memory (main DAW usually largest)
    def mem_key(p: psutil.Process) -> int:
        try:
            return p.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    return max(candidates, key=mem_key)


def _set_priority(pid: int, priority_class: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not handle:
        # Try with limited access
        handle = kernel32.OpenProcess(0x0200 | 0x0400, False, pid)  # SET|QUERY
    if not handle:
        return False
    try:
        ok = bool(kernel32.SetPriorityClass(handle, priority_class))
        return ok
    finally:
        kernel32.CloseHandle(handle)


def _set_timer_resolution_05ms() -> bool:
    try:
        ntdll = ctypes.windll.ntdll
        current = ctypes.c_ulong()
        # 5000 = 0.5 ms in 100-ns units
        status = ntdll.NtSetTimerResolution(5000, True, ctypes.byref(current))
        return status == 0
    except Exception:
        return False


def _set_ultimate_power_plan() -> str:
    """Try Ultimate Performance, then High Performance. Needs admin for some plans."""
    ultimate = "e9a42b02-d5df-448d-aa00-03f14749eb61"
    high = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    for guid, label in ((ultimate, "Ultimate Performance"), (high, "High Performance")):
        try:
            r = subprocess.run(
                ["powercfg", "/setactive", guid],
                capture_output=True,
                timeout=5,
            )
            if r.returncode == 0:
                return label
        except Exception:
            continue
    return "unchanged (need admin?)"


def run_boost(use_power_plan: bool = True) -> int:
    if sys.platform != "win32":
        print("boost is Windows-only")
        return 1

    proc = find_ableton_live_process()
    if not proc:
        print("Ableton Live not running (looking for Live Suite/Standard — not AddOns/Index).")
        print("Start Ableton Live, then run: python -m afr boost")
        return 1

    p_cores = detect_p_cores()
    all_cores = list(range(psutil.cpu_count(logical=True) or 1))

    try:
        before_aff = proc.cpu_affinity()
        before_prio = proc.nice()
    except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
        print(f"Cannot read process state: {e}")
        return 1

    print(f"Target: {proc.name()}  PID={proc.pid}")
    try:
        print(f"  exe: {proc.exe()}")
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    print(f"  BEFORE affinity : {before_aff}")
    print(f"  BEFORE priority : {before_prio}")

    try:
        proc.cpu_affinity(p_cores)
        print(f"  AFTER  affinity : {proc.cpu_affinity()}  (P-cores / performance cores)")
    except psutil.AccessDenied:
        print("  Affinity: AccessDenied — run as Administrator")
        return 1
    except Exception as e:
        print(f"  Affinity failed: {e}")
        return 1

    if _set_priority(proc.pid, HIGH_PRIORITY_CLASS):
        try:
            after_prio = proc.nice()
        except Exception:
            after_prio = "HIGH"
        print(f"  AFTER  priority : {after_prio}  (HIGH, not REALTIME)")
    else:
        print("  Priority: could not set HIGH (try Admin)")

    if _set_timer_resolution_05ms():
        print("  Timer resolution: 0.5 ms")
    else:
        print("  Timer resolution: skipped")

    if use_power_plan:
        plan = _set_ultimate_power_plan()
        print(f"  Power plan: {plan}")

    print("\nBoost applied. Export/render in Ableton now, then: python -m afr reset")
    return 0


def run_reset() -> int:
    if sys.platform != "win32":
        print("reset is Windows-only")
        return 1

    proc = find_ableton_live_process()
    if not proc:
        print("Ableton Live not running — nothing to reset.")
        return 1

    all_cores = list(range(psutil.cpu_count(logical=True) or 1))

    try:
        before_aff = proc.cpu_affinity()
        before_prio = proc.nice()
    except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
        print(f"Cannot read process state: {e}")
        return 1

    print(f"Target: {proc.name()}  PID={proc.pid}")
    print(f"  BEFORE affinity : {before_aff}")
    print(f"  BEFORE priority : {before_prio}")

    try:
        proc.cpu_affinity(all_cores)
        print(f"  AFTER  affinity : {proc.cpu_affinity()}  (all cores)")
    except Exception as e:
        print(f"  Affinity reset failed: {e}")
        return 1

    if _set_priority(proc.pid, NORMAL_PRIORITY_CLASS):
        try:
            after_prio = proc.nice()
        except Exception:
            after_prio = "NORMAL"
        print(f"  AFTER  priority : {after_prio}")
    else:
        print("  Priority: could not set NORMAL")

    print("\nReset done.")
    return 0
