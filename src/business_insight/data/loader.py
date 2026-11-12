"""Leitura de planilhas CSV e Excel.

Cuidados pensados para dados reais de empresas brasileiras:
- CSV costuma usar ';' como separador e vírgula como decimal;
- encoding pode ser UTF-8 ou Windows-1252 (Excel em português);
- lemos tudo como TEXTO no CSV e deixamos a conversão para o validador,
  que sabe lidar com '1.234,56' e datas dd/mm/aaaa.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

SUPPORTED_SUFFIXES = {".csv", ".xlsx"}
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


class LoaderError(Exception):
    """Erro de leitura com mensagem pensada para o usuário final."""


def _read_bytes(source, filename: str | None) -> tuple[bytes, str | None]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        return path.read_bytes(), filename or path.name
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), filename
    if hasattr(source, "read"):
        return source.read(), filename or getattr(source, "name", None)
    raise LoaderError("Fonte de dados inválida.")


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")  # nunca falha


def _detect_separator(text: str) -> str:
    """Escolhe o separador mais frequente na linha de cabeçalho."""
    header = text.splitlines()[0] if text else ""
    counts = {sep: header.count(sep) for sep in (",", ";", "\t", "|")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_table(source, filename: str | None = None) -> pd.DataFrame:
    """Lê CSV/XLSX (caminho, bytes ou arquivo) e devolve um DataFrame bruto."""
    data, name = _read_bytes(source, filename)
    if not data:
        raise LoaderError("O arquivo está vazio.")
    if len(data) > MAX_BYTES:
        raise LoaderError("Arquivo muito grande (limite de 50 MB).")

    suffix = Path(name).suffix.lower() if name else ""
    if suffix not in SUPPORTED_SUFFIXES:
        raise LoaderError(
            f"Formato '{suffix or 'desconhecido'}' não suportado. Use CSV ou XLSX."
        )

    try:
        if suffix == ".csv":
            text = _decode(data)
            df = pd.read_csv(io.StringIO(text), sep=_detect_separator(text),
                             dtype=str, skipinitialspace=True)
        else:
            df = pd.read_excel(io.BytesIO(data), engine="openpyxl")
    except Exception as exc:  # pandas/openpyxl lançam vários tipos de erro
        raise LoaderError(f"Não foi possível ler o arquivo: {exc}") from exc

    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        raise LoaderError("Nenhuma linha de dados encontrada no arquivo.")
    return df.reset_index(drop=True)
