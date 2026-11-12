import math

import pandas as pd

from builders_first.cohort import index_month, month_index, monthly_active, retention


def _act(rows):
    return pd.DataFrame(rows, columns=["ecosystem", "month", "dev"])


def test_month_index_roundtrip():
    s = pd.Series(["2021-01", "2021-12", "2022-01"])
    i = month_index(s)
    assert list(i.diff().dropna()) == [11, 1]
    assert index_month(int(i[2])) == "2022-01"


def test_monthly_active_and_new():
    act = _act([("X", "2022-01", "a"), ("X", "2022-01", "b"), ("X", "2022-02", "a"), ("X", "2022-02", "c")])
    m = monthly_active(act).set_index("month")
    assert m.loc["2022-01", "mad"] == 2 and m.loc["2022-01", "new_devs"] == 2
    assert m.loc["2022-02", "mad"] == 2 and m.loc["2022-02", "new_devs"] == 1


def test_retention_strict_and_smoothed():
    # a: active m0, m3 -> retained at k=3. b: active m0, m4 -> smoothed only. c: m0 only.
    act = _act([
        ("X", "2022-01", "a"), ("X", "2022-04", "a"),
        ("X", "2022-01", "b"), ("X", "2022-05", "b"),
        ("X", "2022-01", "c"),
        ("X", "2022-12", "z"),  # extends the window; its cohort lacks follow-up and is excluded
    ])
    r = retention(act, ks=(3,), last_month="2022-12").iloc[0]
    assert r.cohort_devs == 3
    assert math.isclose(r.retention, 1 / 3)
    assert math.isclose(r.retention_smooth, 2 / 3)


def test_retention_excludes_incomplete_followup():
    act = _act([("X", "2022-01", "a"), ("X", "2022-06", "a")])
    r = retention(act, ks=(6,), last_month="2022-07").iloc[0]
    assert r.cohort_devs == 0  # needs month +7 for the smoothed window
