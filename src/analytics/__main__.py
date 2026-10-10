"""CLI local: não aplica migrations nem grava no Supabase."""

import argparse
import json
from pathlib import Path

from src.analytics.build import build, digest
from src.analytics.metrics import AnalyticsError
from src.analytics.snapshots import write_snapshot
from src.config import PROJECT_ROOT, load_settings


def main():
    parser = argparse.ArgumentParser(description="Constrói indicadores reais e snapshot protegido do MVP.")
    parser.add_argument("--plan", type=Path, default=PROJECT_ROOT / "data/processed/stage4_plan.json")
    parser.add_argument("--cpc-year", type=int, default=2023)
    parser.add_argument("--approve-local", metavar="JUSTIFICATIVA", help="Aprova somente o snapshot local após validação técnica.")
    args = parser.parse_args()
    try:
        settings = load_settings()
        payload = build(args.plan, settings.data_dir, args.cpc_year)
        if args.approve_local:
            checksum = write_snapshot(payload, settings.outputs_dir / "public_snapshot.json", args.approve_local)
            print("Snapshot local protegido gerado. SHA-256:", checksum)
        else:
            path = PROJECT_ROOT / "data/processed/analytics_candidate.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
            print("Candidato administrativo gerado; aprovação local pendente. SHA-256:", digest(payload))
        print("Cobertura de cursos:", payload["coverage"])
        print("Integrados: seis coortes no horizonte comum, Enade 2025, evasão estadual e mapa municipal 2022.")
        print("Limite: associação financiamento–evasão exige desagregação compatível.")
    except (AnalyticsError, OSError, ValueError, KeyError) as error:
        # Sem tracebacks de bibliotecas nem conteúdo de linhas de entrada.
        message = str(error) if isinstance(error, AnalyticsError) else "Falha de leitura ou layout. Confira os arquivos e contratos locais."
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
