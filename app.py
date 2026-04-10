import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import json

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Monitor IPCA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS CUSTOMIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0d0f14;
    --surface: #151820;
    --surface2: #1c2030;
    --border: #252a3a;
    --accent: #4fd1c5;
    --accent2: #f6ad55;
    --accent3: #fc8181;
    --text: #e2e8f0;
    --text-muted: #718096;
    --green: #68d391;
    --red: #fc8181;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.main { background-color: var(--bg); }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* Header */
.header-box {
    background: linear-gradient(135deg, #151820 0%, #1a1f30 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.header-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: -0.02em;
    margin: 0;
}
.header-sub {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.3rem;
    font-family: 'IBM Plex Mono', monospace;
}

/* KPI Cards */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
}
.kpi-card.orange::before { background: var(--accent2); }
.kpi-card.red::before { background: var(--accent3); }
.kpi-card.green::before { background: var(--green); }
.kpi-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; font-family: 'IBM Plex Mono', monospace; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 600; color: var(--text); line-height: 1.1; margin: 0.3rem 0 0.2rem; }
.kpi-delta { font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; }
.kpi-delta.up { color: var(--red); }
.kpi-delta.down { color: var(--green); }
.kpi-delta.neutral { color: var(--text-muted); }

/* Section titles */
.section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem;
}

/* Table */
.contrib-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.contrib-table th {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    padding: 0.5rem 1rem;
    text-align: right;
    border-bottom: 1px solid var(--border);
}
.contrib-table th:first-child { text-align: left; }
.contrib-table td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid rgba(37,42,58,0.5);
    color: var(--text);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    text-align: right;
}
.contrib-table td:first-child { text-align: left; color: var(--text); }
.contrib-table tr:hover td { background: var(--surface2); }
.contrib-table .rank { color: var(--accent); font-weight: 600; min-width: 1.5rem; display: inline-block; }
.bar-cell { display: flex; align-items: center; gap: 0.5rem; justify-content: flex-end; }
.bar-mini { height: 6px; border-radius: 3px; background: var(--accent); min-width: 4px; }

/* Footer */
.footer { font-size: 0.72rem; color: var(--text-muted); text-align: center; padding: 2rem 0 1rem; font-family: 'IBM Plex Mono', monospace; }

/* Stale data warning */
.stale-warn {
    background: rgba(246,173,85,0.1);
    border: 1px solid rgba(246,173,85,0.3);
    border-radius: 6px;
    padding: 0.7rem 1rem;
    font-size: 0.8rem;
    color: var(--accent2);
    margin-bottom: 1rem;
    font-family: 'IBM Plex Mono', monospace;
}

div[data-testid="stTabs"] button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
}
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--accent); }

.stSpinner > div { border-top-color: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FUNÇÕES DE DADOS
# ─────────────────────────────────────────────

BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json&dataInicial=01/01/2017"
SIDRA_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/{}/variaveis/{}?localidades=N1[all]&classificacao=315[all]"

NUCLEOS_SGS = {
    "EX0":  27838,
    "EX3":  27839,
    "MS":   11427,
    "DP":   16122,
}

CLASSIFICACOES_SGS = {
    "Livres":           11428,
    "Comercializáveis": 4447,
    "Não-comercializáveis": 4448,
    "Monitorados":      4449,
    "Serviços":         10844,
    "Alimentação dom.": 1415,
    "Industriais":      4452,
    "Serviços intensivos em trabalho": 28291,
}

DIFUSAO_SGS = 21379

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="#0d0f14",
        plot_bgcolor="#0d0f14",
        font=dict(family="IBM Plex Mono, monospace", color="#e2e8f0", size=11),
        xaxis=dict(gridcolor="#1c2030", linecolor="#252a3a", tickcolor="#252a3a"),
        yaxis=dict(gridcolor="#1c2030", linecolor="#252a3a", tickcolor="#252a3a"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#252a3a", borderwidth=1),
        margin=dict(l=40, r=20, t=40, b=40),
    )
)

COLORS = ["#4fd1c5", "#f6ad55", "#fc8181", "#68d391", "#b794f4", "#76e4f7", "#fbd38d", "#e53e3e"]


@st.cache_data(ttl=3600)
def fetch_sgd(codigo: int) -> pd.Series:
    try:
        r = requests.get(BCB_URL.format(codigo), timeout=20)
        data = r.json()
        df = pd.DataFrame(data)
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce")
        df = df.set_index("data")["valor"].dropna()
        df.index = df.index.to_period("M")
        return df
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600)
def fetch_sidra_subitens(periodo: str = "202001-202412") -> pd.DataFrame:
    """Busca variação mensal (var=63) e peso mensal (var=66) por subitem."""
    try:
        # Variação mensal
        url_var = f"https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/{periodo}/variaveis/63?localidades=N1[all]&classificacao=315[7169,7170,7445,1284,7625,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100]"
        r_var = requests.get(url_var, timeout=30)

        # Peso mensal
        url_peso = f"https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/{periodo}/variaveis/66?localidades=N1[all]&classificacao=315[7169,7170,7445,1284,7625,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100]"
        r_peso = requests.get(url_peso, timeout=30)

        return r_var.json(), r_peso.json()
    except Exception as e:
        return None, None


@st.cache_data(ttl=3600)
def fetch_sidra_grupos() -> pd.DataFrame:
    """Busca variação e peso dos grupos principais (tabela 7060)."""
    try:
        hoje = datetime.now()
        # últimos 36 períodos mensais
        from dateutil.relativedelta import relativedelta
        start = hoje - relativedelta(months=48)
        periodo = f"{start.strftime('%Y%m')}-{hoje.strftime('%Y%m')}"

        url = f"https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/{periodo}/variaveis/63|2265|69|66?localidades=N1[all]&classificacao=315[7169,7170,7445,1284,7625]"
        r = requests.get(url, timeout=30)
        data = r.json()
        return data
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_ipca_series() -> dict:
    """Retorna série do IPCA cheio + acumulados."""
    ipca = fetch_sgd(433)
    if ipca.empty:
        return {}

    # Acumulado 12m
    ipca12 = ((1 + ipca / 100).rolling(12).apply(lambda x: x.prod()) - 1) * 100
    # Acumulado no ano
    def acum_ano(s):
        result = []
        for period in s.index:
            year_data = s[s.index.year == period.year]
            cum = ((1 + year_data / 100).cumprod() - 1) * 100
            result.append(cum.iloc[-1] if len(cum) > 0 else np.nan)
        return pd.Series(result, index=s.index)

    ipcaano = acum_ano(ipca)

    return {"mensal": ipca, "acum12m": ipca12, "acumano": ipcaano}


def parse_sidra_response(data: list) -> pd.DataFrame:
    """Parseia resposta da API SIDRA em DataFrame."""
    rows = []
    if not data:
        return pd.DataFrame()
    for item in data:
        var_id = item.get("id")
        var_nome = item.get("variavel")
        for res in item.get("resultados", []):
            classificacoes = res.get("classificacoes", [])
            cat_nome = ""
            cat_id = ""
            for cl in classificacoes:
                for cat_id_k, cat_nome_v in cl.get("categoria", {}).items():
                    cat_nome = cat_nome_v
                    cat_id = cat_id_k
            for serie in res.get("series", []):
                for periodo, valor in serie.get("serie", {}).items():
                    rows.append({
                        "variavel_id": var_id,
                        "variavel": var_nome,
                        "categoria_id": cat_id,
                        "categoria": cat_nome,
                        "periodo": periodo,
                        "valor": float(valor) if valor not in ["...", "-", ""] else np.nan,
                    })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_nucleos() -> pd.DataFrame:
    nucleos = {}
    for nome, codigo in NUCLEOS_SGS.items():
        s = fetch_sgd(codigo)
        if not s.empty:
            nucleos[nome] = s
    if not nucleos:
        return pd.DataFrame()
    df = pd.DataFrame(nucleos)
    # Mediana dos núcleos (por linha)
    df["Mediana"] = df.median(axis=1)
    # Acumular 12m
    df12 = df.copy()
    for col in df.columns:
        df12[col] = ((1 + df[col] / 100).rolling(12).apply(lambda x: x.prod()) - 1) * 100
    return df, df12


@st.cache_data(ttl=3600)
def get_classificacoes() -> pd.DataFrame:
    series = {}
    for nome, codigo in CLASSIFICACOES_SGS.items():
        s = fetch_sgd(codigo)
        if not s.empty:
            series[nome] = s
    if not series:
        return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(series)
    df12 = df.copy()
    for col in df.columns:
        df12[col] = ((1 + df[col] / 100).rolling(12).apply(lambda x: x.prod()) - 1) * 100
    return df, df12


@st.cache_data(ttl=3600)
def get_difusao() -> pd.Series:
    return fetch_sgd(DIFUSAO_SGS)


# ─────────────────────────────────────────────
# HELPER: últimos N períodos
# ─────────────────────────────────────────────
def last_n(series: pd.Series, n: int = 36) -> pd.Series:
    return series.dropna().iloc[-n:]


def fmt_pct(v, decimals=2):
    if pd.isna(v):
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.{decimals}f}%"


def delta_arrow(v):
    if pd.isna(v):
        return ""
    return "▲" if v > 0 else "▼"


# ─────────────────────────────────────────────
# FUNÇÃO: CONTRIBUIÇÕES POR SUBITEM
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_contribuicoes_ultimo_mes() -> pd.DataFrame:
    """
    Busca variação mensal e peso mensal dos subitens do IPCA do último mês disponível.
    Calcula contribuição = (peso/100) * variação e retorna top 10.
    """
    try:
        hoje = datetime.now()
        # Tenta os últimos 3 meses para garantir que pegamos o mais recente
        from dateutil.relativedelta import relativedelta
        meses = []
        for i in range(3):
            m = hoje - relativedelta(months=i)
            meses.append(m.strftime("%Y%m"))
        periodo = f"{meses[-1]}-{meses[0]}"

        # Variável 63 = variação mensal, 66 = peso mensal
        url = (
            f"https://servicodados.ibge.gov.br/api/v3/agregados/7060"
            f"/periodos/{periodo}/variaveis/63|66"
            f"?localidades=N1[all]"
            f"&classificacao=315[all]"
        )
        r = requests.get(url, timeout=45)
        data = r.json()

        df = parse_sidra_response(data)
        if df.empty:
            return pd.DataFrame()

        # Filtra subitens (exclui índice geral e grupos)
        grupos_excluir = {"Índice geral", "1.Alimentação e bebidas", "2.Habitação",
                          "3.Artigos de residência", "4.Vestuário", "5.Transportes",
                          "6.Saúde e cuidados pessoais", "7.Despesas pessoais",
                          "8.Educação", "9.Comunicação"}

        df_filtered = df[~df["categoria"].isin(grupos_excluir)].copy()

        # Separa variação e peso
        df_var = df_filtered[df_filtered["variavel_id"] == "63"].copy()
        df_peso = df_filtered[df_filtered["variavel_id"] == "66"].copy()

        # Pega o período mais recente disponível
        periodos_disponiveis = sorted(df_var["periodo"].unique(), reverse=True)
        if not periodos_disponiveis:
            return pd.DataFrame()

        ultimo_periodo = periodos_disponiveis[0]

        df_var_last = df_var[df_var["periodo"] == ultimo_periodo][["categoria", "valor"]].rename(columns={"valor": "variacao"})
        df_peso_last = df_peso[df_peso["periodo"] == ultimo_periodo][["categoria", "valor"]].rename(columns={"valor": "peso"})

        merged = df_var_last.merge(df_peso_last, on="categoria", how="inner")
        merged = merged.dropna(subset=["variacao", "peso"])
        merged["contribuicao"] = (merged["peso"] / 100) * merged["variacao"]

        # IPCA cheio do período
        ipca_total = merged["contribuicao"].sum()
        if ipca_total != 0:
            merged["pct_total"] = (merged["contribuicao"] / abs(ipca_total)) * 100
        else:
            merged["pct_total"] = np.nan

        top10 = merged.nlargest(10, "contribuicao").reset_index(drop=True)
        top10.index = top10.index + 1

        return top10, ultimo_periodo, ipca_total

    except Exception as e:
        return pd.DataFrame(), "", 0.0


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
agora = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="header-box">
  <div class="header-title">// Monitor IPCA</div>
  <div class="header-sub">Índice Nacional de Preços ao Consumidor Amplo · IBGE/BCB · Atualizado: {agora}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CARREGA DADOS PRINCIPAIS
# ─────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    ipca_dict = get_ipca_series()
    difusao = get_difusao()

if not ipca_dict or "mensal" not in ipca_dict:
    st.error("Não foi possível carregar os dados do IPCA. Tente novamente em alguns instantes.")
    st.stop()

ipca_m = ipca_dict["mensal"]
ipca_12 = ipca_dict["acum12m"].dropna()
ipca_ano = ipca_dict["acumano"].dropna()

ultimo = ipca_m.dropna().iloc[-1]
penultimo = ipca_m.dropna().iloc[-2]
delta_m = ultimo - penultimo
acum12_atual = ipca_12.iloc[-1] if not ipca_12.empty else np.nan
acum12_ant = ipca_12.iloc[-2] if len(ipca_12) >= 2 else np.nan
delta_12 = acum12_atual - acum12_ant
acumano_atual = ipca_ano.iloc[-1] if not ipca_ano.empty else np.nan
dif_ultimo = not difusao.empty

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
ref_periodo = str(ipca_m.dropna().index[-1])

def kpi_html(label, value, delta, delta_label, card_class=""):
    delta_class = "up" if delta > 0 else ("down" if delta < 0 else "neutral")
    arrow = delta_arrow(delta)
    return f"""
    <div class="kpi-card {card_class}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-delta {delta_class}">{arrow} {delta_label}</div>
    </div>"""

dif_val = f"{difusao.dropna().iloc[-1]:.1f}%" if dif_ultimo else "—"
dif_delta = (difusao.dropna().iloc[-1] - difusao.dropna().iloc[-2]) if dif_ultimo and len(difusao.dropna()) >= 2 else 0

st.markdown(f"""
<div class="kpi-grid">
  {kpi_html(f"IPCA Mensal · {ref_periodo}", fmt_pct(ultimo), delta_m, f"vs mês anterior ({fmt_pct(penultimo)})", "orange" if ultimo > 0.5 else "")}
  {kpi_html("Acumulado 12 meses", fmt_pct(acum12_atual), delta_12, f"vs 12m anterior ({fmt_pct(acum12_ant)})", "red" if acum12_atual > 6 else "")}
  {kpi_html(f"Acumulado no ano", fmt_pct(acumano_atual), 0, f"Ref: {ipca_ano.index[-1].year}" if not ipca_ano.empty else "", "green")}
  {kpi_html("Índice de Difusão", dif_val, dif_delta, f"vs mês anterior")}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ABAS
# ─────────────────────────────────────────────
tabs = st.tabs(["📈 Headline", "🗂️ Grupos & Classificações", "🎯 Núcleos", "🔀 Difusão", "🏆 Top Contribuições"])

# ════════════════════════════════════════════
# ABA 1 — HEADLINE
# ════════════════════════════════════════════
with tabs[0]:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Variação Mensal (% a.m.)</div>', unsafe_allow_html=True)
        s = last_n(ipca_m, 36)
        cores = ["#fc8181" if v > 0 else "#68d391" for v in s.values]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[str(p) for p in s.index],
            y=s.values,
            marker_color=cores,
            name="IPCA m/m",
        ))
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=320, title="")
        fig.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Acumulado 12 Meses (% a.a.)</div>', unsafe_allow_html=True)
        s12 = last_n(ipca_12, 48)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[str(p) for p in s12.index],
            y=s12.values,
            mode="lines",
            line=dict(color="#4fd1c5", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(79,209,197,0.08)",
            name="12m",
        ))
        # Meta de inflação (banda 1.5pp em torno da meta)
        meta_anos = {2022: 3.5, 2023: 3.25, 2024: 3.0, 2025: 3.0, 2026: 3.0}
        for ano, meta in meta_anos.items():
            periodos_ano = [str(p) for p in s12.index if p.year == ano]
            if periodos_ano:
                fig2.add_shape(type="rect",
                    x0=periodos_ano[0], x1=periodos_ano[-1],
                    y0=meta-1.5, y1=meta+1.5,
                    fillcolor="rgba(104,211,145,0.06)", line=dict(width=0))
        fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=320)
        fig2.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig2, use_container_width=True)

    # Acumulado no ano + tabela resumo
    col3, col4 = st.columns([2, 1])
    with col3:
        st.markdown('<div class="section-title">Acumulado no Ano (%)</div>', unsafe_allow_html=True)
        s_ano = last_n(ipca_ano, 36)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=[str(p) for p in s_ano.index],
            y=s_ano.values,
            mode="lines",
            line=dict(color="#f6ad55", width=2),
            name="Acum. ano",
        ))
        fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=260)
        fig3.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Resumo Recente</div>', unsafe_allow_html=True)
        ultimos_12 = ipca_m.dropna().iloc[-12:]
        rows_html = ""
        for period, val in reversed(list(ultimos_12.items())):
            cor = "#fc8181" if val > 0.5 else ("#f6ad55" if val > 0.3 else "#68d391")
            rows_html += f"<tr><td style='text-align:left'>{period}</td><td style='color:{cor}'>{fmt_pct(val)}</td></tr>"
        st.markdown(f"""
        <table class="contrib-table" style="font-size:0.78rem">
          <thead><tr><th style="text-align:left">Período</th><th>Var. m/m</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)


# ════════════════════════════════════════════
# ABA 2 — GRUPOS & CLASSIFICAÇÕES
# ════════════════════════════════════════════
with tabs[1]:
    with st.spinner("Carregando classificações..."):
        df_class, df_class12 = get_classificacoes()

    if not df_class.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Variação Mensal por Classificação</div>', unsafe_allow_html=True)
            df_plot = df_class.dropna(how="all").iloc[-24:]
            fig = go.Figure()
            for i, col in enumerate(df_plot.columns):
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in df_plot.index],
                    y=df_plot[col],
                    name=col,
                    line=dict(color=COLORS[i % len(COLORS)], width=1.8),
                    mode="lines",
                ))
            fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
            fig.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Acumulado 12m por Classificação</div>', unsafe_allow_html=True)
            df_plot12 = df_class12.dropna(how="all").iloc[-24:]
            fig2 = go.Figure()
            for i, col in enumerate(df_plot12.columns):
                fig2.add_trace(go.Scatter(
                    x=[str(p) for p in df_plot12.index],
                    y=df_plot12[col],
                    name=col,
                    line=dict(color=COLORS[i % len(COLORS)], width=1.8),
                    mode="lines",
                ))
            fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
            fig2.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig2, use_container_width=True)

        # Tabela snapshot do último mês
        st.markdown('<div class="section-title">Snapshot — Último Mês Disponível</div>', unsafe_allow_html=True)
        last_row = df_class.dropna(how="all").iloc[-1]
        last_12_row = df_class12.dropna(how="all").iloc[-1]
        snap_df = pd.DataFrame({
            "Classificação": last_row.index,
            "Var. Mensal": last_row.values,
            "Acum. 12m": last_12_row.values,
        })
        rows_html = ""
        for _, r in snap_df.iterrows():
            cor_m = "#fc8181" if r["Var. Mensal"] > 0.5 else ("#f6ad55" if r["Var. Mensal"] > 0 else "#68d391")
            cor_12 = "#fc8181" if r["Acum. 12m"] > 6 else ("#f6ad55" if r["Acum. 12m"] > 3 else "#68d391")
            rows_html += f"<tr><td style='text-align:left'>{r['Classificação']}</td><td style='color:{cor_m}'>{fmt_pct(r['Var. Mensal'])}</td><td style='color:{cor_12}'>{fmt_pct(r['Acum. 12m'])}</td></tr>"
        st.markdown(f"""
        <table class="contrib-table">
          <thead><tr><th style="text-align:left">Classificação</th><th>Var. Mensal</th><th>Acum. 12m</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.info("Dados de classificações não disponíveis no momento.")


# ════════════════════════════════════════════
# ABA 3 — NÚCLEOS
# ════════════════════════════════════════════
with tabs[2]:
    with st.spinner("Carregando núcleos..."):
        result_nuc = get_nucleos()

    if isinstance(result_nuc, tuple) and len(result_nuc) == 2:
        df_nuc, df_nuc12 = result_nuc

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Núcleos — Variação Mensal (% a.m.)</div>', unsafe_allow_html=True)
            df_plot = df_nuc.dropna(how="all").iloc[-36:]
            fig = go.Figure()
            # IPCA cheio como referência
            ipca_ref = last_n(ipca_m, 36)
            fig.add_trace(go.Bar(
                x=[str(p) for p in ipca_ref.index],
                y=ipca_ref.values,
                name="IPCA cheio",
                marker_color="rgba(255,255,255,0.08)",
                marker_line_width=0,
            ))
            styles = {"EX0": "#4fd1c5", "EX3": "#f6ad55", "MS": "#fc8181", "DP": "#68d391", "Mediana": "#b794f4"}
            dashes = {"Mediana": "dash"}
            for col in df_plot.columns:
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in df_plot.index],
                    y=df_plot[col],
                    name=col,
                    line=dict(color=styles.get(col, "#76e4f7"), width=2.2 if col != "Mediana" else 2,
                              dash=dashes.get(col, "solid")),
                    mode="lines",
                ))
            fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
            fig.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Núcleos — Acumulado 12 Meses (% a.a.)</div>', unsafe_allow_html=True)
            df_plot12 = df_nuc12.dropna(how="all").iloc[-36:]
            fig2 = go.Figure()
            ipca12_ref = last_n(ipca_12, 36)
            fig2.add_trace(go.Scatter(
                x=[str(p) for p in ipca12_ref.index],
                y=ipca12_ref.values,
                name="IPCA 12m",
                line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dot"),
                mode="lines",
            ))
            for col in df_plot12.columns:
                fig2.add_trace(go.Scatter(
                    x=[str(p) for p in df_plot12.index],
                    y=df_plot12[col],
                    name=col,
                    line=dict(color=styles.get(col, "#76e4f7"), width=2.2 if col != "Mediana" else 2,
                              dash=dashes.get(col, "solid")),
                    mode="lines",
                ))
            fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
            fig2.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig2, use_container_width=True)

        # Tabela snapshot núcleos
        st.markdown('<div class="section-title">Núcleos — Snapshot Último Mês</div>', unsafe_allow_html=True)
        last_nuc = df_nuc.dropna(how="all").iloc[-1]
        last_nuc12 = df_nuc12.dropna(how="all").iloc[-1]
        rows_html = ""
        desc = {
            "EX0": "Excl. alim. domicílio + monitorados",
            "EX3": "Excl. alim. domicílio + monitorados + semi-dur.",
            "MS":  "Médias aparadas com suavização",
            "DP":  "Dupla ponderação",
            "Mediana": "Mediana dos quatro núcleos acima",
        }
        for nome in df_nuc.columns:
            v_m = last_nuc.get(nome, np.nan)
            v_12 = last_nuc12.get(nome, np.nan)
            cor_m = "#fc8181" if v_m > 0.5 else ("#f6ad55" if v_m > 0.3 else "#68d391")
            rows_html += f"""
            <tr>
              <td style='text-align:left'><span style='color:{styles.get(nome,"#fff")};font-weight:600'>{nome}</span></td>
              <td style='text-align:left;color:var(--text-muted);font-size:0.75rem'>{desc.get(nome,'')}</td>
              <td style='color:{cor_m}'>{fmt_pct(v_m)}</td>
              <td>{fmt_pct(v_12)}</td>
            </tr>"""
        st.markdown(f"""
        <table class="contrib-table">
          <thead><tr><th style="text-align:left">Núcleo</th><th style="text-align:left">Descrição</th><th>Var. Mensal</th><th>Acum. 12m</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.72rem;color:var(--text-muted);margin-top:1rem;font-family:'IBM Plex Mono',monospace">
        ⓘ P55 (percentil 55 ponderado) não é disponibilizado como série SGS direta pelo BCB — é calculado internamente.
        A mediana acima é calculada sobre EX0, EX3, MS e DP.
        Fonte: BCB/SGS.
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Dados de núcleos não disponíveis no momento.")


# ════════════════════════════════════════════
# ABA 4 — DIFUSÃO
# ════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-title">Índice de Difusão — % de itens com variação positiva</div>', unsafe_allow_html=True)
    if not difusao.empty:
        dif = last_n(difusao, 48)
        dif_ma3 = dif.rolling(3).mean()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[str(p) for p in dif.index],
            y=dif.values,
            name="Difusão",
            marker_color="rgba(79,209,197,0.4)",
            marker_line_width=0,
        ))
        fig.add_trace(go.Scatter(
            x=[str(p) for p in dif_ma3.index],
            y=dif_ma3.values,
            name="Média 3m",
            line=dict(color="#f6ad55", width=2),
            mode="lines",
        ))
        fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.2)", annotation_text="50%")
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=380, yaxis_ticksuffix="%")
        fig.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Difusão atual", f"{dif.iloc[-1]:.1f}%")
        col2.metric("Média 3m", f"{dif_ma3.iloc[-1]:.1f}%")
        col3.metric("Média 12m", f"{dif.iloc[-12:].mean():.1f}%")
    else:
        st.info("Dados de difusão não disponíveis.")


# ════════════════════════════════════════════
# ABA 5 — TOP CONTRIBUIÇÕES
# ════════════════════════════════════════════
with tabs[4]:
    with st.spinner("Calculando contribuições por subitem..."):
        result_contrib = get_contribuicoes_ultimo_mes()

    if isinstance(result_contrib, tuple) and len(result_contrib) == 3:
        top10, ultimo_periodo, ipca_total = result_contrib

        if not top10.empty:
            # Formata período
            periodo_fmt = f"{ultimo_periodo[4:6]}/{ultimo_periodo[:4]}" if len(ultimo_periodo) == 6 else ultimo_periodo

            st.markdown(f'<div class="section-title">Top 10 Subitens — Maiores Contribuições · {periodo_fmt}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-size:0.78rem;color:var(--text-muted);font-family:'IBM Plex Mono',monospace;margin-bottom:1rem">
            IPCA cheio reconstruído (soma contribuições): <span style="color:var(--accent);font-weight:600">{fmt_pct(ipca_total)}</span>
            &nbsp;·&nbsp; Contribuição = (Peso ÷ 100) × Variação mensal &nbsp;·&nbsp; Fonte: IBGE/SIDRA
            </div>""", unsafe_allow_html=True)

            max_contrib = top10["contribuicao"].max()
            rows_html = ""
            for i, row in top10.iterrows():
                bar_w = int((row["contribuicao"] / max_contrib) * 120) if max_contrib > 0 else 0
                cor = "#fc8181" if row["contribuicao"] > 0.1 else ("#f6ad55" if row["contribuicao"] > 0.05 else "#4fd1c5")
                rows_html += f"""
                <tr>
                  <td style='text-align:left'><span class='rank'>{i}</span> {row['categoria']}</td>
                  <td>{fmt_pct(row['peso'], 4)}</td>
                  <td style='color:{cor}'>{fmt_pct(row['variacao'])}</td>
                  <td>
                    <div class="bar-cell">
                      <span style='color:{cor}'>{fmt_pct(row['contribuicao'], 4)}</span>
                      <div class="bar-mini" style="width:{bar_w}px;background:{cor}"></div>
                    </div>
                  </td>
                  <td style='color:{cor};font-weight:600'>{row['pct_total']:.1f}%</td>
                </tr>"""

            st.markdown(f"""
            <table class="contrib-table">
              <thead>
                <tr>
                  <th style="text-align:left">Subitem</th>
                  <th>Peso (%)</th>
                  <th>Var. Mensal</th>
                  <th>Contribuição (p.p.)</th>
                  <th>% do IPCA</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>""", unsafe_allow_html=True)

            # Gráfico de barras horizontal
            st.markdown('<div class="section-title" style="margin-top:1.5rem">Visualização das Contribuições</div>', unsafe_allow_html=True)
            fig = go.Figure()
            categorias = [f"{i}. {r['categoria'][:35]}..." if len(r['categoria']) > 35 else f"{i}. {r['categoria']}"
                          for i, r in top10.iterrows()]
            fig.add_trace(go.Bar(
                y=categorias[::-1],
                x=top10["contribuicao"].values[::-1],
                orientation="h",
                marker_color=["#fc8181" if v > 0.1 else "#f6ad55" for v in top10["contribuicao"].values[::-1]],
                text=[fmt_pct(v, 4) for v in top10["contribuicao"].values[::-1]],
                textposition="outside",
                textfont=dict(size=10, color="#e2e8f0"),
            ))
            fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=420, xaxis_ticksuffix=" p.p.")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Dados de contribuição não disponíveis para o período mais recente.")
    else:
        st.info("Dados de contribuição não puderam ser carregados.")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Fontes: IBGE/SIDRA (Tabela 7060) · BCB/SGS · Dados atualizados automaticamente a cada hora.<br>
  Monitor IPCA — uso analítico · Elaborado com Streamlit + Plotly
</div>
""", unsafe_allow_html=True)
