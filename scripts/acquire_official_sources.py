"""Download reproduzível de fontes complementares oficiais, sem cargas remotas."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data/raw/complementares_20261010"
INEP = "https://download.inep.gov.br/"
IBGE = "https://servicodados.ibge.gov.br/api/"
SOURCES = {
    "enade_licenciaturas_2025.xlsx": INEP + "educacao_superior/indicadores/resultados/2025/conceito_enade_licenciaturas.xlsx",
    "ibge_9514_metadados.json": IBGE + "v3/agregados/9514/metadados",
    "ibge_18_24_municipios_mt_2022.json": IBGE + "v3/agregados/9514/periodos/2022/variaveis/93?" + urlencode({
        "localidades": "N6[N3[51]]", "classificacao": "2[6794]|287[6575,6576,6577,6578,6579,6580,6581]|286[113635]"}),
    "ibge_municipios_mt_atual.json": IBGE + "v1/localidades/estados/51/municipios",
    "ibge_malha_mt_2022.geojson": IBGE + "v3/malhas/estados/51?" + urlencode({
        "formato": "application/vnd.geo+json", "qualidade": "minima", "intrarregiao": "municipio", "periodo": "2022"}),
    "metodologia_trajetoria_2017.pdf": INEP + "informacoes_estatisticas/indicadores_educacionais/2017/metodologia_indicadores_trajetoria_curso.pdf",
    "apresentacao_censo_2024.pdf": INEP + "educacao_superior/censo_superior/documentos/2024/apresentacao_censo_da_educacao_superior_2024.pdf",
    "enade_pnd_resultados_2025.pdf": INEP + "educacao_superior/enade/pnd_e_enade_2025_cursos.pdf",
    "fluxo_uf_2010_2024.zip": INEP + "informacoes_estatisticas/indicadores_educacionais/indicadores_fluxo_UF_2010_2024.zip",
}
for year in range(2016, 2021):
    SOURCES[f"trajetoria_{year}_2024.zip"] = INEP + f"informacoes_estatisticas/indicadores_educacionais/indicadores_trajetoria_es_{year}_2024.zip"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(name, url, previous):
    target = DESTINATION / name
    if target.exists():
        entry = previous.get(name)
        if not entry or entry["url"] != url or entry["sha256"] != sha(target):
            raise ValueError("Arquivo existente sem proveniência compatível: " + name)
        return name, entry, "reused"
    request = Request(url, headers={"User-Agent": "RotaDiploma/1.0 academic-data-validation", "Accept-Encoding": "identity"})
    temporary = target.with_suffix(target.suffix + ".part")
    if sys.platform == "win32" and urlparse(url).hostname == "download.inep.gov.br":
        # INEP não entrega toda a cadeia intermediária a OpenSSL. Schannel do
        # Windows resolve a cadeia mantendo validação de TLS e hostname ativa.
        # URL/caminho são dados via ambiente, não interpolados em código shell.
        script = '''$ErrorActionPreference='Stop'
        [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
        $head = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $env:ROTA_SOURCE_URL -TimeoutSec 45
        if ([long]$head.Headers['Content-Length'] -gt 700000000) { throw 'Arquivo acima do limite' }
        $reply = Invoke-WebRequest -UseBasicParsing -Uri $env:ROTA_SOURCE_URL -OutFile $env:ROTA_SOURCE_TARGET -PassThru -TimeoutSec 180
        @{url=$reply.BaseResponse.ResponseUri.AbsoluteUri;headers=@{'Content-Type'=$reply.Headers['Content-Type'];'Last-Modified'=$reply.Headers['Last-Modified'];ETag=$reply.Headers['ETag']}} | ConvertTo-Json -Compress
        '''
        env = {**os.environ, "ROTA_SOURCE_URL": url, "ROTA_SOURCE_TARGET": str(temporary)}
        completed = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                                   env=env, capture_output=True, text=True, encoding="utf-8", timeout=230,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if completed.returncode:
            raise ValueError("Download HTTPS nativo falhou: " + name)
        native = json.loads(completed.stdout.lstrip("\ufeff"))
        final_url, headers = native["url"], native["headers"]
    else:
        with urlopen(request, timeout=45) as response, temporary.open("wb") as output:
            final_url = response.geturl()
            total = 0
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > 700_000_000:
                    raise ValueError("Download excede limite de 700 MB.")
                output.write(block)
            headers = {key: response.headers.get(key) for key in ["Content-Type", "Last-Modified", "ETag"]}
    if urlparse(final_url).hostname not in {"download.inep.gov.br", "servicodados.ibge.gov.br", "apisidra.ibge.gov.br", "geoftp.ibge.gov.br"}:
        raise ValueError("Redirecionamento para domínio não autorizado.")
    # Alguns endpoints IBGE enviam gzip mesmo quando se pede identity.
    with temporary.open("rb") as stream:
        signature = stream.read(8)
    if signature[:2] == b"\x1f\x8b":
        temporary.write_bytes(gzip.decompress(temporary.read_bytes()))
    if target.suffix in {".json", ".geojson"}:
        obj = json.loads(temporary.read_text(encoding="utf-8-sig"))
        if not isinstance(obj, (dict, list)) or (isinstance(obj, dict) and "erro" in obj):
            raise ValueError("Resposta JSON incompatível.")
    elif target.suffix in {".xlsx", ".zip"}:
        if not zipfile.is_zipfile(temporary):
            raise ValueError("Resposta não é XLSX/ZIP.")
    elif target.suffix == ".pdf" and not signature.startswith(b"%PDF"):
        raise ValueError("Resposta não é PDF.")
    temporary.replace(target)
    return name, {"url": url, "resolved_url": final_url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                  "sha256": sha(target), "bytes": target.stat().st_size, "headers": headers}, "downloaded"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", choices=list(SOURCES))
    args = parser.parse_args()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest_path = DESTINATION / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": {}}
    selected = args.only or list(SOURCES)
    failures = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(download, name, SOURCES[name], manifest["files"]): name for name in selected}
        for future in as_completed(jobs):
            name = jobs[future]
            try:
                name, entry, status = future.result()
                manifest["files"][name] = entry
                tmp = manifest_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(manifest_path)
                print(name, status, entry["bytes"], "bytes", flush=True)
            except Exception as error:
                failures.append(name)
                print(name, "FAILED", type(error).__name__, flush=True)
    if failures:
        print("Fontes pendentes:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
