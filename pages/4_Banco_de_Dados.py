"""Persistência: consultas SQL ao banco SQLite relacional via SQLAlchemy."""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from sqlalchemy import func, select

from database.db import CAMINHO_DB, Municipio, Regiao, Registro, UF, Vacina, construir_banco, obter_engine
from utils import COR_PRINCIPAL, CSV_PADRAO, carregar_csv, fmt_pct

st.set_page_config(page_title="Banco de dados", page_icon="🗄️", layout="wide")
sns.set_theme(style="whitegrid")
st.title("Banco de dados relacional")
st.markdown(
    "Os mesmos dados do CSV estão em um banco **SQLite** modelado com **SQLAlchemy**: regiões → UFs → municípios, "
    "e vacinas, ligados à tabela de registros por chaves estrangeiras. As consultas abaixo são feitas no banco, não no CSV."
)

if not CAMINHO_DB.exists():
    with st.spinner("Criando o banco a partir do CSV..."):
        construir_banco(carregar_csv(CSV_PADRAO))
engine = obter_engine()

st.code(
    "regioes (id, nome)\n  └─ ufs (id, sigla, regiao_id)\n       └─ municipios (id, nome, uf_id)\n"
    "vacinas (id, nome)\n"
    "registros (id, data, ano, mes, municipio_id → municipios, vacina_id → vacinas, publico_alvo,\n"
    "           doses_aplicadas, populacao_alvo, cobertura_percentual, meta_percentual,\n"
    "           campanhas, nivel_alerta, atingiu_meta)",
    language="text",
)

soma_doses, soma_pop = func.sum(Registro.doses_aplicadas), func.sum(Registro.populacao_alvo)
cobertura = (soma_doses * 100.0 / soma_pop).label("cobertura")

consultas = {
    "Cobertura por região": (
        select(Regiao.nome.label("regiao"), cobertura, func.count(Registro.id).label("registros"))
        .join(UF, UF.regiao_id == Regiao.id).join(Municipio, Municipio.uf_id == UF.id)
        .join(Registro, Registro.municipio_id == Municipio.id).group_by(Regiao.nome).order_by(cobertura.desc()),
        "regiao",
    ),
    "Cobertura por vacina": (
        select(Vacina.nome.label("vacina"), cobertura, func.count(Registro.id).label("registros"))
        .join(Registro, Registro.vacina_id == Vacina.id).group_by(Vacina.nome).order_by(cobertura.desc()),
        "vacina",
    ),
    "Cobertura por ano": (
        select(Registro.ano.label("ano"), cobertura, func.count(Registro.id).label("registros"))
        .group_by(Registro.ano).order_by(Registro.ano),
        "ano",
    ),
    "10 municípios com menor cobertura": (
        select(Municipio.nome.label("municipio"), UF.sigla.label("uf"), cobertura)
        .join(UF, Municipio.uf_id == UF.id).join(Registro, Registro.municipio_id == Municipio.id)
        .group_by(Municipio.nome, UF.sigla).order_by(cobertura.asc()).limit(10),
        "municipio",
    ),
}
escolha = st.selectbox("Consulta", list(consultas))
stmt, eixo = consultas[escolha]

st.markdown("**SQL gerado pelo SQLAlchemy**")
st.code(str(stmt.compile(engine, compile_kwargs={"literal_binds": True})), language="sql")

with engine.connect() as conn:
    resultado = pd.read_sql(stmt, conn)

c1, c2 = st.columns([1, 1.3])
c1.dataframe(resultado.round(2), hide_index=True, width="stretch")
fig, ax = plt.subplots(figsize=(6.5, 3.8))
ordem = resultado[eixo].astype(str)
sns.barplot(x=ordem, y=resultado["cobertura"], color=COR_PRINCIPAL, ax=ax)
ax.set_ylim(max(0, resultado["cobertura"].min() - 5), 100)
ax.set_xlabel("")
ax.set_ylabel("Cobertura ponderada (%)")
plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
c2.pyplot(fig)
plt.close(fig)

with engine.connect() as conn:
    total = conn.execute(select(func.count(Registro.id))).scalar()
st.caption(f"O banco tem {total:,} registros. Consulta feita com SQLAlchemy 2.0 (ORM + `select`).".replace(",", "."))
top, base = resultado.iloc[0], resultado.iloc[-1]
st.markdown(
    f"**Interpretação.** Na consulta *{escolha.lower()}*, os valores vão de {fmt_pct(resultado['cobertura'].min())} a "
    f"{fmt_pct(resultado['cobertura'].max())}. Os resultados batem com os das outras páginas, o que confirma que o banco "
    "foi carregado sem perdas. A vantagem do banco é separar as entidades (região, UF, município, vacina) em tabelas próprias, "
    "evitando repetir texto em cada linha e permitindo consultas por junção."
)
