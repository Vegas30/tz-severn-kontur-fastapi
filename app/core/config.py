from pydantic_settings import BaseSettings
from functools import lru_cache 

class Settings(BaseSettings):
    
    #Application
    APP_NAME: str = "Document Center API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False 

    #DataBase
    DATABASE_URL: str = "sqlite:///.app.db"

    #JWT Settings 
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "UTF-8"
        case_sensitive = True 

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()