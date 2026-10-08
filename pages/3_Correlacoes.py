"""Correlação estatística entre cobertura e demais variáveis numéricas."""
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from utils import COR_PRINCIPAL, aplicar_filtros, exigir_dados, fmt_pct, obter_base

st.set_page_config(page_title="Correlações", page_icon="📈", layout="wide")
sns.set_theme(style="whitegrid")
st.title("Correlações")
st.markdown(
    "Quais variáveis acompanham a cobertura? Atenção: **correlação não é causalidade**, e nesta base a "
    "cobertura é calculada a partir de doses ÷ população, então a ligação com as doses é em parte mecânica."
)

dados = aplicar_filtros(obter_base())
exigir_dados(dados)
if len(dados) < 30:
    st.warning("Poucos registros (menos de 30) para uma correlação confiável. Amplie os filtros.")

metodo = st.radio("Método", ["pearson", "spearman"], horizontal=True,
                  help="Pearson mede relação linear; Spearman mede relação de ordem e resiste a outliers.")
cols = ["cobertura_percentual", "doses_aplicadas", "populacao_alvo", "campanhas", "meta_percentual", "ano", "mes"]
corr = dados[cols].corr(method=metodo)

col_a, col_b = st.columns([1.1, 1])
with col_a:
    fig, ax = plt.subplots(figsize=(6.5, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True, ax=ax,
                cbar_kws={"shrink": 0.8})
    ax.set_xticklabels([c.replace("_", "\n") for c in cols], rotation=0, fontsize=7)
    ax.set_yticklabels([c.replace("_", " ") for c in cols], rotation=0, fontsize=8)
    st.pyplot(fig)
    plt.close(fig)
with col_b:
    x = st.selectbox("Comparar a cobertura com", ["doses_aplicadas", "populacao_alvo", "campanhas", "meta_percentual"])
    amostra = dados.sample(min(len(dados), 1500), random_state=1)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.regplot(data=amostra, x=x, y="cobertura_percentual", scatter_kws={"alpha": 0.25, "s": 14, "color": COR_PRINCIPAL},
                line_kws={"color": "#C2410C"}, ax=ax)
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel("Cobertura (%)")
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Gráfico com até 1.500 registros sorteados, para manter a leitura.")

st.subheader("Campanhas e cobertura")
g = dados.groupby("grupo_campanhas").agg(registros=("ano", "size"), cobertura_media=("cobertura_percentual", "mean"),
                                        criticos=("nivel_alerta", lambda s: (s == "Crítico").mean() * 100)).reindex(
    ["0", "1", "2", "3 ou mais"]).dropna().round(2)
c1, c2 = st.columns([1, 1.4])
c1.dataframe(g.rename(columns={"registros": "Registros", "cobertura_media": "Cobertura média (%)", "criticos": "% crítico"}),
             width="stretch")
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=dados, x="grupo_campanhas", y="cobertura_percentual", order=list(g.index), color="#BFDCDB", ax=ax, fliersize=2)
ax.set_xlabel("Campanhas no mês")
ax.set_ylabel("Cobertura (%)")
c2.pyplot(fig)
plt.close(fig)

r_doses = corr.loc["cobertura_percentual", "doses_aplicadas"]
r_camp = corr.loc["cobertura_percentual", "campanhas"]
r_pop = corr.loc["cobertura_percentual", "populacao_alvo"]
st.markdown(
    f"""**Interpretação ({metodo}).** A correlação da cobertura com as doses é **{r_doses:.2f}** (fraca) e com a população-alvo é
**{r_pop:.2f}** (nula): municípios maiores não têm cobertura maior. Com o número de campanhas, o coeficiente é **{r_camp:.2f}**,
isto é, **não há relação linear mensurável** entre mais campanhas e maior cobertura nesta base. A média de cobertura é praticamente
a mesma com 0, 1 ou 2 campanhas; os grupos com muitas campanhas têm poucos registros e não permitem conclusão."""
)
