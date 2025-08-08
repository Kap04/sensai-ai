import os
from os.path import join
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from functools import lru_cache
from api.config import UPLOAD_FOLDER_NAME


root_dir = os.path.dirname(os.path.abspath(__file__))
env_path = join(root_dir, ".env.aws")
if os.path.exists(env_path):
    load_dotenv(env_path)



class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    openai_api_key: str 
    openai_base_url: str = "https://agent.dev.hyperverge.org"
    openai_model: str = "openai/gpt-4o-mini"
    database_url: str
    s3_bucket_name: str | None = None  # only relevant when running the code remotely
    s3_folder_name: str | None = None  # only relevant when running the code remotely
    local_upload_folder: str = (
        UPLOAD_FOLDER_NAME  # hardcoded variable for local file storage
    )
    bugsnag_api_key: str | None = None
    env: str | None = None
    slack_user_signup_webhook_url: str | None = None
    slack_course_created_webhook_url: str | None = None
    slack_usage_stats_webhook_url: str | None = None
    phoenix_endpoint: str | None = None
    phoenix_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=join(root_dir, ".env"))


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

if settings.phoenix_api_key is not None:
    os.environ["PHOENIX_API_KEY"] = settings.phoenix_api_key


