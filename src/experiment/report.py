"""Concise Markdown summary of experiment results."""
from __future__ import annotations

from .stats import Result


def line(result: Result) -> str:
    mark = "significant" if result.significant else "not significant"
    return (f"- {result.metric}: {result.estimate:+.4f} "
            f"[{result.ci_low:+.4f}, {result.ci_high:+.4f}], "
            f"p = {result.p_value:.4f} ({mark})")


def report(results: dict[str, Result], arms: tuple[int, int]) -> str:
    lines = ["# Experiment analysis", ""]
    lines.append(f"- Arms: control n = {arms[0]}, treatment n = {arms[1]}")
    lines.append("")
    lines += [line(r) for r in results.values()]
    return "\n".join(lines) + "\n"
