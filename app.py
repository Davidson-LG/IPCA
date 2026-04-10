import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Monitor IPCA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS — TEMA LIGHT
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg:       #f8f9fc;
  --surface:  #ffffff;
  --surface2: #f1f3f8;
  --border:   #dde1ea;
  --accent:   #1a56db;
  --accent2:  #d97706;
  --red:      #dc2626;
  --green:    #16a34a;
  --text:     #111827;
  --muted:    #6b7280;
  --tag-bg:   #eff6ff;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg) !important;
  color: var(--text);
}
.main { background-color: var(--bg) !important; }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* ── Header ── */
.hdr {
  display: flex; align-items: center; gap: 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 5px solid var(--accent);
  border-radius: 10px;
  padding: 1.2rem 1.8rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.hdr-title { font-size: 1.5rem; font-weight: 700; color: var(--accent); letter-spacing: -.02em; }
.hdr-sub   { font-size: .8rem; color: var(--muted); margin-top: .15rem; font-family: 'IBM Plex Mono', monospace; }

/* ── KPI grid ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.1rem 1.4rem;
  position: relative;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.kpi::after {
  content: ''; position: absolute;
  bottom: 0; left: 1.4rem; right: 1.4rem; height: 3px;
  border-radius: 0 0 4px 4px;
  background: var(--accent);
}
.kpi.warn::after { background: var(--accent2); }
.kpi.danger::after { background: var(--red); }
.kpi.good::after { background: var(--green); }
.kpi-lbl { font-size: .7rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .07em; }
.kpi-val { font-family: 'IBM Plex Mono', monospace; font-size: 2rem; font-weight: 600; color: var(--text); line-height: 1.15; margin: .3rem 0 .2rem; }
.kpi-dlt { font-size: .75rem; font-family: 'IBM Plex Mono', monospace; }
.kpi-dlt.up   { color: var(--red);   }
.kpi-dlt.down { color: var(--green); }
.kpi-dlt.flat { color: var(--muted); }

/* ── Section titles ── */
.stitle {
  font-size: .72rem; font-weight: 600; color: var(--muted);
  text-transform: uppercase; letter-spacing: .1em;
  border-bottom: 2px solid var(--border);
  padding-bottom: .4rem; margin: 1.2rem 0 .8rem;
}

/* ── Tables ── */
.tbl { width: 100%; border-collapse: collapse; font-size: .83rem; }
.tbl th {
  font-size: .68rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; color: var(--muted);
  padding: .5rem .9rem; text-align: right;
  border-bottom: 2px solid var(--border);
  background: var(--surface2);
}
.tbl th:first-child { text-align: left; }
.tbl td {
  padding: .55rem .9rem;
  border-bottom: 1px solid var(--border);
  font-family: 'IBM Plex Mono', monospace;
  font-size: .79rem; text-align: right;
  color: var(--text);
}
.tbl td:first-child { text-align: left; font-family: 'Inter', sans-serif; }
.tbl tr:hover td { background: var(--surface2); }
.rnk { color: var(--accent); font-weight: 700; min-width: 1.4rem; display: inline-block; }
.bar-outer { display: inline-flex; align-items: center; gap: .4rem; justify-content: flex-end; }
.bar-inner { height: 6px; border-radius: 3px; }

/* ── Footer ── */
.ftr { font-size: .7rem; color: var(--muted); text-align: center; padding: 2rem 0 1rem; font-family: 'IBM Plex Mono', monospace; border-top: 1px solid var(--border); margin-top: 2rem; }

/* ── Tabs ── */
div[data-testid="stTabs"] button { font-family: 'Inter', sans-serif; font-size: .82rem; font-weight: 500; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--accent) !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json&dataInicial=01/01/2015"

# Séries SGS confirmadas
CLASSIFICACOES = {
    "Livres":           11428,
    "Comercializáveis": 4447,
    "Não-comerc.":      4448,
    "Monitorados":      4449,
    "Serviços":         10844,
    "Alim. domicílio":  27864,   # corrigido conforme solicitado
    "Industriais":      11465,
    "Serv. int. trabalho": 10843,
}

NUCLEOS = {"EX0": 27838, "EX3": 27839, "MS": 11427, "DP": 16122}

# Plotly layout base — TEMA LIGHT
LAY = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8f9fc",
    font=dict(family="Inter, sans-serif", color="#111827", size=11),
    xaxis=dict(gridcolor="#e5e7eb", linecolor="#d1d5db", tickcolor="#d1d5db", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#e5e7eb", linecolor="#d1d5db", tickcolor="#d1d5db"),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e5e7eb", borderwidth=1, font=dict(size=10)),
    margin=dict(l=44, r=16, t=48, b=36),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor="#d1d5db", font=dict(color="#111827", size=11)),
)

CORES = ["#1a56db", "#d97706", "#dc2626", "#16a34a", "#7c3aed", "#0891b2", "#be185d", "#065f46"]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt(v, d=2):
    if pd.isna(v): return "—"
    return f"{'+'if v>0 else ''}{v:.{d}f}%"

def arw(v): return "▲" if v > 0 else ("▼" if v < 0 else "—")

def acum12(s):
    return ((1 + s/100).rolling(12).apply(np.prod) - 1) * 100

def acumano(s):
    s = s.dropna()
    out = []
    for p in s.index:
        yr = s[s.index.year == p.year]
        out.append(((1 + yr / 100).cumprod() - 1).iloc[-1] * 100)
    return pd.Series(out, index=s.index)

def ma3(s): return s.rolling(3).mean()

def last_n(s, n=36): return s.dropna().iloc[-n:]

def annotate_last(fig, xs, ys, color, suffix="%"):
    """Anotação flutuante com o valor do último ponto."""
    if not len(ys): return
    v = ys[-1]
    if pd.isna(v): return
    fig.add_annotation(
        x=str(xs[-1]), y=v,
        text=f"<b>{v:+.2f}{suffix}</b>",
        showarrow=False,
        font=dict(size=10, color=color),
        xanchor="left", yanchor="middle",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=color, borderwidth=1, borderpad=3,
    )

# ─────────────────────────────────────────────
# FETCH SGS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_sgs(codigo):
    try:
        r = requests.get(BCB_URL.format(codigo), timeout=25)
        df = pd.DataFrame(r.json())
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
        s = df.set_index("data")["valor"].dropna()
        s.index = s.index.to_period("M")
        return s
    except Exception:
        return pd.Series(dtype=float)

# ─────────────────────────────────────────────
# FETCH SIDRA — contribuições (subitens, itens, grupos)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_contribuicoes():
    """
    Tabela 7060, variáveis 63 (var mensal) e 66 (peso).
    Hierarquia pelo comprimento do código numérico da categoria:
      - 1 dígito  → grupo   (ex: "1")
      - 2 dígitos → subgrupo (ex: "11")
      - 4 dígitos → item    (ex: "1101")
      - 7 dígitos → subitem (ex: "1101002")
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
        return {}, "", 0.0

    rows = []
    for item in data:
        var_id = item.get("id")
        for res in item.get("resultados", []):
            cl = res.get("classificacoes", [{}])[0]
            for cat_id_str, cat_nome in cl.get("categoria", {}).items():
                for serie in res.get("series", []):
                    for per, val in serie["serie"].items():
                        try: v = float(val)
                        except: v = np.nan
                        rows.append({
                            "var_id": var_id,
                            "cat_id": cat_id_str,
                            "cat_nome": cat_nome,
                            "periodo": per,
                            "valor": v,
                        })

    if not rows:
        return {}, "", 0.0

    df = pd.DataFrame(rows)

    # Período mais recente com dados
    ultimo = sorted(df["periodo"].unique(), reverse=True)[0]
    dfu = df[df["periodo"] == ultimo].copy()

    df_var = dfu[dfu["var_id"] == "63"][["cat_id","cat_nome","valor"]].rename(columns={"valor":"variacao"})
    df_pes = dfu[dfu["var_id"] == "66"][["cat_id","valor"]].rename(columns={"valor":"peso"})
    m = df_var.merge(df_pes, on="cat_id", how="inner").dropna(subset=["variacao","peso"])
    m["contribuicao"] = (m["peso"] / 100) * m["variacao"]

    # ── CLASSIFICAR por comprimento do cat_id numérico ──
    # A tabela 7060 usa códigos numéricos: 7169=Índice geral (especial),
    # depois grupos (1-9), subgrupos (11,12,...), itens (1101,...), subitens (1101001,...)
    # Separamos pelo comprimento do código NUMÉRICO original
    import re
    def nivel(cat_id_str):
        # IDs especiais: 7169=geral, 7170=1.Alim, 7445=2.Hab, 1284=3.Art, 7625=4.Vest, etc.
        # são IDs de 4 dígitos mas são grupos — identificamos pelo nome
        nome = m.loc[m["cat_id"]==cat_id_str, "cat_nome"].values
        nome = nome[0] if len(nome) else ""
        if nome == "Índice geral": return "geral"
        # IDs numéricos de comprimento variável
        digits = re.sub(r'\D','', cat_id_str)
        n = len(digits)
        if n <= 1: return "grupo"
        if n == 2: return "subgrupo"
        if n == 4: return "item"
        if n >= 5: return "subitem"
        return "outro"

    m["nivel"] = m["cat_id"].apply(nivel)

    # IPCA total = categoria "Índice geral"
    ipca_total_row = m[m["nivel"] == "geral"]["contribuicao"]
    ipca_total = ipca_total_row.iloc[0] if not ipca_total_row.empty else m[m["nivel"]=="subitem"]["contribuicao"].sum()

    def top10(nivel_str):
        sub = m[m["nivel"] == nivel_str].copy()
        sub = sub.dropna(subset=["contribuicao"])
        if sub.empty: return pd.DataFrame()
        sub = sub.nlargest(10, "contribuicao").reset_index(drop=True)
        sub.index += 1
        sub["pct_total"] = (sub["contribuicao"] / abs(ipca_total) * 100) if ipca_total else np.nan
        return sub

    periodo_fmt = f"{ultimo[4:6]}/{ultimo[:4]}" if len(ultimo)==6 else ultimo

    return {
        "subitem": top10("subitem"),
        "item":    top10("item"),
        "grupo":   top10("grupo"),
    }, periodo_fmt, ipca_total

# ─────────────────────────────────────────────
# CARREGA TUDO
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all():
    ipca = fetch_sgs(433)
    dif  = fetch_sgs(21379)
    nuc  = {n: fetch_sgs(c) for n, c in NUCLEOS.items()}
    cla  = {n: fetch_sgs(c) for n, c in CLASSIFICACOES.items()}
    return ipca, dif, nuc, cla

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
agora = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-title">📊 Monitor IPCA</div>
    <div class="hdr-sub">Índice Nacional de Preços ao Consumidor Amplo · IBGE/SIDRA &amp; BCB/SGS · {agora}</div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Carregando dados..."):
    ipca, dif, nuc_raw, cla_raw = load_all()

if ipca.empty:
    st.error("Falha ao carregar IPCA. Tente recarregar a página.")
    st.stop()

# Derivados
ipca_12  = acum12(ipca).dropna()
ipca_ano = acumano(ipca)
ipca_ma  = ma3(ipca).dropna()

ult   = ipca.dropna().iloc[-1]
penu  = ipca.dropna().iloc[-2]
dm    = ult - penu
a12   = ipca_12.iloc[-1] if not ipca_12.empty else np.nan
a12p  = ipca_12.iloc[-2] if len(ipca_12)>=2   else np.nan
aano  = ipca_ano.iloc[-1] if not ipca_ano.empty else np.nan
ref   = str(ipca.dropna().index[-1])
dv    = dif.dropna().iloc[-1] if not dif.empty else np.nan
dd    = (dif.dropna().iloc[-1]-dif.dropna().iloc[-2]) if len(dif.dropna())>=2 else 0

def kpi_html(lbl, val, delta, sub, cls=""):
    dc = "up" if delta>0 else ("down" if delta<0 else "flat")
    return f"""<div class="kpi {cls}">
  <div class="kpi-lbl">{lbl}</div>
  <div class="kpi-val">{val}</div>
  <div class="kpi-dlt {dc}">{arw(delta)} {sub}</div>
</div>"""

st.markdown(f"""<div class="kpi-grid">
  {kpi_html(f"IPCA Mensal · {ref}", fmt(ult), dm, f"vs ant. ({fmt(penu)})", "warn" if ult>0.5 else "")}
  {kpi_html("Acumulado 12 meses", fmt(a12), a12-(a12p or 0), f"ant.: {fmt(a12p)}", "danger" if a12>6 else "")}
  {kpi_html(f"Acumulado {ipca_ano.index[-1].year}", fmt(aano), 0, f"até {ref}", "good")}
  {kpi_html("Índice de Difusão", f"{dv:.1f}%" if not pd.isna(dv) else "—", dd, "vs mês anterior")}
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ABAS
# ─────────────────────────────────────────────
tabs = st.tabs(["📈 Headline", "🗂️ Grupos & Classificações", "🎯 Núcleos", "🔀 Difusão", "🏆 Top Contribuições"])

# ══════════════════════════════════════════════
# ABA 1 — HEADLINE
# ══════════════════════════════════════════════
with tabs[0]:
    c1, c2 = st.columns(2)

    # Mensal — barras + último valor anotado + MM3
    with c1:
        st.markdown('<div class="stitle">Variação Mensal (% a.m.) · Fonte: BCB/SGS 433</div>', unsafe_allow_html=True)
        s  = last_n(ipca, 36)
        sm = ma3(s).dropna()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[str(p) for p in s.index], y=s.values,
            name="IPCA m/m",
            marker_color=["#dc2626" if v>0 else "#16a34a" for v in s.values],
            marker_line_width=0,
        ))
        fig.add_trace(go.Scatter(
            x=[str(p) for p in sm.index], y=sm.values,
            name="MM3", mode="lines",
            line=dict(color="#d97706", width=2.2),
        ))
        # Anotação do último valor (IPCA, não só MM3)
        annotate_last(fig, list(s.index), s.values, "#dc2626")
        fig.update_layout(**LAY, height=320,
            title=dict(text=f"Último: <b>{fmt(ult)}</b>  ·  MM3: <b>{fmt(sm.iloc[-1])}</b>", font=dict(size=12, color="#111827")))
        fig.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig, use_container_width=True)

    # Acumulado 12m — linha + área + MM3
    with c2:
        st.markdown('<div class="stitle">Acumulado 12 Meses (% a.a.) · Fonte: BCB/SGS 433</div>', unsafe_allow_html=True)
        s12  = last_n(ipca_12, 48)
        s12m = ma3(s12).dropna()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[str(p) for p in s12.index], y=s12.values,
            name="12m", mode="lines",
            line=dict(color="#1a56db", width=2.5),
            fill="tozeroy", fillcolor="rgba(26,86,219,0.07)",
        ))
        fig2.add_trace(go.Scatter(
            x=[str(p) for p in s12m.index], y=s12m.values,
            name="MM3", mode="lines",
            line=dict(color="#d97706", width=2, dash="dot"),
        ))
        for ano, meta in {2022:3.5,2023:3.25,2024:3.0,2025:3.0,2026:3.0}.items():
            ps = [str(p) for p in s12.index if p.year==ano]
            if ps:
                fig2.add_shape(type="rect", x0=ps[0], x1=ps[-1],
                    y0=meta-1.5, y1=meta+1.5,
                    fillcolor="rgba(22,163,74,0.06)", line=dict(width=0))
        annotate_last(fig2, list(s12.index), s12.values, "#1a56db")
        fig2.update_layout(**LAY, height=320,
            title=dict(text=f"Último: <b>{fmt(a12)}</b>  ·  MM3: <b>{fmt(s12m.iloc[-1])}</b>", font=dict(size=12, color="#111827")))
        fig2.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns([2, 1])

    # Acumulado no ano — BARRAS
    with c3:
        st.markdown('<div class="stitle">Acumulado no Ano (%) · Fonte: BCB/SGS 433</div>', unsafe_allow_html=True)
        sa  = last_n(ipca_ano, 48)
        sam = ma3(sa).dropna()
        # Agrupa por ano: pega o valor de dezembro (ou último disponível) de cada ano
        ultimos_por_ano = sa.groupby(sa.index.year).last()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=[str(a) for a in ultimos_por_ano.index],
            y=ultimos_por_ano.values,
            name="Fechamento ano",
            marker_color=["#dc2626" if v>5 else ("#d97706" if v>3 else "#1a56db")
                          for v in ultimos_por_ano.values],
            marker_line_width=0,
            text=[f"{v:.2f}%" for v in ultimos_por_ano.values],
            textposition="outside",
            textfont=dict(size=10),
        ))
        fig3.update_layout(**LAY, height=300,
            title=dict(text=f"Ano corrente até {ref}: <b>{fmt(aano)}</b>", font=dict(size=12, color="#111827")))
        st.plotly_chart(fig3, use_container_width=True)

    # Tabela resumo
    with c4:
        st.markdown('<div class="stitle">Últimos 14 meses</div>', unsafe_allow_html=True)
        ultimos = ipca.dropna().iloc[-14:]
        rows = ""
        for p, v in reversed(list(ultimos.items())):
            cor = "#dc2626" if v>0.5 else ("#d97706" if v>0.3 else "#16a34a")
            rows += f"<tr><td style='text-align:left'>{p}</td><td style='color:{cor}'>{fmt(v)}</td></tr>"
        st.markdown(f"""<table class="tbl" style="font-size:.77rem">
          <thead><tr><th style="text-align:left">Período</th><th>Var. m/m</th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ABA 2 — GRUPOS & CLASSIFICAÇÕES
# ══════════════════════════════════════════════
with tabs[1]:
    frames = {n: s for n, s in cla_raw.items() if not s.empty}
    if frames:
        df_cl  = pd.DataFrame(frames).dropna(how="all")
        df_12  = pd.DataFrame({c: acum12(df_cl[c]) for c in df_cl.columns}).dropna(how="all")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="stitle">Variação Mensal · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
            dp = df_cl.iloc[-36:]
            fig = go.Figure()
            for i, col in enumerate(dp.columns):
                s = dp[col].dropna(); sm = ma3(s).dropna()
                cor = CORES[i % len(CORES)]
                fig.add_trace(go.Scatter(x=[str(p) for p in s.index], y=s.values,
                    name=col, mode="lines", line=dict(color=cor, width=1.8)))
                fig.add_trace(go.Scatter(x=[str(p) for p in sm.index], y=sm.values,
                    name=f"{col} MM3", mode="lines",
                    line=dict(color=cor, width=1.2, dash="dot"), showlegend=False))
                annotate_last(fig, list(s.index), s.values, cor)
            fig.update_layout(**LAY, height=400,
                title=dict(text="Sólido = mensal · Pontilhado = MM3", font=dict(size=11)))
            fig.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown('<div class="stitle">Acumulado 12m · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
            dp12 = df_12.iloc[-36:]
            fig2 = go.Figure()
            for i, col in enumerate(dp12.columns):
                s = dp12[col].dropna(); sm = ma3(s).dropna()
                cor = CORES[i % len(CORES)]
                fig2.add_trace(go.Scatter(x=[str(p) for p in s.index], y=s.values,
                    name=col, mode="lines", line=dict(color=cor, width=1.8)))
                fig2.add_trace(go.Scatter(x=[str(p) for p in sm.index], y=sm.values,
                    name=f"{col} MM3", mode="lines",
                    line=dict(color=cor, width=1.2, dash="dot"), showlegend=False))
                annotate_last(fig2, list(s.index), s.values, cor)
            fig2.update_layout(**LAY, height=400,
                title=dict(text="Sólido = 12m · Pontilhado = MM3", font=dict(size=11)))
            fig2.update_xaxes(tickangle=-45, nticks=12)
            st.plotly_chart(fig2, use_container_width=True)

        # Snapshot tabela
        st.markdown('<div class="stitle">Snapshot — Último Mês Disponível · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        rows = ""
        for nome in df_cl.columns:
            s = df_cl[nome].dropna(); s12c = df_12[nome].dropna()
            vm  = s.iloc[-1]    if not s.empty   else np.nan
            v12 = s12c.iloc[-1] if not s12c.empty else np.nan
            vma = ma3(s).dropna().iloc[-1] if len(s)>=3 else np.nan
            cm  = "#dc2626" if vm>0.5  else ("#d97706" if vm>0  else "#16a34a")
            c12 = "#dc2626" if v12>6   else ("#d97706" if v12>3 else "#16a34a")
            rows += f"""<tr>
              <td style='text-align:left;font-weight:500'>{nome}</td>
              <td style='color:{cm}'>{fmt(vm)}</td>
              <td style='color:#6b7280'>{fmt(vma)}</td>
              <td style='color:{c12}'>{fmt(v12)}</td>
            </tr>"""
        st.markdown(f"""<table class="tbl">
          <thead><tr>
            <th style="text-align:left">Classificação</th>
            <th>Var. Mensal</th><th>MM3</th><th>Acum. 12m</th>
          </tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.info("Dados de classificações indisponíveis.")


# ══════════════════════════════════════════════
# ABA 3 — NÚCLEOS
# ══════════════════════════════════════════════
with tabs[2]:
    nf = {n: s for n, s in nuc_raw.items() if not s.empty}
    if nf:
        df_n   = pd.DataFrame(nf).dropna(how="all")
        df_n["Mediana"] = df_n.median(axis=1)
        df_n12 = pd.DataFrame({c: acum12(df_n[c]) for c in df_n.columns}).dropna(how="all")
        df_nano = pd.DataFrame({c: acumano(df_n[c]) for c in df_n.columns if not df_n[c].dropna().empty})

        COR_N = "#9ca3af"      # cinza neutro para núcleos
        COR_M = "#d97706"      # laranja para mediana
        COR_I = "#1a56db"      # azul para IPCA ref

        def plot_nuc(df_plot, ipca_ref, is_bar_ref=False, title=""):
            fig = go.Figure()
            # IPCA referência
            if is_bar_ref:
                fig.add_trace(go.Bar(
                    x=[str(p) for p in ipca_ref.index], y=ipca_ref.values,
                    name="IPCA cheio", marker_color="rgba(26,86,219,0.12)",
                    marker_line_color="rgba(26,86,219,0.3)", marker_line_width=1,
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in ipca_ref.index], y=ipca_ref.values,
                    name="IPCA cheio", mode="lines",
                    line=dict(color="rgba(26,86,219,0.35)", width=1.5, dash="dash"),
                ))
            for col in [c for c in df_plot.columns if c != "Mediana"]:
                s = df_plot[col].dropna(); sm = ma3(s).dropna()
                fig.add_trace(go.Scatter(x=[str(p) for p in s.index], y=s.values,
                    name=col, mode="lines", line=dict(color=COR_N, width=1.5)))
                fig.add_trace(go.Scatter(x=[str(p) for p in sm.index], y=sm.values,
                    name=f"{col} MM3", mode="lines",
                    line=dict(color=COR_N, width=1, dash="dot"), showlegend=False))
            med = df_plot["Mediana"].dropna(); med_m = ma3(med).dropna()
            fig.add_trace(go.Scatter(x=[str(p) for p in med.index], y=med.values,
                name="Mediana", mode="lines", line=dict(color=COR_M, width=3)))
            fig.add_trace(go.Scatter(x=[str(p) for p in med_m.index], y=med_m.values,
                name="Mediana MM3", mode="lines", line=dict(color=COR_M, width=2, dash="dot")))
            annotate_last(fig, list(med.index), med.values, COR_M)
            fig.update_layout(**LAY, height=360,
                title=dict(text=title, font=dict(size=11, color="#111827")))
            fig.update_xaxes(tickangle=-45, nticks=12)
            return fig

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="stitle">Variação Mensal · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
            fig_m = plot_nuc(df_n.iloc[-36:], last_n(ipca,36), is_bar_ref=True,
                title="Cinza = núcleos  ·  Laranja = Mediana (destaque)  ·  Barras = IPCA cheio")
            st.plotly_chart(fig_m, use_container_width=True)
        with c2:
            st.markdown('<div class="stitle">Acumulado 12m · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
            fig_12 = plot_nuc(df_n12.iloc[-36:], last_n(ipca_12,36),
                title="Cinza = núcleos  ·  Laranja = Mediana (destaque)  ·  Tracejado = IPCA 12m")
            st.plotly_chart(fig_12, use_container_width=True)

        # Acumulado anual — BARRAS por ano
        st.markdown('<div class="stitle">Acumulado no Ano — Comparativo · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        fig_ano = go.Figure()
        # Para barras: pega o valor de dezembro (ou último) de cada ano
        mediana_ano = df_nano["Mediana"].dropna() if "Mediana" in df_nano.columns else pd.Series(dtype=float)
        ipca_ano_g  = acumano(ipca)
        todos = {"IPCA": ipca_ano_g, "Mediana": mediana_ano}
        for nuc_n in [c for c in df_nano.columns if c != "Mediana"]:
            todos[nuc_n] = df_nano[nuc_n].dropna()

        cores_bar = {"IPCA": "#1a56db", "Mediana": "#d97706",
                     "EX0": "#9ca3af", "EX3": "#9ca3af", "MS": "#9ca3af", "DP": "#9ca3af"}
        for nome, serie in todos.items():
            if serie.empty: continue
            by_ano = serie.groupby(serie.index.year).last()
            fig_ano.add_trace(go.Bar(
                x=[str(a) for a in by_ano.index],
                y=by_ano.values,
                name=nome,
                marker_color=cores_bar.get(nome, "#9ca3af"),
                text=[f"{v:.1f}%" for v in by_ano.values],
                textposition="outside",
                textfont=dict(size=9),
            ))
        fig_ano.update_layout(**LAY, height=360, barmode="group",
            title=dict(text="Fechamento anual por núcleo — azul=IPCA, laranja=Mediana, cinza=núcleos individuais",
                       font=dict(size=11, color="#111827")))
        st.plotly_chart(fig_ano, use_container_width=True)

        # Tabela snapshot
        st.markdown('<div class="stitle">Snapshot Último Mês · Fonte: BCB/SGS</div>', unsafe_allow_html=True)
        DESC = {
            "EX0": "Excl. alimentação domicílio + monitorados",
            "EX3": "Excl. alim. dom. + monitorados + semi-duráveis",
            "MS":  "Médias aparadas com suavização",
            "DP":  "Dupla ponderação",
            "Mediana": "Mediana de EX0, EX3, MS e DP",
        }
        rows = ""
        for nome in df_n.columns:
            s  = df_n[nome].dropna(); s12c = df_n12[nome].dropna() if nome in df_n12 else pd.Series(dtype=float)
            vm  = s.iloc[-1]    if not s.empty   else np.nan
            v12 = s12c.iloc[-1] if not s12c.empty else np.nan
            vma = ma3(s).dropna().iloc[-1] if len(s)>=3 else np.nan
            cor = COR_M if nome=="Mediana" else COR_N
            cm  = "#dc2626" if vm>0.5 else ("#d97706" if vm>0.3 else "#16a34a")
            rows += f"""<tr>
              <td style='text-align:left'><span style='font-weight:600;color:{cor}'>{nome}</span></td>
              <td style='text-align:left;color:#6b7280;font-size:.75rem'>{DESC.get(nome,'')}</td>
              <td style='color:{cm}'>{fmt(vm)}</td>
              <td style='color:#6b7280'>{fmt(vma)}</td>
              <td>{fmt(v12)}</td>
            </tr>"""
        st.markdown(f"""<table class="tbl">
          <thead><tr>
            <th style="text-align:left">Núcleo</th><th style="text-align:left">Metodologia</th>
            <th>Mensal</th><th>MM3</th><th>Acum. 12m</th>
          </tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.info("Dados de núcleos indisponíveis.")


# ══════════════════════════════════════════════
# ABA 4 — DIFUSÃO
# ══════════════════════════════════════════════
with tabs[3]:
    if not dif.empty:
        d = last_n(dif, 60); dm3 = ma3(d).dropna()
        st.markdown('<div class="stitle">Índice de Difusão — % de itens com variação positiva · Fonte: BCB/SGS 21379</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[str(p) for p in d.index], y=d.values,
            name="Difusão", marker_color="rgba(26,86,219,0.3)",
            marker_line_color="rgba(26,86,219,0.6)", marker_line_width=1))
        fig.add_trace(go.Scatter(x=[str(p) for p in dm3.index], y=dm3.values,
            name="MM3", mode="lines", line=dict(color="#d97706", width=2.2)))
        fig.add_hline(y=50, line_dash="dash", line_color="#9ca3af",
            annotation_text="50%", annotation_font_color="#6b7280")
        annotate_last(fig, list(d.index), d.values, "#1a56db")
        fig.update_layout(**LAY, height=420,
            title=dict(text=f"Último: <b>{d.iloc[-1]:.1f}%</b>  ·  MM3: <b>{dm3.iloc[-1]:.1f}%</b>  ·  Média 12m: <b>{d.iloc[-12:].mean():.1f}%</b>",
                       font=dict(size=12, color="#111827")),
            yaxis_ticksuffix="%")
        fig.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig, use_container_width=True)
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Difusão atual",  f"{d.iloc[-1]:.1f}%")
        cc2.metric("Média 3m",       f"{dm3.iloc[-1]:.1f}%")
        cc3.metric("Média 12m",      f"{d.iloc[-12:].mean():.1f}%")
    else:
        st.info("Dados de difusão indisponíveis.")


# ══════════════════════════════════════════════
# ABA 5 — TOP CONTRIBUIÇÕES
# ══════════════════════════════════════════════
with tabs[4]:
    with st.spinner("Calculando contribuições..."):
        tops, periodo_fmt, ipca_total = fetch_contribuicoes()

    if not tops:
        st.info("Dados de contribuição não disponíveis.")
    else:
        st.markdown(f"""
        <div style="font-size:.8rem;color:#6b7280;font-family:'IBM Plex Mono',monospace;
             background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:.7rem 1rem;margin-bottom:1rem">
        Período: <b style="color:#1a56db">{periodo_fmt}</b>
        &nbsp;·&nbsp; IPCA reconstruído: <b style="color:#1a56db">{fmt(ipca_total)}</b>
        &nbsp;·&nbsp; Contribuição = (Peso ÷ 100) × Variação mensal
        &nbsp;·&nbsp; Fonte: IBGE/SIDRA Tabela 7060
        </div>""", unsafe_allow_html=True)

        def render_table(df, titulo):
            if df is None or df.empty:
                st.markdown(f'<div class="stitle">{titulo}</div>', unsafe_allow_html=True)
                st.info("Sem dados para este nível.")
                return
            st.markdown(f'<div class="stitle">{titulo}</div>', unsafe_allow_html=True)
            mx = df["contribuicao"].max()
            rows = ""
            for i, row in df.iterrows():
                bw = int((row["contribuicao"]/mx)*90) if mx>0 else 0
                cor = "#dc2626" if row["contribuicao"]>0.1 else ("#d97706" if row["contribuicao"]>0.04 else "#1a56db")
                pct = f"{row['pct_total']:.1f}%" if not pd.isna(row.get("pct_total", np.nan)) else "—"
                rows += f"""<tr>
                  <td style='text-align:left'><span class='rnk'>{i}</span>{row['cat_nome']}</td>
                  <td>{fmt(row['peso'],4)}</td>
                  <td style='color:{cor}'>{fmt(row['variacao'])}</td>
                  <td><div class="bar-outer">
                    <span style='color:{cor}'>{fmt(row['contribuicao'],4)}</span>
                    <div class="bar-inner" style="width:{bw}px;background:{cor}"></div>
                  </div></td>
                  <td style='color:{cor};font-weight:600'>{pct}</td>
                </tr>"""
            st.markdown(f"""<table class="tbl">
              <thead><tr>
                <th style="text-align:left">Item</th>
                <th>Peso (%)</th><th>Var. m/m</th>
                <th>Contribuição (p.p.)</th><th>% do IPCA</th>
              </tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # Subitens e Itens lado a lado
        cc1, cc2 = st.columns(2)
        with cc1:
            render_table(tops.get("subitem"), "Top 10 Subitens")
        with cc2:
            render_table(tops.get("item"), "Top 10 Itens")

        st.markdown("<br>", unsafe_allow_html=True)
        render_table(tops.get("grupo"), "Contribuição por Grupo")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="ftr">
  Fontes: IBGE/SIDRA Tabela 7060 (variação mensal var.63, peso var.66) · BCB/SGS (séries temporais)<br>
  Dados atualizados automaticamente a cada hora · Monitor IPCA — uso analítico
</div>
""", unsafe_allow_html=True)
