"""SQLAlchemy com psycopg 3, TLS e leitura por padrao."""

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError

from src.config import Settings, load_settings


class DatabaseUnavailable(RuntimeError):
    """Erro seguro: nao propaga mensagens do driver com dados de conexao."""


def create_database_engine(
    settings: Settings | None = None, *, public: bool = False, readonly: bool = True
) -> Engine:
    settings = settings or load_settings()
    url = make_url(settings.require_database_url(public=public))
    if public and not readonly:
        raise ValueError("A conexao publica deve ser somente leitura.")
    engine = create_engine(
        url,
        connect_args={
            "sslmode": url.query.get("sslmode", "require"),
            "connect_timeout": settings.connect_timeout,
            "options": f"-c statement_timeout={settings.statement_timeout_ms}",
        },
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=1,
        hide_parameters=True,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def set_readonly(dbapi_connection, connection_record):
        dbapi_connection.read_only = readonly

    return engine


def check_connection(settings: Settings | None = None, *, public: bool = False) -> bool:
    engine = create_database_engine(settings, public=public)
    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT 1")).scalar_one() != 1:
                raise DatabaseUnavailable("Resposta inesperada do banco.")
            if not conn.connection.driver_connection.pgconn.ssl_in_use:
                raise DatabaseUnavailable("Conexao sem TLS rejeitada.")
        return True
    except SQLAlchemyError:
        raise DatabaseUnavailable(
            "Nao foi possivel conectar. Confira rede e configuracao local; detalhes protegidos."
        ) from None
    finally:
        engine.dispose()
