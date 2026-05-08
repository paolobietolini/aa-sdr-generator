import logging
from datetime import datetime, timedelta
from pathlib import Path


def setup_logging(log_dir: Path, retention_days: int = 30) -> None:
    """Configure the root logger to write to a timestamped file in log_dir.

    Existing FileHandlers are removed first so this function is safe to call
    multiple times (e.g., in tests). Old log files beyond retention_days are
    deleted before the new file is opened so the new file is never self-purged.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    _purge_old_logs(log_dir, retention_days)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_file = log_dir / f"{timestamp}_run.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Remove any existing FileHandlers to make setup_logging idempotent
    for h in root.handlers[:]:
        if isinstance(h, logging.FileHandler):
            root.removeHandler(h)
    root.addHandler(handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("authlib").setLevel(logging.WARNING)


def _purge_old_logs(log_dir: Path, retention_days: int) -> None:
    """Delete log files in log_dir that were last modified more than retention_days ago."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    for f in log_dir.glob("*.log"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            try:
                f.unlink()
            except OSError:
                pass
