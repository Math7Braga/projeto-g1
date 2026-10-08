"""Funções compartilhadas entre as páginas do dashboard (carga, limpeza, filtros e KPIs)."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).parent
CSV_PADRAO = RAIZ / "dados" / "simulacao_cobertura_vacinal_brasil.csv"

COLUNAS_OBRIGATORIAS = [
    "ano", "mes", "data", "regiao", "uf", "municipio", "vacina", "doses_aplicadas",
    "publico_alvo", "cobertura_percentual", "meta_percentual", "populacao_alvo",
    "campanhas", "nivel_alerta",
]
ORDEM_ALERTA = ["Crítico", "Atenção", "Adequado"]
CORES_ALERTA = {"Crítico": "#C2410C", "Atenção": "#E0A100", "Adequado": "#0E7C7B"}
COR_PRINCIPAL = "#0E7C7B"
COR_TINTA = "#14233B"

# Coordenadas aproximadas dos municípios da base (latitude, longitude) para o mapa.
COORDENADAS = {
    "Manaus": (-3.119, -60.022), "Belém": (-1.456, -48.502), "Santarém": (-2.443, -54.708),
    "Porto Velho": (-8.761, -63.900), "Palmas": (-10.184, -48.333), "Salvador": (-12.971, -38.501),
    "Feira de Santana": (-12.267, -38.967), "Recife": (-8.054, -34.881),
    "Jaboatão dos Guararapes": (-8.113, -35.015), "Fortaleza": (-3.732, -38.527),
    "Juazeiro do Norte": (-7.213, -39.315), "São Luís": (-2.530, -44.303),
    "João Pessoa": (-7.115, -34.863), "Brasília": (-15.794, -47.882), "Goiânia": (-16.686, -49.264),
    "Aparecida de Goiânia": (-16.823, -49.247), "Cuiabá": (-15.601, -56.098),
    "Campo Grande": (-20.469, -54.620), "São Paulo": (-23.550, -46.633), "Campinas": (-22.909, -47.063),
    "Ribeirão Preto": (-21.178, -47.810), "Rio de Janeiro": (-22.907, -43.173),
    "Niterói": (-22.883, -43.104), "Nova Iguaçu": (-22.759, -43.451), "Petrópolis": (-22.505, -43.179),
    "Belo Horizonte": (-19.917, -43.934), "Uberlândia": (-18.919, -48.277),
    "Juiz de Fora": (-21.761, -43.350), "Vitória": (-20.315, -40.312), "Vila Velha": (-20.329, -40.292),
    "Serra": (-20.121, -40.307), "Curitiba": (-25.428, -49.273), "Londrina": (-23.310, -51.163),
    "Porto Alegre": (-30.034, -51.217), "Caxias do Sul": (-29.168, -51.179),
    "Florianópolis": (-27.595, -48.548), "Joinville": (-26.304, -48.846),
}


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza e engenharia de atributos."""
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["regiao", "uf", "municipio", "vacina", "publico_alvo", "nivel_alerta"]:
        df[col] = df[col].astype(str).str.strip()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data", "cobertura_percentual", "populacao_alvo"]).drop_duplicates()
    df["cobertura_percentual"] = df["cobertura_percentual"].clip(0, 100)
    # Atributos derivados
    df["periodo"] = df["data"].dt.to_period("M").dt.to_timestamp()
    df["trimestre"] = df["data"].dt.quarter
    df["gap_meta"] = df["cobertura_percentual"] - df["meta_percentual"]
    df["atingiu_meta"] = df["gap_meta"] >= 0
    df["grupo_campanhas"] = pd.cut(
        df["campanhas"], bins=[-1, 0, 1, 2, np.inf], labels=["0", "1", "2", "3 ou mais"]
    ).astype(str)
    return df


@st.cache_data(show_spinner=False)
def carregar_csv(origem) -> pd.DataFrame:
    return preparar(pd.read_csv(origem, encoding="utf-8-sig"))


def obter_base() -> pd.DataFrame:
    """Carrega a base padrão ou um CSV enviado pelo usuário (com a mesma estrutura)."""
    with st.sidebar.expander("Usar outro arquivo CSV"):
        arquivo = st.file_uploader("CSV com as mesmas colunas da base original", type="csv")
        if arquivo is not None:
            try:
                bruto = pd.read_csv(arquivo, encoding="utf-8-sig")
                bruto.columns = [c.strip().lower() for c in bruto.columns]
                faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in bruto.columns]
                if faltando:
                    st.error(f"Colunas ausentes: {', '.join(faltando)}. Usando a base padrão.")
                else:
                    st.success("Arquivo carregado.")
                    return preparar(bruto)
            except Exception as erro:  # arquivo ilegível
                st.error(f"Não foi possível ler o arquivo: {erro}")
    return carregar_csv(CSV_PADRAO)


def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Filtros múltiplos na barra lateral. Retorna o DataFrame filtrado."""
    st.sidebar.header("Filtros")
    ano_min, ano_max = int(df["ano"].min()), int(df["ano"].max())
    anos = st.sidebar.slider("Período (anos)", ano_min, ano_max, (ano_min, ano_max))
    regioes = st.sidebar.multiselect("Região", sorted(df["regiao"].unique()))
    ufs_disp = sorted(df[df["regiao"].isin(regioes)]["uf"].unique() if regioes else df["uf"].unique())
    ufs = st.sidebar.multiselect("UF", ufs_disp)
    vacinas = st.sidebar.multiselect("Vacina", sorted(df["vacina"].unique()))
    publicos = st.sidebar.multiselect("Público-alvo", sorted(df["publico_alvo"].unique()))
    st.sidebar.caption("Deixe um filtro vazio para incluir todas as opções.")

    f = df[df["ano"].between(*anos)]
    if regioes:
        f = f[f["regiao"].isin(regioes)]
    if ufs:
        f = f[f["uf"].isin(ufs)]
    if vacinas:
        f = f[f["vacina"].isin(vacinas)]
    if publicos:
        f = f[f["publico_alvo"].isin(publicos)]
    return f


def cobertura_ponderada(df: pd.DataFrame) -> float:
    """Doses aplicadas / população-alvo (cada registro pesa pelo tamanho do seu público)."""
    pop = df["populacao_alvo"].sum()
    return float(df["doses_aplicadas"].sum() / pop * 100) if pop else float("nan")


def calcular_kpis(df: pd.DataFrame) -> dict:
    return {
        "registros": len(df),
        "doses": int(df["doses_aplicadas"].sum()),
        "cobertura": cobertura_ponderada(df),
        "mediana": float(df["cobertura_percentual"].median()),
        "meta_atingida": float(df["atingiu_meta"].mean() * 100),
        "criticos": float((df["nivel_alerta"] == "Crítico").mean() * 100),
        "gap": float(df["gap_meta"].mean()),
    }


def fmt_int(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


def fmt_pct(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",") + "%"


def fmt_pp(x: float, casas: int = 1) -> str:
    return f"{x:+.{casas}f}".replace(".", ",") + " p.p."


def agrupar_cobertura(df: pd.DataFrame, por: str) -> pd.DataFrame:
    """Cobertura ponderada, % de registros críticos e nº de registros por grupo."""
    g = df.groupby(por).agg(
        doses=("doses_aplicadas", "sum"),
        pop=("populacao_alvo", "sum"),
        registros=("ano", "size"),
        criticos=("nivel_alerta", lambda s: (s == "Crítico").mean() * 100),
        meta_atingida=("atingiu_meta", lambda s: s.mean() * 100),
    )
    g["cobertura"] = g["doses"] / g["pop"] * 100
    return g.reset_index().drop(columns="pop")


def exigir_dados(df: pd.DataFrame):
    if df.empty:
        st.warning("Nenhum registro com os filtros atuais. Amplie a seleção na barra lateral.")
        st.stop()
