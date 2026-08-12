from interest_estimation.utils.config import load_config


def test_load_default_config():
    config = load_config("configs/default.yaml")
    assert config.detection.model == "yolo11n.pt"
    assert config.scoring.version == "v1"
    assert config.features.body_direction.enabled is False
    assert config.features.dwell_time.enabled is True


def test_missing_output_scale_defaults_to_100():
    config = load_config("configs/default.yaml")
    assert config.scoring.output_scale == 100.0
