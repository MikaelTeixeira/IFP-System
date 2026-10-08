import os
from pathlib import Path
from urllib.parse import quote_plus


INSTANCE_DIR = Path(__file__).resolve().parents[1] / "instance"
# database.env is the current settings file; mysql.env is still read for older local setups.
SETTINGS_FILES = (INSTANCE_DIR / "database.env", INSTANCE_DIR / "mysql.env")


def _local_database_settings():
    settings = {}
    settings_file = next((path for path in SETTINGS_FILES if path.exists()), None)
    if settings_file:
        for line in settings_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip()
    for key in ("IFP_DATABASE_URL", "IFP_MYSQL_HOST", "IFP_MYSQL_PORT", "IFP_MYSQL_DATABASE", "IFP_MYSQL_USER", "IFP_MYSQL_PASSWORD"):
        if os.environ.get(key) is not None:
            settings[key] = os.environ[key]
    return settings


def _postgres_url(url):
    """Accept the URI Supabase shows (postgresql://...) and use the installed psycopg 3 driver over TLS."""
    scheme, rest = url.split("://", 1)
    if scheme in {"postgres", "postgresql"}:
        url = f"postgresql+psycopg://{rest}"
    # Read the host after the last "@" so passwords with URL-special characters cannot confuse parsing.
    host = url.rsplit("@", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    if "sslmode=" not in url and host.endswith((".supabase.com", ".supabase.co")):
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def _engine_options(url):
    options = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        # Supabase poolers (Supavisor) do not keep server-side prepared statements across clients.
        options["connect_args"] = {"prepare_threshold": None}
    return options


def _database_configuration():
    settings = _local_database_settings()
    if settings.get("IFP_DATABASE_URL"):
        url = settings["IFP_DATABASE_URL"]
        return (_postgres_url(url) if url.startswith(("postgres://", "postgresql")) else url), True
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
DATABASE_ENGINE_OPTIONS = _engine_options(DATABASE_URI)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ifp-frontend-demonstracao")
    TEMPLATES_AUTO_RELOAD = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    QUESTION_IMAGE_MAX_BYTES = 2 * 1024 * 1024
    SCAN_UPLOAD_MAX_BYTES = 50 * 1024 * 1024
    SCAN_MAX_PAGES = 300
    SCAN_MAX_PIXELS = 40_000_000
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = DATABASE_ENGINE_OPTIONS
    DATABASE_ENABLED = DATABASE_ENABLED
    UPLOAD_ROOT = str(Path(__file__).resolve().parents[1] / "instance" / "uploads")
    SCAN_ROOT = str(Path(__file__).resolve().parents[1] / "instance" / "answer-scans")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "ifp-testes"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    DATABASE_ENABLED = True
    UPLOAD_ROOT = str(Path(__file__).resolve().parents[1] / "tmp" / "test-uploads")
    SCAN_ROOT = str(Path(__file__).resolve().parents[1] / "tmp" / "test-answer-scans")
