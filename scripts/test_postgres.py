"""PostgreSQL temporário em loopback; nunca lê DATABASE_URL ou .env.local.

Requer binários PostgreSQL locais. Mantém arquivos de diagnóstico ignorados no Git
e encerra somente a instância criada por esta execução, mesmo se os testes falharem.
"""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import uuid

from sqlalchemy import create_engine, text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-bin", type=Path, default=Path("C:/Program Files/PostgreSQL/18/bin"))
    parser.add_argument("--real-plan", type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    folder = project / "data/processed" / ("pg-test-" + uuid.uuid4().hex[:12])
    folder.mkdir(parents=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    suffix = ".exe" if os.name == "nt" else ""
    initdb = args.pg_bin / ("initdb" + suffix)
    pgctl = args.pg_bin / ("pg_ctl" + suffix)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    def command(*parts):
        # No Windows, processos descendentes podem manter pipes capturados abertos.
        # Arquivo de log + stdin fechado permite aguardar apenas o controlador.
        with (folder / "commands.log").open("ab") as log:
            result = subprocess.run([str(p) for p in parts], stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, creationflags=flags, timeout=120)
        if result.returncode:
            raise RuntimeError("Comando PostgreSQL falhou; consulte o log local de testes.")
    data = folder / "cluster"
    command(initdb, "-D", data, "--username=rota_test", "--auth=trust", "--encoding=UTF8", "--no-locale")
    # Trust é exclusivo deste cluster de testes sem credenciais reais e limitado a loopback.
    with (data / "postgresql.conf").open("a", encoding="utf-8") as file:
        file.write(f"\nlisten_addresses = '127.0.0.1'\nport = {port}\nssl = off\n")
    started = False
    try:
        command(pgctl, "-D", data, "-l", folder / "postgres.log", "-w", "start")
        started = True
        url = f"postgresql+psycopg://rota_test@127.0.0.1:{port}/rota_stage4_test"
        engine = create_engine(url.replace("/rota_stage4_test", "/postgres"), isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text("CREATE DATABASE rota_stage4_test"))
        engine.dispose()
        env = {**os.environ, "ROTA_TEST_DATABASE_URL": url}
        log_path = folder / "pytest.log"
        with log_path.open("wb") as log:
            result = subprocess.run([sys.executable, "-m", "pytest", "-q", "--junitxml=" + str(folder / "pytest.xml")],
                                    cwd=project, env=env, creationflags=flags, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL)
        print(log_path.read_text(encoding="utf-8", errors="replace")[-5000:], flush=True)
        if result.returncode:
            return result.returncode
        if args.real_plan:
            # Só resultados administrativos do plano indicado; nenhuma conexão externa.
            sys.path.insert(0, str(project))
            from src.database.persistence import migrate, apply_plan, withdraw_batches
            engine = create_engine(url, hide_parameters=True)
            try:
                plan = json.loads(args.real_plan.read_text(encoding="utf-8"))
                migrate(engine)
                first = apply_plan(engine, plan)
                second = apply_plan(engine, plan)
                assert all(item["status"] == "loaded" for item in first)
                assert all(item["status"] == "reused" for item in second)
                with engine.connect() as conn:
                    totals = {name: conn.execute(text(f"SELECT count(*) FROM staging.{name}_atual")).scalar_one() for name in ["trajetoria", "censo_curso"]}
                    assert sum(totals.values()) == plan["total_rows"]
                changed = withdraw_batches(engine, [item["batch_id"] for item in plan["batches"]], "Reversão do ensaio local da Etapa 4")
                with engine.connect() as conn:
                    assert conn.execute(text("SELECT count(*) FROM meta.importacoes WHERE status='loaded'")).scalar_one() == 0
                    assert conn.execute(text("SELECT count(*) FROM staging.trajetoria_atual")).scalar_one() == 0
                    assert conn.execute(text("SELECT count(*) FROM staging.censo_curso_atual")).scalar_one() == 0
                summary = {"loaded": first, "repeated": second, "totals": totals, "withdrawn": changed, "supabase_modified": False}
                (folder / "real_plan_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
                print(json.dumps(summary), flush=True)
            finally:
                engine.dispose()
        print("Testes locais concluídos. Instância temporária será encerrada.", flush=True)
        return 0
    finally:
        if started:
            command(pgctl, "-D", data, "-m", "fast", "-w", "stop")
        print("Diagnóstico local:", folder, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
