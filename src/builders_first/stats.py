"""Statistics: GH Archive coverage rule, coverage adjustment, and the C2/C3a tests."""
from __future__ import annotations

import contextlib
import io
import warnings

import numpy as np
import pandas as pd

COVERAGE_THRESHOLD = 0.80   # month is "good" if push AND PR volume >= 80% of trailing 12-month median
COVERAGE_WINDOW = 12


def coverage_table(vol: pd.DataFrame) -> pd.DataFrame:
    """vol: month, push_events, pr_events -> adds push_ratio, pr_ratio, good."""
    v = vol.sort_values("month").reset_index(drop=True).copy()
    for col, out in (("push_events", "push_ratio"), ("pr_events", "pr_ratio")):
        ref = v[col].shift(1).rolling(COVERAGE_WINDOW).median()
        v[out] = v[col] / ref
    # The first 12 months have no trailing reference; treat them as good.
    v["good"] = ((v.push_ratio >= COVERAGE_THRESHOLD) | v.push_ratio.isna()) & (
        (v.pr_ratio >= COVERAGE_THRESHOLD) | v.pr_ratio.isna())
    return v


def last_good_month(vol: pd.DataFrame) -> str:
    """Month before the final unbroken run of failing months (the tail collapse)."""
    v = coverage_table(vol)
    good = v.good.tolist()
    i = len(good) - 1
    while i >= 0 and not good[i]:
        i -= 1
    if i < 0:
        raise ValueError("no good month")
    return v.month[i]


def coverage_break(vol: pd.DataFrame, last_good: str) -> str | None:
    """First failing month at or before last_good (a level break inside the analysis window)."""
    v = coverage_table(vol)
    bad = v[(~v.good) & (v.month <= last_good)]
    return None if bad.empty else bad.month.iloc[0]


def coverage_factor(vol: pd.DataFrame, last_good: str) -> pd.Series:
    """Per-month factor c_t <= 1 to divide MAD by (coverage-adjusted MAD).

    c_t = 1 before the first level break; from the break on, c_t = min(1, (push+PR)_t / reference),
    reference = median push+PR volume of the 12 months before the break. Assumes developer loss is
    proportional to event loss, which over-corrects (low-activity developers are lost first), so the
    adjusted series is a conservative upper bound on true MAD.
    """
    v = vol.sort_values("month").set_index("month")
    tot = v.push_events + v.pr_events
    brk = coverage_break(vol, last_good)
    c = pd.Series(1.0, index=tot.index)
    if brk is None:
        return c
    pos = tot.index.get_loc(brk)
    ref = tot.iloc[max(0, pos - COVERAGE_WINDOW):pos].median()
    after = tot.index >= brk
    c[after] = np.minimum(1.0, tot[after] / ref)
    return c


# ---------------------------------------------------------------- time series (C2)

def dlog(s: pd.Series) -> pd.Series:
    return np.log(s.astype(float)).diff().dropna()


def adf_pvalue(x: pd.Series) -> float:
    from statsmodels.tsa.stattools import adfuller

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        return float(adfuller(x.dropna(), autolag="AIC")[1])


def cross_correlation(x: pd.Series, y: pd.Series, max_lag: int = 6) -> dict[int, float]:
    """corr(x_{t-l}, y_t) for l = 0..max_lag (positive l: x leads y)."""
    return {lag: float(pd.concat([x.shift(lag), y], axis=1).dropna().corr().iloc[0, 1]) for lag in range(max_lag + 1)}


def granger_pvalues(y: pd.Series, x: pd.Series, max_lag: int = 6) -> dict[int, float]:
    """p-value (SSR F-test) that x Granger-causes y, for lag orders 1..max_lag."""
    from statsmodels.tsa.stattools import grangercausalitytests

    df = pd.concat([y, x], axis=1).dropna()
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        res = grangercausalitytests(df.values, maxlag=max_lag)  # older statsmodels print results
    return {lag: float(res[lag][0]["ssr_ftest"][1]) for lag in range(1, max_lag + 1)}


def _lagged(y: pd.Series, x: pd.Series | None, p: int) -> pd.DataFrame:
    cols = {f"y_l{i}": y.shift(i) for i in range(1, p + 1)}
    if x is not None:
        cols.update({f"x_l{i}": x.shift(i) for i in range(1, p + 1)})
    return pd.DataFrame(cols).assign(y=y).dropna()


def out_of_sample(y: pd.Series, x: pd.Series, p: int, train_end: str) -> dict:
    """One-step-ahead forecasts on the test window: AR(p) of y vs AR(p) + p lags of x.

    Both fit by OLS on months <= train_end; returns RMSEs and their ratio (<1 means x helps).
    """
    out = {}
    for name, xx in (("restricted", None), ("unrestricted", x)):
        d = _lagged(y, xx, p)
        X = np.column_stack([np.ones(len(d)), d.drop(columns="y").values])
        train = (d.index <= train_end)
        beta, *_ = np.linalg.lstsq(X[train], d.y.values[train], rcond=None)
        err = d.y.values[~train] - X[~train] @ beta
        out[f"rmse_{name}"] = float(np.sqrt(np.mean(err ** 2)))
        out["n_test"] = int((~train).sum())
        out["n_train"] = int(train.sum())
    out["rmse_ratio"] = out["rmse_unrestricted"] / out["rmse_restricted"]
    return out


# ---------------------------------------------------------------- C3a

def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    ph = successes / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (float(centre - half), float(centre + half))


def mann_whitney_p(a: pd.Series, b: pd.Series) -> float:
    from scipy.stats import mannwhitneyu

    return float(mannwhitneyu(a, b, alternative="two-sided").pvalue)
