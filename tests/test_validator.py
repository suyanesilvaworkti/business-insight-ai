import pandas as pd

from business_insight.data.validator import apply_mapping_and_validate

MAPPING = {"data": "d", "pedido_id": "p", "valor_total": "v"}


def test_parses_brazilian_numbers_and_dates():
    raw = pd.DataFrame({"d": ["05/01/2025", "06/01/2025"], "p": ["1", "2"],
                        "v": ["1.234,56", "R$ 99,90"]})
    df, report = apply_mapping_and_validate(raw, MAPPING)
    assert report.ok
    assert df["valor_total"].tolist() == [1234.56, 99.9]
    assert df["data"].iloc[0] == pd.Timestamp("2025-01-05")


def test_parses_iso_dates():
    raw = pd.DataFrame({"d": ["2025-03-01", "2025-03-02"], "p": ["1", "2"], "v": ["10", "20"]})
    df, report = apply_mapping_and_validate(raw, MAPPING)
    assert report.ok
    assert df["data"].iloc[1] == pd.Timestamp("2025-03-02")


def test_drops_invalid_rows_and_reports_it():
    raw = pd.DataFrame({"d": ["2025-03-01", "lixo", "2025-03-03"], "p": ["1", "2", "3"],
                        "v": ["10", "20", "abc"]})
    df, report = apply_mapping_and_validate(raw, MAPPING)
    assert len(df) == 1
    assert report.rows_in == 3 and report.rows_out == 1
    assert any("descartadas" in w for w in report.warnings)


def test_missing_required_column_is_an_error():
    raw = pd.DataFrame({"d": ["2025-03-01"], "p": ["1"], "v": ["10"]})
    df, report = apply_mapping_and_validate(raw, {"data": "d", "pedido_id": "p", "valor_total": None})
    assert df is None
    assert not report.ok


def test_same_source_column_used_twice_is_an_error():
    raw = pd.DataFrame({"d": ["2025-03-01"], "v": ["10"]})
    df, report = apply_mapping_and_validate(raw, {"data": "d", "pedido_id": "v", "valor_total": "v"})
    assert df is None
    assert any("mais de um campo" in e for e in report.errors)


def test_negative_values_are_kept_but_flagged():
    raw = pd.DataFrame({"d": ["2025-03-01", "2025-03-02"], "p": ["1", "2"], "v": ["10", "-5"]})
    df, report = apply_mapping_and_validate(raw, MAPPING)
    assert len(df) == 2
    assert any("negativo" in w for w in report.warnings)


def test_short_history_is_flagged():
    raw = pd.DataFrame({"d": ["2025-03-01", "2025-03-10"], "p": ["1", "2"], "v": ["10", "20"]})
    _, report = apply_mapping_and_validate(raw, MAPPING)
    assert any("Histórico curto" in w for w in report.warnings)


def test_missing_text_becomes_nao_informado():
    mapping = {**MAPPING, "produto": "prod"}
    raw = pd.DataFrame({"d": ["2025-03-01", "2025-03-02"], "p": ["1", "2"], "v": ["10", "20"],
                        "prod": ["A", None]})
    df, report = apply_mapping_and_validate(raw, mapping)
    assert df["produto"].tolist() == ["A", "Não informado"]
    assert any("sem 'Produto'" in w for w in report.warnings)


def test_reports_unavailable_optional_columns():
    raw = pd.DataFrame({"d": ["2025-03-01"], "p": ["1"], "v": ["10"]})
    _, report = apply_mapping_and_validate(raw, MAPPING)
    assert any("indisponíveis" in i for i in report.infos)
