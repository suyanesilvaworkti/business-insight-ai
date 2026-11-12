"""Gera (ou regenera) data/sample/vendas_ficticias.csv.

Uso:  python scripts/generate_sample_data.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from business_insight.config import SAMPLE_DATA_PATH  # noqa: E402
from business_insight.data.sample_data import write_sample_csv  # noqa: E402

if __name__ == "__main__":
    path = write_sample_csv(SAMPLE_DATA_PATH)
    print(f"Base fictícia gerada em: {path}")
