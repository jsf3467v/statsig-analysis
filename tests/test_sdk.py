import pytest

from experiment import sdk

pytestmark = pytest.mark.skipif(not sdk.SDK_AVAILABLE, reason="statsig SDK not installed")


def test_offline_gate_and_track():
    client = sdk.session()
    client.override_gate("new_flow", True)
    assert sdk.gate(client, "user_1", "new_flow") is True
    sdk.track(client, "user_1", "purchase", "1", {"variant": "treatment"})
    sdk.shutdown(client)
