"""Análise geográfica: mapa interativo (Plotly) da cobertura por município."""
import plotly.express as px
import streamlit as st

from utils import (
    COORDENADAS, agrupar_cobertura, aplicar_filtros, exigir_dados, fmt_int, fmt_pct, obter_base,
)

st.set_page_config(page_title="Mapa da cobertura", page_icon="🗺️", layout="wide")
st.title("Mapa da cobertura vacinal")
st.markdown("Cada círculo é um município. A cor mostra a cobertura ponderada e o tamanho, o total de doses aplicadas.")

dados = aplicar_filtros(obter_base())
exigir_dados(dados)

metrica = st.radio(
    "Cor do círculo", ["Cobertura ponderada (%)", "% de registros críticos", "% de registros que atingiram a meta"],
    horizontal=True,
)
coluna = {"Cobertura ponderada (%)": "cobertura", "% de registros críticos": "criticos",
          "% de registros que atingiram a meta": "meta_atingida"}[metrica]

mun = agrupar_cobertura(dados, ["regiao", "uf", "municipio"])
mun["lat"] = mun["municipio"].map(lambda m: COORDENADAS.get(m, (None, None))[0])
mun["lon"] = mun["municipio"].map(lambda m: COORDENADAS.get(m, (None, None))[1])
sem_coord = mun[mun["lat"].isna()]
mun = mun.dropna(subset=["lat"])
if not sem_coord.empty:
    st.caption(f"{len(sem_coord)} município(s) sem coordenada cadastrada ficaram fora do mapa.")

escala = "RdYlGn_r" if coluna == "criticos" else "RdYlGn"
fig = px.scatter_map(
    mun, lat="lat", lon="lon", color=coluna, size="doses", size_max=28,
    color_continuous_scale=escala, hover_name="municipio",
    hover_data={"uf": True, "cobertura": ":.1f", "criticos": ":.1f", "meta_atingida": ":.1f",
                "doses": ":,", "lat": False, "lon": False},
    labels={"cobertura": "Cobertura (%)", "criticos": "% crítico", "meta_atingida": "% meta atingida",
            "doses": "Doses", "uf": "UF"},
    zoom=3, center={"lat": -14.5, "lon": -52}, height=620, map_style="carto-positron",
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar_title=metrica.split(" (")[0])
st.plotly_chart(fig, width="stretch")

st.subheader("Ranking por UF")
uf = agrupar_cobertura(dados, ["regiao", "uf"]).sort_values("cobertura", ascending=False)
fig2 = px.bar(uf, x="uf", y="cobertura", color="regiao", labels={"cobertura": "Cobertura (%)", "uf": "UF", "regiao": "Região"},
              hover_data={"doses": ":,", "registros": True})
fig2.update_yaxes(range=[max(0, uf["cobertura"].min() - 5), 100])
fig2.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig2, width="stretch")

alta, baixa = mun.loc[mun["cobertura"].idxmax()], mun.loc[mun["cobertura"].idxmin()]
st.markdown(
    f"**Interpretação.** O município com maior cobertura na seleção é **{alta['municipio']} ({alta['uf']})**, "
    f"com {fmt_pct(alta['cobertura'])}; o menor é **{baixa['municipio']} ({baixa['uf']})**, com {fmt_pct(baixa['cobertura'])}. "
    "As cores variam pouco entre regiões, sem um bloco geográfico claramente melhor ou pior. "
    "Municípios com poucos registros no filtro (ex.: ao escolher uma vacina e um público específicos) "
    "oscilam mais e não devem ser comparados diretamente."
)
with st.expander("Tabela dos municípios"):
    st.dataframe(mun.drop(columns=["lat", "lon"]).sort_values("cobertura").round(2), hide_index=True, width="stretch")
