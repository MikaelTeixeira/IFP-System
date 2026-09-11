import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ifp-frontend-demonstracao")
    TEMPLATES_AUTO_RELOAD = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "ifp-testes"

