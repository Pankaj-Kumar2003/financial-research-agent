import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        GEMINI_API_KEY: str = ""
        OPENAI_API_KEY: str = ""
        GROQ_API_KEY: str = ""
        OPENROUTER_API_KEY: str = ""
        NEWS_API_KEY: str = ""
        USER_AGENT: str = "FinancialResearchAgent/1.0 (contact@example.com)"

        class Config:
            env_file = ".env"
            extra = "ignore"

    settings = Settings()

except ImportError:
    class Settings:
        def __init__(self):
            self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
            self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
            self.NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
            self.USER_AGENT = os.getenv("USER_AGENT", "FinancialResearchAgent/1.0 (contact@example.com)")

    settings = Settings()
