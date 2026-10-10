from pathlib import Path

import pytest

from src.config import ConfigurationError, PROJECT_ROOT, Settings, load_settings
from src.database.connection import create_database_engine

URL = "postgresql://example:local-test-secret@localhost/example"


def test_environment_precedence_and_hidden_secrets(tmp_path):
    env = tmp_path / ".env.local"
    env.write_text(f"DATABASE_URL={URL}\nDATA_DIR=../Dados\n", encoding="utf-8")
    settings = load_settings(env, {"DB_CONNECT_TIMEOUT": "20"})
    assert settings.connect_timeout == 20
    assert "local-test-secret" not in repr(settings)
    assert settings.data_dir == (PROJECT_ROOT.parent / "Dados").resolve()
    assert load_settings(env, {"DATABASE_URL": ""}).database_url is None


@pytest.mark.parametrize("value", ["https://example.com", "postgresql://", URL + "?sslmode=disable", URL + "?options=unsafe"])
def test_reject_invalid_url_without_echoing_it(value):
    with pytest.raises(ConfigurationError) as exc:
        Settings(database_url=value).require_database_url()
    assert value not in str(exc.value)
    assert "local-test-secret" not in str(exc.value)


def test_public_connection_never_falls_back_to_admin():
    with pytest.raises(ConfigurationError, match="PUBLIC_DATABASE_URL"):
        create_database_engine(Settings(database_url=URL), public=True)


def test_engine_driver_and_public_write_guard():
    settings = Settings(database_url=URL, public_database_url=URL)
    engine = create_database_engine(settings)
    assert engine.dialect.driver == "psycopg"
    assert engine.hide_parameters
    engine.dispose()
    with pytest.raises(ValueError, match="somente leitura"):
        create_database_engine(settings, public=True, readonly=False)


@pytest.mark.parametrize("value", ["0", "-1", "oops", "121"])
def test_timeout_bounds(tmp_path, value):
    with pytest.raises(ConfigurationError):
        load_settings(tmp_path / "missing", {"DB_CONNECT_TIMEOUT": value})


def test_no_credentials_needed_for_offline_configuration(tmp_path):
    settings = load_settings(tmp_path / "missing", {})
    assert settings.database_url is None
    assert isinstance(settings.outputs_dir, Path)
