# Ableton Fast Render (`afr`)

**DE:** Windows-Tool, das den laufenden **Ableton Live**-Prozess für Export-/Render-Sessions optimiert (P-Cores, Priority, Timer).  
**EN:** Windows utility that boosts the running **Ableton Live** process for export/render sessions (P-cores, priority, timer).

> Honest scope (v0.1): this does **not** replace Ableton’s exporter, does **not** inject DLLs, and does **not** claim FL-Studio-level magic. Ableton has **no official headless `--export-audio` API**. OSC / stem automation is roadmap only.

## What it does / Was es macht

| Command | Effect |
|---------|--------|
| `python -m afr check` | Detect CPU/RAM, Live install path, running Live process |
| `python -m afr boost` | Pin Live to performance cores, set **HIGH** priority (not REALTIME), 0.5 ms timer, optional Ultimate/High power plan |
| `python -m afr reset` | Restore all-core affinity + normal priority |

Process matching targets **Ableton Live \* Suite/Standard** only — **never** `Ableton AddOns`, `Ableton Index`, or Web Connector.

## What it does NOT / Was es nicht macht

- Kein Fake-„FL-Speed“-Marketing / no fake FL-speed claims  
- Keine DLL-Injection / CUDA-VST / process hacks  
- Kein headless Audio-Export — Ableton bietet das offiziell nicht  
- Kein AbletonOSC-Stem-Export in v0.1 (Roadmap)

## Requirements

- Windows 10/11  
- Python 3.10+  
- Ableton Live 11/12 (Suite/Standard/…)  
- `pip install -r requirements.txt` (`psutil`)

Admin rights help for power-plan changes; affinity/priority often work without Admin.

## Quick start

```bat
cd C:\Users\vikto\Tools\ableton-fast-render
pip install -r requirements.txt
python -m afr check
REM Start Ableton Live, then:
python -m afr boost
REM Export in Ableton (File > Export Audio/Video) …
python -m afr reset
```

Or double-click `START.bat` / `START.bat boost`.

## Hybrid CPUs (Intel P/E-cores)

On hybrid Intel CPUs, `boost` pins Live to the first performance-oriented logical cores (heuristic: typically indices `0–7` when ≥16 logical cores). `reset` restores all logical cores.

## Roadmap

- AbletonOSC hotkeys for stem export  
- Optional GUI  
- Benchmark notes (before/after wall-clock on known projects)

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

Use at your own risk. Raising process priority can make the UI less responsive for other apps. Prefer **HIGH**, never leave REALTIME on for daily work.
