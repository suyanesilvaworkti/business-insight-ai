from business_insight.data.schema import normalize_name, suggest_mapping


def test_normalize_name_removes_accents_and_symbols():
    assert normalize_name(" Dt Emissão ") == "dt_emissao"
    assert normalize_name("Valor Total (R$)") == "valor_total_r"


def test_suggest_mapping_finds_common_portuguese_names():
    cols = ["Dt Emissão", "Num Pedido", "Valor Total", "Descrição Produto", "Qtde", "Observações"]
    mapping = suggest_mapping(cols)
    assert mapping["data"] == "Dt Emissão"
    assert mapping["pedido_id"] == "Num Pedido"
    assert mapping["valor_total"] == "Valor Total"
    assert mapping["produto"] == "Descrição Produto"
    assert mapping["quantidade"] == "Qtde"
    assert mapping["custo"] is None


def test_suggest_mapping_never_reuses_a_column():
    mapping = suggest_mapping(["valor", "total"])
    used = [v for v in mapping.values() if v]
    assert len(used) == len(set(used))
