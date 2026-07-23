"""Statsig SDK integration.

With a server secret in STATSIG_SERVER_SECRET (and network), this talks to a
live Statsig project. Without one it runs offline via disable_network and local
overrides, so the call pattern -- gates, experiment reads, and event logging --
runs anywhere. Degrades gracefully if the SDK package is absent.
"""
from __future__ import annotations

import os

try:
    from statsig_python_core import Statsig, StatsigOptions, StatsigUser
    SDK_AVAILABLE = True
except Exception:
    SDK_AVAILABLE = False


def session(secret: str | None = None, environment: str | None = None):
    """Initialized Statsig client; offline when no secret is supplied."""
    if not SDK_AVAILABLE:
        raise RuntimeError("statsig-python-core is not installed")
    secret = secret or os.environ.get("STATSIG_SERVER_SECRET")
    options = StatsigOptions()
    options.environment = environment or os.environ.get("STATSIG_ENVIRONMENT", "production")
    options.output_log_level = "error"
    options.disable_network = secret is None
    client = Statsig(secret or "secret-offline", options)
    client.initialize().wait()
    return client


def gate(client, user_id: str, name: str) -> bool:
    return client.check_gate(StatsigUser(user_id=user_id), name)


def variant(client, user_id: str, experiment: str, default: str = "control") -> str:
    exp = client.get_experiment(StatsigUser(user_id=user_id), experiment)
    return exp.get_string("variant", default)


def track(client, user_id: str, event: str,
          value: str | None = None, metadata: dict | None = None) -> None:
    client.log_event(StatsigUser(user_id=user_id), event, value, metadata)


def shutdown(client) -> None:
    client.flush_events()
    client.shutdown().wait()
