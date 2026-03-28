import streamlit as st
import pandas as pd
import numpy as np
import os, re, io, json
from datetime import datetime
from groq import Groq
from scipy import stats as scipy_stats

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════
#  🔑  PASTE YOUR GROQ API KEY HERE
# ══════════════════════════════════════════════════════════════════════
GROQ_API_KEY = "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"

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="DataCommerce – Analyse Decisionnelle", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
  html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
  .stApp{background:linear-gradient(180deg,#FFF9E6 0%,#FFFFFF 100%);color:#374151;}
  .app-header{display:flex;justify-content:space-between;align-items:center;padding:1rem 0;margin-bottom:2rem;border-bottom:1px solid rgba(0,0,0,0.05);}
  .logo-text{font-size:1.8rem;font-weight:700;color:#065F46;}
  .user-greeting{color:#92400E;font-weight:500;font-size:0.95rem;}
  .hero-title{font-size:2.4rem;font-weight:700;color:#1F2937;margin-bottom:0.5rem;text-align:center;}
  .hero-sub{color:#6B7280;font-size:1.1rem;margin-bottom:2.5rem;text-align:center;}
  .chat-user{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px 12px 2px 12px;padding:1rem;margin:0.5rem 0 0.5rem 15%;color:#1F2937;}
  .chat-assistant{background:linear-gradient(135deg,#F59E0B,#10B981);border-radius:12px 12px 12px 2px;padding:1.5rem;margin:0.5rem 15% 0.5rem 0;color:#FFFFFF;line-height:1.6;white-space:pre-wrap;}
  .chat-label{font-size:0.8rem;font-weight:600;margin-bottom:4px;}
  .chat-label-user{color:#6B7280;text-align:right;}
  .chat-label-bot{color:#059669;}
  .stButton>button{background:linear-gradient(90deg,#F59E0B 0%,#10B981 100%)!important;color:white!important;border:none!important;border-radius:50px!important;padding:0.6rem 2.5rem!important;font-weight:600!important;}
  .report-cover{background:linear-gradient(135deg,#064E3B 0%,#065F46 50%,#047857 100%);border-radius:20px;padding:3rem 2.5rem;margin-bottom:2rem;color:white;position:relative;overflow:hidden;}
  .report-cover::before{content:'';position:absolute;top:-60px;right:-60px;width:260px;height:260px;background:rgba(245,158,11,0.12);border-radius:50%;}
  .report-cover::after{content:'';position:absolute;bottom:-40px;left:-40px;width:180px;height:180px;background:rgba(16,185,129,0.10);border-radius:50%;}
  .report-cover-label{font-size:0.75rem;letter-spacing:0.18em;text-transform:uppercase;color:#6EE7B7;font-weight:600;margin-bottom:0.5rem;}
  .report-cover-title{font-size:2.1rem;font-weight:700;line-height:1.2;margin-bottom:0.5rem;}
  .report-cover-sub{font-size:1rem;color:#A7F3D0;margin-bottom:1.5rem;}
  .report-cover-meta{display:flex;gap:2rem;flex-wrap:wrap;}
  .report-cover-meta span{font-size:0.82rem;color:#D1FAE5;}
  .report-section{background:#FFFFFF;border:1px solid #F3F4F6;border-radius:16px;padding:1.8rem 2rem;margin-bottom:1.5rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);}
  .report-section-header{display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;padding-bottom:0.8rem;border-bottom:2px solid #F3F4F6;}
  .section-icon{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;}
  .icon-blue{background:#EFF6FF}.icon-amber{background:#FFFBEB}.icon-green{background:#ECFDF5}.icon-red{background:#FEF2F2}.icon-purple{background:#F5F3FF}.icon-teal{background:#F0FDFA}.icon-orange{background:#FFF7ED}
  .section-title{font-size:1.1rem;font-weight:700;color:#111827;}
  .section-badge{margin-left:auto;font-size:0.7rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;padding:3px 10px;border-radius:20px;background:#F3F4F6;color:#6B7280;}
  .kpi-card{background:linear-gradient(145deg,#F9FAFB,#FFFFFF);border:1px solid #E5E7EB;border-radius:12px;padding:1.2rem;text-align:center;margin-bottom:0.5rem;}
  .kpi-value{font-size:1.9rem;font-weight:700;color:#065F46;line-height:1;margin-bottom:4px;}
  .kpi-label{font-size:0.78rem;color:#9CA3AF;font-weight:500;text-transform:uppercase;letter-spacing:0.06em;}
  .kpi-trend{font-size:0.78rem;font-weight:600;margin-top:4px;}
  .trend-up{color:#10B981}.trend-down{color:#EF4444}.trend-neutral{color:#F59E0B}
  .alert-item{display:flex;align-items:flex-start;gap:12px;padding:1rem 1.2rem;border-radius:10px;margin-bottom:0.75rem;border-left:4px solid transparent;}
  .alert-critical{background:#FEF2F2;border-color:#EF4444}.alert-warning{background:#FFFBEB;border-color:#F59E0B}.alert-ok{background:#ECFDF5;border-color:#10B981}
  .alert-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-top:5px;}
  .dot-red{background:#EF4444}.dot-amber{background:#F59E0B}.dot-green{background:#10B981}
  .alert-title{font-weight:600;font-size:0.9rem;color:#111827;}
  .alert-body{font-size:0.83rem;color:#6B7280;margin-top:2px;line-height:1.5;}
  .reco-item{display:flex;gap:14px;padding:1rem 0;border-bottom:1px solid #F9FAFB;}
  .reco-item:last-child{border-bottom:none}
  .reco-number{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#F59E0B,#10B981);color:white;font-weight:700;font-size:0.8rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
  .reco-text{font-size:0.9rem;color:#374151;line-height:1.6;}
  .insight-text{font-size:0.9rem;color:#4B5563;line-height:1.8;padding:0.3rem 0;border-bottom:1px solid #F9FAFB;margin-bottom:0.4rem;}
  .insight-text:last-child{border-bottom:none}
  .insight-bullet::before{content:"▸ ";color:#10B981;font-weight:700;}
  .exec-summary{font-size:1rem;line-height:1.85;color:#374151;padding:0.5rem 0;}
  .report-footer{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.5rem;background:#F9FAFB;border-radius:12px;margin-top:2rem;font-size:0.78rem;color:#9CA3AF;}
  .confidence-label{font-size:0.78rem;color:#9CA3AF;margin-bottom:4px;display:flex;justify-content:space-between;}
  .confidence-bar{height:6px;background:#F3F4F6;border-radius:99px;overflow:hidden;}
  .confidence-fill{height:100%;background:linear-gradient(90deg,#F59E0B,#10B981);border-radius:99px;}
  .clean-stat{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem;font-size:0.85rem;color:#374151;}
  .clean-stat span{font-weight:700;color:#065F46;}
  .chart-label{font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px;padding:2px 8px;background:#F3F4F6;border-radius:6px;display:inline-block;}
  .segment-card{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:1rem;margin-bottom:0.6rem;}
  .segment-title{font-weight:700;color:#111827;font-size:0.9rem;}
  .segment-delta-pos{color:#10B981;font-weight:700;}
  .segment-delta-neg{color:#EF4444;font-weight:700;}
  .anomaly-row{background:#FEF2F2;border-left:3px solid #EF4444;padding:0.5rem 0.8rem;border-radius:6px;margin-bottom:4px;font-size:0.82rem;color:#374151;}
  .trend-badge-up{background:#ECFDF5;color:#065F46;padding:2px 8px;border-radius:20px;font-size:0.75rem;font-weight:700;}
  .trend-badge-down{background:#FEF2F2;color:#DC2626;padding:2px 8px;border-radius:20px;font-size:0.75rem;font-weight:700;}
  .trend-badge-flat{background:#FFFBEB;color:#92400E;padding:2px 8px;border-radius:20px;font-size:0.75rem;font-weight:700;}
  .stat-pill{display:inline-block;background:#F3F4F6;border-radius:20px;padding:3px 10px;font-size:0.75rem;color:#6B7280;margin:2px;}
  .stat-pill strong{color:#065F46;}
  .nlq-box{background:linear-gradient(135deg,#F0FDFA,#ECFDF5);border:1px solid #A7F3D0;border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

# ── PLOTLY THEME ───────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit, sans-serif", color="#374151"),
    margin=dict(l=20, r=20, t=44, b=20),
    colorway=["#10B981","#F59E0B","#3B82F6","#8B5CF6","#EF4444","#06B6D4","#F97316","#84CC16"],
)
def apply_theme(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(showgrid=True, gridcolor="#F3F4F6", linecolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6", linecolor="#E5E7EB")
    return fig

BRAND = ["#10B981","#F59E0B","#3B82F6","#8B5CF6","#EF4444","#06B6D4","#F97316","#84CC16"]

# ══════════════════════════════════════════════════════════════════════
#  🧠  DEEP DATASET PROFILER
# ══════════════════════════════════════════════════════════════════════
def analyze_dataframe(df):
    profile = {
        "num_cols": df.select_dtypes(include="number").columns.tolist(),
        "cat_cols": df.select_dtypes(include=["object","category"]).columns.tolist(),
        "date_cols": [], "bool_cols": [], "id_cols": [],
        "binary_num_cols": [], "high_card_cats": [], "low_card_cats": [],
        "skewed_cols": [], "correlated_pairs": [], "time_series_col": None,
        "target_candidates": [], "n_rows": len(df), "n_cols": len(df.columns),
        "outlier_cols": {}, "trend_info": {}, "segment_insights": [],
        "anomaly_rows": pd.DataFrame(),
    }

    # Detect date columns
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            profile["date_cols"].append(col)
        elif df[col].dtype == object:
            date_kws = ["date","time","year","month","day","année","mois","jour","periode","semaine","timestamp"]
            if any(kw in col.lower() for kw in date_kws):
                try:
                    pd.to_datetime(df[col].dropna().head(5), infer_datetime_format=True)
                    profile["date_cols"].append(col)
                except: pass

    profile["bool_cols"] = df.select_dtypes(include="bool").columns.tolist()

    # ID columns
    for col in df.columns:
        if df[col].nunique() == len(df) or any(kw in col.lower() for kw in ["id","code","ref","uuid","key","index","no."]):
            profile["id_cols"].append(col)

    profile["num_cols"] = [c for c in profile["num_cols"] if c not in profile["id_cols"]]
    profile["cat_cols"] = [c for c in profile["cat_cols"] if c not in profile["id_cols"] and c not in profile["date_cols"]]

    for col in profile["num_cols"]:
        if df[col].nunique() <= 2:
            profile["binary_num_cols"].append(col)

    for col in profile["cat_cols"]:
        n = df[col].nunique()
        (profile["low_card_cats"] if n <= 8 else profile["high_card_cats"]).append(col)

    # Skewness
    for col in profile["num_cols"]:
        try:
            if abs(df[col].skew()) > 1.5:
                profile["skewed_cols"].append(col)
        except: pass

    # Correlations
    pure_num = [c for c in profile["num_cols"] if c not in profile["binary_num_cols"]]
    if len(pure_num) >= 2:
        corr = df[pure_num].corr()
        pairs = []
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                v = corr.iloc[i,j]
                if not np.isnan(v):
                    pairs.append((corr.columns[i], corr.columns[j], round(v,3)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        profile["correlated_pairs"] = pairs[:5]

    if profile["date_cols"] and profile["num_cols"]:
        profile["time_series_col"] = profile["date_cols"][0]

    profile["target_candidates"] = [c for c in profile["num_cols"] if c not in profile["binary_num_cols"]][:3]

    # ── Outlier detection per column (Z-score + IQR) ──
    for col in profile["num_cols"]:
        try:
            col_data = df[col].dropna()
            Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            IQR = Q3 - Q1
            lo, hi = Q1 - 1.5*IQR, Q3 + 1.5*IQR
            n_out = ((df[col] < lo) | (df[col] > hi)).sum()
            z_scores = np.abs(scipy_stats.zscore(col_data))
            n_zscore = (z_scores > 3).sum()
            profile["outlier_cols"][col] = {
                "iqr_count": int(n_out), "zscore_count": int(n_zscore),
                "pct": round(n_out / len(df) * 100, 1), "low": round(lo,2), "high": round(hi,2)
            }
        except: pass

    # ── Trend detection on time series ──
    if profile["date_cols"] and profile["num_cols"]:
        date_col = profile["date_cols"][0]
        for ycol in profile["num_cols"][:3]:
            try:
                tmp = df[[date_col, ycol]].copy().dropna()
                tmp[date_col] = pd.to_datetime(tmp[date_col], infer_datetime_format=True, errors="coerce")
                tmp = tmp.dropna().sort_values(date_col)
                if len(tmp) >= 4:
                    x = np.arange(len(tmp))
                    slope, intercept, r, p, se = scipy_stats.linregress(x, tmp[ycol].values)
                    direction = "up" if slope > 0 else "down"
                    strength = abs(r)
                    pct_change = ((tmp[ycol].iloc[-1] - tmp[ycol].iloc[0]) / (abs(tmp[ycol].iloc[0]) + 1e-9)) * 100
                    profile["trend_info"][ycol] = {
                        "slope": round(slope,4), "r": round(r,3), "p": round(p,4),
                        "direction": direction, "strength": round(strength,2),
                        "pct_change": round(pct_change,1), "significant": p < 0.05
                    }
            except: pass

    # ── Automatic segment insights (groupby discovery) ──
    if profile["low_card_cats"] and profile["target_candidates"]:
        cat_col = profile["low_card_cats"][0]
        y_col = profile["target_candidates"][0]
        try:
            grp = df.groupby(cat_col)[y_col].agg(["mean","count"]).reset_index()
            grp.columns = [cat_col, "mean", "count"]
            global_mean = df[y_col].mean()
            grp["delta_pct"] = ((grp["mean"] - global_mean) / (abs(global_mean) + 1e-9) * 100).round(1)
            grp = grp.sort_values("delta_pct", ascending=False)
            profile["segment_insights"] = grp.to_dict("records")
        except: pass

    # ── Anomaly rows: Z-score > 3.5 on any numeric column ──
    try:
        if profile["num_cols"]:
            num_data = df[profile["num_cols"]].dropna(how="all")
            z = pd.DataFrame(np.abs(scipy_stats.zscore(num_data.fillna(num_data.median()), nan_policy="omit")),
                             columns=num_data.columns, index=num_data.index)
            anomaly_mask = (z > 3.5).any(axis=1)
            profile["anomaly_rows"] = df[anomaly_mask].head(10)
    except: pass

    return profile


# ══════════════════════════════════════════════════════════════════════
#  📊  SMART CHART ENGINE
# ══════════════════════════════════════════════════════════════════════
def decide_charts(df, profile):
    charts = []
    num = profile["num_cols"]
    dates = profile["date_cols"]
    low_cat = profile["low_card_cats"]
    high_cat = profile["high_card_cats"]
    binary = profile["binary_num_cols"]
    skewed = profile["skewed_cols"]
    pairs = profile["correlated_pairs"]
    pure_num = [c for c in num if c not in binary]

    # 1. Time series first
    if dates and num:
        y_col = pure_num[0] if pure_num else num[0]
        charts.append({"type":"timeseries","x":dates[0],"y":y_col,"title":f"Évolution de {y_col}","label":"Série Temporelle"})
        extra = [c for c in pure_num if c != y_col][:2]
        if extra:
            charts.append({"type":"timeseries_multi","x":dates[0],"y":[y_col]+extra,"title":"Métriques clés dans le temps","label":"Tendances Multiples"})

    # 2. Strong correlation scatter
    if pairs and abs(pairs[0][2]) > 0.4:
        a,b,v = pairs[0]
        charts.append({"type":"scatter","x":a,"y":b,"corr":v,"title":f"Corrélation {a} × {b} (r={v:+.2f})","label":"Corrélation"})

    # 3. Segment bar
    if low_cat and pure_num:
        charts.append({"type":"segment_bar","x":low_cat[0],"y":pure_num[0],"title":f"Moyenne de {pure_num[0]} par {low_cat[0]}","label":"Analyse Segment"})

    # 4. Skewed / normal distribution
    if skewed:
        charts.append({"type":"histogram_log","col":skewed[0],"title":f"Distribution asymétrique — {skewed[0]}","label":"Distribution Log"})
    elif pure_num and not dates:
        charts.append({"type":"histogram","col":pure_num[0],"title":f"Distribution — {pure_num[0]}","label":"Distribution"})

    # 5. Binary donut
    if binary:
        charts.append({"type":"donut","col":binary[0],"title":f"Répartition — {binary[0]}","label":"Variable Binaire"})

    # 6. Low-card pie
    if low_cat and df[low_cat[0]].nunique() <= 6:
        charts.append({"type":"pie","col":low_cat[0],"title":f"Répartition — {low_cat[0]}","label":"Catégories"})

    # 7. High-card hbar
    if high_cat:
        charts.append({"type":"hbar","col":high_cat[0],"title":f"Top 10 — {high_cat[0]}","label":"Top Valeurs"})

    # 8. Heatmap
    if len(pure_num) >= 3:
        charts.append({"type":"heatmap","cols":pure_num[:8],"title":"Matrice de Corrélation","label":"Corrélations"})

    # 9. Grouped boxplot
    if low_cat and pure_num:
        charts.append({"type":"box","x":low_cat[0],"y":pure_num[0],"title":f"Distribution de {pure_num[0]} par {low_cat[0]}","label":"Boxplot Groupé"})

    # 10. Missing values
    miss = df.isnull().sum(); miss = miss[miss>0]
    if len(miss) > 0:
        charts.append({"type":"missing","data":miss,"title":"Valeurs Manquantes","label":"Qualité Données"})

    # 11. P10/P50/P90 percentile chart
    if pure_num:
        charts.append({"type":"percentile","cols":pure_num[:5],"title":"Bandes Percentiles P10/P50/P90","label":"Percentiles"})

    # 12. Outlier highlight scatter
    if pure_num and profile["outlier_cols"]:
        top_out_col = max(profile["outlier_cols"], key=lambda c: profile["outlier_cols"][c]["iqr_count"])
        if len(pure_num) >= 2:
            other = [c for c in pure_num if c != top_out_col][0]
            charts.append({"type":"outlier_scatter","x":other,"y":top_out_col,"title":f"Outliers — {top_out_col}","label":"Détection Outliers"})

    return charts[:8]


def render_chart(df, spec, profile=None, key_prefix="rc"):
    t = spec["type"]; title = spec.get("title","")
    _key = f"{key_prefix}_{t}_{hash(title) % 99999}"
    try:
        if t == "timeseries":
            tmp = df.copy()
            tmp[spec["x"]] = pd.to_datetime(tmp[spec["x"]], infer_datetime_format=True, errors="coerce")
            tmp = tmp.dropna(subset=[spec["x"]]).sort_values(spec["x"])
            trend = (profile or {}).get("trend_info",{}).get(spec["y"],{})
            fig = px.line(tmp, x=spec["x"], y=spec["y"], title=title, color_discrete_sequence=["#10B981"])
            fig.update_traces(line_width=2.5, fill="tozeroy", fillcolor="rgba(16,185,129,0.06)")
            if trend.get("significant"):
                badge = "↑ Hausse significative" if trend["direction"]=="up" else "↓ Baisse significative"
                fig.add_annotation(text=badge, xref="paper", yref="paper", x=0.01, y=0.97, showarrow=False,
                                   font=dict(color="#065F46",size=11), bgcolor="#ECFDF5", bordercolor="#A7F3D0", borderwidth=1)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_ts")

        elif t == "timeseries_multi":
            tmp = df.copy()
            tmp[spec["x"]] = pd.to_datetime(tmp[spec["x"]], infer_datetime_format=True, errors="coerce")
            tmp = tmp.dropna(subset=[spec["x"]]).sort_values(spec["x"])
            fig = px.line(tmp, x=spec["x"], y=spec["y"], title=title)
            fig.update_traces(line_width=2)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_tsm")

        elif t == "scatter":
            col_data = df[[spec["x"],spec["y"]]].dropna()
            Q1x,Q3x = col_data[spec["x"]].quantile(0.25),col_data[spec["x"]].quantile(0.75)
            Q1y,Q3y = col_data[spec["y"]].quantile(0.25),col_data[spec["y"]].quantile(0.75)
            IQRx,IQRy = Q3x-Q1x, Q3y-Q1y
            is_out = ((col_data[spec["x"]]<Q1x-1.5*IQRx)|(col_data[spec["x"]]>Q3x+1.5*IQRx)|(col_data[spec["y"]]<Q1y-1.5*IQRy)|(col_data[spec["y"]]>Q3y+1.5*IQRy))
            col_data = col_data.copy(); col_data["type"] = np.where(is_out,"Outlier","Normal")
            fig = px.scatter(col_data, x=spec["x"], y=spec["y"], title=title, color="type",
                             color_discrete_map={"Normal":"#3B82F6","Outlier":"#EF4444"},
                             trendline="ols", opacity=0.65, trendline_scope="overall",
                             trendline_color_override="#F59E0B")
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_sc")

        elif t == "segment_bar":
            agg = df.groupby(spec["x"])[spec["y"]].mean().reset_index().sort_values(spec["y"],ascending=False).head(12)
            global_mean = df[spec["y"]].mean()
            agg["color"] = agg[spec["y"]].apply(lambda v: "#10B981" if v >= global_mean else "#EF4444")
            fig = px.bar(agg, x=spec["x"], y=spec["y"], title=title, color="color",
                         color_discrete_map="identity", text=spec["y"])
            fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
            fig.add_hline(y=global_mean, line_dash="dot", line_color="#F59E0B",
                          annotation_text=f"Moyenne globale: {global_mean:.2f}", annotation_position="top right")
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_sb")

        elif t == "histogram":
            fig = px.histogram(df, x=spec["col"], nbins=40, title=title, marginal="box",
                               color_discrete_sequence=["#10B981"])
            fig.update_traces(marker_line_color="#065F46", marker_line_width=0.5)
            # Add mean and median lines
            mean_val = df[spec["col"]].mean(); med_val = df[spec["col"]].median()
            fig.add_vline(x=mean_val, line_dash="dash", line_color="#F59E0B",
                          annotation_text=f"Moy: {mean_val:.2f}", annotation_position="top")
            fig.add_vline(x=med_val, line_dash="dot", line_color="#3B82F6",
                          annotation_text=f"Med: {med_val:.2f}", annotation_position="top right")
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_hi")

        elif t == "histogram_log":
            col_data = df[spec["col"]].dropna()
            pos = col_data[col_data > 0]
            fig = px.histogram(pos if len(pos) > 10 else col_data, x=spec["col"],
                               nbins=40, title=title, color_discrete_sequence=["#F59E0B"], log_y=True)
            fig.update_traces(marker_line_color="#92400E", marker_line_width=0.5)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_hl")

        elif t == "donut":
            vc = df[spec["col"]].value_counts()
            fig = go.Figure(data=[go.Pie(labels=vc.index.astype(str), values=vc.values,
                                         hole=0.6, marker_colors=["#10B981","#F59E0B","#3B82F6","#EF4444"])])
            fig.update_layout(title=title, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, key=_key+"_do")

        elif t == "pie":
            vc = df[spec["col"]].value_counts().head(8)
            fig = px.pie(values=vc.values, names=vc.index.astype(str), title=title,
                         color_discrete_sequence=BRAND)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_pi")

        elif t == "hbar":
            vc = df[spec["col"]].value_counts().head(10)
            fig = px.bar(x=vc.values, y=vc.index.astype(str), orientation="h", title=title,
                         color=vc.values, color_continuous_scale=["#A7F3D0","#10B981","#065F46"],
                         text=vc.values)
            fig.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig.update_layout(yaxis=dict(autorange="reversed"), **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, key=_key+"_hb")

        elif t == "heatmap":
            corr = df[spec["cols"]].corr()
            fig = go.Figure(data=go.Heatmap(
                z=corr.values, x=corr.columns, y=corr.columns,
                colorscale=[[0,"#EF4444"],[0.5,"#FFFFFF"],[1,"#10B981"]],
                zmin=-1, zmax=1, text=np.round(corr.values,2),
                texttemplate="%{text}", textfont={"size":9}
            ))
            fig.update_layout(title=title, height=380, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, key=_key+"_hm")

        elif t == "box":
            top_cats = df[spec["x"]].value_counts().head(8).index
            tmp = df[df[spec["x"]].isin(top_cats)]
            fig = px.box(tmp, x=spec["x"], y=spec["y"], title=title,
                         color=spec["x"], points="outliers",
                         color_discrete_sequence=BRAND)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_bx")

        elif t == "missing":
            miss = spec["data"]
            mdf = pd.DataFrame({"Colonne":miss.index, "Pct (%)": (miss/len(df)*100).round(1).values})
            fig = px.bar(mdf, x="Colonne", y="Pct (%)", title=title,
                         color="Pct (%)", color_continuous_scale=["#10B981","#F59E0B","#EF4444"],
                         text="Pct (%)")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_ms")

        elif t == "percentile":
            cols = spec["cols"]
            p10 = df[cols].quantile(0.10)
            p50 = df[cols].quantile(0.50)
            p90 = df[cols].quantile(0.90)
            fig = go.Figure()
            x = list(range(len(cols)))
            fig.add_trace(go.Scatter(x=cols, y=p90.values, name="P90", line=dict(color="#EF4444", width=2, dash="dot"), mode="lines+markers"))
            fig.add_trace(go.Scatter(x=cols, y=p50.values, name="P50 (Médiane)", line=dict(color="#10B981", width=3), mode="lines+markers"))
            fig.add_trace(go.Scatter(x=cols, y=p10.values, name="P10", line=dict(color="#3B82F6", width=2, dash="dot"), mode="lines+markers",
                                     fill="tonexty", fillcolor="rgba(16,185,129,0.06)"))
            fig.update_layout(title=title, **PLOTLY_LAYOUT)
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_pc")

        elif t == "outlier_scatter":
            col_data = df[[spec["x"],spec["y"]]].dropna().copy()
            Q1,Q3 = col_data[spec["y"]].quantile(0.25),col_data[spec["y"]].quantile(0.75)
            IQR = Q3-Q1
            col_data["Statut"] = np.where((col_data[spec["y"]]<Q1-1.5*IQR)|(col_data[spec["y"]]>Q3+1.5*IQR),"Outlier","Normal")
            fig = px.scatter(col_data, x=spec["x"], y=spec["y"], color="Statut",
                             color_discrete_map={"Normal":"rgba(16,185,129,0.5)","Outlier":"#EF4444"},
                             title=title, size_max=10,
                             symbol="Statut", symbol_map={"Normal":"circle","Outlier":"x"})
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True, key=_key+"_os")

    except Exception as e:
        st.caption(f"Erreur graphique : {e}")


# ══════════════════════════════════════════════════════════════════════
#  💬  NATURAL LANGUAGE CHART BUILDER
# ══════════════════════════════════════════════════════════════════════
def nl_to_chart(question, df, profile):
    """Use AI to parse a natural language question into a chart spec and render it."""
    col_info = {
        "numeric": profile["num_cols"],
        "categorical": profile["cat_cols"],
        "dates": profile["date_cols"],
        "sample_values": {c: df[c].dropna().unique()[:5].tolist() for c in (profile["cat_cols"])[:3]}
    }
    prompt = f"""Tu es un expert en visualisation de données. L'utilisateur demande: "{question}"

Colonnes disponibles: {json.dumps(col_info, ensure_ascii=False)}

Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans explication) décrivant le meilleur graphique:
{{
  "type": "bar|line|scatter|pie|histogram|box|heatmap",
  "x": "nom_colonne_ou_null",
  "y": "nom_colonne_ou_null",
  "color": "nom_colonne_ou_null",
  "title": "titre du graphique",
  "agg": "mean|sum|count|median",
  "top_n": 10,
  "explanation": "pourquoi ce graphique"
}}"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.1, max_tokens=400
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'```json|```','',raw).strip()
        spec = json.loads(raw)
        return spec
    except Exception as e:
        return {"error": str(e)}

def render_nl_chart(spec, df):
    """Render a chart from AI-generated spec."""
    try:
        t = spec.get("type","bar")
        x = spec.get("x"); y = spec.get("y")
        color = spec.get("color"); title = spec.get("title","Graphique")
        agg = spec.get("agg","mean"); top_n = spec.get("top_n",10)

        if t in ["bar","column"]:
            if x and y:
                if df[x].dtype == object or df[x].nunique() < 30:
                    grp = df.groupby(x)[y].agg(agg).reset_index().sort_values(y, ascending=False).head(top_n)
                    fig = px.bar(grp, x=x, y=y, title=title, color=y,
                                 color_continuous_scale=["#A7F3D0","#10B981","#065F46"],
                                 text=y)
                    fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
                else:
                    fig = px.bar(df.head(top_n), x=x, y=y, title=title, color_discrete_sequence=["#10B981"])
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)
            elif x:
                vc = df[x].value_counts().head(top_n)
                fig = px.bar(x=vc.index.astype(str), y=vc.values, title=title, color_discrete_sequence=["#10B981"])
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "line":
            if x and y:
                tmp = df[[x,y]].dropna()
                try: tmp[x] = pd.to_datetime(tmp[x], infer_datetime_format=True, errors="coerce")
                except: pass
                tmp = tmp.sort_values(x)
                ycols = [y] + ([color] if color and color in df.columns else [])
                fig = px.line(tmp, x=x, y=ycols, title=title)
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "scatter":
            if x and y:
                fig = px.scatter(df, x=x, y=y, color=color if color in (df.columns.tolist() if color else []) else None,
                                 title=title, trendline="ols", opacity=0.6)
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "pie":
            col = x or y
            if col:
                vc = df[col].value_counts().head(top_n)
                fig = px.pie(values=vc.values, names=vc.index.astype(str), title=title,
                             color_discrete_sequence=BRAND)
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "histogram":
            col = y or x
            if col:
                fig = px.histogram(df, x=col, nbins=40, title=title, marginal="box",
                                   color_discrete_sequence=["#10B981"])
                apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "box":
            if x and y:
                fig = px.box(df, x=x, y=y, title=title, color=x, points="outliers",
                             color_discrete_sequence=BRAND)
            elif y:
                fig = px.box(df, y=y, title=title, color_discrete_sequence=["#10B981"])
            apply_theme(fig); st.plotly_chart(fig, use_container_width=True)

        elif t == "heatmap":
            num_cols = df.select_dtypes(include="number").columns.tolist()[:8]
            corr = df[num_cols].corr()
            fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns,
                                             colorscale=[[0,"#EF4444"],[0.5,"#FFFFFF"],[1,"#10B981"]],
                                             zmin=-1, zmax=1, text=np.round(corr.values,2),
                                             texttemplate="%{text}", textfont={"size":9}))
            fig.update_layout(title=title, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        if spec.get("explanation"):
            st.caption(f"💡 {spec['explanation']}")

    except Exception as e:
        st.error(f"Erreur lors du rendu : {e}")


# ══════════════════════════════════════════════════════════════════════
#  📐  ADVANCED STATISTICS ENGINE
# ══════════════════════════════════════════════════════════════════════
def compute_advanced_stats(df, profile):
    """Compute P10/P50/P90, CV, normality test, and segment delta per numeric col."""
    results = {}
    for col in profile["num_cols"]:
        try:
            col_data = df[col].dropna()
            if len(col_data) < 3: continue
            mean = col_data.mean(); std = col_data.std(); median = col_data.median()
            cv = (std / mean * 100) if mean != 0 else None
            p10, p50, p90 = col_data.quantile([0.1, 0.5, 0.9]).values
            stat, pval = scipy_stats.shapiro(col_data.sample(min(50, len(col_data)), random_state=42)) if len(col_data) >= 3 else (None, None)
            pct_above_mean = (col_data > mean).mean() * 100
            results[col] = {
                "mean": round(mean,2), "median": round(median,2), "std": round(std,2),
                "cv": round(cv,1) if cv is not None else None,
                "p10": round(p10,2), "p50": round(p50,2), "p90": round(p90,2),
                "normal_pval": round(pval,4) if pval is not None else None,
                "is_normal": (pval > 0.05) if pval is not None else None,
                "pct_above_mean": round(pct_above_mean,1)
            }
        except: pass
    return results


# ══════════════════════════════════════════════════════════════════════
#  🤖  AI HELPERS
# ══════════════════════════════════════════════════════════════════════
def build_dataset_context(df, filename, profile=None):
    rows, cols = df.shape
    p = profile or analyze_dataframe(df)
    missing_info = {c: int(df[c].isnull().sum()) for c in df.columns if df[c].isnull().sum() > 0}
    stats = df[p["num_cols"]].describe().to_string() if p["num_cols"] else "N/A"
    trend_summary = {k: f"{v['direction']} {v['pct_change']:+.1f}% (p={v['p']:.3f})" for k,v in p.get("trend_info",{}).items()}
    outlier_summary = {k: f"{v['iqr_count']} outliers ({v['pct']}%)" for k,v in p.get("outlier_cols",{}).items() if v['iqr_count']>0}
    return (f"File: {filename}\nShape: {rows}x{cols}\nNumeric: {p['num_cols']}\n"
            f"Categorical: {p['cat_cols']}\nDates: {p['date_cols']}\nMissing: {missing_info}\n"
            f"Trends: {trend_summary}\nOutliers: {outlier_summary}\n"
            f"Stats:\n{stats}\nSample:\n{df.head(5).to_string()}")

def get_ai_response(messages, context):
    client = Groq(api_key=GROQ_API_KEY)
    system = f"Vous êtes un expert senior en analyse de données et stratégie d'entreprise. Dataset:\n{context}"
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":system}] + messages,
        temperature=0.4, max_tokens=2048
    )
    return completion.choices[0].message.content

def render_chat_message(role, content):
    if role == "user":
        st.markdown(f'<p class="chat-label chat-label-user">Vous</p><div class="chat-user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="chat-label chat-label-bot">Expert IA DataCommerce</p><div class="chat-assistant">{content}</div>', unsafe_allow_html=True)

def clean_text(t): return re.sub(r'[*#`_~]','',t or "").strip()
def extract_bullets(text):
    if not text: return []
    return [l.strip() for l in re.split(r'\n[-•·▸▹►\d+\.\)]+\s*', text) if len(l.strip()) > 15][:8]


# ══════════════════════════════════════════════════════════════════════
#  📄  PDF EXPORT
# ══════════════════════════════════════════════════════════════════════
def generate_pdf_report(raw_text, df, filename):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    now = datetime.now()
    rows, cols_n = df.shape
    num_cols = df.select_dtypes(include="number").columns.tolist()
    missing_pct = round((df.isnull().sum().sum()/(rows*cols_n))*100,1)
    completeness = round(100-missing_pct,1)

    ts=ParagraphStyle("t",parent=styles["Normal"],fontSize=20,fontName="Helvetica-Bold",textColor=colors.HexColor("#065F46"),spaceAfter=6)
    ss=ParagraphStyle("s",parent=styles["Normal"],fontSize=9,textColor=colors.HexColor("#6B7280"),spaceAfter=14)
    h2=ParagraphStyle("h2",parent=styles["Normal"],fontSize=12,fontName="Helvetica-Bold",textColor=colors.HexColor("#111827"),spaceBefore=12,spaceAfter=5)
    bs=ParagraphStyle("b",parent=styles["Normal"],fontSize=9,textColor=colors.HexColor("#374151"),leading=14,spaceAfter=3)
    fs=ParagraphStyle("f",parent=styles["Normal"],fontSize=7,textColor=colors.HexColor("#9CA3AF"),alignment=TA_CENTER)

    story=[]
    story.append(Paragraph("RAPPORT STRATÉGIQUE · DATACOMMERCE",ParagraphStyle("lbl",parent=styles["Normal"],fontSize=7.5,textColor=colors.HexColor("#9CA3AF"),fontName="Helvetica-Bold",spaceAfter=4)))
    story.append(Paragraph(f"Analyse : {filename}",ts))
    story.append(Paragraph(f"Généré le {now.strftime('%d %B %Y à %H:%M')} · Confidentiel",ss))
    story.append(HRFlowable(width="100%",thickness=2,color=colors.HexColor("#065F46"),spaceAfter=10))
    meta=[["Lignes","Colonnes","Complétude","Vars Numériques"],[f"{rows:,}",f"{cols_n}",f"{completeness}%",f"{len(num_cols)}"]]
    mt=Table(meta,colWidths=[4.2*cm]*4)
    mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F3F4F6")),("TEXTCOLOR",(0,0),(-1,0),colors.HexColor("#6B7280")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),7.5),("BACKGROUND",(0,1),(-1,1),colors.HexColor("#ECFDF5")),("TEXTCOLOR",(0,1),(-1,1),colors.HexColor("#065F46")),("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,1),(-1,1),13),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#E5E7EB")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#E5E7EB")),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.append(mt); story.append(Spacer(1,12))
    sp={k:re.search(v,raw_text,re.I|re.S) for k,v in {"exec":r'(?:résumé\s+exécutif|synthèse)(.*?)(?=\n##|\Z)',"kpi":r'(?:kpi|statistiques\s+clés)(.*?)(?=\n##|\Z)',"alerts":r'(?:alertes?|anomalies)(.*?)(?=\n##|\Z)',"insights":r'(?:insights?|observations\s+clés)(.*?)(?=\n##|\Z)',"recos":r'(?:recommandations?)(.*?)(?=\n##|\Z)'}.items()}
    for key,title in [("exec","1. Résumé Exécutif"),("kpi","2. KPI & Statistiques"),("alerts","3. Alertes & Anomalies"),("insights","4. Insights Clés"),("recos","5. Recommandations")]:
        story.append(Paragraph(title,h2))
        story.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#E5E7EB"),spaceAfter=5))
        content=clean_text(sp[key].group(1)) if sp.get(key) and sp[key] else (clean_text(raw_text[:500]) if key=="exec" else "")
        bullets=extract_bullets(content)
        for b in (bullets[:6] if bullets else [l.strip() for l in content[:500].split("\n") if len(l.strip())>10][:6]):
            story.append(Paragraph(f"• {b[:280]}",bs))
        story.append(Spacer(1,6))
    if num_cols:
        story.append(Paragraph("6. Statistiques Descriptives",h2))
        story.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#E5E7EB"),spaceAfter=5))
        sdf=df[num_cols[:6]].describe().round(2)
        td=[[""] + list(sdf.columns)] + [[idx]+[str(v) for v in sdf.loc[idx]] for idx in sdf.index]
        cw=[2.5*cm]+[min(3.5*cm,14*cm/max(len(num_cols[:6]),1))]*len(sdf.columns)
        stt=Table(td,colWidths=cw[:len(td[0])])
        stt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#065F46")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7.5),("ALIGN",(1,0),(-1,-1),"CENTER"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F9FAFB")]),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#E5E7EB")),("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#E5E7EB")),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        story.append(stt)
    story.append(Spacer(1,14))
    story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor("#E5E7EB"),spaceAfter=5))
    story.append(Paragraph(f"DataCommerce Analytics Engine · Confidentiel · {now.strftime('%d/%m/%Y %H:%M')} · LLaMA 3.3 70B",fs))
    doc.build(story); return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
#  🖥️  REPORT RENDERER
# ══════════════════════════════════════════════════════════════════════
def parse_and_render_report(raw_text, df, filename, profile):
    now = datetime.now()
    rows, cols = df.shape
    num_cols = profile["num_cols"]
    missing_total = df.isnull().sum().sum()
    missing_pct = round((missing_total/(rows*cols))*100,1)
    completeness = round(100-missing_pct,1)
    confidence = min(95,max(60,100-missing_pct*2+(5 if rows>1000 else 0)+(3 if profile["date_cols"] else 0)))

    # Cover
    st.markdown(f"""
    <div class="report-cover">
      <div class="report-cover-label">Rapport Stratégique & Intelligence Décisionnelle</div>
      <div class="report-cover-title">Analyse Complète du Dataset<br><span style="color:#6EE7B7">{filename}</span></div>
      <div class="report-cover-sub">Généré par DataCommerce AI Analytics Engine · Confidentiel</div>
      <div class="report-cover-meta">
        <span>📅 {now.strftime("%d %B %Y, %H:%M")}</span>
        <span>📊 {rows:,} lignes · {cols} colonnes</span>
        <span>✅ Complétude : {completeness}%</span>
        <span>🔢 {len(num_cols)} variables numériques</span>
        {"<span>📅 Série temporelle détectée</span>" if profile["date_cols"] else ""}
      </div>
    </div>""", unsafe_allow_html=True)

    # Confidence + trend badges
    trend_html = ""
    for col, info in list(profile.get("trend_info",{}).items())[:3]:
        badge_cls = "trend-badge-up" if info["direction"]=="up" else "trend-badge-down"
        arrow = "↑" if info["direction"]=="up" else "↓"
        sig = "★" if info["significant"] else ""
        trend_html += f'<span class="{badge_cls}" style="margin-right:8px">{sig}{arrow} {col}: {info["pct_change"]:+.1f}%</span>'

    st.markdown(f"""
    <div class="report-section" style="padding:1.2rem 2rem;">
      <div class="confidence-label"><span>🎯 Indice de Confiance de l'Analyse</span><span><strong>{confidence:.0f}%</strong></span></div>
      <div class="confidence-bar"><div class="confidence-fill" style="width:{confidence}%"></div></div>
      {f'<div style="margin-top:10px">{trend_html}</div>' if trend_html else ""}
    </div>""", unsafe_allow_html=True)

    # Parse sections
    sections = {k: re.search(v, raw_text, re.I|re.S) for k,v in {
        "exec": r'(?:résumé\s+exécutif|synthèse|compréhension)(.*?)(?=\n##|\Z)',
        "kpi":  r'(?:kpi|statistiques\s+clés)(.*?)(?=\n##|\Z)',
        "alerts":r'(?:alertes?|anomalies)(.*?)(?=\n##|\Z)',
        "insights":r'(?:insights?|observations\s+clés)(.*?)(?=\n##|\Z)',
        "recos":r'(?:recommandations?)(.*?)(?=\n##|\Z)',
    }.items()}

    # Executive summary
    exec_text = clean_text(sections["exec"].group(1)) if sections["exec"] else clean_text(raw_text[:800])
    if exec_text:
        st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-blue">📋</div><div class="section-title">Résumé Exécutif</div><div class="section-badge">Executive Summary</div></div><div class="exec-summary">{exec_text[:900]}</div></div>', unsafe_allow_html=True)

    # KPI cards
    tm = {"up":("▲","trend-up"),"down":("▼","trend-down"),"neutral":("●","trend-neutral")}
    kpis = [(f"{rows:,}","Enregistrements","neutral"),(f"{cols}","Variables","neutral"),(f"{completeness}%","Complétude","up" if completeness>90 else "down"),(f"{len(num_cols)}","Vars Numériques","neutral")]
    c = st.columns(4)
    for i,(val,label,trend) in enumerate(kpis):
        sym,cls=tm[trend]
        with c[i]: st.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div><div class="kpi-trend {cls}">{sym}</div></div>', unsafe_allow_html=True)

    if num_cols:
        adv = compute_advanced_stats(df, profile)
        st.markdown("<br>", unsafe_allow_html=True)
        ec = st.columns(min(4, len(num_cols)))
        for i, col in enumerate(num_cols[:4]):
            s = adv.get(col,{})
            mv = s.get("mean", df[col].mean())
            cv_str = f" · CV {s['cv']:.0f}%" if s.get("cv") else ""
            with ec[i]:
                st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="font-size:1.3rem">{mv:,.1f}</div><div class="kpi-label">{col[:16]}</div><div style="font-size:0.72rem;color:#9CA3AF;margin-top:2px">P10:{s.get("p10","?")} · P90:{s.get("p90","?")}{cv_str}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Smart charts
    if PLOTLY_AVAILABLE:
        chart_specs = decide_charts(df, profile)
        if chart_specs:
            st.markdown('<div class="report-section"><div class="report-section-header"><div class="section-icon icon-teal">📈</div><div class="section-title">Visualisations Intelligentes</div><div class="section-badge">Auto-sélectionnées</div></div></div>', unsafe_allow_html=True)
            for i in range(0, len(chart_specs), 2):
                cc = st.columns(2)
                for j, spec in enumerate(chart_specs[i:i+2]):
                    with cc[j]:
                        st.markdown(f'<span class="chart-label">{spec.get("label","")}</span>', unsafe_allow_html=True)
                        render_chart(df, spec, profile, key_prefix=f"rpt_{i}_{j}")

    # Segment insights
    if profile.get("segment_insights"):
        segs = profile["segment_insights"]
        cat_col = profile["low_card_cats"][0] if profile["low_card_cats"] else "Segment"
        y_col = profile["target_candidates"][0] if profile["target_candidates"] else "Valeur"
        segs_html = ""
        for s in segs[:6]:
            d = s.get("delta_pct",0)
            cls = "segment-delta-pos" if d >= 0 else "segment-delta-neg"
            arrow = "▲" if d >= 0 else "▼"
            segs_html += f'<div class="segment-card"><span class="segment-title">{s.get(cat_col,"?")} </span><span style="color:#6B7280;font-size:0.82rem">· moy {y_col}: {s.get("mean",0):.2f} · n={s.get("count",0):,}</span><span class="{cls}" style="float:right">{arrow} {abs(d):.1f}% vs moyenne</span></div>'
        st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-orange">🔬</div><div class="section-title">Analyse des Segments</div><div class="section-badge">Segment Discovery</div></div>{segs_html}</div>', unsafe_allow_html=True)

    # Anomaly rows
    if not profile["anomaly_rows"].empty:
        n_anom = len(profile["anomaly_rows"])
        anom_html = f'<div class="anomaly-row">⚠️ {n_anom} ligne(s) avec des valeurs extrêmes détectées (Z-score > 3.5)</div>'
        st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-red">🚨</div><div class="section-title">Lignes Anomales Détectées</div><div class="section-badge">Anomaly Detection</div></div>{anom_html}</div>', unsafe_allow_html=True)
        with st.expander(f"Voir les {n_anom} lignes anomales"):
            st.dataframe(profile["anomaly_rows"], use_container_width=True)

    # Alerts
    amap={"critical":("alert-critical","dot-red"),"warning":("alert-warning","dot-amber"),"ok":("alert-ok","dot-green")}
    auto_alerts=[]
    if missing_pct>20: auto_alerts.append(("critical","Valeurs Manquantes Critiques",f"{missing_pct}% des données manquantes."))
    elif missing_pct>5: auto_alerts.append(("warning","Valeurs Manquantes Modérées",f"{missing_pct}% de données manquantes."))
    else: auto_alerts.append(("ok","Qualité des Données Satisfaisante",f"{missing_pct}% de valeurs manquantes seulement."))
    if rows<500: auto_alerts.append(("warning","Volume Limité",f"{rows} enregistrements — significativité statistique réduite."))
    if profile["date_cols"]: auto_alerts.append(("ok","Série Temporelle Détectée",f"Colonne date identifiée : {profile['date_cols'][0]}."))
    if profile["correlated_pairs"] and abs(profile["correlated_pairs"][0][2])>0.7:
        a,b,v=profile["correlated_pairs"][0]
        auto_alerts.append(("warning","Forte Corrélation",f"{a} ↔ {b}: r={v:+.2f}. Risque de multicolinéarité."))
    top_out = {k:v for k,v in profile.get("outlier_cols",{}).items() if v["pct"]>5}
    if top_out:
        col_out = list(top_out.keys())[0]
        auto_alerts.append(("warning","Outliers Significatifs",f"Colonne '{col_out}': {top_out[col_out]['pct']}% de valeurs aberrantes."))
    alert_text = sections["alerts"].group(1) if sections["alerts"] else ""
    ab = extract_bullets(clean_text(alert_text))
    ah=""
    for sev,title,body in auto_alerts:
        ac,dc=amap[sev]; ah+=f'<div class="alert-item {ac}"><div class="alert-dot {dc}"></div><div><div class="alert-title">{title}</div><div class="alert-body">{body}</div></div></div>'
    for b in ab[:2]:
        sev="critical" if any(w in b.lower() for w in ["critique","erreur","manqu","anomal"]) else "warning" if any(w in b.lower() for w in ["attention","faible"]) else "ok"
        ac,dc=amap[sev]; ah+=f'<div class="alert-item {ac}"><div class="alert-dot {dc}"></div><div><div class="alert-title">Observation IA</div><div class="alert-body">{b[:180]}</div></div></div>'
    st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-red">🚨</div><div class="section-title">Alertes & Qualité des Données</div><div class="section-badge">Monitoring</div></div>{ah}</div>', unsafe_allow_html=True)

    # Insights
    it=sections["insights"].group(1) if sections["insights"] else ""
    ibs=extract_bullets(clean_text(it)) or extract_bullets(clean_text(raw_text))[:5]
    if ibs:
        ih="".join([f'<div class="insight-text insight-bullet">{b[:220]}</div>' for b in ibs[:6]])
        st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-purple">🔍</div><div class="section-title">Insights & Observations Clés</div><div class="section-badge">Analyse IA</div></div>{ih}</div>', unsafe_allow_html=True)

    # Recommendations
    rt=sections["recos"].group(1) if sections["recos"] else ""
    rbs=extract_bullets(clean_text(rt)) or extract_bullets(clean_text(raw_text[len(raw_text)//2:]))[:5]
    if rbs:
        rh="".join([f'<div class="reco-item"><div class="reco-number">{i+1}</div><div class="reco-text">{b[:250]}</div></div>' for i,b in enumerate(rbs[:6])])
        st.markdown(f'<div class="report-section"><div class="report-section-header"><div class="section-icon icon-green">💼</div><div class="section-title">Recommandations Stratégiques</div><div class="section-badge">Action Plan</div></div>{rh}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="report-footer"><span>🏢 DataCommerce Analytics Engine · Rapport Confidentiel</span><span>Généré le {now.strftime("%d/%m/%Y à %H:%M:%S")}</span><span>Modèle : LLaMA 3.3 70B · v5.0</span></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  📊  EDA TAB
# ══════════════════════════════════════════════════════════════════════
def render_eda_tab(df, profile):
    num_cols = profile["num_cols"]; cat_cols = profile["cat_cols"]
    adv_stats = compute_advanced_stats(df, profile)
    st.markdown("### Analyse Exploratoire des Données")

    eda_tabs = st.tabs(["Distributions","Corrélations","Valeurs Manquantes","Outliers","Catégories","Séries Temporelles","Stats Avancées","Graphiques Auto","Question → Graphique"])

    with eda_tabs[0]:
        if num_cols:
            sel=st.selectbox("Variable numérique",num_cols,key="eda_dist")
            c1,c2=st.columns(2)
            with c1:
                fig=px.histogram(df,x=sel,nbins=40,marginal="box",title=f"Distribution — {sel}",color_discrete_sequence=["#10B981"])
                mean_v=df[sel].mean(); med_v=df[sel].median()
                fig.add_vline(x=mean_v,line_dash="dash",line_color="#F59E0B",annotation_text=f"Moy:{mean_v:.2f}")
                fig.add_vline(x=med_v,line_dash="dot",line_color="#3B82F6",annotation_text=f"Med:{med_v:.2f}")
                apply_theme(fig); st.plotly_chart(fig,use_container_width=True,key="eda_dist_hist")
            with c2:
                fig2=px.violin(df,y=sel,box=True,points="outliers",title=f"Violin — {sel}",color_discrete_sequence=["#F59E0B"])
                apply_theme(fig2); st.plotly_chart(fig2,use_container_width=True,key="eda_dist_violin")
            s=adv_stats.get(sel,{})
            if s:
                pills="".join([f'<span class="stat-pill"><strong>{k}:</strong> {v}</span>' for k,v in [("P10",s.get("p10")),("P50",s.get("p50")),("P90",s.get("p90")),("CV",f"{s.get('cv')}%" if s.get('cv') else "N/A"),("Normal","✅" if s.get("is_normal") else "❌")] if v is not None])
                st.markdown(pills, unsafe_allow_html=True)
            if len(num_cols)>1:
                st.markdown("**Vue globale**")
                n=min(4,len(num_cols[:8])); gcols=st.columns(n)
                for i,col in enumerate(num_cols[:8]):
                    with gcols[i%n]:
                        fm=px.histogram(df,x=col,nbins=20,color_discrete_sequence=["#3B82F6"],height=180)
                        fm.update_layout(title=dict(text=col,font_size=11),showlegend=False,margin=dict(l=5,r=5,t=28,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
                        fm.update_xaxes(showticklabels=False); fm.update_yaxes(showticklabels=False)
                        st.plotly_chart(fm,use_container_width=True,key=f"eda_mini_{col}")
        else: st.info("Aucune variable numérique.")

    with eda_tabs[1]:
        if len(num_cols)>=2:
            corr=df[num_cols].corr()
            fig=go.Figure(data=go.Heatmap(z=corr.values,x=corr.columns,y=corr.columns,colorscale=[[0,"#EF4444"],[0.5,"#FFFFFF"],[1,"#10B981"]],zmin=-1,zmax=1,text=np.round(corr.values,2),texttemplate="%{text}",textfont={"size":10}))
            fig.update_layout(title="Matrice de Corrélation",height=500,**PLOTLY_LAYOUT)
            st.plotly_chart(fig,use_container_width=True,key="eda_corr_heatmap")
            pairs=[(corr.columns[i],corr.columns[j],round(corr.iloc[i,j],3)) for i in range(len(corr.columns)) for j in range(i+1,len(corr.columns))]
            pairs.sort(key=lambda x:abs(x[2]),reverse=True)
            st.markdown("**Top corrélations — Scatter interactif :**")
            if pairs:
                sel_pair=st.selectbox("Paire",options=[f"{a} × {b} (r={v:+.3f})" for a,b,v in pairs[:8]],key="corr_pair")
                idx=next(i for i,p in enumerate(pairs[:8]) if f"{p[0]} × {p[1]}" in sel_pair)
                a,b,v=pairs[idx]
                fig2=px.scatter(df,x=a,y=b,title=f"{a} vs {b} (r={v:+.3f})",trendline="ols",opacity=0.6,trendline_color_override="#F59E0B",color_discrete_sequence=["#3B82F6"])
                apply_theme(fig2); st.plotly_chart(fig2,use_container_width=True,key="eda_corr_scatter")
        else: st.info("Corrélation nécessite ≥2 variables numériques.")

    with eda_tabs[2]:
        miss=df.isnull().sum(); miss_pct=(miss/len(df)*100).round(1)
        mdf=pd.DataFrame({"Colonne":miss.index,"Manquants":miss.values,"Pct (%)":miss_pct.values})
        mdf=mdf[mdf["Manquants"]>0].sort_values("Manquants",ascending=False)
        if len(mdf)>0:
            c1,c2=st.columns([2,1])
            with c1:
                fig=px.bar(mdf,x="Colonne",y="Pct (%)",title="% Valeurs Manquantes",color="Pct (%)",color_continuous_scale=["#10B981","#F59E0B","#EF4444"],text="Pct (%)")
                fig.update_traces(texttemplate="%{text:.1f}%",textposition="outside")
                apply_theme(fig); st.plotly_chart(fig,use_container_width=True,key="eda_missing_bar")
            with c2: st.dataframe(mdf,use_container_width=True,height=300)
        else: st.success("Aucune valeur manquante !")

    with eda_tabs[3]:
        if num_cols:
            sel=st.selectbox("Variable",num_cols,key="eda_out")
            out_info=profile["outlier_cols"].get(sel,{})
            Q1,Q3=df[sel].quantile(0.25),df[sel].quantile(0.75); IQR=Q3-Q1
            lo,hi=Q1-1.5*IQR,Q3+1.5*IQR
            c1,c2=st.columns([3,1])
            with c1:
                col_data=df[sel].dropna().copy()
                col_data_df=col_data.reset_index()
                col_data_df.columns=["index",sel]
                col_data_df["Statut"]=np.where((col_data_df[sel]<lo)|(col_data_df[sel]>hi),"Outlier","Normal")
                fig=px.scatter(col_data_df,x="index",y=sel,color="Statut",title=f"Outliers — {sel}",
                               color_discrete_map={"Normal":"rgba(16,185,129,0.5)","Outlier":"#EF4444"},
                               symbol="Statut",symbol_map={"Normal":"circle","Outlier":"x"})
                fig.add_hline(y=lo,line_dash="dot",line_color="#F59E0B",annotation_text=f"Borne inf {lo:.1f}")
                fig.add_hline(y=hi,line_dash="dot",line_color="#F59E0B",annotation_text=f"Borne sup {hi:.1f}")
                apply_theme(fig); st.plotly_chart(fig,use_container_width=True,key="eda_outlier_scatter")
            with c2:
                for label,val in [("Q1",Q1),("Q3",Q3),("IQR",IQR),("Borne inf",lo),("Borne sup",hi)]:
                    st.markdown(f'<div class="clean-stat">{label} : <span>{val:.2f}</span></div>',unsafe_allow_html=True)
                n_out=out_info.get("iqr_count",0)
                sev_color="#EF4444" if out_info.get("pct",0)>10 else "#F59E0B" if out_info.get("pct",0)>3 else "#10B981"
                st.markdown(f'<div class="clean-stat">Outliers IQR : <span style="color:{sev_color}">{n_out} ({out_info.get("pct",0)}%)</span></div>',unsafe_allow_html=True)
                st.markdown(f'<div class="clean-stat">Outliers Z>3 : <span>{out_info.get("zscore_count",0)}</span></div>',unsafe_allow_html=True)
        else: st.info("Aucune variable numérique.")

    with eda_tabs[4]:
        if cat_cols:
            sel=st.selectbox("Variable catégorielle",cat_cols,key="eda_cat")
            topn=st.slider("Nb valeurs",5,30,10,key="eda_topn")
            counts=df[sel].value_counts().head(topn)
            c1,c2=st.columns(2)
            with c1:
                fig=px.bar(x=counts.values,y=counts.index.astype(str),orientation="h",title=f"Top {topn} — {sel}",color=counts.values,color_continuous_scale=["#A7F3D0","#10B981","#065F46"],text=counts.values)
                fig.update_traces(texttemplate="%{text:,}",textposition="outside")
                fig.update_layout(yaxis=dict(autorange="reversed"),**PLOTLY_LAYOUT)
                st.plotly_chart(fig,use_container_width=True,key="eda_cat_bar")
            with c2:
                fig2=px.pie(values=counts.values,names=counts.index.astype(str),title=f"Répartition — {sel}",color_discrete_sequence=BRAND)
                apply_theme(fig2); st.plotly_chart(fig2,use_container_width=True,key="eda_cat_pie")
            # Segment comparison: cat × first numeric
            if num_cols:
                y_sel=st.selectbox("Comparer avec",num_cols,key="eda_seg_y")
                agg_fn=st.radio("Agrégation",["mean","sum","median","count"],horizontal=True,key="eda_seg_agg")
                grp=df.groupby(sel)[y_sel].agg(agg_fn).reset_index().sort_values(y_sel,ascending=False).head(topn)
                fig3=px.bar(grp,x=sel,y=y_sel,title=f"{agg_fn.capitalize()} de {y_sel} par {sel}",
                            color=y_sel,color_continuous_scale=["#A7F3D0","#10B981","#065F46"],text=y_sel)
                fig3.update_traces(texttemplate="%{text:.2s}",textposition="outside")
                apply_theme(fig3); st.plotly_chart(fig3,use_container_width=True,key="eda_cat_seg")
        else: st.info("Aucune variable catégorielle.")

    with eda_tabs[5]:
        if profile["date_cols"] and num_cols:
            date_col=st.selectbox("Colonne date",profile["date_cols"],key="ts_date")
            y_col=st.selectbox("Métrique",num_cols,key="ts_y")
            try:
                tmp=df[[date_col,y_col]].copy().dropna()
                tmp[date_col]=pd.to_datetime(tmp[date_col],infer_datetime_format=True,errors="coerce")
                tmp=tmp.dropna().sort_values(date_col)
                resample=st.radio("Agrégation temporelle",["Aucune","Jour","Semaine","Mois","Année"],horizontal=True,key="ts_resample")
                freq_map={"Jour":"D","Semaine":"W","Mois":"ME","Année":"YE"}
                if resample != "Aucune":
                    tmp=tmp.set_index(date_col).resample(freq_map[resample])[y_col].mean().reset_index()
                trend=profile.get("trend_info",{}).get(y_col,{})
                fig=px.line(tmp,x=date_col,y=y_col,title=f"Évolution de {y_col}",color_discrete_sequence=["#10B981"])
                fig.update_traces(line_width=2.5,fill="tozeroy",fillcolor="rgba(16,185,129,0.06)")
                if trend.get("significant"):
                    direction="↑ Hausse" if trend["direction"]=="up" else "↓ Baisse"
                    fig.add_annotation(text=f"{direction} {trend['pct_change']:+.1f}% (p={trend['p']:.3f})",
                                      xref="paper",yref="paper",x=0.01,y=0.97,showarrow=False,
                                      font=dict(color="#065F46",size=11),bgcolor="#ECFDF5",bordercolor="#A7F3D0",borderwidth=1)
                apply_theme(fig); st.plotly_chart(fig,use_container_width=True,key="eda_ts_line")
                if trend:
                    c1,c2,c3=st.columns(3)
                    with c1: st.markdown(f'<div class="clean-stat">Direction : <span>{"↑ Hausse" if trend["direction"]=="up" else "↓ Baisse"}</span></div>',unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="clean-stat">Variation totale : <span>{trend["pct_change"]:+.1f}%</span></div>',unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="clean-stat">Significativité : <span>{"✅ Oui" if trend["significant"] else "❌ Non"} (p={trend["p"]:.3f})</span></div>',unsafe_allow_html=True)
            except Exception as e: st.error(f"Erreur série temporelle : {e}")
        else: st.info("Aucune colonne date détectée.")

    with eda_tabs[6]:
        st.markdown("**Statistiques avancées par variable numérique :**")
        if adv_stats:
            rows_data=[]
            for col,s in adv_stats.items():
                rows_data.append({"Variable":col,"Moyenne":s.get("mean"),"Médiane":s.get("median"),"Std":s.get("std"),"CV (%)":s.get("cv"),"P10":s.get("p10"),"P50":s.get("p50"),"P90":s.get("p90"),"Distribution Normale":("✅" if s.get("is_normal") else "❌") if s.get("is_normal") is not None else "?","% > Moyenne":s.get("pct_above_mean")})
            st.dataframe(pd.DataFrame(rows_data),use_container_width=True,height=400)
            if len(profile["num_cols"])>=2:
                st.markdown("**Bandes Percentiles P10 / P50 / P90 :**")
                cols_sel=profile["num_cols"][:6]
                p10=df[cols_sel].quantile(0.10); p50=df[cols_sel].quantile(0.50); p90=df[cols_sel].quantile(0.90)
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=cols_sel,y=p90.values,name="P90",line=dict(color="#EF4444",width=2,dash="dot"),mode="lines+markers"))
                fig.add_trace(go.Scatter(x=cols_sel,y=p50.values,name="P50",line=dict(color="#10B981",width=3),mode="lines+markers"))
                fig.add_trace(go.Scatter(x=cols_sel,y=p10.values,name="P10",line=dict(color="#3B82F6",width=2,dash="dot"),mode="lines+markers",fill="tonexty",fillcolor="rgba(16,185,129,0.06)"))
                fig.update_layout(title="Bandes Percentiles",**PLOTLY_LAYOUT)
                apply_theme(fig); st.plotly_chart(fig,use_container_width=True,key="eda_adv_percentile")
        else: st.info("Aucune statistique disponible.")

    with eda_tabs[7]:
        st.markdown("**Graphiques auto-sélectionnés selon la structure des données :**")
        chart_specs=decide_charts(df,profile)
        if chart_specs:
            for i in range(0,len(chart_specs),2):
                cc=st.columns(2)
                for j,spec in enumerate(chart_specs[i:i+2]):
                    with cc[j]:
                        st.markdown(f'<span class="chart-label">{spec.get("label","")}</span>',unsafe_allow_html=True)
                        render_chart(df,spec,profile,key_prefix=f"eda_auto_{i}_{j}")
        else: st.info("Aucun graphique disponible.")

    with eda_tabs[8]:
        st.markdown('<div class="nlq-box"><strong>💬 Question → Graphique</strong><br><span style="color:#6B7280;font-size:0.88rem">Décrivez en français le graphique que vous souhaitez. Ex: "Montre moi les ventes par région en barres" ou "Compare le revenu et le coût dans le temps"</span></div>', unsafe_allow_html=True)
        nl_question=st.text_input("Votre question ou demande de graphique :",key="nlq_input",placeholder="Ex: montre moi la distribution des ventes par catégorie...")
        if st.button("Générer le graphique",key="nlq_btn") and nl_question:
            with st.spinner("Analyse de votre demande..."):
                spec=nl_to_chart(nl_question,df,profile)
                if "error" in spec:
                    st.error(f"Erreur : {spec['error']}")
                else:
                    st.markdown(f"**Graphique généré :** {spec.get('title','')} · *{spec.get('explanation','')}*")
                    render_nl_chart(spec,df)

        if "nlq_history" not in st.session_state: st.session_state.nlq_history=[]
        if nl_question and st.session_state.get("nlq_last") != nl_question:
            st.session_state.nlq_last=nl_question


# ══════════════════════════════════════════════════════════════════════
#  🧹  CLEANING TAB
# ══════════════════════════════════════════════════════════════════════
def render_cleaning_tab(df):
    st.markdown("### Module de Nettoyage des Données")
    if "clean_df" not in st.session_state: st.session_state.clean_df=df.copy()
    w=st.session_state.clean_df; rows,cols=w.shape; miss=w.isnull().sum().sum()
    c=st.columns(4)
    with c[0]: st.markdown(f'<div class="kpi-card"><div class="kpi-value">{rows:,}</div><div class="kpi-label">Lignes</div></div>',unsafe_allow_html=True)
    with c[1]: st.markdown(f'<div class="kpi-card"><div class="kpi-value">{cols}</div><div class="kpi-label">Colonnes</div></div>',unsafe_allow_html=True)
    with c[2]: st.markdown(f'<div class="kpi-card"><div class="kpi-value">{miss:,}</div><div class="kpi-label">Valeurs manquantes</div></div>',unsafe_allow_html=True)
    with c[3]: st.markdown(f'<div class="kpi-card"><div class="kpi-value">{w.duplicated().sum()}</div><div class="kpi-label">Doublons</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    ct=st.tabs(["Valeurs Manquantes","Doublons","Renommer","Types","Supprimer Colonnes"])
    with ct[0]:
        mcols=[c for c in w.columns if w[c].isnull().sum()>0]
        if mcols:
            for col in mcols:
                n=w[col].isnull().sum()
                st.markdown(f'<div class="clean-stat">{col} — <span>{n} valeurs ({n/len(w)*100:.1f}%)</span></div>',unsafe_allow_html=True)
            sel=st.selectbox("Colonne",mcols,key="cm_sel")
            strat=st.radio("Stratégie",["Moyenne","Médiane","Mode","Valeur fixe","Supprimer lignes"],key="cm_strat",horizontal=True)
            fval=st.text_input("Valeur",key="cm_fval") if strat=="Valeur fixe" else ""
            if st.button("Appliquer",key="btn_miss"):
                cd=w[sel]
                if strat=="Moyenne" and pd.api.types.is_numeric_dtype(cd): w[sel]=cd.fillna(cd.mean())
                elif strat=="Médiane" and pd.api.types.is_numeric_dtype(cd): w[sel]=cd.fillna(cd.median())
                elif strat=="Mode": w[sel]=cd.fillna(cd.mode()[0])
                elif strat=="Valeur fixe" and fval:
                    try: w[sel]=cd.fillna(float(fval) if pd.api.types.is_numeric_dtype(cd) else fval)
                    except: w[sel]=cd.fillna(fval)
                elif strat=="Supprimer lignes": w=w.dropna(subset=[sel])
                st.session_state.clean_df=w; st.success(f"Appliqué sur '{sel}'"); st.rerun()
        else: st.success("Aucune valeur manquante !")
    with ct[1]:
        nd=w.duplicated().sum()
        if nd>0:
            st.warning(f"{nd} doublons ({nd/len(w)*100:.1f}%)")
            if st.button("Supprimer doublons",key="btn_dup"):
                before=len(w); w=w.drop_duplicates(); st.session_state.clean_df=w
                st.success(f"{before-len(w)} doublons supprimés"); st.rerun()
        else: st.success("Aucun doublon !")
    with ct[2]:
        old=st.selectbox("Colonne",w.columns.tolist(),key="cr_sel")
        new=st.text_input("Nouveau nom",value=old,key="cr_val")
        if st.button("Renommer",key="btn_ren") and new!=old:
            w=w.rename(columns={old:new}); st.session_state.clean_df=w; st.success(f"'{old}' renommé en '{new}'"); st.rerun()
    with ct[3]:
        sel=st.selectbox("Colonne",w.columns.tolist(),key="ctype_sel")
        st.markdown(f'<div class="clean-stat">Type actuel : <span>{str(w[sel].dtype)}</span></div>',unsafe_allow_html=True)
        nt=st.selectbox("Nouveau type",["int64","float64","str","datetime64","bool"],key="ctype_new")
        if st.button("Convertir",key="btn_conv"):
            try:
                if nt=="datetime64": w[sel]=pd.to_datetime(w[sel],errors="coerce")
                elif nt=="str": w[sel]=w[sel].astype(str)
                else: w[sel]=w[sel].astype(nt,errors="ignore")
                st.session_state.clean_df=w; st.success(f"'{sel}' converti en {nt}"); st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")
    with ct[4]:
        drop=st.multiselect("Colonnes à supprimer",w.columns.tolist(),key="cdrop")
        if drop and st.button(f"Supprimer {len(drop)} colonne(s)",key="btn_drop"):
            w=w.drop(columns=drop); st.session_state.clean_df=w; st.success(f"{len(drop)} colonne(s) supprimée(s)"); st.rerun()
    st.markdown("---")
    bc1,bc2,_=st.columns([1,1,3])
    with bc1:
        if st.button("Réinitialiser",key="btn_rst"): st.session_state.clean_df=df.copy(); st.rerun()
    with bc2:
        st.download_button("Télécharger CSV nettoyé",data=w.to_csv(index=False).encode("utf-8"),file_name=f"cleaned_{datetime.now().strftime('%H%M%S')}.csv",mime="text/csv",key="btn_dlcsv")
    st.markdown("**Aperçu :**")
    st.dataframe(w.head(50),use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  🚀  APP SHELL
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<h2 style="color:#065F46;">DataCommerce</h2>', unsafe_allow_html=True)
    uploaded_file=st.file_uploader("Charger un fichier CSV ou Excel",type=["csv","xlsx"])
    if st.button("Réinitialiser",use_container_width=True):
        st.session_state.clear(); st.rerun()

for k,v in [("chat_history",[]),("auto_report",None),("last_file",None),("clean_df",None),("profile",None)]:
    if k not in st.session_state: st.session_state[k]=v

MASTER_PROMPT = """Tu es un analyste de données senior dans un cabinet de conseil de premier rang (tier-1).
Produis un rapport d'analyse stratégique structuré, professionnel et actionnable.

Organise ta réponse EXACTEMENT selon ces sections :

## Résumé Exécutif
Synthèse en 3-4 phrases : nature des données, qualité globale, principal enjeu business identifié.

## KPI et Statistiques Clés
5-7 indicateurs quantitatifs avec chiffres réels issus des données (moyennes, médianes, distributions, corrélations, tendances).

## Alertes et Anomalies
Problèmes de qualité, outliers, incohérences, risques. Classe chaque point : critique / attention / information.

## Insights et Observations Clés
5-6 découvertes non-triviales : patterns, tendances, relations entre variables, segments ou comportements inattendus.

## Recommandations Stratégiques
5 recommandations concrètes commençant par un verbe d'action fort. Chacune doit avoir un impact business clair et mesurable.

Langage : professionnel, précis, orienté décision. Parle comme si tu présentais à un comité de direction.
"""

# -- Query Params handling --
q_params = st.query_params
username = q_params.get("username", "Utilisateur")
project_name = q_params.get("project_name", "Nouveau Projet")

# Header with project context
st.markdown(f'''
<div class="app-header">
    <div class="logo-text">DataCommerce</div>
    <div class="flex items-center gap-4">
        <div class="user-greeting">Bienvenue, <strong>{username}</strong> · <span style="color:#059669">Projet : {project_name}</span></div>
        <a href="http://localhost:5001/logout" target="_self" style="text-decoration:none; color:#EF4444; font-size:0.8rem; font-weight:700; border:1px solid #FECACA; padding:2px 8px; border-radius:50px;">Déconnexion</a>
    </div>
</div>
''', unsafe_allow_html=True)

if uploaded_file:
    if st.session_state.last_file != uploaded_file.name:
        st.session_state.auto_report=None; st.session_state.chat_history=[]
        st.session_state.last_file=uploaded_file.name; st.session_state.clean_df=None; st.session_state.profile=None

    raw_df=pd.read_csv(uploaded_file) if uploaded_file.name.endswith("csv") else pd.read_excel(uploaded_file)
    if st.session_state.clean_df is None: st.session_state.clean_df=raw_df.copy()
    df=st.session_state.clean_df

    # Run profile once and cache in session state
    if st.session_state.profile is None:
        with st.spinner("Analyse de la structure des données..."):
            st.session_state.profile=analyze_dataframe(df)
    profile=st.session_state.profile

    context=build_dataset_context(df,uploaded_file.name,profile)

    if st.session_state.auto_report is None:
        with st.spinner("Génération du rapport IA..."):
            try: st.session_state.auto_report=get_ai_response([{"role":"user","content":MASTER_PROMPT}],context)
            except Exception as e: st.error(f"Erreur IA : {e}")

    tab0,tab1,tab2,tab3,tab4,tab5=st.tabs(["Rapport IA","EDA Avancé","Nettoyage","Aperçu","Chat Expert","Archives"])

    with tab0:
        if st.session_state.auto_report:
            parse_and_render_report(st.session_state.auto_report,df,uploaded_file.name,profile)
            st.markdown("<br>",unsafe_allow_html=True)
            b1,b2,_=st.columns([1,1,3])
            with b1:
                if st.button("Archiver le rapport"):
                    if not os.path.exists("reports"): os.makedirs("reports")
                    with open(f"reports/IA_Report_{datetime.now().strftime('%H%M%S')}.txt","w",encoding="utf-8") as f:
                        f.write(st.session_state.auto_report)
                    st.success("Rapport archivé.")
            with b2:
                if REPORTLAB_AVAILABLE:
                    pdf_bytes=generate_pdf_report(st.session_state.auto_report,df,uploaded_file.name)
                    st.download_button("Télécharger PDF",data=pdf_bytes,file_name=f"DataCommerce_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",mime="application/pdf",key="btn_pdf")
                else: st.caption("Installez `reportlab` pour PDF.")
            with st.expander("Voir le texte brut IA"): st.text(st.session_state.auto_report)
        else: st.warning("Erreur lors de la génération. Vérifiez votre clé API.")

    with tab1: render_eda_tab(df,profile)
    with tab2: render_cleaning_tab(raw_df)
    with tab3:
        st.markdown("**Dataset actuel :**")
        st.dataframe(df.head(100),use_container_width=True)
    with tab4:
        st.markdown('<div class="glass-card">',unsafe_allow_html=True)
        for msg in st.session_state.chat_history: render_chat_message(msg["role"],msg["content"])
        with st.form("chat"):
            u_in=st.text_input("Posez votre question au Data Expert IA...")
            if st.form_submit_button("Envoyer") and u_in:
                enriched=context+(f"\n\nRapport précédent:\n{st.session_state.auto_report[:1000]}" if st.session_state.auto_report else "")
                st.session_state.chat_history.append({"role":"user","content":u_in})
                reply=get_ai_response(st.session_state.chat_history,enriched)
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    with tab5:
        st.markdown('<div class="glass-card">',unsafe_allow_html=True)
        if os.path.exists("reports"):
            files=sorted(os.listdir("reports"),reverse=True)
            if files:
                for f in files:
                    c1,c2=st.columns([3,1]); c1.write(f)
                    with open(os.path.join("reports",f),"r",encoding="utf-8") as fh:
                        c2.download_button("Télécharger",data=fh.read(),file_name=f,key=f"dl_{f}")
            else: st.info("Aucun rapport archivé.")
        else: st.info("Aucun rapport archivé.")
        st.markdown('</div>',unsafe_allow_html=True)

else:
    st.markdown('<h1 class="hero-title">Rapport IA Automatique</h1>',unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Chargez un fichier CSV ou Excel pour une analyse professionnelle instantanée.</p>',unsafe_allow_html=True)
    c=st.columns(4)
    for col,title,desc in [(c[0],"Rapport IA","Analyse stratégique automatique"),(c[1],"EDA Avancé","9 onglets d'analyse"),(c[2],"Nettoyage","Transformez vos données"),(c[3],"Export PDF","Rapport téléchargeable")]:
        with col: st.markdown(f'<div class="kpi-card"><div class="kpi-label" style="margin-top:8px;font-size:0.9rem;color:#065F46;font-weight:700">{title}</div><div style="font-size:0.78rem;color:#9CA3AF;margin-top:4px">{desc}</div></div>',unsafe_allow_html=True)