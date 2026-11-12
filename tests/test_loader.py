import io

import pandas as pd
import pytest

from business_insight.data.loader import LoaderError, load_table


def test_loads_semicolon_latin1_csv_as_text():
    content = "Data;Descrição;Valor\n05/01/2025;Café;1.234,56\n".encode("latin-1")
    df = load_table(content, "vendas.csv")
    assert list(df.columns) == ["Data", "Descrição", "Valor"]
    assert df.iloc[0]["Valor"] == "1.234,56"
    assert df.iloc[0]["Descrição"] == "Café"


def test_loads_comma_csv_utf8():
    df = load_table("a,b\n1,2\n".encode("utf-8"), "x.csv")
    assert list(df.columns) == ["a", "b"]


def test_loads_xlsx():
    buffer = io.BytesIO()
    pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).to_excel(buffer, index=False)
    df = load_table(buffer.getvalue(), "x.xlsx")
    assert len(df) == 2


def test_rejects_unsupported_format():
    with pytest.raises(LoaderError):
        load_table(b"abc", "x.txt")


def test_rejects_empty_file():
    with pytest.raises(LoaderError):
        load_table(b"", "x.csv")


def test_rejects_header_only_csv():
    with pytest.raises(LoaderError):
        load_table(b"a,b\n", "x.csv")
