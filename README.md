# Cobertura vacinal no Brasil, 2015–2024

Projeto individual da **Avaliação G1 — Linguagem de Programação: Análise e Visualização de Dados com Python**.

**Nome: Matheus Braga**

**Professor: Alexandre Louzada**

**Materia: Linguagem de Programação**

Análise exploratória e dashboard interativo sobre uma base **simulada** de cobertura vacinal (4.440 registros, 37 municípios, 6 vacinas, 2015–2024).

- **Página do projeto (GitHub Pages):** https://Math7Braga.github.io/projeto-g1/
- **Dashboard (Streamlit Community Cloud):** https://projeto-g1-cobertura-vacinal.streamlit.app
- **Repositório:** https://github.com/Math7Braga/projeto-g1

## Principais resultados
- Cobertura ponderada de 84,0%; só 34,8% dos registros atingem a meta e 21,6% estão em nível crítico.
- Sem tendência no tempo (+0,04 p.p. por ano) e diferenças pequenas entre vacinas, regiões e públicos-alvo.
- Número de campanhas sem relação com a cobertura (Spearman ≈ 0,00).

## Tecnologias
Python · Pandas · NumPy · Matplotlib · Seaborn · Plotly · SQLAlchemy + SQLite · Streamlit · GitHub

## Funcionalidades
| Tipo | Itens |
|---|---|
| Intermediárias | filtros múltiplos, KPIs dinâmicos, análise temporal, dashboard em seções, visualizações comparativas, análise geográfica, upload de CSV |
| Avançadas | dashboard multipágina, mapa interativo (Plotly), persistência em banco (SQLAlchemy + SQLite) com modelo relacional, correlação estatística |

## Estrutura
```
projeto-g1/
├── app.py                 # página principal do dashboard
├── pages/                 # mapa, correlações e banco de dados
├── utils.py               # carga, limpeza, filtros e KPIs
├── requirements.txt
├── index.html             # página do projeto (GitHub Pages)
├── dados/                 # CSV original
├── database/              # modelo SQLAlchemy e vacinas.db
├── notebooks/             # análise completa (.ipynb)
└── imagens/               # gráficos exportados do notebook
```

## Como executar
```bash
pip install -r requirements.txt
streamlit run app.py
```
Para recriar o banco: `python -m database.db`.

## Publicação
1. **GitHub:** crie o repositório `projeto-g1` e envie todos os arquivos.
2. **GitHub Pages:** em *Settings → Pages*, escolha a branch `main` e a pasta `/ (root)`.
3. **Streamlit Community Cloud:** em share.streamlit.io, conecte o repositório e defina `app.py` como arquivo principal.

## Limitações
Dados simulados; a cobertura é derivada de doses ÷ população; o nível de alerta depende diretamente da meta.
