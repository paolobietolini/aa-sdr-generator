import base64
import json

from core.auth import Auth


def _make_token(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def test_decode_token_extracts_org_and_client_id():
    payload = {"org": "test_org", "client_id": "test_client", "created_at": "1000"}
    result = Auth._decode_token(_make_token(payload))
    assert result["org"] == "test_org"
    assert result["client_id"] == "test_client"


def test_decode_token_extracts_created_at():
    payload = {"created_at": "1714567890000"}
    result = Auth._decode_token(_make_token(payload))
    assert result["created_at"] == "1714567890000"


def test_decode_token_handles_all_padding_lengths():
    # base64 padding is needed for lengths % 4 == 1, 2, 3 — exercise all three
    for extra in ["", "x", "xx"]:
        payload = {"key": extra}
        result = Auth._decode_token(_make_token(payload))
        assert result["key"] == extra
