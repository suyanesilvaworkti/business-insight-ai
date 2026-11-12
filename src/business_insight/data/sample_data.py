"""Gerador da base fictícia de vendas (determinística: mesma semente, mesmos dados).

A base tem PADRÕES PLANTADOS de propósito. Nas próximas etapas o sistema deve
encontrá-los sozinho, o que serve de "gabarito" para testar nossos cálculos:

1. Crescimento geral de ~1,5% ao mês, mais fim de semana fraco e pico em nov/dez.
2. 14/03/2026: pico de vendas (promoção relâmpago)    -> anomalia positiva.
3. 22/08/2026: quase nenhuma venda (sistema fora do ar) -> anomalia negativa.
4. "Cadeira Ergonômica X" perde vendas a partir de jun/2026 -> produto em queda.
5. Região Sul cai pela metade a partir de set/2026       -> região em queda.
6. Desconto médio sobe em out/2026                       -> margem pressionada.

Todos os nomes e números são inventados.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START, END = "2025-01-01", "2026-10-31"

# (produto, categoria, preço de tabela, custo como fração do preço, popularidade)
PRODUCTS = [
    ("Notebook Pro 14", "Informática", 4200.0, 0.72, 3),
    ("Monitor 24 pol", "Informática", 980.0, 0.70, 5),
    ("Impressora Laser", "Informática", 1450.0, 0.74, 2),
    ("Mouse Sem Fio", "Periféricos", 89.0, 0.45, 10),
    ("Teclado Mecânico", "Periféricos", 320.0, 0.55, 6),
    ("Headset USB", "Periféricos", 210.0, 0.50, 7),
    ("Webcam HD", "Periféricos", 180.0, 0.52, 4),
    ("Cadeira Ergonômica X", "Escritório", 1350.0, 0.62, 4),
    ("Mesa Regulável", "Escritório", 1890.0, 0.66, 2),
    ("Hub USB-C", "Acessórios", 140.0, 0.48, 8),
    ("Mochila Executiva", "Acessórios", 260.0, 0.50, 5),
    ("Suporte para Notebook", "Acessórios", 95.0, 0.42, 7),
]
REGIONS = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
REGION_WEIGHTS = np.array([0.38, 0.18, 0.22, 0.12, 0.10])
SELLERS = ["Ana Souza", "Bruno Lima", "Carla Dias", "Diego Alves",
           "Elisa Rocha", "Fábio Nunes", "Gabriela Melo", "Heitor Prado"]
N_CUSTOMERS = 150

FLASH_SALE_DAY = pd.Timestamp("2026-03-14")
OUTAGE_DAY = pd.Timestamp("2026-08-22")
CHAIR_DECLINE_START = pd.Timestamp("2026-06-01")
SOUTH_DROP_START = pd.Timestamp("2026-09-01")
DISCOUNT_SPIKE_START = pd.Timestamp("2026-10-01")
CHAIR_NAME = "Cadeira Ergonômica X"


def _expected_orders(day: pd.Timestamp) -> float:
    """Número esperado de pedidos no dia (antes do sorteio aleatório)."""
    month_index = (day.year - 2025) * 12 + day.month - 1
    growth = 1.015 ** month_index
    weekday = {5: 0.6, 6: 0.3}.get(day.weekday(), 1.0)
    season = {11: 1.35, 12: 1.5, 1: 0.85}.get(day.month, 1.0)
    expected = 14 * growth * weekday * season
    if day == FLASH_SALE_DAY:
        expected *= 3.2
    if day == OUTAGE_DAY:
        expected *= 0.05
    return expected


def generate(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = [p[0] for p in PRODUCTS]
    base_popularity = np.array([p[4] for p in PRODUCTS], dtype=float)
    chair_idx = names.index(CHAIR_NAME)

    customers = [f"CLI-{i:03d}" for i in range(1, N_CUSTOMERS + 1)]
    customer_weights = 1 / np.arange(1, N_CUSTOMERS + 1) ** 0.7
    customer_weights /= customer_weights.sum()

    rows = []
    for day in pd.date_range(START, END, freq="D"):
        n_orders = rng.poisson(_expected_orders(day))
        if n_orders == 0:
            continue

        popularity = base_popularity.copy()
        if day >= CHAIR_DECLINE_START:
            months = (day - CHAIR_DECLINE_START).days / 30
            popularity[chair_idx] *= max(0.25, 1 - 0.15 * months)
        popularity /= popularity.sum()

        region_w = REGION_WEIGHTS.copy()
        if day >= SOUTH_DROP_START:
            region_w[REGIONS.index("Sul")] *= 0.5
        region_w /= region_w.sum()

        product_idx = rng.choice(len(PRODUCTS), size=n_orders, p=popularity)
        regions = rng.choice(REGIONS, size=n_orders, p=region_w)
        sellers = rng.choice(SELLERS, size=n_orders)
        clients = rng.choice(customers, size=n_orders, p=customer_weights)
        if day >= DISCOUNT_SPIKE_START:
            discounts = rng.choice([0.05, 0.10, 0.15, 0.20], size=n_orders, p=[0.2, 0.3, 0.3, 0.2])
        else:
            discounts = rng.choice([0.0, 0.05, 0.10], size=n_orders, p=[0.45, 0.40, 0.15])

        for i in range(n_orders):
            product, category, list_price, cost_pct, _ = PRODUCTS[product_idx[i]]
            if list_price < 300:
                qty = int(min(6, 1 + rng.poisson(0.6)))
            else:
                qty = 1 + int(rng.random() < 0.10)
            unit_price = round(list_price * rng.normal(1, 0.02), 2)
            discount = float(discounts[i])
            rows.append({
                "data": day,
                "cliente": clients[i],
                "produto": product,
                "categoria": category,
                "regiao": regions[i],
                "vendedor": sellers[i],
                "quantidade": qty,
                "preco_unitario": unit_price,
                "desconto": discount,
                "valor_total": round(qty * unit_price * (1 - discount), 2),
                "custo": round(qty * list_price * cost_pct * rng.normal(1, 0.01), 2),
            })

    df = pd.DataFrame(rows)
    df.insert(0, "pedido_id", [f"PED-{i:06d}" for i in range(1, len(df) + 1)])
    return df


def write_sample_csv(path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generate().to_csv(path, index=False, date_format="%Y-%m-%d")
    return path
