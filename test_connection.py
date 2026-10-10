from src.config import ConfigurationError
from src.database.connection import DatabaseUnavailable, check_connection


def main():
    try:
        check_connection()
    except (ConfigurationError, DatabaseUnavailable) as exc:
        print(str(exc))
        return 1
    print("Conexão OK: 1 (TLS ativo; somente leitura)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
