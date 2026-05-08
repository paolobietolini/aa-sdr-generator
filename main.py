import logging
import sys
import time
from pathlib import Path

from core.client import AdobeAnalyticsClient, AdobeClient
from config.sdr_config import SdrConfig
from exporters.excel import generate_sdr
from core.log_setup import setup_logging

logger = logging.getLogger(__name__)


def main(config_path: str = "config.yaml") -> None:
    config = SdrConfig.from_yaml(config_path)
    setup_logging(Path("logs"), config.log_retention_days)

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
