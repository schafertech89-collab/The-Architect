"""
Configuration management for the Coinbase LangChain Tool Server.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Coinbase API settings
    COINBASE_API_KEY: Optional[str] = Field(default=None, env="COINBASE_API_KEY")
    COINBASE_PRIVATE_KEY: Optional[str] = Field(default=None, env="COINBASE_PRIVATE_KEY")
    COINBASE_API_SECRET: Optional[str] = Field(default=None, env="COINBASE_API_SECRET")
    COINBASE_PASSPHRASE: Optional[str] = Field(default=None, env="COINBASE_PASSPHRASE")
    COINBASE_SANDBOX: bool = Field(default=False, env="COINBASE_SANDBOX")
    
    @property
    def private_key(self) -> Optional[str]:
        """Get private key from either COINBASE_PRIVATE_KEY or COINBASE_API_SECRET."""
        return self.COINBASE_PRIVATE_KEY or self.COINBASE_API_SECRET
    
    # API settings
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
