import os

class Settings:
    PROJECT_NAME: str = "target99"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "target99_super_secret_signing_key_for_jwt_tokens_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # SQLite local DB path
    DATABASE_URL: str = "sqlite:///./db.sqlite3"
    
    # Mock Admin credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin99"

settings = Settings()
