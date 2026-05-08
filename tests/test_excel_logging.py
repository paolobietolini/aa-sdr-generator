import logging
from unittest.mock import MagicMock, patch

import pytest

from exporters.excel import generate_sdr


def test_warns_when_no_suites_matched(tmp_path, caplog):
    client = MagicMock()
    client.get_suites.return_value = []

    config = MagicMock()
    config.rsids.include = ["test*"]
    config.rsids.exclude = []

    with caplog.at_level(logging.WARNING, logger="exporters.excel"):
        result = generate_sdr(client, config)

    assert result == []
    assert any("No report suites matched" in r.message for r in caplog.records)


def test_logs_info_per_suite(tmp_path, caplog):
    suite = MagicMock()
    suite.rsid = "test_rsid"

    client = MagicMock()
    client.get_suites.return_value = [suite]
    client.get_dimensions.return_value = []
    client.get_metrics.return_value = []
    client.get_calculated_metrics.return_value = []
    client.get_segments.return_value = []

    config = MagicMock()
    config.rsids.include = ["*"]
    config.rsids.exclude = []
    config.metadata.organization = "Test Org"
    config.output_dir = tmp_path

    with patch("exporters.excel.openpyxl.load_workbook") as mock_wb:
        wb = MagicMock()
        mock_wb.return_value = wb
        wb.__getitem__ = MagicMock(return_value=MagicMock(max_row=6))

        with caplog.at_level(logging.INFO, logger="exporters.excel"):
            generate_sdr(client, config)

    messages = [r.message for r in caplog.records]
    assert any("test_rsid" in m for m in messages)


def test_logs_error_and_continues_on_suite_failure(tmp_path, caplog):
    suite_a = MagicMock()
    suite_a.rsid = "bad_rsid"   # processed first — will raise
    suite_b = MagicMock()
    suite_b.rsid = "good_rsid"  # processed second — will succeed

    client = MagicMock()
    client.get_suites.return_value = [suite_a, suite_b]
    client.get_dimensions.side_effect = [RuntimeError("API down"), []]
    client.get_metrics.return_value = []
    client.get_calculated_metrics.return_value = []
    client.get_segments.return_value = []

    config = MagicMock()
    config.rsids.include = ["*"]
    config.rsids.exclude = []
    config.metadata.organization = "Test Org"
    config.metadata.author = None
    config.output_dir = tmp_path

    with patch("exporters.excel.openpyxl.load_workbook") as mock_wb:
        wb = MagicMock()
        mock_wb.return_value = wb
        wb.__getitem__ = MagicMock(return_value=MagicMock(max_row=6))

        with caplog.at_level(logging.ERROR, logger="exporters.excel"):
            result = generate_sdr(client, config)

    error_messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("bad_rsid" in m for m in error_messages)
    assert any(f.name.startswith("good_rsid_") and f.name.endswith("_sdr.xlsx") for f in result)
