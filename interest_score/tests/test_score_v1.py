from interest_estimation.scoring import score_v1


def test_compute_score_weighted_sum():
    normalized = {"dwell_time": 1.0, "speed": 0.5, "body_direction": 0.0, "face_direction": 0.0}
    weights = {"dwell_time": 0.4, "speed": 0.3, "body_direction": 0.3, "face_direction": 0.0}

    score = score_v1.compute_score(normalized, weights, output_scale=100.0)

    assert score == (1.0 * 0.4 + 0.5 * 0.3) * 100.0


def test_speed_is_inverted_feature():
    assert "speed" in score_v1.INVERT_FEATURES
    assert "dwell_time" not in score_v1.INVERT_FEATURES
