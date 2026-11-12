"""Configurações centrais do projeto.

Tudo que pode mudar entre ambientes (chaves, modelo) vem de variáveis de
ambiente / arquivo .env. Nada de segredo escrito no código.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# src/business_insight/config.py -> raiz do projeto é 2 níveis acima da pasta do pacote
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

APP_NAME = "Business Insight AI"
SAMPLE_DATA_PATH = ROOT / "data" / "sample" / "vendas_ficticias.csv"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
