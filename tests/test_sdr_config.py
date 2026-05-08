from pathlib import Path
import pytest
from config.sdr_config import SdrConfig


def test_log_retention_days_defaults_to_30():
    config = SdrConfig()
    assert config.log_retention_days == 30


def test_log_retention_days_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_retention_days: 7\n")
    config = SdrConfig.from_yaml(config_file)
    assert config.log_retention_days == 7
