# Base fictícia: gabarito dos padrões plantados

Arquivo: `data/sample/vendas_ficticias.csv` (01/01/2025 a 31/10/2026, ~9,5 mil pedidos).
Gerada por `src/business_insight/data/sample_data.py` com semente fixa (resultado reproduzível).

| Padrão | Quando | O que o sistema deve detectar |
|---|---|---|
| Crescimento geral (~1,5% ao mês) | todo o período | tendência de alta na receita |
| Sazonalidade | fim de semana fraco; pico em nov/dez | padrão semanal e mensal |
| Pico de vendas (promoção relâmpago) | 14/03/2026 | anomalia positiva |
| Quase nenhuma venda (sistema fora do ar) | 22/08/2026 | anomalia negativa |
| Cadeira Ergonômica X em queda | a partir de jun/2026 | produto com queda contínua |
| Região Sul cai pela metade | a partir de set/2026 | região com queda |
| Desconto médio sobe | out/2026 | margem pressionada |

Todos os nomes e números são fictícios.
