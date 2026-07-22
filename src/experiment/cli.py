"""Command-line entry point.

    python -m experiment simulate
    python -m experiment analyze data/experiment.csv --out docs/results.md
    python -m experiment size --base 0.10 --mde 0.012
    python -m experiment sdk-demo
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from .report import report
from .simulate import simulate
from .stats import cuped, power, sample_size, two_proportion, welch, winsorize


def table(path: str) -> dict[str, np.ndarray]:
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    body = np.array(rows[1:], dtype=float).T
    return {name: body[i] for i, name in enumerate(rows[0])}


def analysis(data: dict[str, np.ndarray]) -> tuple[dict, tuple[int, int]]:
    arm, conv, rev = data["arm"].astype(int), data["converted"].astype(int), data["revenue"]
    control, treat = arm == 0, arm == 1
    winsor, adjusted = winsorize(rev), cuped(rev, data["pre_revenue"])
    results = {
        "conversion": two_proportion(int(conv[control].sum()), int(control.sum()),
                                     int(conv[treat].sum()), int(treat.sum())),
        "revenue": welch(rev[control], rev[treat]),
        "revenue_winsorized": welch(winsor[control], winsor[treat]),
        "revenue_cuped": welch(adjusted[control], adjusted[treat]),
    }
    return results, (int(control.sum()), int(treat.sum()))


def cmd_simulate(args: argparse.Namespace) -> int:
    path = simulate(Path(args.out))
    print(f"Dataset ready at {path}", file=sys.stderr)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    results, arms = analysis(table(args.data))
    text = report(results, arms)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(f"Wrote report to {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


def cmd_size(args: argparse.Namespace) -> int:
    n = sample_size(args.base, args.mde, args.alpha, args.power)
    achieved = power(args.base, args.mde, n, args.alpha)
    print(f"{n} units per arm for {args.power:.0%} power "
          f"(achieved {achieved:.3f}) at alpha {args.alpha}")
    return 0


def cmd_sdk(args: argparse.Namespace) -> int:
    from . import sdk
    if not sdk.SDK_AVAILABLE:
        print("statsig-python-core not installed; skipping demo.", file=sys.stderr)
        return 0
    client = sdk.session()
    client.override_experiment("checkout_flow", {"variant": "treatment"})
    for uid in (f"user_{i}" for i in range(3)):
        chosen = sdk.variant(client, uid, "checkout_flow")
        sdk.track(client, uid, "purchase", "1", {"variant": chosen})
        print(f"{uid}: variant={chosen}, exposure + purchase logged")
    sdk.shutdown(client)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="experiment", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("simulate", help="write the synthetic dataset")
    s.add_argument("--out", default="data/experiment.csv")
    s.set_defaults(func=cmd_simulate)

    a = sub.add_parser("analyze", help="analyze an experiment CSV")
    a.add_argument("data")
    a.add_argument("--out", help="write a Markdown report to this path")
    a.set_defaults(func=cmd_analyze)

    z = sub.add_parser("size", help="required sample size per arm")
    z.add_argument("--base", type=float, required=True)
    z.add_argument("--mde", type=float, required=True)
    z.add_argument("--alpha", type=float, default=0.05)
    z.add_argument("--power", type=float, default=0.8)
    z.set_defaults(func=cmd_size)

    d = sub.add_parser("sdk-demo", help="run the offline Statsig SDK demo")
    d.set_defaults(func=cmd_sdk)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
