import os
from pathlib import Path
from urllib.parse import quote_plus


def _local_mysql_settings():
    settings = {}
    settings_file = Path(__file__).resolve().parents[1] / "instance" / "mysql.env"
    if settings_file.exists():
        for line in settings_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip()
    for key in ("IFP_DATABASE_URL", "IFP_MYSQL_HOST", "IFP_MYSQL_PORT", "IFP_MYSQL_DATABASE", "IFP_MYSQL_USER", "IFP_MYSQL_PASSWORD"):
        if os.environ.get(key) is not None:
            settings[key] = os.environ[key]
    return settings


def _database_configuration():
    settings = _local_mysql_settings()
    if settings.get("IFP_DATABASE_URL"):
        return settings["IFP_DATABASE_URL"], True
    user = settings.get("IFP_MYSQL_USER")
    password = settings.get("IFP_MYSQL_PASSWORD")
    if user and password is not None:
        host = settings.get("IFP_MYSQL_HOST", "127.0.0.1")
        port = settings.get("IFP_MYSQL_PORT", "3306")
        database = settings.get("IFP_MYSQL_DATABASE", "instituto_fabiana_pinto")
        url = f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}?charset=utf8mb4"
        return url, True
    return "sqlite:///:memory:", False


DATABASE_URI, DATABASE_ENABLED = _database_configuration()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ifp-frontend-demonstracao")
    TEMPLATES_AUTO_RELOAD = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    QUESTION_IMAGE_MAX_BYTES = 2 * 1024 * 1024
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    DATABASE_ENABLED = DATABASE_ENABLED
    UPLOAD_ROOT = str(Path(__file__).resolve().parents[1] / "instance" / "uploads")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "ifp-testes"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DATABASE_ENABLED = True
    UPLOAD_ROOT = str(Path(__file__).resolve().parents[1] / "tmp" / "test-uploads")
