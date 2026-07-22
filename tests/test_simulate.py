from experiment.simulate import dataset, simulate
from experiment.stats import two_proportion


def test_reproducible():
    a, b = dataset(n=2000, seed=3), dataset(n=2000, seed=3)
    assert (a["converted"] == b["converted"]).all()
    assert (a["revenue"] == b["revenue"]).all()


def test_shape_and_balance():
    d = dataset(n=4000, seed=3)
    assert d["arm"].size == 4000
    assert 0.45 < d["arm"].mean() < 0.55


def test_ground_truth_effect_recovered():
    d = dataset(n=40000, base_rate=0.10, lift=0.012, seed=7)
    arm, conv = d["arm"], d["converted"]
    c, t = arm == 0, arm == 1
    r = two_proportion(int(conv[c].sum()), int(c.sum()),
                       int(conv[t].sum()), int(t.sum()))
    assert r.significant
    assert abs(r.estimate - 0.012) < 0.01


def test_save_point(tmp_path):
    path = tmp_path / "exp.csv"
    first = simulate(path, n=1000, seed=3)
    assert first.exists()
    assert simulate(path, n=1000, seed=3) == first
