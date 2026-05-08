from pathlib import Path
import pytest
import yaml
from pydantic import ValidationError
from config.sdr_config import SdrConfig


def test_log_retention_days_defaults_to_30():
    config = SdrConfig()
    assert config.log_retention_days == 30


def test_log_retention_days_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_retention_days: 7\n")
    config = SdrConfig.from_yaml(config_file)
    assert config.log_retention_days == 7


def test_from_yaml_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        SdrConfig.from_yaml("/nonexistent/path/config.yaml")


def test_from_yaml_invalid_yaml_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: [unclosed\n")
    with pytest.raises(yaml.YAMLError):
        SdrConfig.from_yaml(config_file)


def test_from_yaml_wrong_field_type_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_retention_days: not_a_number\n")
    with pytest.raises(ValidationError):
        SdrConfig.from_yaml(config_file)
