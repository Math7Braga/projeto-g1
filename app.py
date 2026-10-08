"""Página principal do dashboard: Cobertura Vacinal no Brasil (2015–2024)."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from utils import (
    COR_PRINCIPAL, CORES_ALERTA, ORDEM_ALERTA, agrupar_cobertura, aplicar_filtros,
    calcular_kpis, exigir_dados, fmt_int, fmt_pct, fmt_pp, obter_base,
)

st.set_page_config(page_title="Cobertura Vacinal no Brasil", page_icon="💉", layout="wide")
sns.set_theme(style="whitegrid", context="notebook")

# ---------------------------------------------------------------- cabeçalho
st.title("Cobertura vacinal no Brasil, 2015–2024")
st.markdown(
    """
**Problema.** A cobertura vacinal mede quanto do público-alvo recebeu a vacina. Quando ela fica abaixo da
meta (80% ou 95%, conforme o registro), cresce o risco de surtos de doenças evitáveis. Este painel
investiga **onde, quando e para quais vacinas a cobertura fica abaixo da meta** e se as campanhas de
vacinação acompanham essa diferença.

A base é uma **simulação** com 4.440 registros mensais de 37 municípios, 6 vacinas e 5 públicos-alvo.
Use os filtros à esquerda; todos os números e textos desta página são recalculados.
"""
)

base = obter_base()
dados = aplicar_filtros(base)
exigir_dados(dados)

# ---------------------------------------------------------------- KPIs
k, k0 = calcular_kpis(dados), calcular_kpis(base)
st.subheader("Indicadores")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Cobertura ponderada", fmt_pct(k["cobertura"]), fmt_pp(k["cobertura"] - k0["cobertura"]) + " vs. base toda")
c2.metric("Registros que atingiram a meta", fmt_pct(k["meta_atingida"]), fmt_pp(k["meta_atingida"] - k0["meta_atingida"]) + " vs. base toda")
c3.metric("Registros em nível crítico", fmt_pct(k["criticos"]), fmt_pp(k["criticos"] - k0["criticos"]) + " vs. base toda", delta_color="inverse")
c4.metric("Distância média da meta", fmt_pp(k["gap"]))
c5.metric("Doses aplicadas", fmt_int(k["doses"]))
st.caption(
    "Cobertura ponderada = doses aplicadas ÷ população-alvo (registros com público maior pesam mais). "
    "Meta atingida = cobertura ≥ meta do registro. Nível crítico = 15 p.p. ou mais abaixo da meta."
)

# ---------------------------------------------------------------- seções
tab_tempo, tab_comp, tab_dist, tab_tab = st.tabs(
    ["Evolução no tempo", "Comparativos", "Distribuição e alertas", "Tabelas"]
)

with tab_tempo:
    mensal = agrupar_cobertura(dados, "periodo").sort_values("periodo")
    mensal["media_12m"] = mensal["cobertura"].rolling(12, min_periods=6).mean()
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(mensal["periodo"], mensal["cobertura"], color=COR_PRINCIPAL, alpha=0.35, lw=1.2, label="Mensal")
    ax.plot(mensal["periodo"], mensal["media_12m"], color=COR_PRINCIPAL, lw=2.5, label="Média móvel de 12 meses")
    ax.axhline(dados["meta_percentual"].mean(), color="#C2410C", ls="--", lw=1.2, label="Meta média dos registros")
    ax.set_xlabel("")
    ax.set_ylabel("Cobertura ponderada (%)")
    ax.legend(frameon=False, loc="lower left")
    st.pyplot(fig)
    plt.close(fig)

    anual = agrupar_cobertura(dados, "ano")
    melhor, pior = anual.loc[anual["cobertura"].idxmax()], anual.loc[anual["cobertura"].idxmin()]
    amp = melhor["cobertura"] - pior["cobertura"]
    st.markdown(
        f"**Interpretação.** O melhor ano na seleção foi **{int(melhor['ano'])}** "
        f"({fmt_pct(melhor['cobertura'])}) e o pior foi **{int(pior['ano'])}** ({fmt_pct(pior['cobertura'])}), "
        f"uma amplitude de {fmt_pp(amp, 1).replace('+', '')}. "
        + ("A série é praticamente estável: não há tendência clara de alta ou queda. "
           if amp < 3 else "Há variação relevante entre anos. ")
        + "A oscilação mensal é maior que a diferença entre anos."
    )

with tab_comp:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Por vacina**")
        vac = agrupar_cobertura(dados, "vacina").sort_values("cobertura")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=vac, y="vacina", x="cobertura", color=COR_PRINCIPAL, ax=ax)
        ax.set_xlim(max(0, vac["cobertura"].min() - 8), 100)
        ax.set_xlabel("Cobertura ponderada (%)")
        ax.set_ylabel("")
        for i, v in enumerate(vac["cobertura"]):
            ax.text(v + 0.2, i, fmt_pct(v), va="center", fontsize=9)
        st.pyplot(fig)
        plt.close(fig)
    with col_b:
        st.markdown("**Região × ano**")
        pivo = (
            dados.groupby(["regiao", "ano"]).apply(
                lambda g: g["doses_aplicadas"].sum() / g["populacao_alvo"].sum() * 100, include_groups=False
            ).unstack()
        )
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(pivo, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "%"}, ax=ax,
                    annot_kws={"fontsize": 8})
        ax.set_xlabel("")
        ax.set_ylabel("")
        st.pyplot(fig)
        plt.close(fig)

    reg = agrupar_cobertura(dados, "regiao").sort_values("cobertura")
    vac_top, vac_bot = vac.iloc[-1], vac.iloc[0]
    st.markdown(
        f"**Interpretação.** Entre as vacinas, **{vac_top['vacina']}** tem a maior cobertura "
        f"({fmt_pct(vac_top['cobertura'])}) e **{vac_bot['vacina']}** a menor ({fmt_pct(vac_bot['cobertura'])}). "
        f"Entre as regiões, a diferença vai de {reg.iloc[0]['regiao']} ({fmt_pct(reg.iloc[0]['cobertura'])}) "
        f"a {reg.iloc[-1]['regiao']} ({fmt_pct(reg.iloc[-1]['cobertura'])}). "
        "Diferenças de poucos pontos percentuais entre grupos são pequenas diante da dispersão dentro de cada grupo "
        "(veja a aba seguinte)."
    )

with tab_dist:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Distribuição da cobertura por registro**")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(dados["cobertura_percentual"], bins=30, kde=True, color=COR_PRINCIPAL, ax=ax)
        ax.axvline(dados["cobertura_percentual"].median(), color=COR_PRINCIPAL, ls="--", lw=1.5)
        ax.set_xlabel("Cobertura (%)")
        ax.set_ylabel("Registros")
        st.pyplot(fig)
        plt.close(fig)
    with col_b:
        st.markdown("**Níveis de alerta por região**")
        al = pd.crosstab(dados["regiao"], dados["nivel_alerta"], normalize="index").reindex(columns=ORDEM_ALERTA, fill_value=0) * 100
        fig, ax = plt.subplots(figsize=(6, 4))
        al.plot(kind="barh", stacked=True, color=[CORES_ALERTA[c] for c in ORDEM_ALERTA], ax=ax, width=0.7)
        ax.set_xlabel("% dos registros")
        ax.set_ylabel("")
        ax.set_xlim(0, 100)
        ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2))
        st.pyplot(fig)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 3.2))
    sns.boxplot(data=dados, x="publico_alvo", y="cobertura_percentual", color="#BFDCDB", ax=ax, fliersize=2)
    ax.set_xlabel("")
    ax.set_ylabel("Cobertura (%)")
    st.pyplot(fig)
    plt.close(fig)

    q05, q95 = dados["cobertura_percentual"].quantile([0.05, 0.95])
    st.markdown(
        f"**Interpretação.** Metade dos registros fica entre {fmt_pct(dados['cobertura_percentual'].quantile(.25))} "
        f"e {fmt_pct(dados['cobertura_percentual'].quantile(.75))}, e 90% deles entre {fmt_pct(q05)} e {fmt_pct(q95)}. "
        f"Só **{fmt_pct(k['meta_atingida'])}** dos registros atingiram a meta e **{fmt_pct(k['criticos'])}** estão em nível crítico. "
        "As caixas dos públicos-alvo se sobrepõem quase totalmente: a variação está dentro de cada grupo, "
        "e não entre eles."
    )

with tab_tab:
    st.markdown("**Municípios com menor e maior cobertura**")
    mun = agrupar_cobertura(dados, ["regiao", "uf", "municipio"]).sort_values("cobertura")
    mun = mun.rename(columns={
        "regiao": "Região", "uf": "UF", "municipio": "Município", "doses": "Doses",
        "registros": "Registros", "criticos": "% crítico", "meta_atingida": "% meta atingida", "cobertura": "Cobertura (%)",
    }).round(2)
    ca, cb = st.columns(2)
    ca.caption("10 menores")
    ca.dataframe(mun.head(10), hide_index=True, width="stretch")
    cb.caption("10 maiores")
    cb.dataframe(mun.tail(10).iloc[::-1], hide_index=True, width="stretch")
    st.markdown("**Registros filtrados**")
    cols = ["data", "regiao", "uf", "municipio", "vacina", "publico_alvo", "doses_aplicadas",
            "populacao_alvo", "cobertura_percentual", "meta_percentual", "campanhas", "nivel_alerta"]
    st.dataframe(dados[cols].sort_values("data", ascending=False), hide_index=True, width="stretch")
    st.download_button("Baixar registros filtrados (CSV)", dados[cols].to_csv(index=False).encode("utf-8-sig"),
                       "cobertura_filtrada.csv", "text/csv")

# ---------------------------------------------------------------- conclusão
st.divider()
st.subheader("Conclusão executiva")
reg_pior = agrupar_cobertura(dados, "regiao").sort_values("cobertura").iloc[0]
st.markdown(
    f"""
Na seleção atual, a cobertura ponderada é **{fmt_pct(k['cobertura'])}**, em média {fmt_pp(abs(k['gap']))} abaixo da meta.
Isso significa que **{fmt_pct(100 - k['meta_atingida'])} dos registros ficaram abaixo da meta** e {fmt_pct(k['criticos'])} estão em nível crítico.

- **Onde agir primeiro:** a menor cobertura está em *{reg_pior['regiao']}* ({fmt_pct(reg_pior['cobertura'])}), mas a diferença para as demais regiões é pequena.
  O problema aparece em todo o país, não em um recorte específico.
- **Metas:** boa parte da distância vem de metas de 95%. Reavaliar o que é possível alcançar por vacina ajuda a priorizar.
- **Campanhas:** na página *Correlações*, o número de campanhas praticamente não acompanha a cobertura nesta base.
  Vale medir o efeito de cada campanha com dados mais detalhados antes de ampliar o investimento.
- **Limite:** os dados são simulados; os resultados ilustram o método e não devem orientar decisões reais.
"""
)
