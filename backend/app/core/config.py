from pydantic_setting import BaseSetting

class Setting(BaseSetting):
    APP_NAME: str = "OCR MiniProject"
    DEBUG: bool = False

    #DB
    DATABASE_URL: str

    #API Key
    OPENAI_API_KEY : str = ""

    #CORS
    ALLOWED_ORIGINS: list[str] = ["http://"]

    class Config:
        env_file = ".env"

settings = Setting()