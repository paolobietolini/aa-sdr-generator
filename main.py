import logging
import sys
import time
from pathlib import Path

from core.client import AdobeAnalyticsClient, AdobeClient
from config.sdr_config import SdrConfig
from exporters.excel import generate_sdr
from core.log_setup import setup_logging

logger = logging.getLogger(__name__)

_HERE = Path(__file__).parent


def main(config_path: Path | str | None = None) -> None:
    """Load config, set up logging, and generate the SDR files."""
    if config_path is None:
        config_path = _HERE / "config.yaml"
    config_path = Path(config_path)

    config = SdrConfig.from_yaml(config_path)

    # Resolve paths relative to the config file so cron invocations work correctly
    # regardless of the working directory.
    config_dir = config_path.parent
    if not config.template_path.is_absolute():
        config.template_path = (config_dir / config.template_path).resolve()
    if not config.output_dir.is_absolute():
        config.output_dir = (config_dir / config.output_dir).resolve()

    setup_logging(_HERE / "logs", config.log_retention_days)

    logger.info("Run started — config=%s output_dir=%s", config_path, config.output_dir)
    start = time.monotonic()

    try:
        client = AdobeAnalyticsClient(AdobeClient())
        files = generate_sdr(client, config)
        elapsed = time.monotonic() - start
        logger.info("Run complete — %d file(s) written in %.1fs", len(files), elapsed)
    except Exception:
        logger.exception("Run failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
