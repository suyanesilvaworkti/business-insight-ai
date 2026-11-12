<<<<<<< HEAD
# 📊 Business Insight AI

Agente de inteligência artificial para análise de indicadores de vendas.
Você envia uma planilha (CSV ou Excel) e recebe KPIs, comparação entre períodos,
gráficos, tendências, anomalias, alertas, recomendações e respostas a perguntas
em linguagem natural.

## Princípios

- **O código calcula, a IA interpreta.** Todos os números saem de funções Python testadas (Pandas). A IA nunca calcula.
- **Só os dados disponíveis.** A IA trabalha apenas com os fatos calculados e informa quando não há dados suficientes.
- **Fato ≠ hipótese ≠ recomendação.** Cada saída da IA separa esses três blocos.
- **Privacidade.** Para a IA vão apenas agregados (totais, médias, rankings), nunca linhas brutas de clientes.

## Status do projeto

- [x] **Etapa 0** – Setup (estrutura, ambiente, Git)
- [x] **Etapa 1** – Dados: base fictícia, leitura CSV/Excel, mapeamento de colunas, validação
- [ ] **Etapa 2** – KPIs e comparação entre períodos
- [ ] **Etapa 3** – Dashboard com gráficos
- [ ] **Etapa 4** – Tendências, anomalias e alertas
- [ ] **Etapa 5** – Insights e recomendações com IA (Claude)
- [ ] **Etapa 6** – Perguntas em linguagem natural
- [ ] **Etapa 7** – Polimento e publicação

## Como rodar

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # preencha ANTHROPIC_API_KEY (só necessário a partir da Etapa 5)

streamlit run app.py               # abre em http://localhost:8501
```

Testes:

```bash
python -m pytest
```

Regenerar a base fictícia:

```bash
python scripts/generate_sample_data.py
```

## Estrutura

```
app.py                         interface Streamlit
src/business_insight/
  config.py                    configurações (.env)
  data/                        schema, loader, validator, gerador da base fictícia
  analytics/                   KPIs, períodos, tendências, anomalias, alertas (Etapas 2 e 4)
  viz/                         gráficos (Etapa 3)
  ai/                          integração com Claude (Etapas 5 e 6)
  ui/                          componentes de interface
data/sample/                   base fictícia de exemplo
tests/                         testes automatizados (pytest)
scripts/                       utilitários
docs/                          documentação
```

## Usando com dados reais

1. Coloque a planilha em `data/real/` (a pasta é ignorada pelo Git) ou envie pela interface.
2. Na tela, faça o mapeamento das suas colunas para os campos do sistema.
3. Confira os avisos de validação antes de confiar nas análises.

**Nunca** faça commit de planilhas reais nem do arquivo `.env`.

## Base fictícia

A base de exemplo tem padrões plantados (anomalias, produto em queda, região em queda,
aumento de desconto). Veja [docs/base_ficticia.md](docs/base_ficticia.md). Eles servem
de gabarito: o sistema deve encontrá-los sozinho nas próximas etapas.
=======
