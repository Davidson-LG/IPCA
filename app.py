import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────
st.set_page_config(page_title="Monitor IPCA", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
:root {
  --bg:#0d0f14; --surface:#151820; --surface2:#1c2030; --border:#252a3a;
  --accent:#4fd1c5; --accent2:#f6ad55; --accent3:#fc8181;
  --text:#e2e8f0; --muted:#718096; --green:#68d391; --red:#fc8181;
}
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);}
.main{background:var(--bg);}
.block-container{padding:1.5rem 2rem;max-width:1400px;}
.header-box{background:linear-gradient(135deg,#151820,#1a1f30);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:8px;padding:1.5rem 2rem;margin-bottom:1.5rem;}
.header-title{font-family:'IBM Plex Mono',monospace;font-size:1.8rem;font-weight:600;color:var(--accent);letter-spacing:-.02em;margin:0;}
.header-sub{font-size:.85rem;color:var(--muted);margin-top:.3rem;font-family:'IBM Plex Mono',monospace;}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.2rem 1.5rem;position:relative;overflow:hidden;}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent);}
.kpi-card.orange::before{background:var(--accent2);}
.kpi-card.red::before{background:var(--accent3);}
.kpi-card.green::before{background:var(--green);}
.kpi-label{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-family:'IBM Plex Mono',monospace;}
.kpi-value{font-family:'IBM Plex Mono',monospace;font-size:2.2rem;font-weight:600;color:var(--text);line-height:1.1;margin:.3rem 0 .2rem;}
.kpi-delta{font-size:.78rem;font-family:'IBM Plex Mono',monospace;}
.kpi-delta.up{color:var(--red);}
.kpi-delta.down{color:var(--green);}
.kpi-delta.neutral{color:var(--muted);}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;border-bottom:1px solid var(--border);padding-bottom:.5rem;margin:1.5rem 0 1rem;}
.contrib-table{width:100%;border-collapse:collapse;font-size:.88rem;}
.contrib-table th{font-family:'IBM Plex Mono',monospace;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);padding:.5rem 1rem;text-align:right;border-bottom:1px solid var(--border);}
.contrib-table th:first-child{text-align:left;}
.contrib-table td{padding:.6rem 1rem;border-bottom:1px solid rgba(37,42,58,.5);font-family:'IBM Plex Mono',monospace;font-size:.82rem;text-align:right;}
.contrib-table td:first-child{text-align:left;}
.contrib-table tr:hover td{background:var(--surface2);}
.rank{color:var(--accent);font-weight:600;min-width:1.5rem;display:inline-block;}
.footer{font-size:.72rem;color:var(--muted);text-align:center;padding:2rem 0 1rem;font-family:'IBM Plex Mono',monospace;}
div[data-testid="stTabs"] button{font-family:'IBM Plex Mono',monospace;font-size:.8rem;color:var(--muted);}
div[data-testid="stTabs"] button[aria-selected="true"]{color:var(--accent);}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json&dataInicial=01/01/2015"

SGS = {
    "IPCA":             433,
    "EX0":              27838,
    "EX3":              27839,
    "MS":               11427,
    "DP":               16122,
    "Difusão":          21379,
    "Livres":           11428,
    "Comercializáveis": 4447,
    "Não-comerc.":      4448,
    "Monitorados":      4449,
    "Serviços":         10844,
    "Alim. domicílio":  1415,
    "Industriais":      11465,       # IPCA-bens industriais (correto)
    "Serv. int. trabalho": 10843,    # serviços intensivos em trabalho
    "Duráveis":         10841,
    "Semi-duráveis":    10842,
    "Não-duráveis":     10843,
}

# Só essas séries vão na aba Grupos
CLASSIFICACOES = {
    "Livres":           11428,
    "Comercializáveis": 4447,
    "Não-comerc.":      4448,
    "Monitorados":      4449,
    "Serviços":         10844,
    "Alim. domicílio":  1415,
    "Industriais":      11465,
    "Serv. int. trabalho": 10843,
}

NUCLEOS_SGS = {"EX0": 27838, "EX3": 27839, "MS": 11427, "DP": 16122}

LAYOUT = dict(
    paper_bgcolor="#0d0f14", plot_bgcolor="#0d0f14",
    font=dict(family="IBM Plex Mono, monospace", color="#e2e8f0", size=11),
    xaxis=dict(gridcolor="#1c2030", linecolor="#252a3a", tickcolor="#252a3a"),
    yaxis=dict(gridcolor="#1c2030", linecolor="#252a3a", tickcolor="#252a3a"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#252a3a", borderwidth=1),
    margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
)

def ann(label_text):
    """Anotação de último valor num gráfico."""
    return label_text

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt(v, d=2):
    if pd.isna(v): return "—"
    s = "+" if v > 0 else ""
    return f"{s}{v:.{d}f}%"

def arrow(v):
    if pd.isna(v): return ""
    return "▲" if v > 0 else "▼"

def acum12(s: pd.Series) -> pd.Series:
    return ((1 + s/100).rolling(12).apply(np.prod) - 1) * 100

def acumano(s: pd.Series) -> pd.Series:
    out = []
    for p in s.index:
        yr = s[s.index.year == p.year]
        out.append(((1 + yr/100).cumprod() - 1).iloc[-1] * 100)
    return pd.Series(out, index=s.index)

def ma3(s: pd.Series) -> pd.Series:
    return s.rolling(3).mean()

def last_n(s: pd.Series, n=36) -> pd.Series:
    return s.dropna().iloc[-n:]

def add_last_annotation(fig, x_vals, y_vals, color="#4fd1c5", row=None, col=None):
    """Adiciona anotação com valor do último ponto."""
    if len(y_vals) == 0: return
    last_x = str(x_vals[-1])
    last_y = y_vals[-1]
    if pd.isna(last_y): return
    kwargs = dict(
        x=last_x, y=last_y,
        text=f" {last_y:.2f}%",
        showarrow=False,
        font=dict(size=10, color=color),
        xanchor="left",
    )
    if row and col:
        kwargs.update(row=row, col=col)
    fig.add_annotation(**kwargs)

# ─────────────────────────────────────────────
# FETCH SGS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch(codigo: int) -> pd.Series:
    try:
        r = requests.get(BCB.format(codigo), timeout=25)
        df = pd.DataFrame(r.json())
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
        s = df.set_index("data")["valor"].dropna()
        s.index = s.index.to_period("M")
        return s
    except Exception:
        return pd.Series(dtype=float)

# ─────────────────────────────────────────────
# FETCH SIDRA — grupos (variável 63 = var mensal)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_sidra_grupos() -> pd.DataFrame:
    """Retorna DataFrame com var. mensal por grupo (colunas = grupos, índice = período)."""
    hoje = datetime.now()
    start = hoje - relativedelta(months=50)
    periodo = f"{start.strftime('%Y%m')}-{hoje.strftime('%Y%m')}"
    # variável 63 = variação mensal; classificação 315 = estrutura do IPCA
    # categorias dos grupos principais: 7169=Geral, 7170=Alimentação, 7445=Habitação,
    # 1284=Artigos residência, 7625=Vestuário, e os demais grupos
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/7060"
        f"/periodos/{periodo}/variaveis/63"
        f"?localidades=N1[all]&classificacao=315[7169,7170,7445,1284,7625,7626,7627,7628,7629,7630]"
    )
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        rows = []
        for item in data:
            for res in item.get("resultados", []):
                cat = list(res["classificacoes"][0]["categoria"].values())[0]
                for serie in res.get("series", []):
                    for periodo_k, valor in serie["serie"].items():
                        try:
                            v = float(valor)
                        except (ValueError, TypeError):
                            v = np.nan
                        rows.append({"categoria": cat, "periodo": periodo_k, "valor": v})
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame()
        df["periodo"] = pd.to_datetime(df["periodo"], format="%Y%m").dt.to_period("M")
        df = df.pivot(index="periodo", columns="categoria", values="valor").sort_index()
        return df
    except Exception:
        return pd.DataFrame()

# ─────────────────────────────────────────────
# FETCH SIDRA — contribuições subitens + subgrupos + grupos
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_contribuicoes():
    """
    Busca variação mensal (var 63) e peso (var 66) para subitens, subgrupos e grupos.
    Retorna (top10_subitens, top10_subgrupos, top5_grupos, periodo_str, ipca_total).
    """
    hoje = datetime.now()
    start = hoje - relativedelta(months=3)
    periodo = f"{start.strftime('%Y%m')}-{hoje.strftime('%Y%m')}"

    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/7060"
        f"/periodos/{periodo}/variaveis/63|66"
        f"?localidades=N1[all]&classificacao=315[all]"
    )
    try:
        r = requests.get(url, timeout=45)
        data = r.json()
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "", 0.0

    rows = []
    for item in data:
        var_id = item.get("id")
        for res in item.get("resultados", []):
            cl = res.get("classificacoes", [{}])[0]
            cat_items = cl.get("categoria", {})
            for cat_id, cat_nome in cat_items.items():
                for serie in res.get("series", []):
                    for periodo_k, valor in serie["serie"].items():
                        try:
                            v = float(valor)
                        except (ValueError, TypeError):
                            v = np.nan
                        rows.append({
                            "var_id": var_id,
                            "cat_id": int(cat_id),
                            "cat_nome": cat_nome,
                            "periodo": periodo_k,
                            "valor": v,
                        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "", 0.0

    # Período mais recente
    ultimo = sorted(df["periodo"].unique(), reverse=True)[0]

    df_u = df[df["periodo"] == ultimo].copy()
    df_var = df_u[df_u["var_id"] == "63"][["cat_id","cat_nome","valor"]].rename(columns={"valor":"variacao"})
    df_pes = df_u[df_u["var_id"] == "66"][["cat_id","valor"]].rename(columns={"valor":"peso"})
    merged = df_var.merge(df_pes, on="cat_id", how="inner").dropna(subset=["variacao","peso"])
    merged["contribuicao"] = (merged["peso"] / 100) * merged["variacao"]

    # Hierarquia IBGE: cat_id < 100 = grupos; 100-999 = subgrupos; >= 1000 = subitens
    # Grupos principais têm IDs específicos (7169=Geral, 7170=Alimentação, etc.)
    # Usamos a nomenclatura: grupos id<10000 e com "." no nome = grupos/subgrupos
    # Subitens são os mais granulares — cat_id >= 7000 ou nomes sem "."
    # Abordagem: separar pelo padrão do nome
    def nivel(nome):
        # Grupos têm format "N.Descrição" onde N é 1 dígito
        import re
        if re.match(r'^\d\.', nome): return "grupo"
        if re.match(r'^\d{1,2}\.\d{1,2}', nome): return "subgrupo"
        if nome in ["Índice geral"]: return "geral"
        return "subitem"

    merged["nivel"] = merged["cat_nome"].apply(nivel)

    ipca_total = merged[merged["nivel"] == "geral"]["contribuicao"].sum()
    if ipca_total == 0:
        ipca_total = merged[merged["nivel"] == "subitem"]["contribuicao"].sum()

    def top10_df(filtro_nivel):
        sub = merged[merged["nivel"] == filtro_nivel].copy()
        sub = sub.dropna(subset=["contribuicao"])
        sub = sub.nlargest(10, "contribuicao").reset_index(drop=True)
        sub.index += 1
        if ipca_total != 0:
            sub["pct_total"] = (sub["contribuicao"] / abs(ipca_total)) * 100
        else:
            sub["pct_total"] = np.nan
        return sub

    top_sub    = top10_df("subitem")
    top_subgrp = top10_df("subgrupo")
    top_grp    = top10_df("grupo")

    periodo_fmt = f"{ultimo[4:6]}/{ultimo[:4]}" if len(ultimo) == 6 else ultimo
    return top_sub, top_subgrp, top_grp, periodo_fmt, ipca_total

# ─────────────────────────────────────────────
# CARREGA DADOS PRINCIPAIS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all():
    ipca = fetch(433)
    nucleos = {n: fetch(c) for n, c in NUCLEOS_SGS.items()}
    classif = {n: fetch(c) for n, c in CLASSIFICACOES.items()}
    difusao = fetch(21379)
    return ipca, nucleos, classif, difusao

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
agora = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="header-box">
  <div class="header-title">// Monitor IPCA</div>
  <div class="header-sub">Índice Nacional de Preços ao Consumidor Amplo · Fonte: IBGE/SIDRA &amp; BCB/SGS · {agora}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Carregando dados..."):
    ipca, nucleos_raw, classif_raw, difusao = load_all()

if ipca.empty:
    st.error("Falha ao carregar IPCA. Tente recarregar a página.")
    st.stop()

# Derivados do IPCA
ipca_12  = acum12(ipca).dropna()
ipca_ano = acumano(ipca.dropna())
ipca_ma  = ma3(ipca).dropna()

ultimo_val   = ipca.dropna().iloc[-1]
penultimo_val= ipca.dropna().iloc[-2]
delta_m      = ultimo_val - penultimo_val
acum12_val   = ipca_12.iloc[-1] if not ipca_12.empty else np.nan
acum12_ant   = ipca_12.iloc[-2] if len(ipca_12) >= 2 else np.nan
acumano_val  = ipca_ano.iloc[-1] if not ipca_ano.empty else np.nan
ref_periodo  = str(ipca.dropna().index[-1])

dif_val   = difusao.dropna().iloc[-1]  if not difusao.empty else np.nan
dif_delta = (difusao.dropna().iloc[-1] - difusao.dropna().iloc[-2]) if len(difusao.dropna()) >= 2 else 0

def kpi(label, value, delta, sub, cls=""):
    dc = "up" if delta > 0 else ("down" if delta < 0 else "neutral")
    return f"""<div class="kpi-card {cls}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-delta {dc}">{arrow(delta)} {sub}</div>
</div>"""

st.markdown(f"""
<div class="kpi-grid">
  {kpi(f"IPCA Mensal · {ref_periodo}", fmt(ultimo_val), delta_m, f"vs mês ant. ({fmt(penultimo_val)})", "orange" if ultimo_val>0.5 else "")}
  {kpi("Acumulado 12 meses", fmt(acum12_val), acum12_val-acum12_ant if not pd.isna(acum12_ant) else 0, f"ant.: {fmt(acum12_ant)}", "red" if acum12_val>6 else "")}
  {kpi(f"Acumulado {ipca_ano.index[-1].year}", fmt(acumano_val), 0, f"até {ref_periodo}", "green")}
  {kpi("Índice de Difusão", f"{dif_val:.1f}%" if not pd.isna(dif_val) else "—", dif_delta, "vs mês anterior")}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ABAS
# ─────────────────────────────────────────────
tabs = st.tabs(["📈 Headline", "🗂️ Grupos & Classificações", "🎯 Núcleos", "🔀 Difusão", "🏆 Top Contribuições"])

# ══════════════════════════════════════════════════════
# ABA 1 — HEADLINE
# ══════════════════════════════════════════════════════
with tabs[0]:
    col1, col2 = st.columns(2)

    # — Variação mensal + MM3
    with col1:
        st.markdown('<div class="section-title">Variação Mensal (% a.m.)</div>', unsafe_allow_html=True)
        s = last_n(ipca, 36)
        s_ma = ma3(s).dropna()
        xs = [str(p) for p in s.index]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=xs, y=s.values,
            name="IPCA m/m",
            marker_color=["#fc8181" if v>0 else "#68d391" for v in s.values],
            marker_line_width=0,
        ))
        fig.add_trace(go.Scatter(
            x=[str(p) for p in s_ma.index], y=s_ma.values,
            name="MM3", line=dict(color="#f6ad55", width=2, dash="dot"), mode="lines",
        ))
        add_last_annotation(fig, list(s_ma.index), s_ma.values, "#f6ad55")
        fig.update_layout(**LAYOUT, height=320,
            title=dict(text=f"Último: <b>{fmt(ultimo_val)}</b>  |  MM3: <b>{fmt(s_ma.iloc[-1])}</b>", font=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)

    # — Acumulado 12m + MM3
    with col2:
        st.markdown('<div class="section-title">Acumulado 12 Meses (% a.a.)</div>', unsafe_allow_html=True)
        s12 = last_n(ipca_12, 48)
        s12_ma = ma3(s12).dropna()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[str(p) for p in s12.index], y=s12.values,
            name="12m", line=dict(color="#4fd1c5", width=2.5),
            fill="tozeroy", fillcolor="rgba(79,209,197,0.08)",
        ))
        fig2.add_trace(go.Scatter(
            x=[str(p) for p in s12_ma.index], y=s12_ma.values,
            name="MM3", line=dict(color="#f6ad55", width=2, dash="dot"), mode="lines",
        ))
        # Banda da meta
        for ano, meta in {2022:3.5,2023:3.25,2024:3.0,2025:3.0,2026:3.0}.items():
            ps = [str(p) for p in s12.index if p.year==ano]
            if ps:
                fig2.add_shape(type="rect", x0=ps[0], x1=ps[-1], y0=meta-1.5, y1=meta+1.5,
                    fillcolor="rgba(104,211,145,0.06)", line=dict(width=0))
        add_last_annotation(fig2, list(s12.index), s12.values, "#4fd1c5")
        fig2.update_layout(**LAYOUT, height=320,
            title=dict(text=f"Último: <b>{fmt(s12.iloc[-1])}</b>  |  MM3: <b>{fmt(s12_ma.iloc[-1])}</b>", font=dict(size=12)))
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns([2,1])

    # — Acumulado no ano (mesmo estilo do 12m)
    with col3:
        st.markdown('<div class="section-title">Acumulado no Ano (%)</div>', unsafe_allow_html=True)
        s_ano = last_n(ipca_ano, 48)
        s_ano_ma = ma3(s_ano).dropna()
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=[str(p) for p in s_ano.index], y=s_ano.values,
            name="Acum. ano", line=dict(color="#4fd1c5", width=2.5),
            fill="tozeroy", fillcolor="rgba(79,209,197,0.08)",
        ))
        fig3.add_trace(go.Scatter(
            x=[str(p) for p in s_ano_ma.index], y=s_ano_ma.values,
            name="MM3", line=dict(color="#f6ad55", width=2, dash="dot"), mode="lines",
        ))
        add_last_annotation(fig3, list(s_ano.index), s_ano.values, "#4fd1c5")
        fig3.update_layout(**LAYOUT, height=280,
            title=dict(text=f"Último: <b>{fmt(s_ano.iloc[-1])}</b>  |  MM3: <b>{fmt(s_ano_ma.iloc[-1]) if not s_ano_ma.empty else '—'}</b>", font=dict(size=12)))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Resumo Recente</div>', unsafe_allow_html=True)
        ultimos = ipca.dropna().iloc[-14:]
        rows_html = ""
        for period, val in reversed(list(ultimos.items())):
            cor = "#fc8181" if val>0.5 else ("#f6ad55" if val>0.3 else "#68d391")
            rows_html += f"<tr><td style='text-align:left'>{period}</td><td style='color:{cor}'>{fmt(val)}</td></tr>"
        st.markdown(f"""
        <table class="contrib-table" style="font-size:.78rem">
          <thead><tr><th style="text-align:left">Período</th><th>Var. m/m</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ABA 2 — GRUPOS & CLASSIFICAÇÕES
# ══════════════════════════════════════════════════════
with tabs[1]:
    # Constrói df das classificações via SGS (correto)
    frames = {}
    for nome, serie in classif_raw.items():
        if not serie.empty:
            frames[nome] = serie

    if frames:
        df_cl = pd.DataFrame(frames).dropna(how="all")
        df_cl12 = pd.DataFrame({c: acum12(df_cl[c]) for c in df_cl.columns}).dropna(how="all")

        CORES_CL = ["#4fd1c5","#f6ad55","#fc8181","#68d391","#b794f4","#76e4f7","#fbd38d","#e53e3e"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Variação Mensal por Classificação</div>', unsafe_allow_html=True)
            dp = df_cl.iloc[-36:]
            fig = go.Figure()
            for i, col in enumerate(dp.columns):
                s = dp[col].dropna()
                s_ma = ma3(s).dropna()
                cor = CORES_CL[i % len(CORES_CL)]
                fig.add_trace(go.Scatter(x=[str(p) for p in s.index], y=s.values,
                    name=col, line=dict(color=cor, width=1.8), mode="lines"))
                fig.add_trace(go.Scatter(x=[str(p) for p in s_ma.index], y=s_ma.values,
                    name=f"{col} MM3", line=dict(color=cor, width=1.2, dash="dot"), mode="lines",
                    showlegend=False))
                add_last_annotation(fig, list(s.index), s.values, cor)
            fig.update_layout(**LAYOUT, height=400,
                title=dict(text="Mensal — linhas sólidas; MM3 — pontilhado", font=dict(size=11)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Acumulado 12m por Classificação</div>', unsafe_allow_html=True)
            dp12 = df_cl12.iloc[-36:]
            fig2 = go.Figure()
            for i, col in enumerate(dp12.columns):
                s = dp12[col].dropna()
                s_ma = ma3(s).dropna()
                cor = CORES_CL[i % len(CORES_CL)]
                fig2.add_trace(go.Scatter(x=[str(p) for p in s.index], y=s.values,
                    name=col, line=dict(color=cor, width=1.8), mode="lines"))
                fig2.add_trace(go.Scatter(x=[str(p) for p in s_ma.index], y=s_ma.values,
                    name=f"{col} MM3", line=dict(color=cor, width=1.2, dash="dot"), mode="lines",
                    showlegend=False))
                add_last_annotation(fig2, list(s.index), s.values, cor)
            fig2.update_layout(**LAYOUT, height=400,
                title=dict(text="Acum. 12m — linhas sólidas; MM3 — pontilhado", font=dict(size=11)))
            st.plotly_chart(fig2, use_container_width=True)

        # Snapshot
        st.markdown('<div class="section-title">Snapshot — Último Mês Disponível · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        rows_html = ""
        for nome in df_cl.columns:
            s = df_cl[nome].dropna()
            s12_col = df_cl12[nome].dropna()
            v_m  = s.iloc[-1]  if not s.empty     else np.nan
            v_12 = s12_col.iloc[-1] if not s12_col.empty else np.nan
            v_ma = ma3(s).dropna().iloc[-1] if len(s) >= 3 else np.nan
            cor_m  = "#fc8181" if v_m>0.5   else ("#f6ad55" if v_m>0   else "#68d391")
            cor_12 = "#fc8181" if v_12>6    else ("#f6ad55" if v_12>3  else "#68d391")
            rows_html += f"""<tr>
              <td style='text-align:left'>{nome}</td>
              <td style='color:{cor_m}'>{fmt(v_m)}</td>
              <td style='color:var(--muted)'>{fmt(v_ma)}</td>
              <td style='color:{cor_12}'>{fmt(v_12)}</td>
            </tr>"""
        st.markdown(f"""
        <table class="contrib-table">
          <thead><tr>
            <th style="text-align:left">Classificação</th>
            <th>Var. Mensal</th><th>MM3</th><th>Acum. 12m</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.info("Dados de classificações indisponíveis no momento.")


# ══════════════════════════════════════════════════════
# ABA 3 — NÚCLEOS
# ══════════════════════════════════════════════════════
with tabs[2]:
    nuc_frames = {}
    for nome, s in nucleos_raw.items():
        if not s.empty:
            nuc_frames[nome] = s

    if nuc_frames:
        df_nuc = pd.DataFrame(nuc_frames).dropna(how="all")
        df_nuc["Mediana"] = df_nuc.median(axis=1)

        df_nuc12 = pd.DataFrame({c: acum12(df_nuc[c]) for c in df_nuc.columns}).dropna(how="all")
        df_nucano = pd.DataFrame({c: acumano(df_nuc[c].dropna()) for c in df_nuc.columns})

        COR_NEUTRO = "rgba(113,128,150,0.7)"  # cinza
        COR_MEDIANA = "#f6ad55"               # laranja de destaque
        COR_IPCA    = "rgba(255,255,255,0.25)"

        def plot_nucleos(df_plot, ipca_ref, title_text):
            fig = go.Figure()
            # IPCA de referência (barra cinza fundo)
            fig.add_trace(go.Bar(
                x=[str(p) for p in ipca_ref.index], y=ipca_ref.values,
                name="IPCA cheio", marker_color="rgba(255,255,255,0.06)",
                marker_line_width=0, showlegend=True,
            ))
            # Núcleos individuais — cor neutra
            for col in [c for c in df_plot.columns if c != "Mediana"]:
                s = df_plot[col].dropna()
                s_ma = ma3(s).dropna()
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in s.index], y=s.values,
                    name=col, mode="lines",
                    line=dict(color=COR_NEUTRO, width=1.5),
                ))
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in s_ma.index], y=s_ma.values,
                    name=f"{col} MM3", mode="lines",
                    line=dict(color=COR_NEUTRO, width=1, dash="dot"),
                    showlegend=False,
                ))
            # Mediana — destaque
            med = df_plot["Mediana"].dropna()
            med_ma = ma3(med).dropna()
            fig.add_trace(go.Scatter(
                x=[str(p) for p in med.index], y=med.values,
                name="Mediana", mode="lines",
                line=dict(color=COR_MEDIANA, width=2.8),
            ))
            fig.add_trace(go.Scatter(
                x=[str(p) for p in med_ma.index], y=med_ma.values,
                name="Mediana MM3", mode="lines",
                line=dict(color=COR_MEDIANA, width=1.8, dash="dot"),
            ))
            add_last_annotation(fig, list(med.index), med.values, COR_MEDIANA)
            fig.update_layout(**LAYOUT, height=380,
                title=dict(text=title_text, font=dict(size=11)))
            return fig

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Núcleos — Variação Mensal</div>', unsafe_allow_html=True)
            ipca_ref = last_n(ipca, 36)
            fig_m = plot_nucleos(df_nuc.iloc[-36:], ipca_ref,
                "Cinza = núcleos individuais · Laranja = Mediana (destaque)")
            st.plotly_chart(fig_m, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Núcleos — Acumulado 12m</div>', unsafe_allow_html=True)
            ipca12_ref = last_n(ipca_12, 36)
            fig_12 = plot_nucleos(df_nuc12.iloc[-36:], ipca12_ref,
                "Cinza = núcleos individuais · Laranja = Mediana (destaque)")
            st.plotly_chart(fig_12, use_container_width=True)

        # Acumulado anual dos núcleos
        st.markdown('<div class="section-title">Núcleos — Acumulado no Ano</div>', unsafe_allow_html=True)
        ipca_ano_ref = last_n(ipca_ano, 36)
        fig_ano = plot_nucleos(df_nucano.iloc[-36:].dropna(how="all"), ipca_ano_ref,
            "Acumulado no ano — Cinza = núcleos individuais · Laranja = Mediana")
        st.plotly_chart(fig_ano, use_container_width=True)

        # Snapshot tabela
        st.markdown('<div class="section-title">Núcleos — Snapshot Último Mês · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        DESC = {
            "EX0": "Excl. alimentação no domicílio + monitorados",
            "EX3": "Excl. alim. domicílio + monitorados + semi-duráveis",
            "MS":  "Médias aparadas com suavização",
            "DP":  "Dupla ponderação",
            "Mediana": "Mediana dos quatro núcleos acima",
        }
        rows_html = ""
        for nome in df_nuc.columns:
            s = df_nuc[nome].dropna()
            s12 = df_nuc12[nome].dropna()
            v_m  = s.iloc[-1]  if not s.empty  else np.nan
            v_12 = s12.iloc[-1] if not s12.empty else np.nan
            v_ma = ma3(s).dropna().iloc[-1] if len(s)>=3 else np.nan
            cor = COR_MEDIANA if nome=="Mediana" else COR_NEUTRO
            c_m = "#fc8181" if v_m>0.5 else ("#f6ad55" if v_m>0.3 else "#68d391")
            rows_html += f"""<tr>
              <td style='text-align:left'><span style='color:{cor};font-weight:600'>{nome}</span></td>
              <td style='text-align:left;color:var(--muted);font-size:.75rem'>{DESC.get(nome,'')}</td>
              <td style='color:{c_m}'>{fmt(v_m)}</td>
              <td style='color:var(--muted)'>{fmt(v_ma)}</td>
              <td>{fmt(v_12)}</td>
            </tr>"""
        st.markdown(f"""
        <table class="contrib-table">
          <thead><tr>
            <th style="text-align:left">Núcleo</th>
            <th style="text-align:left">Metodologia</th>
            <th>Mensal</th><th>MM3</th><th>Acum. 12m</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.info("Dados de núcleos indisponíveis.")


# ══════════════════════════════════════════════════════
# ABA 4 — DIFUSÃO
# ══════════════════════════════════════════════════════
with tabs[3]:
    if not difusao.empty:
        dif = last_n(difusao, 60)
        dif_ma = ma3(dif).dropna()
        st.markdown('<div class="section-title">Índice de Difusão — % itens com variação positiva · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[str(p) for p in dif.index], y=dif.values,
            name="Difusão", marker_color="rgba(79,209,197,0.35)", marker_line_width=0))
        fig.add_trace(go.Scatter(x=[str(p) for p in dif_ma.index], y=dif_ma.values,
            name="MM3", line=dict(color="#f6ad55", width=2.2), mode="lines"))
        fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.2)", annotation_text="50%")
        add_last_annotation(fig, list(dif.index), dif.values, "#4fd1c5")
        fig.update_layout(**LAYOUT, height=400,
            title=dict(text=f"Último: <b>{dif.iloc[-1]:.1f}%</b>  |  MM3: <b>{dif_ma.iloc[-1]:.1f}%</b>", font=dict(size=12)),
            yaxis_ticksuffix="%")
        fig.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Difusão atual", f"{dif.iloc[-1]:.1f}%")
        c2.metric("Média 3m", f"{dif_ma.iloc[-1]:.1f}%")
        c3.metric("Média 12m", f"{dif.iloc[-12:].mean():.1f}%")
    else:
        st.info("Dados de difusão indisponíveis.")


# ══════════════════════════════════════════════════════
# ABA 5 — TOP CONTRIBUIÇÕES
# ══════════════════════════════════════════════════════
with tabs[4]:
    with st.spinner("Calculando contribuições..."):
        top_sub, top_subgrp, top_grp, periodo_fmt, ipca_total = fetch_contribuicoes()

    if top_sub.empty and top_grp.empty:
        st.info("Dados de contribuição não disponíveis para o período mais recente.")
    else:
        st.markdown(f"""
        <div style="font-size:.8rem;color:var(--muted);font-family:'IBM Plex Mono',monospace;margin-bottom:1rem">
        Período de referência: <span style="color:var(--accent);font-weight:600">{periodo_fmt}</span>
        &nbsp;·&nbsp; IPCA cheio (soma contribuições): <span style="color:var(--accent);font-weight:600">{fmt(ipca_total)}</span>
        &nbsp;·&nbsp; Contribuição = (Peso ÷ 100) × Variação mensal &nbsp;·&nbsp; Fonte: IBGE/SIDRA (Tabela 7060)
        </div>""", unsafe_allow_html=True)

        def render_contrib_table(df, titulo):
            if df.empty:
                st.info(f"Sem dados para {titulo}.")
                return
            st.markdown(f'<div class="section-title">{titulo}</div>', unsafe_allow_html=True)
            max_c = df["contribuicao"].max()
            rows_html = ""
            for i, row in df.iterrows():
                bw = int((row["contribuicao"]/max_c)*100) if max_c>0 else 0
                cor = "#fc8181" if row["contribuicao"]>0.1 else ("#f6ad55" if row["contribuicao"]>0.04 else "#4fd1c5")
                pct = f"{row['pct_total']:.1f}%" if not pd.isna(row.get("pct_total", np.nan)) else "—"
                rows_html += f"""<tr>
                  <td style='text-align:left'><span class='rank'>{i}</span> {row['cat_nome']}</td>
                  <td>{fmt(row['peso'],4)}</td>
                  <td style='color:{cor}'>{fmt(row['variacao'])}</td>
                  <td>
                    <span style='color:{cor}'>{fmt(row['contribuicao'],4)}</span>
                    <span style='display:inline-block;height:6px;width:{bw}px;border-radius:3px;
                      background:{cor};margin-left:6px;vertical-align:middle'></span>
                  </td>
                  <td style='color:{cor};font-weight:600'>{pct}</td>
                </tr>"""
            st.markdown(f"""
            <table class="contrib-table">
              <thead><tr>
                <th style="text-align:left">Item</th>
                <th>Peso (%)</th><th>Var. m/m</th>
                <th>Contribuição (p.p.)</th><th>% do IPCA</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            render_contrib_table(top_sub,  "Top 10 Subitens")
        with col2:
            render_contrib_table(top_subgrp, "Top 10 Subgrupos")

        st.markdown("<br>", unsafe_allow_html=True)
        render_contrib_table(top_grp, "Contribuição por Grupo")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Fontes: IBGE/SIDRA Tabela 7060 · BCB/SGS · Dados atualizados automaticamente (cache 1h)<br>
  Monitor IPCA — uso analítico interno
</div>
""", unsafe_allow_html=True)
