import os
from pydantic_settings import BaseSettings, SettingsConfigDict
# from dotenv import load_dotenv # pydantic-settings handles .env loading if python-dotenv is installed

# Determine the root directory of the project
# config.py is in job_scraping_app/app/core/
# .env should be in job_scraping_app/
# So, path to .env is two levels up from this file's directory.
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")
# print(f"Calculated .env path: {ENV_FILE_PATH}") # For debugging path calculation

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Scraping Application"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str # This will be loaded from environment or .env

    # Example of other settings you might have
    # SECRET_KEY: str = "your_secret_key" # For JWT, etc.
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Pydantic V2 configuration using model_config
    # pydantic-settings will automatically attempt to load from a .env file
    # in the current working directory or a parent directory if python-dotenv is installed.
    # Explicitly setting env_file path relative to this file:
    # The path to .env is effectively '../../.env' from this file (app/core/config.py)
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra fields from .env not defined in Settings
    )

settings = Settings()

# You can add a check here to ensure DATABASE_URL is loaded
if not settings.DATABASE_URL:
    # This warning might appear during build on Heroku if .env is not present
    # but DATABASE_URL is set directly as a config var.
    print("Warning: DATABASE_URL could not be loaded by Pydantic settings. Ensure it's set as an environment variable or in .env.")
else:
    # For security, you might not want to print the full URL in production logs
    # This print statement is more for local debugging.
    # In Heroku, avoid printing sensitive URLs to logs if possible.
    # print(f"DATABASE_URL successfully loaded into Pydantic settings: {settings.DATABASE_URL[:settings.DATABASE_URL.rfind('/')+1]}********")
    pass # Keep logs cleaner in production
