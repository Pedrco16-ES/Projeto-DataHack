from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import OperationalError

from src.database import connection


def test_database_failure_is_sanitized_and_pool_disposed(monkeypatch):
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("secret SQL", {}, Exception("secret password"))
    monkeypatch.setattr(connection, "create_database_engine", lambda *a, **k: engine)
    with pytest.raises(connection.DatabaseUnavailable) as exc:
        connection.check_connection()
    assert "secret" not in str(exc.value)
    engine.dispose.assert_called_once()


def test_tls_required_and_pool_disposed(monkeypatch):
    engine = MagicMock()
    conn = engine.connect.return_value.__enter__.return_value
    conn.execute.return_value.scalar_one.return_value = 1
    conn.connection.driver_connection = SimpleNamespace(pgconn=SimpleNamespace(ssl_in_use=False))
    monkeypatch.setattr(connection, "create_database_engine", lambda *a, **k: engine)
    with pytest.raises(connection.DatabaseUnavailable, match="TLS"):
        connection.check_connection()
    engine.dispose.assert_called_once()
