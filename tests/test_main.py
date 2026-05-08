import logging
import pytest
from unittest.mock import MagicMock, patch

from main import main


def test_main_calls_setup_logging(tmp_path):
    with patch("main.SdrConfig.from_yaml") as mock_cfg_cls, \
         patch("main.setup_logging") as mock_setup, \
         patch("main.AdobeClient"), \
         patch("main.AdobeAnalyticsClient"), \
         patch("main.generate_sdr", return_value=[]):
        cfg = MagicMock()
        cfg.log_retention_days = 30
        cfg.output_dir = tmp_path
        mock_cfg_cls.return_value = cfg

        main()

    mock_setup.assert_called_once()
    args = mock_setup.call_args[0]
    assert args[1] == 30  # retention_days passed through


def test_main_exits_1_on_exception(tmp_path):
    with patch("main.SdrConfig.from_yaml") as mock_cfg_cls, \
         patch("main.setup_logging"), \
         patch("main.AdobeClient"), \
         patch("main.AdobeAnalyticsClient"), \
         patch("main.generate_sdr", side_effect=RuntimeError("boom")):
        cfg = MagicMock()
        cfg.log_retention_days = 30
        cfg.output_dir = tmp_path
        mock_cfg_cls.return_value = cfg

        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 1


def test_main_logs_run_start_and_complete(tmp_path, caplog):
    with patch("main.SdrConfig.from_yaml") as mock_cfg_cls, \
         patch("main.setup_logging"), \
         patch("main.AdobeClient"), \
         patch("main.AdobeAnalyticsClient"), \
         patch("main.generate_sdr", return_value=[tmp_path / "rsid_sdr.xlsx"]):
        cfg = MagicMock()
        cfg.log_retention_days = 30
        cfg.output_dir = tmp_path
        mock_cfg_cls.return_value = cfg

        with caplog.at_level(logging.INFO, logger="main"):
            main()

    messages = [r.message for r in caplog.records]
    assert any("Run started" in m for m in messages)
    assert any("Run complete" in m for m in messages)
