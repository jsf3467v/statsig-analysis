"""Reproducible synthetic experiment with a known ground-truth effect."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

DEFAULT_PATH = Path("data/experiment.csv")
COLUMNS = ["unit", "arm", "converted", "revenue", "pre_revenue"]


def dataset(n: int = 40000, base_rate: float = 0.10, lift: float = 0.012,
            rev_lift: float = 0.5, seed: int = 7) -> dict[str, np.ndarray]:
    """Two balanced arms. Treatment adds `lift` to conversion and `rev_lift` to
    revenue. Revenue tracks a pre-experiment covariate, which CUPED exploits."""
    rng = np.random.default_rng(seed)
    arm = rng.integers(0, 2, size=n)
    converted = (rng.random(n) < base_rate + lift * arm).astype(int)
    pre_revenue = rng.lognormal(mean=3.0, sigma=0.6, size=n)
    revenue = np.maximum(0.0, 0.6 * pre_revenue + rev_lift * arm + rng.normal(0, 4, size=n))
    return {"unit": np.arange(n), "arm": arm, "converted": converted,
            "revenue": revenue, "pre_revenue": pre_revenue}


def simulate(path: Path = DEFAULT_PATH, **kwargs) -> Path:
    """Write the dataset once; reuse it on later runs (a resumable save point)."""
    if Path(path).exists():
        return Path(path)
    data = dataset(**kwargs)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        writer.writerows(zip(*(data[c] for c in COLUMNS), strict=False))
    return Path(path)
