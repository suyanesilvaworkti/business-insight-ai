"""Esquema canônico dos dados de vendas.

O restante do sistema só conhece estes nomes de coluna. A planilha real da
empresa quase nunca terá exatamente estes nomes, então existe um passo de
*mapeamento*: "a sua coluna 'Dt Emissão' corresponde a 'data'".
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ColumnSpec:
    name: str                      # nome canônico usado pelo código
    label: str                     # nome amigável mostrado na interface
    kind: str                      # "date" | "number" | "text"
    required: bool = False
    help: str = ""
    aliases: tuple[str, ...] = ()  # nomes comuns (já normalizados) para auto-mapeamento


COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec("data", "Data da venda", "date", True,
               "Data em que a venda ocorreu.",
               ("data_venda", "data_da_venda", "dt_venda", "dt_emissao", "data_emissao",
                "emissao", "data_pedido", "dt_pedido", "date")),
    ColumnSpec("pedido_id", "Nº do pedido", "text", True,
               "Identificador do pedido/venda.",
               ("pedido", "num_pedido", "numero_pedido", "nr_pedido", "no_pedido",
                "id_pedido", "n_pedido", "order_id", "nf", "nota_fiscal")),
    ColumnSpec("valor_total", "Valor total (R$)", "number", True,
               "Valor da venda já com desconto aplicado.",
               ("valor", "total", "valor_venda", "vl_total", "valor_liquido",
                "faturamento", "receita", "amount")),
    ColumnSpec("produto", "Produto", "text", False, "Nome ou código do produto.",
               ("item", "descricao_produto", "desc_produto", "sku", "product")),
    ColumnSpec("categoria", "Categoria", "text", False, "Categoria/linha do produto.",
               ("grupo", "linha", "familia", "category")),
    ColumnSpec("regiao", "Região", "text", False, "Região, estado ou filial.",
               ("uf", "estado", "filial", "praca", "region")),
    ColumnSpec("vendedor", "Vendedor", "text", False, "Vendedor ou representante.",
               ("representante", "consultor", "seller", "vendedora")),
    ColumnSpec("cliente", "Cliente", "text", False, "Nome ou código do cliente.",
               ("cod_cliente", "id_cliente", "nome_cliente", "customer")),
    ColumnSpec("quantidade", "Quantidade", "number", False, "Unidades vendidas.",
               ("qtd", "qtde", "quant", "unidades", "quantity")),
    ColumnSpec("desconto", "Desconto (fração, 0,10 = 10%)", "number", False,
               "Desconto concedido como fração (0,10 = 10%).",
               ("desc", "perc_desconto", "pct_desconto", "discount")),
    ColumnSpec("custo", "Custo total do pedido (R$)", "number", False,
               "Custo total do pedido; habilita análise de margem.",
               ("custo_total", "cmv", "cpv", "vl_custo", "cost")),
)

COLUMNS_BY_NAME = {c.name: c for c in COLUMNS}
REQUIRED_COLUMNS = [c.name for c in COLUMNS if c.required]


def normalize_name(text: object) -> str:
    """'Dt Emissão ' -> 'dt_emissao' (sem acento, minúsculo, separado por _)."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def suggest_mapping(source_columns: Iterable[str]) -> dict[str, str | None]:
    """Sugere {coluna_canônica: coluna_da_planilha | None} pelo nome."""
    normalized = {normalize_name(c): c for c in source_columns}
    mapping: dict[str, str | None] = {}
    used: set[str] = set()
    for spec in COLUMNS:
        found = None
        for candidate in (spec.name, *spec.aliases):
            source = normalized.get(candidate)
            if source is not None and source not in used:
                found = source
                break
        mapping[spec.name] = found
        if found:
            used.add(found)
    return mapping
