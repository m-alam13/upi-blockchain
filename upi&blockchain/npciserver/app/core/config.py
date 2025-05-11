from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv() 

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str

    class Config:
        env_file = ".env"  # Load from the .env file

settings = Settings()
