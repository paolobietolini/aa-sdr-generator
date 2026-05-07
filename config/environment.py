from typing import Optional
from dotenv import set_key
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = '.env'

_env: Optional['Env'] = None


class Env(BaseSettings):
    client_id: str
    client_secret: str
    scopes: str
    org_id: Optional[str] = None
    global_company_id: Optional[str] = None
    technical_account_id: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')


def get_env() -> 'Env':
    global _env
    if _env is None:
        _env = Env()
    return _env


def write_env(updates: dict[str, str]) -> 'Env':
    for key, value in updates.items():
        set_key(ENV_PATH, key, value)
    return reload()


def reload() -> 'Env':
    global _env
    _env = Env()
    return _env