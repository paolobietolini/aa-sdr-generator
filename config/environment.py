from typing import Optional
from dotenv import set_key, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = '.env'

class Env(BaseSettings):
    client_id: str
    client_secret: str
    scopes: str
    org_id: Optional[str] = None
    global_company_id: Optional[str] = None
    technical_account_id: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')


def write_env(updates: dict[str, str]) -> None:
    for key, value in updates.items():
        set_key(ENV_PATH, key, value)

def reload():
    pass