import pandas as pd

from business_insight.data.sample_data import (
    CHAIR_NAME, FLASH_SALE_DAY, OUTAGE_DAY, generate,
)
from business_insight.data.schema import suggest_mapping
from business_insight.data.validator import apply_mapping_and_validate


def test_generation_is_deterministic():
    pd.testing.assert_frame_equal(generate(), generate())


def test_sample_passes_validation_without_losing_rows():
    raw = generate()
    df, report = apply_mapping_and_validate(raw, suggest_mapping(raw.columns))
    assert report.ok
    assert report.rows_out == report.rows_in == len(raw)


def test_planted_anomalies_exist():
    orders = generate().groupby("data").size()
    median = orders.median()
    assert orders.loc[FLASH_SALE_DAY] > 2 * median
    assert orders.get(OUTAGE_DAY, 0) < 0.25 * median


def test_planted_product_decline_exists():
    df = generate()
    chair = df[df["produto"] == CHAIR_NAME]
    before = chair[(chair["data"] >= "2026-03-01") & (chair["data"] < "2026-06-01")]
    after = chair[chair["data"] >= "2026-08-01"]
    assert len(after) / 3 < len(before) / 3  # pedidos por mês caíram
