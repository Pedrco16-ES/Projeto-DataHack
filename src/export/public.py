"""Exportação somente dos quadros públicos já protegidos pelo construtor."""

from io import BytesIO
import pandas as pd

from src.export.administrative import csv_bytes, spreadsheet_safe


def public_xlsx(frame, metadata):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        spreadsheet_safe(frame).to_excel(writer, sheet_name="Resultados públicos", index=False)
        spreadsheet_safe(pd.DataFrame({"Campo": list(metadata), "Descrição": [str(v) for v in metadata.values()]})).to_excel(
            writer, sheet_name="Metodologia", index=False)
    return output.getvalue()


def public_csv(frame, metadata):
    out = frame.copy()
    for key, value in metadata.items():
        out["meta_" + key] = str(value)
    return csv_bytes(out)
