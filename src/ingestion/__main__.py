"""python -m src.ingestion: diagnóstico e processamento local."""

import argparse
import json
from pathlib import Path

from src.ingestion.pipeline import process_file
from src.ingestion.readers import preview
from src.ingestion.schema import load_contract, validate_mapping, IngestionError


def main():
    parser = argparse.ArgumentParser(description="Trata fontes INEP localmente; não grava no banco.")
    parser.add_argument("action", choices=["preview", "process"])
    parser.add_argument("file", type=Path)
    parser.add_argument("--source", required=True, choices=["trajetoria", "censo_curso"])
    parser.add_argument("--edition", required=True, type=int)
    parser.add_argument("--chunksize", type=int, default=25000)
    parser.add_argument("--member")
    parser.add_argument("--sheet")
    parser.add_argument("--encoding")
    parser.add_argument("--separator")
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--confirm-mapping", action="store_true")
    parser.add_argument("--mapping-reason", default="")
    args = parser.parse_args()
    try:
        mapping = json.loads(args.mapping.read_text(encoding="utf-8")) if args.mapping else None
        mapping = validate_mapping(mapping, args.confirm_mapping, args.mapping_reason)
        if args.action == "preview":
            if args.encoding or args.separator:
                raise IngestionError("A prévia usa detecção automática; --encoding e --separator são opções de process.")
            frame, layout = preview(args.file, load_contract(args.source, args.edition), mapping=mapping,
                                    member=args.member, sheet=args.sheet)
            # CLI retorna metadados; amostra detalhada disponível na interface administrativa.
            print(json.dumps({"layout": layout, "sample_rows": len(frame), "columns": frame.columns.tolist()}, ensure_ascii=False))
        else:
            result = process_file(args.file, args.source, args.edition, chunksize=args.chunksize,
                                  member=args.member, sheet=args.sheet, encoding=args.encoding, separator=args.separator,
                                  mapping=mapping, confirm_mapping=args.confirm_mapping, mapping_reason=args.mapping_reason)
            print(json.dumps({k: result[k] for k in ["batch_id", "batch_dir", "counts", "status", "reused"]}, ensure_ascii=False))
        return 0
    except Exception as error:
        # Os erros de bibliotecas podem conter valores da origem. Nunca despejar traceback de dados.
        print(str(error) if isinstance(error, IngestionError) else "Falha na leitura. Confira formato, acesso e arquivo; conteúdo não exibido.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
