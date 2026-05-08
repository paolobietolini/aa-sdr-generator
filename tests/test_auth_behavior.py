from unittest.mock import MagicMock, patch

from core.auth import Auth


def test_ensure_token_caches_and_does_not_refetch():
    mock_env = MagicMock()
    mock_env.org_id = "org"
    mock_env.technical_account_id = "tech"

    mock_token = MagicMock()
    mock_token.is_expired = False

    with patch("core.auth.get_env", return_value=mock_env), \
         patch.object(Auth, "_fetch_token", return_value=mock_token) as mock_fetch:
        auth = Auth()
        auth.ensure_token()
        auth.ensure_token()
        auth.ensure_token()

    # First ensure_token populates the cache; subsequent calls skip _fetch_token
    assert mock_fetch.call_count == 1


def test_ensure_token_refetches_when_cached_token_is_expired():
    mock_env = MagicMock()
    mock_env.org_id = "org"
    mock_env.technical_account_id = "tech"

    expired_token = MagicMock()
    expired_token.is_expired = True
    fresh_token = MagicMock()
    fresh_token.is_expired = False

    with patch("core.auth.get_env", return_value=mock_env), \
         patch.object(Auth, "_fetch_token", return_value=fresh_token) as mock_fetch:
        auth = Auth()
        auth._token = expired_token  # simulate a cached but now-expired token

        result = auth.ensure_token()

    assert result is fresh_token
    assert mock_fetch.call_count == 1


def test_bootstrap_skips_write_env_when_credentials_present():
    mock_env = MagicMock()
    mock_env.org_id = "existing_org"
    mock_env.technical_account_id = "existing_tech"

    with patch("core.auth.get_env", return_value=mock_env), \
         patch("core.auth.write_env") as mock_write:
        Auth()

    mock_write.assert_not_called()


def test_bootstrap_calls_write_env_when_credentials_missing():
    mock_env = MagicMock()
    mock_env.org_id = None
    mock_env.technical_account_id = None

    mock_token = MagicMock()
    mock_token.claims = {"org": "discovered_org", "client_id": "discovered_client"}
    mock_token.is_expired = False

    with patch("core.auth.get_env", return_value=mock_env), \
         patch("core.auth.write_env", return_value=mock_env) as mock_write, \
         patch.object(Auth, "_fetch_token", return_value=mock_token):
        Auth()

    mock_write.assert_called_once_with(
        {"ORG_ID": "discovered_org", "TECHNICAL_ACCOUNT_ID": "discovered_client"}
    )
