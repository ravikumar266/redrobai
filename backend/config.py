from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Calculate absolute path to the root directory's .env file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load dotenv file explicitly from the absolute path
load_dotenv(dotenv_path=ENV_FILE)

class Settings(BaseSettings):
    """
    App Configuration settings using Pydantic Settings.
    All fields auto-map to environment variable names (case-insensitive).
    Example: GEMINI_API_KEY_1 in .env -> self.GEMINI_API_KEY_1
    """
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Recruitment Copilot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security (JWT)
    SECRET_KEY: str = "your-super-secret-key-for-jwt-do-not-share-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "recruitment_os"

    # Gemini API Keys (rotated on quota exhaustion)
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""

    # Groq API Key (Fallback LLM provider)
    GROQ_API_KEY: str = ""

    # GitHub API Token
    GITHUB_TOKEN: str = ""

    # Tavily Web Search API Key
    TAVILY_API_KEY: str = ""

    # LLM Model Names
    GEMINI_MODEL_NAME: str = "gemini-1.5-pro-latest"
    GROQ_MODEL_NAME: str = "llama-3.1-70b-versatile"

    # Gmail API Configuration
    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_TOKEN_FILE: str = "token.json"
    GMAIL_SENDER_EMAIL: str = ""
    RECRUITER_NOTIFICATION_EMAIL: str = "recruiter@example.com"

    @property
    def gemini_keys(self) -> List[str]:
        """
        Returns a list of all available non-empty Gemini API keys.
        Used by ProviderManager for key rotation.
        """
        return [k for k in [self.GEMINI_API_KEY_1, self.GEMINI_API_KEY_2, self.GEMINI_API_KEY_3] if k]


# Singleton instance — import this everywhere
settings = Settings()
