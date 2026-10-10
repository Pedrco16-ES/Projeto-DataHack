"""Leitura limitada a blocos; ZIP nunca é extraído para caminhos da origem."""

from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
import codecs
import csv
import io
import json
import tempfile
import zipfile

import pandas as pd
from openpyxl import load_workbook

from src.ingestion.schema import IngestionError, column_name, resolve_columns

FORMATS = {".csv", ".xlsx", ".json"}


@contextmanager
def materialize(path: Path, member: str | None = None):
    path = Path(path)
    if path.name.startswith("~$") or not path.is_file():
        raise IngestionError("Arquivo inexistente ou temporário de editor.")
    if path.suffix.lower() != ".zip":
        if member:
            raise IngestionError("Seleção de membro só se aplica a ZIP.")
        if path.suffix.lower() not in FORMATS:
            raise IngestionError("Formato não suportado. Use CSV, XLSX, JSON ou ZIP desses formatos.")
        yield path, None
        return
    with zipfile.ZipFile(path) as archive:
        candidates = [n for n in archive.namelist() if Path(n).suffix.lower() in FORMATS and not Path(n).name.startswith("~$")]
        if member is None:
            if len(candidates) != 1:
                raise IngestionError("ZIP deve ter um único arquivo de dados ou um membro explicitamente selecionado.")
            member = candidates[0]
        if member not in candidates:
            raise IngestionError("Membro não encontrado ou formato não suportado no ZIP.")
        normalized = member.replace("\\", "/")
        if PurePosixPath(normalized).is_absolute() or ".." in PurePosixPath(normalized).parts or ":" in normalized:
            raise IngestionError("Caminho inseguro no ZIP.")
        info = archive.getinfo(member)
        if info.file_size > 4_000_000_000 or info.file_size / max(info.compress_size, 1) > 200:
            raise IngestionError("ZIP excede os limites de tamanho ou compressão segura.")
        with tempfile.TemporaryDirectory(prefix="rota_ingestion_") as temp:
            target = Path(temp) / ("source" + Path(member).suffix.lower())
            with archive.open(member) as source, target.open("wb") as output:
                copied = 0
                while block := source.read(1024 * 1024):
                    copied += len(block)
                    if copied > 4_000_000_000:
                        raise IngestionError("Conteúdo ZIP excede o limite de tamanho.")
                    output.write(block)
            yield target, member


@dataclass
class Layout:
    format: str
    columns: list[str]
    header: int = 0
    encoding: str | None = None
    separator: str | None = None
    sheet: str | None = None

    def to_dict(self):
        return asdict(self)


def detect_layout(path: Path, contract: dict, mapping=None, sheet=None, encoding=None, separator=None) -> Layout:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("rb") as source:
            sample = source.read(65536)
        if encoding is None:
            try:
                codecs.getincrementaldecoder("utf-8-sig")().decode(sample, final=False)
                encoding = "utf-8-sig"
            except UnicodeDecodeError:
                encoding = "latin-1"
        decoded = codecs.getincrementaldecoder(encoding)().decode(sample, final=False)
        if separator is None:
            # Cabeçalho técnico define o delimitador, não os textos de apresentação.
            candidates = [line for line in decoded.splitlines()[:20] if "CO_" in line.upper()]
            line = candidates[0] if candidates else decoded.splitlines()[0] if decoded else ""
            separator = max([";", ",", "\t", "|"], key=line.count)
        rows = list(csv.reader(io.StringIO(decoded), delimiter=separator))[:20]
    elif suffix == ".xlsx":
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            if sheet is None:
                if len(book.sheetnames) != 1:
                    raise IngestionError("Planilha com várias abas: selecione a aba explicitamente.")
                sheet = book.sheetnames[0]
            if sheet not in book.sheetnames:
                raise IngestionError("Aba não encontrada.")
            rows = list(book[sheet].iter_rows(min_row=1, max_row=20, values_only=True))
        finally:
            book.close()
    elif suffix == ".json":
        if path.stat().st_size > 50_000_000:
            raise IngestionError("JSON acima de 50 MB: converta para CSV para processamento em blocos.")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list) or not data or not all(isinstance(r, dict) for r in data):
            raise IngestionError("JSON deve conter uma lista não vazia de objetos tabulares.")
        names = list(dict.fromkeys(k for row in data for k in row))
        return Layout("json", resolve_columns(names, contract, mapping))
    else:
        raise IngestionError("Formato não suportado.")
    for index, row in enumerate(rows):
        normalized = {(mapping or {}).get(column_name(c), column_name(c)) for c in row if c is not None}
        if set(contract["required"]) <= normalized:
            return Layout(suffix[1:], resolve_columns(row, contract, mapping), index, encoding, separator, sheet)
    raise IngestionError("Cabeçalho compatível não encontrado nas primeiras 20 linhas. Confira fonte, edição e mapeamento.")


def read_chunks(path: Path, layout: Layout, chunksize: int = 25000):
    if not 1 <= chunksize <= 100000:
        raise IngestionError("Tamanho do bloco deve estar entre 1 e 100000.")
    if layout.format == "csv":
        with pd.read_csv(path, sep=layout.separator, encoding=layout.encoding, header=layout.header,
                         dtype="string", keep_default_na=False, chunksize=chunksize, on_bad_lines="error") as reader:
            for chunk in reader:
                if not isinstance(chunk.index, pd.RangeIndex):
                    raise IngestionError("Quantidade de campos incompatível com o cabeçalho CSV.")
                chunk.columns = layout.columns
                yield chunk
    elif layout.format == "xlsx":
        # openpyxl faz streaming; pandas transforma e valida cada bloco.
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = book[layout.sheet].iter_rows(min_row=layout.header + 2, values_only=True)
            batch = []
            for row in rows:
                batch.append(row)
                if len(batch) == chunksize:
                    yield pd.DataFrame(batch, columns=layout.columns, dtype=object).astype("string")
                    batch = []
            if batch:
                yield pd.DataFrame(batch, columns=layout.columns, dtype=object).astype("string")
        finally:
            book.close()
    else:
        records = json.loads(path.read_text(encoding="utf-8-sig"))
        data = pd.DataFrame(records, dtype=object).astype("string")
        data.columns = layout.columns
        for start in range(0, len(data), chunksize):
            yield data.iloc[start:start + chunksize].astype("string")


def preview(path: Path, contract: dict, *, mapping=None, member=None, sheet=None) -> tuple[pd.DataFrame, dict]:
    with materialize(Path(path), member) as (actual, selected):
        layout = detect_layout(actual, contract, mapping, sheet)
        if layout.format == "xlsx":
            frame = pd.read_excel(actual, sheet_name=layout.sheet, header=layout.header,
                                  nrows=10, dtype="string", keep_default_na=False)
            frame.columns = layout.columns
        else:
            chunks = read_chunks(actual, layout, 10)
            try:
                frame = next(chunks, pd.DataFrame(columns=layout.columns))
            finally:
                chunks.close()
        return frame, {**layout.to_dict(), "member": selected}
