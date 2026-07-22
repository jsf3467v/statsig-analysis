"""Drive the Statsig SDK against a live experiment.

Reads STATSIG_SERVER_SECRET from the environment. Statsig assigns each user to a
group; conversion is drawn per assigned variant so the pipeline has a real
effect to detect. Run: PYTHONPATH=src python seed_traffic.py
"""
from __future__ import annotations

import argparse
import os
from collections import Counter

import numpy as np

from experiment import sdk

RATES = {"control": 0.10, "treatment": 0.14}


def traffic(experiment: str, event: str, users: int, seed: int) -> None:
    if not sdk.SDK_AVAILABLE:
        raise SystemExit("Install the SDK first: pip install -r requirements-sdk.txt")
    if not os.environ.get("STATSIG_SERVER_SECRET"):
        raise SystemExit("Set STATSIG_SERVER_SECRET to your secret- key first")
    rng = np.random.default_rng(seed)
    client = sdk.session()
    seen, converted = Counter(), Counter()
    for i in range(users):
        uid = f"user_{i}"
        group = sdk.variant(client, uid, experiment)      # logs the exposure
        seen[group] += 1
        if rng.random() < RATES.get(group, RATES["control"]):
            sdk.track(client, uid, event, "1", {"variant": group})
            converted[group] += 1
    sdk.shutdown(client)
    for group in sorted(seen):
        n = seen[group]
        print(f"{group}: {n} users, {converted[group]} {event} ({converted[group] / n:.1%})")
    if len(seen) < 2:
        print("WARNING: only one variant seen. Is the experiment Started, and "
              "does it define a string parameter named 'variant'?")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiment", default="checkout_flow")
    p.add_argument("--event", default="purchase")
    p.add_argument("--users", type=int, default=8000)
    p.add_argument("--seed", type=int, default=11)
    a = p.parse_args()
    traffic(a.experiment, a.event, a.users, a.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
