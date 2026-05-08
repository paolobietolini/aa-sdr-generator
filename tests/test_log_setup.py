import logging
import os
import re
import time
from pathlib import Path

import pytest

from core.log_setup import setup_logging


def test_creates_log_file(tmp_path):
    setup_logging(tmp_path, retention_days=30)
    logs = list(tmp_path.glob("*.log"))
    assert len(logs) == 1


def test_log_file_name_format(tmp_path):
    setup_logging(tmp_path, retention_days=30)
    log_file = next(tmp_path.glob("*.log"))
    assert re.match(r"\d{4}-\d{2}-\d{2}_\d{6}_run\.log", log_file.name)


def test_message_written_to_file(tmp_path):
    setup_logging(tmp_path, retention_days=30)
    logging.getLogger("test_write").info("hello from test")
    log_file = next(tmp_path.glob("*.log"))
    content = log_file.read_text()
    assert "hello from test" in content


def test_retention_purges_old_logs(tmp_path):
    old_log = tmp_path / "2020-01-01_120000_run.log"
    old_log.write_text("old")
    old_mtime = time.time() - (31 * 86400)
    os.utime(old_log, (old_mtime, old_mtime))

    setup_logging(tmp_path, retention_days=30)

    assert not old_log.exists()


def test_retention_keeps_recent_logs(tmp_path):
    recent_log = tmp_path / "2026-05-07_120000_run.log"
    recent_log.write_text("recent")

    setup_logging(tmp_path, retention_days=30)

    assert recent_log.exists()
