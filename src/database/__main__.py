"""Plano por padrão; alterações exigem confirmação do hash revisado."""

import argparse
import json
from pathlib import Path

from src.database.connection import create_database_engine
from src.database.persistence import make_plan, verify_plan, migrate, apply_plan, withdraw_batches, PersistenceError
from src.ingestion.pipeline import sha256


def main():
    parser = argparse.ArgumentParser(description="Planeja e executa persistência privada de lotes revisados.")
    commands = parser.add_subparsers(dest="action", required=True)
    plan_cmd = commands.add_parser("plan", help="Revalida arquivos e gera plano local; não conecta ao banco")
    plan_cmd.add_argument("--inventory", type=Path, required=True)
    plan_cmd.add_argument("--output", type=Path, required=True)
    apply_cmd = commands.add_parser("apply", help="Cria schemas novos e carrega o plano autorizado")
    apply_cmd.add_argument("--plan", type=Path, required=True)
    apply_cmd.add_argument("--approve-plan", required=True, help="SHA-256 exato do plano revisado")
    withdraw = commands.add_parser("withdraw", help="Retira lotes das views atuais, preservando histórico")
    withdraw.add_argument("--plan", type=Path, required=True)
    withdraw.add_argument("--approve-plan", required=True)
    withdraw.add_argument("--reason", required=True)
    args = parser.parse_args()
    engine = None
    try:
        if args.action == "plan":
            inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
            result = make_plan([Path(item["batch_dir"]) for item in inventory])
            # Evita sobrescrever uma decisão anterior sem revisão.
            with args.output.open("x", encoding="utf-8") as file:
                json.dump(result, file, ensure_ascii=False, indent=2)
                file.write("\n")
            print(json.dumps({"plan_sha256": sha256(args.output), "rows": result["total_rows"], "batches": len(result["batches"])}, ensure_ascii=False))
            return 0
        if sha256(args.plan) != args.approve_plan:
            raise PersistenceError("Hash autorizado não corresponde ao arquivo do plano.")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if args.action == "apply":
            verify_plan(plan)
        engine = create_database_engine(readonly=False)
        if args.action == "apply":
            migrated = migrate(engine)
            result = apply_plan(engine, plan)
            print(json.dumps({"migration_created": migrated, "batches": result, "public_approved": False}, ensure_ascii=False))
        else:
            changed = withdraw_batches(engine, [item["batch_id"] for item in plan["batches"]], args.reason)
            print(json.dumps({"withdrawn": changed, "history_preserved": True}))
        return 0
    except Exception as error:
        print(str(error) if isinstance(error, PersistenceError) else "Falha na persistência. Transação da operação revertida; detalhes protegidos. Consulte o estado da migration antes de repetir.")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
