"""Downloads locais; não substituem supressão para publicação."""

from io import BytesIO
import pandas as pd


def spreadsheet_safe(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result:
        if pd.api.types.is_string_dtype(result[column]) or result[column].dtype == object:
            result[column] = result[column].map(
                lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
            )
    return result


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return spreadsheet_safe(frame).to_csv(index=False).encode("utf-8-sig")


def xlsx_bytes(frame: pd.DataFrame) -> bytes:
    if len(frame) > 1_048_575:
        raise ValueError("Planilha acima do limite XLSX; utilize CSV.")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        spreadsheet_safe(frame).to_excel(writer, sheet_name="Dados administrativos", index=False)
    return output.getvalue()
