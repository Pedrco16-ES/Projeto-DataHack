"""Configuracao local: caminhos estaveis e erros sem credenciais."""

from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Mapping
import logging
import os

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(ValueError):
    """Configuracao ausente ou invalida, com mensagem publica segura."""


def validate_database_url(value: str, name: str) -> str:
    try:
        url = make_url(value)
        if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
            raise ValueError
        if not url.host or not url.username or not url.database:
            raise ValueError
        if url.port is not None and not 1 <= url.port <= 65535:
            raise ValueError
        if url.query.get("sslmode", "require") not in {"require", "verify-ca", "verify-full"}:
            raise ValueError
        # Evita opcoes de conexao arbitrarias em URLs de configuracao.
        if set(url.query) - {"sslmode", "sslrootcert"}:
            raise ValueError
    except Exception:
        raise ConfigurationError(
            f"{name}: use uma URL PostgreSQL valida, com TLS e credenciais locais."
        ) from None
    return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


@dataclass(frozen=True)
class Settings:
    database_url: str | None = field(default=None, repr=False)
    public_database_url: str | None = field(default=None, repr=False)
    data_dir: Path = PROJECT_ROOT.parent / "Dados"
    outputs_dir: Path = PROJECT_ROOT / "outputs"
    connect_timeout: int = 10
    statement_timeout_ms: int = 15000

    def require_database_url(self, *, public: bool = False) -> str:
        value = self.public_database_url if public else self.database_url
        name = "PUBLIC_DATABASE_URL" if public else "DATABASE_URL"
        if not value:
            raise ConfigurationError(f"{name} nao configurada.")
        return validate_database_url(value, name)


def load_settings(
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    # O parser dotenv pode registrar linhas invalidas contendo segredos.
    # O log fica bloqueado apenas durante a leitura da configuracao.
    logger = logging.getLogger("dotenv.main")
    disabled = logger.disabled
    logger.disabled = True
    try:
        values = dict(dotenv_values(env_file or PROJECT_ROOT / ".env.local", interpolate=False))
    finally:
        logger.disabled = disabled
    values.update(os.environ if environ is None else environ)

    def path_value(name: str, default: str) -> Path:
        path = Path(values.get(name) or default).expanduser()
        return (PROJECT_ROOT / path).resolve() if not path.is_absolute() else path.resolve()

    def integer(name: str, default: int, maximum: int) -> int:
        try:
            value = int(values.get(name) or default)
            if not 1 <= value <= maximum:
                raise ValueError
            return value
        except (TypeError, ValueError):
            raise ConfigurationError(f"{name} deve estar entre 1 e {maximum}.") from None

    return Settings(
        database_url=values.get("DATABASE_URL") or None,
        public_database_url=values.get("PUBLIC_DATABASE_URL") or None,
        data_dir=path_value("DATA_DIR", "../Dados"),
        outputs_dir=path_value("OUTPUTS_DIR", "outputs"),
        connect_timeout=integer("DB_CONNECT_TIMEOUT", 10, 120),
        statement_timeout_ms=integer("DB_STATEMENT_TIMEOUT_MS", 15000, 300000),
    )
