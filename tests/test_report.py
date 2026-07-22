from experiment.report import report
from experiment.stats import two_proportion


def test_report_markdown():
    r = {"conversion": two_proportion(200, 1000, 240, 1000)}
    text = report(r, arms=(1000, 1000))
    assert text.startswith("# Experiment analysis")
    assert "conversion_diff" in text
    assert "control n = 1000" in text
