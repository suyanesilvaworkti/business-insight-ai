"""Validação e limpeza dos dados.

Recebe a tabela bruta + o mapeamento de colunas e devolve:
- um DataFrame limpo, com os nomes e tipos canônicos;
- um ValidationReport dizendo, de forma transparente, o que foi encontrado,
  o que foi descartado e quais análises ficam indisponíveis.

Princípio: nunca corrigir dados em silêncio. Tudo que é descartado ou
suspeito vira uma mensagem no relatório.
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field

import pandas as pd

from .schema import COLUMNS, COLUMNS_BY_NAME, REQUIRED_COLUMNS

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
MISSING_TEXT = "Não informado"
MIN_HISTORY_DAYS = 60


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    rows_in: int = 0
    rows_out: int = 0
    date_min: pd.Timestamp | None = None
    date_max: pd.Timestamp | None = None
    available_columns: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_dates(series: pd.Series) -> pd.Series:
    """Converte para datas aceitando ISO (aaaa-mm-dd) e formato brasileiro (dd/mm/aaaa)."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    text = series.astype(str).str.strip()
    sample = text[series.notna()].head(200)
    if len(sample) and sample.str.match(ISO_DATE).all():
        return pd.to_datetime(text, format="ISO8601", errors="coerce")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(text, dayfirst=True, errors="coerce")


def to_number(series: pd.Series) -> pd.Series:
    """Converte para número aceitando '1.234,56', 'R$ 99,90' e '99.90'.

    Limitação conhecida: '1.234' (só ponto) é lido como 1,234 (decimal), não
    como mil duzentos e trinta e quatro.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    s = series.astype(str).str.strip().str.replace(r"[R$\s]", "", regex=True)
    has_both = s.str.contains(".", regex=False) & s.str.contains(",", regex=False)
    s = s.where(~has_both, s.str.replace(".", "", regex=False))
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def apply_mapping_and_validate(
    raw: pd.DataFrame, mapping: dict[str, str | None]
) -> tuple[pd.DataFrame | None, ValidationReport]:
    """Aplica o mapeamento, converte tipos e valida. Retorna (df | None, relatório)."""
    report = ValidationReport(rows_in=len(raw))

    if raw.empty:
        report.errors.append("A planilha não tem linhas de dados.")
        return None, report

    for name in REQUIRED_COLUMNS:
        source = mapping.get(name)
        if not source or source not in raw.columns:
            report.errors.append(
                f"A coluna obrigatória '{COLUMNS_BY_NAME[name].label}' não foi mapeada."
            )

    chosen = [s for n, s in mapping.items() if s and n in COLUMNS_BY_NAME]
    repeated = sorted({s for s in chosen if chosen.count(s) > 1})
    for source in repeated:
        report.errors.append(
            f"A coluna '{source}' foi usada para mais de um campo. Cada coluna só pode ter um uso."
        )

    if report.errors:
        return None, report

    df = pd.DataFrame(
        {n: raw[s] for n, s in mapping.items() if s and n in COLUMNS_BY_NAME and s in raw.columns}
    )

    for name in df.columns:
        kind = COLUMNS_BY_NAME[name].kind
        if kind == "date":
            df[name] = parse_dates(df[name]).dt.normalize()
        elif kind == "number":
            df[name] = to_number(df[name])
        else:
            df[name] = df[name].astype("string").str.strip().replace("", pd.NA)

    # --- linhas inutilizáveis: sem data ou sem valor ---------------------------------
    invalid = df["data"].isna() | df["valor_total"].isna()
    n_invalid = int(invalid.sum())
    if n_invalid:
        pct = n_invalid / len(df) * 100
        report.warnings.append(
            f"{n_invalid} linha(s) ({pct:.1f}%) foram descartadas por data ou valor total "
            "ausente/inválido."
        )
        df = df.loc[~invalid]

    if df.empty:
        report.errors.append(
            "Nenhuma linha válida após a limpeza. Confira se as colunas de data e valor "
            "foram mapeadas corretamente."
        )
        return None, report

    # --- textos vazios viram 'Não informado' (para não sumirem em agrupamentos) ---------
    for name in df.columns:
        if COLUMNS_BY_NAME[name].kind == "text":
            n_missing = int(df[name].isna().sum())
            if n_missing:
                label = COLUMNS_BY_NAME[name].label
                report.warnings.append(
                    f"{n_missing} linha(s) sem '{label}'; agrupadas como '{MISSING_TEXT}'."
                )
            df[name] = df[name].fillna(MISSING_TEXT).astype(str)

    # --- números opcionais com muitos vazios --------------------------------------------
    for name in df.columns:
        spec = COLUMNS_BY_NAME[name]
        if spec.kind == "number" and name != "valor_total":
            pct_null = df[name].isna().mean() * 100
            if pct_null > 0:
                report.warnings.append(
                    f"{pct_null:.1f}% dos valores de '{spec.label}' estão vazios ou inválidos."
                )

    # --- sinais de dado suspeito ---------------------------------------------------------
    n_negative = int((df["valor_total"] < 0).sum())
    if n_negative:
        report.warnings.append(
            f"{n_negative} linha(s) com valor total negativo (devoluções/estornos?). "
            "Foram mantidas."
        )

    n_dupes = int(df.duplicated().sum())
    if n_dupes:
        report.warnings.append(
            f"{n_dupes} linha(s) totalmente duplicadas. Foram mantidas; confirme se não é "
            "erro de exportação."
        )

    if "desconto" in df.columns and df["desconto"].max() > 1:
        report.warnings.append(
            "Há valores de 'desconto' acima de 1. O sistema espera fração (0,10 = 10%); "
            "confirme o formato antes de analisar descontos."
        )

    # --- período e histórico -------------------------------------------------------------
    df = df.sort_values("data").reset_index(drop=True)
    report.date_min, report.date_max = df["data"].min(), df["data"].max()
    span_days = (report.date_max - report.date_min).days + 1
    if span_days < MIN_HISTORY_DAYS:
        report.warnings.append(
            f"Histórico curto ({span_days} dias). Comparações, tendências e anomalias terão "
            "pouca confiabilidade."
        )

    # --- análises indisponíveis por falta de coluna -------------------------------------
    missing_optional = [c.label for c in COLUMNS if not c.required and c.name not in df.columns]
    if missing_optional:
        report.infos.append(
            "Colunas opcionais não mapeadas: " + ", ".join(missing_optional) + ". "
            "As análises que dependem delas ficarão indisponíveis."
        )

    report.rows_out = len(df)
    report.available_columns = list(df.columns)
    return df, report
