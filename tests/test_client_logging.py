import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from core.client import AdobeClient


@pytest.fixture
def client():
    mock_auth = MagicMock()
    mock_auth.env.client_id = "test_client"
    mock_auth.token.access_token = "test_token"
    with patch("core.client.Auth", return_value=mock_auth), \
         patch("core.client.certifi.where", return_value=None):
        c = AdobeClient()
    c.auth = mock_auth
    return c


def test_logs_warning_on_401_retry(client, caplog):
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.raise_for_status = MagicMock()

    unauthorized = MagicMock()
    unauthorized.status_code = 401
    unauthorized.raise_for_status = MagicMock()

    client.session.request = MagicMock(side_effect=[unauthorized, ok_response])
    client.auth.refresh = MagicMock()

    with caplog.at_level(logging.WARNING, logger="core.client"):
        client._authenticated_request("get", "https://example.com/test")

    assert any("401" in r.message for r in caplog.records)


def test_logs_debug_per_paginated_page(client, caplog):
    page0 = MagicMock()
    page0.status_code = 200
    page0.raise_for_status = MagicMock()
    page0.json.return_value = {"content": ["item1"], "lastPage": False}

    page1 = MagicMock()
    page1.status_code = 200
    page1.raise_for_status = MagicMock()
    page1.json.return_value = {"content": ["item2"], "lastPage": True}

    client.session.request = MagicMock(side_effect=[page0, page1])
    client.auth.ensure_token = MagicMock()

    with caplog.at_level(logging.DEBUG, logger="core.client"):
        client._paginated_request("get", "https://example.com/list")

    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert len(debug_messages) >= 2
