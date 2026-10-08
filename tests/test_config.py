from app.config import _engine_options, _postgres_url


def test_supabase_uri_uses_psycopg_driver_and_tls():
    url = _postgres_url("postgresql://postgres.abc:segredo@aws-0-sa-east-1.pooler.supabase.com:5432/postgres")
    assert url == "postgresql+psycopg://postgres.abc:segredo@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"


def test_explicit_driver_and_sslmode_are_kept():
    url = "postgresql+psycopg://user:pass@db.example.com:5432/app?sslmode=verify-full"
    assert _postgres_url(url) == url


def test_postgres_engine_disables_server_side_prepares_for_poolers():
    assert _engine_options("postgresql+psycopg://u:p@h/db")["connect_args"] == {"prepare_threshold": None}
    assert "connect_args" not in _engine_options("sqlite:///:memory:")


def test_password_with_url_special_characters_does_not_break_host_detection():
    url = _postgres_url("postgresql://postgres.abc:a[b]c@aws-1-us-west-2.pooler.supabase.com:5432/postgres")
    assert url.endswith("pooler.supabase.com:5432/postgres?sslmode=require")
