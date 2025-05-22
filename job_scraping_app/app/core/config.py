import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load .env file from the project root (job_scraping_app)
# This assumes the config.py file is in job_scraping_app/app/core/
# Adjust the path if your structure is different.
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Scraping Application"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str

    # Example of other settings you might have
    # SECRET_KEY: str = "your_secret_key" # For JWT, etc.
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env" # Specifies the .env file to load if not using load_dotenv explicitly above
        env_file_encoding = 'utf-8'
        # case_sensitive = True # Default is False, meaning env vars can be uppercase

settings = Settings()

# You can add a check here to ensure DATABASE_URL is loaded
if not settings.DATABASE_URL:
    print("Warning: DATABASE_URL is not set. Please check your .env file or environment variables.")
else:
    # For security, you might not want to print the full URL in production logs
    print(f"DATABASE_URL loaded: {settings.DATABASE_URL[:settings.DATABASE_URL.rfind('/')+1]}********")
