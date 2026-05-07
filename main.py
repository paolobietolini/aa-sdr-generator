from core.client import AdobeAnalyticsClient, AdobeClient
from config.sdr_config import SdrConfig
from exporters.excel import generate_sdr


def main(config_path: str = "config.yaml") -> None:
    config = SdrConfig.from_yaml(config_path)
    client = AdobeAnalyticsClient(AdobeClient())
    generate_sdr(client, config)


if __name__ == "__main__":
    main()
