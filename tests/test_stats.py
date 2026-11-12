import numpy as np
import pandas as pd

from builders_first import stats


def _vol(push, pr):
    months = pd.period_range("2022-01", periods=len(push), freq="M").strftime("%Y-%m")
    return pd.DataFrame({"month": months, "push_events": push, "pr_events": pr})


def test_last_good_month_ignores_mid_dip_and_cuts_tail():
    push = [100] * 14 + [60] * 2 + [100] * 6 + [100, 30, 20]
    pr = [10] * 22 + [2, 10, 1]          # PR collapse starts one month before the push collapse
    v = _vol(push, pr)
    assert stats.last_good_month(v) == v.month[21]
    assert stats.coverage_break(v, v.month[21]) == v.month[14]


def test_coverage_factor_only_after_break_and_capped():
    push = [100] * 14 + [60] * 4 + [120] * 4
    pr = [0] * 22
    v = _vol(push, pr)
    c = stats.coverage_factor(v, v.month.iloc[-1])
    assert (c.iloc[:14] == 1).all()
    assert np.isclose(c.iloc[14], 0.6)
    assert (c.iloc[18:] == 1).all()


def test_granger_detects_leading_series():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=200))
    y = 0.8 * x.shift(2).fillna(0) + 0.3 * pd.Series(rng.normal(size=200))
    p = stats.granger_pvalues(y, x, max_lag=3)
    assert p[2] < 1e-6 and p[3] < 1e-6
    cc = stats.cross_correlation(x, y, 3)
    assert max(cc, key=cc.get) == 2


def test_out_of_sample_prefers_true_model():
    rng = np.random.default_rng(1)
    idx = pd.period_range("2015-01", periods=150, freq="M").strftime("%Y-%m")
    x = pd.Series(rng.normal(size=150), index=idx)
    y = (0.9 * x.shift(1)).fillna(0) + 0.2 * pd.Series(rng.normal(size=150), index=idx)
    r = stats.out_of_sample(y, x, p=1, train_end="2022-12")
    assert r["rmse_ratio"] < 0.5 and r["n_test"] > 0


def test_wilson_ci():
    lo, hi = stats.wilson_ci(12, 100)
    assert 0.06 < lo < 0.12 < hi < 0.21
