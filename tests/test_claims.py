from builders_first.claims import _status, verdict


def test_status_fragile_when_raw_and_adjusted_disagree():
    assert _status(True, True) == "HOLDS"
    assert _status(False, False) == "KILLED"
    assert _status(True, False) == "FRAGILE"
    assert _status(False, True) == "FRAGILE"
    assert _status(True) == "HOLDS"


def test_verdict_counts_only_holds():
    assert verdict(["HOLDS", "HOLDS", "KILLED"]) == "Bull"
    assert verdict(["HOLDS", "FRAGILE", "FRAGILE"]) == "Neutral"
    assert verdict(["FRAGILE", "KILLED", "KILLED"]) == "Bear"
