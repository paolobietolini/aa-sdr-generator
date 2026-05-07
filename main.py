from core.client import AdobeAnalyticsClient, AdobeClient

client = AdobeAnalyticsClient(AdobeClient())
s = client.get_metrics(rsid='aldinordbe')

print(s)
