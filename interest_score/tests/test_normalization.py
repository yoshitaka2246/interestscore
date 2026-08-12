from interest_estimation.scoring.normalization import normalize_min_max


def test_normalize_min_max_basic():
    result = normalize_min_max({1: 0.0, 2: 5.0, 3: 10.0})
    assert result[1] == 0.0
    assert result[2] == 0.5
    assert result[3] == 1.0


def test_normalize_min_max_invert():
    result = normalize_min_max({1: 0.0, 2: 10.0}, invert=True)
    assert result[1] == 1.0
    assert result[2] == 0.0


def test_normalize_min_max_no_variance():
    result = normalize_min_max({1: 3.0, 2: 3.0})
    assert result == {1: 0.0, 2: 0.0}


def test_normalize_min_max_empty():
    assert normalize_min_max({}) == {}
