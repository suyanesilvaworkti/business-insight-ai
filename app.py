"""Business Insight AI - interface Streamlit.

Etapa 1: carregar dados (fictícios ou planilha própria), mapear colunas,
validar e pré-visualizar. KPIs, gráficos, alertas e IA entram nas próximas etapas.

Rodar:  streamlit run app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))  # permite `import business_insight` sem instalar o pacote

import streamlit as st  # noqa: E402

from business_insight.config import APP_NAME, SAMPLE_DATA_PATH  # noqa: E402
from business_insight.data.loader import LoaderError, load_table  # noqa: E402
from business_insight.data.sample_data import write_sample_csv  # noqa: E402
from business_insight.data.schema import COLUMNS, suggest_mapping  # noqa: E402
from business_insight.data.validator import apply_mapping_and_validate  # noqa: E402

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")

NOT_USED = "— não usar —"
SOURCE_SAMPLE = "Base fictícia de exemplo"
SOURCE_UPLOAD = "Enviar minha planilha"


@st.cache_data(show_spinner=False)
def load_sample():
    if not SAMPLE_DATA_PATH.exists():
        write_sample_csv(SAMPLE_DATA_PATH)
    return load_table(SAMPLE_DATA_PATH)


@st.cache_data(show_spinner=False)
def load_upload(data: bytes, filename: str):
    return load_table(data, filename)


def fmt_date(value) -> str:
    return value.strftime("%d/%m/%Y") if value is not None else "-"


st.title(f"📊 {APP_NAME}")
st.caption("Indicadores de vendas calculados pelo código, interpretados pela IA e sempre baseados nos seus dados.")

with st.sidebar:
    st.header("Dados")
    source = st.radio("Fonte dos dados", [SOURCE_SAMPLE, SOURCE_UPLOAD])
    uploaded = None
    if source == SOURCE_UPLOAD:
        uploaded = st.file_uploader("CSV ou Excel (.xlsx)", type=["csv", "xlsx"])
        st.caption("Nesta etapa, nenhum dado é enviado a qualquer serviço de IA.")

# --- 1. leitura -----------------------------------------------------------------------
raw, signature, load_error = None, None, None
if source == SOURCE_SAMPLE:
    raw, signature = load_sample(), "sample"
elif uploaded is not None:
    try:
        raw = load_upload(uploaded.getvalue(), uploaded.name)
        signature = f"{uploaded.name}-{uploaded.size}"
    except LoaderError as exc:
        load_error = str(exc)

if load_error:
    st.error(load_error)
    st.stop()
if raw is None:
    st.info("Envie uma planilha CSV ou Excel na barra lateral para começar.")
    st.stop()

st.success(f"Arquivo lido: {len(raw):,} linhas e {len(raw.columns)} colunas.".replace(",", "."))

# --- 2. mapeamento de colunas ----------------------------------------------------------
st.subheader("1. Mapeamento de colunas")
st.write("Indique qual coluna da sua planilha corresponde a cada campo. Campos com * são obrigatórios.")

suggested = suggest_mapping(list(raw.columns))
options = [NOT_USED] + list(raw.columns)
mapping: dict[str, str | None] = {}
grid = st.columns(3)
for i, spec in enumerate(COLUMNS):
    default = suggested[spec.name]
    with grid[i % 3]:
        choice = st.selectbox(
            spec.label + (" *" if spec.required else ""),
            options,
            index=options.index(default) if default else 0,
            key=f"map_{signature}_{spec.name}",
            help=spec.help,
        )
    mapping[spec.name] = None if choice == NOT_USED else choice

# --- 3. validação ----------------------------------------------------------------------
st.subheader("2. Validação dos dados")
df, report = apply_mapping_and_validate(raw, mapping)

for message in report.errors:
    st.error(message)
for message in report.warnings:
    st.warning(message)
for message in report.infos:
    st.info(message)

if not report.ok or df is None:
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Linhas lidas", f"{report.rows_in:,}".replace(",", "."))
c2.metric("Linhas válidas", f"{report.rows_out:,}".replace(",", "."))
c3.metric("Início", fmt_date(report.date_min))
c4.metric("Fim", fmt_date(report.date_max))

unused = [c for c in raw.columns if c not in mapping.values()]
if unused:
    st.caption("Colunas da planilha não utilizadas: " + ", ".join(unused))

st.session_state["df"] = df  # as próximas etapas leem os dados limpos daqui

# --- 4. prévia -------------------------------------------------------------------------
st.subheader("3. Prévia dos dados limpos")
st.dataframe(df.head(100), width="stretch", hide_index=True)

st.divider()
st.info("✅ Etapa 1 concluída: dados carregados e validados. Próxima etapa: KPIs e comparação entre períodos.")
