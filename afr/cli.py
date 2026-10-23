"""CLI for Ableton Fast Render."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="afr",
        description="Ableton Fast Render — boost Ableton Live for faster export sessions (Windows).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Detect system + Ableton Live install / running process")
    p_boost = sub.add_parser("boost", help="Pin Live to P-cores, raise priority, tighten timer")
    p_boost.add_argument(
        "--no-power-plan",
        action="store_true",
        help="Do not change Windows power plan",
    )
    sub.add_parser("reset", help="Restore all-core affinity and normal priority")

    args = parser.parse_args(argv)

    if args.command == "check":
        from afr.check import run_check
        return run_check()
    if args.command == "boost":
        from afr.boost import run_boost
        return run_boost(use_power_plan=not args.no_power_plan)
    if args.command == "reset":
        from afr.boost import run_reset
        return run_reset()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
