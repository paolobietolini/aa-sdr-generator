import logging
from unittest.mock import MagicMock, patch

import pytest

from core.auth import Auth


def test_bootstrap_logs_info_when_writing_env(caplog):
    mock_env = MagicMock()
    mock_env.org_id = None
    mock_env.technical_account_id = None

    mock_token = MagicMock()
    mock_token.claims = {"org": "test_org", "client_id": "test_client"}
    mock_token.is_expired = False

    with patch("core.auth.get_env", return_value=mock_env), \
         patch("core.auth.write_env", return_value=mock_env), \
         patch.object(Auth, "_fetch_token", return_value=mock_token), \
         caplog.at_level(logging.INFO, logger="core.auth"):
        Auth()

    assert any(r.message == "Bootstrap: writing ORG_ID and TECHNICAL_ACCOUNT_ID to .env" for r in caplog.records)


def test_fetch_token_logs_debug(caplog):
    mock_env = MagicMock()
    mock_env.org_id = "org"
    mock_env.technical_account_id = "tech"
    mock_env.client_id = "cid"
    mock_env.client_secret = "csecret"
    mock_env.scopes = "openid"

    mock_token = MagicMock()
    mock_token.is_expired = False

    with patch("core.auth.get_env", return_value=mock_env), \
         patch.object(Auth, "_fetch_token", return_value=mock_token):
        auth = Auth()

    with patch("core.auth.OAuth2Session") as mock_session_cls, \
         patch.object(Auth, "_decode_token", return_value={"created_at": "0", "org": "x", "client_id": "y"}), \
         caplog.at_level(logging.DEBUG, logger="core.auth"):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.fetch_token.return_value = {
            "access_token": "a.b.c",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        auth._fetch_token()

    assert any(r.message == "Fetching access token from Adobe IMS" for r in caplog.records)
