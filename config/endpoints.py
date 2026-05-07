class BaseUrls:
    IMS_ENDPOINT="https://ims-na1.adobelogin.com"
    AA_ENDPOINT="https://analytics.adobe.io"
    TOKEN_URL=f"{IMS_ENDPOINT}/ims/token/v3"

class AAEndpoints:
    SUITES = "/reportsuites/collections/suites"
    METRICS = "/metrics"
    DIMENSIONS = "/dimensions"
    SEGMENTS = "/segments"
    CALCULATED_METRICS = "/calculatedmetrics"
    DISCOVERY = "/discovery/me"

    @staticmethod
    def api_base(global_company_id: str) -> str:
        return f"{BaseUrls.AA_ENDPOINT}/api/{global_company_id}"

    @staticmethod
    def discovery_url() -> str:
        return f"{BaseUrls.AA_ENDPOINT}{AAEndpoints.DISCOVERY}"
