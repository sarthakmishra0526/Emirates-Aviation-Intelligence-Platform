"""
Emirates Aviation Intelligence Platform — v3 FIXED
Fixes:
  1. KPI cards use st.columns() instead of HTML — eliminates raw HTML rendering
  2. LAYOUT dict has NO xaxis/yaxis keys — passed separately to avoid duplicate kwarg error
  3. apply_layout() uses fig.update_layout() cleanly
"""

try:
    import streamlit as st
except Exception as e:
    raise ImportError(
        "streamlit is required to run this app. Install it with: pip install streamlit\n"
        f"Original error: {e}"
    )
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io, os, warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Emirates Aviation Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MONTH_MAP  = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
DOW_MAP    = {1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat",7:"Sun"}
SEASON_MAP = {1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
              6:"Summer",7:"Summer",8:"Summer",9:"Fall",10:"Fall",11:"Fall",12:"Winter"}
CANCEL_MAP = {"A":"Carrier","B":"Weather","C":"NAS","D":"Security"}

RED   = "#C8102E"
GOLD  = "#D4AF37"
MUTED = "#8A9BB0"

PALETTE = ["#C8102E","#D4AF37","#2563EB","#16A34A",
           "#EA580C","#7C3AED","#0D9488","#DB2777",
           "#F59E0B","#06B6D4","#84CC16","#EC4899"]

# ── LAYOUT base — NO xaxis/yaxis keys (causes duplicate kwarg error) ──
BASE = dict(
    plot_bgcolor ="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#E5E7EB", size=12),
    title_font=dict(size=15, color="#fff"),
    legend=dict(bgcolor="rgba(0,0,0,0.5)",bordercolor="rgba(200,16,46,0.3)",borderwidth=1,
                font=dict(size=11,color="#D1D5DB")),
    hoverlabel=dict(bgcolor="#1F2937",bordercolor=RED,font=dict(color="#fff",size=12)),
)

# Standard axis dicts — reuse when needed
AX = dict(gridcolor="rgba(255,255,255,0.05)",zeroline=False,color=MUTED,tickfont=dict(size=11))

def ul(fig, h=400, title="", **extra):
    """Apply base layout + height + title + any extras. Never pass xaxis/yaxis/margin in extra."""
    kw = {**BASE, "height": h, "margin": dict(l=10,r=10,t=40,b=10),
           "xaxis": AX, "yaxis": AX}
    kw.update(extra)  # extra can override xaxis/yaxis safely
    fig.update_layout(**kw)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=15, color="#fff")))
    return fig

CFG = {"displayModeBar": False}

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#0B0F19!important;color:#E5E7EB!important;}
.main .block-container{padding:0 2rem 3rem!important;max-width:1500px;background:#0B0F19!important;}
header[data-testid="stHeader"]{background:#08090F!important;border-bottom:1px solid rgba(200,16,46,0.2);}

[data-testid="stSidebar"]{background:linear-gradient(180deg,#08090F,#0D1020)!important;border-right:1px solid rgba(200,16,46,0.2)!important;}

/* KPI card via st.metric override */
[data-testid="metric-container"]{
  background:rgba(255,255,255,0.045)!important;
  border:1px solid rgba(200,16,46,0.30)!important;
  border-radius:14px!important;
  padding:1.1rem 1rem!important;
  position:relative!important;
  overflow:hidden!important;
}
[data-testid="metric-container"]::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#C8102E,#D4AF37);
}
[data-testid="stMetricLabel"] p{color:#6B7280!important;font-size:.67rem!important;text-transform:uppercase;letter-spacing:.12em;}
[data-testid="stMetricValue"]{color:#fff!important;font-family:'Playfair Display',serif!important;font-size:1.6rem!important;}
[data-testid="stMetricDelta"]{font-size:.72rem!important;}
[data-testid="stMetricDelta"] svg{display:none!important;}

.pg-title{background:linear-gradient(135deg,rgba(200,16,46,.1),rgba(212,175,55,.05));border-left:4px solid #C8102E;border-radius:0 12px 12px 0;padding:1rem 1.5rem;margin-bottom:1.8rem;}
.pg-title h2{margin:0;font-family:'Playfair Display',serif;font-size:1.7rem;color:#fff;}
.pg-title p{margin:4px 0 0;color:#6B7280;font-size:.82rem;}

.sec-hdr{display:flex;align-items:center;gap:10px;margin:1.4rem 0 1rem;padding-bottom:.65rem;border-bottom:1px solid rgba(200,16,46,0.2);}
.sec-title{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:#fff;}
.sec-badge{background:#C8102E;color:#fff;font-size:.6rem;padding:3px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:.1em;font-weight:600;}

.ins-card{background:linear-gradient(135deg,rgba(200,16,46,.07),rgba(212,175,55,.05));border:1px solid rgba(212,175,55,.28);border-radius:12px;padding:1rem 1.2rem 1rem 2.4rem;margin-bottom:.9rem;position:relative;}
.ins-num{position:absolute;top:-9px;left:14px;background:#C8102E;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;}
.ins-title{font-weight:600;color:#D4AF37;font-size:.88rem;margin-bottom:.3rem;}
.ins-body{font-size:.8rem;color:#9CA3AF;line-height:1.65;}

.divider{height:1px;background:linear-gradient(90deg,transparent,#C8102E,#D4AF37,transparent);margin:1.4rem 0;opacity:.35;}

.rec-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:0 12px 12px 0;padding:1.1rem 1.3rem;margin-bottom:.9rem;}

[data-baseweb="tab"]{color:#6B7280!important;font-size:.82rem!important;padding:8px 18px!important;}
[aria-selected="true"]{color:#fff!important;border-bottom:2px solid #C8102E!important;}
[data-baseweb="select"]>div{background:rgba(255,255,255,.05)!important;border:1px solid rgba(200,16,46,.25)!important;color:#E5E7EB!important;border-radius:8px!important;}
[data-testid="stExpander"]{border:1px solid rgba(200,16,46,.2)!important;border-radius:10px!important;background:rgba(255,255,255,.02)!important;}
[data-testid="stDownloadButton"]>button{background:linear-gradient(135deg,#C8102E,#9B0C23)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-weight:600!important;}
::-webkit-scrollbar{width:5px;height:5px;} ::-webkit-scrollbar-track{background:#0B0F19;} ::-webkit-scrollbar-thumb{background:#C8102E;border-radius:3px;}
footer,#MainMenu,[data-testid="stDecoration"]{display:none!important;}
</style>
""", unsafe_allow_html=True)

# ── Helper UI ──────────────────────────────────────────────────────
def pg(icon, title, sub=""):
    s = f"<p>{sub}</p>" if sub else ""
    st.markdown(f'<div class="pg-title"><h2>{icon} {title}</h2>{s}</div>', unsafe_allow_html=True)

def sec(title, badge=""):
    b = f'<span class="sec-badge">{badge}</span>' if badge else ""
    st.markdown(f'<div class="sec-hdr"><span class="sec-title">{title}</span>{b}</div>', unsafe_allow_html=True)

def div():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

def ins(n, title, body):
    st.markdown(f'<div class="ins-card"><div class="ins-num">{n}</div><div class="ins-title">{title}</div><div class="ins-body">{body}</div></div>', unsafe_allow_html=True)

def kpi(cols_list, items):
    """Render KPI metrics using st.metric — no HTML, no rendering bugs."""
    for col, it in zip(cols_list, items):
        with col:
            delta = it.get("sub", None)
            st.metric(label=f"{it['ico']}  {it['lbl']}", value=it["val"], delta=delta)

# ── Data Loading ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    fl = pd.read_csv(os.path.join(DATA_DIR, "flights.csv"), low_memory=False)
    al = pd.read_csv(os.path.join(DATA_DIR, "airlines.csv"))
    ap = pd.read_csv(os.path.join(DATA_DIR, "airports.csv"))

    for c in ["DEPARTURE_DELAY","ARRIVAL_DELAY","AIR_SYSTEM_DELAY","SECURITY_DELAY",
               "AIRLINE_DELAY","LATE_AIRCRAFT_DELAY","WEATHER_DELAY","DISTANCE"]:
        if c in fl.columns:
            fl[c] = pd.to_numeric(fl[c], errors="coerce").fillna(0)

    fl["CANCELLED"]  = fl["CANCELLED"].fillna(0).astype(int)
    fl["DIVERTED"]   = fl["DIVERTED"].fillna(0).astype(int)
    fl["CANCELLATION_REASON"] = fl["CANCELLATION_REASON"].fillna("N/A")

    fl["MONTH_NAME"] = fl["MONTH"].map(MONTH_MAP)
    fl["DAY_NAME"]   = fl["DAY_OF_WEEK"].map(DOW_MAP)
    fl["SEASON"]     = fl["MONTH"].map(SEASON_MAP)
    fl["QUARTER"]    = fl["MONTH"].apply(lambda m: f"Q{(m-1)//3+1}")
    fl["ROUTE"]      = fl["ORIGIN_AIRPORT"] + " → " + fl["DESTINATION_AIRPORT"]
    fl["CANCEL_DESC"]= fl["CANCELLATION_REASON"].map(CANCEL_MAP).fillna("Not Cancelled")
    fl["OTP_FLAG"]   = ((fl["ARRIVAL_DELAY"] <= 15) & (fl["CANCELLED"] == 0)).astype(int)
    fl["DELAY_CAT"]  = fl["ARRIVAL_DELAY"].apply(
        lambda d: "On Time" if d<=0 else "Minor 1-15m" if d<=15 else
                  "Moderate 16-60m" if d<=60 else "Severe 61-120m" if d<=120 else "Critical >120m")

    def dep_h(x):
        try: return int(str(int(x)).zfill(4)[:2])
        except: return -1
    fl["DEP_HOUR"] = fl["SCHEDULED_DEPARTURE"].apply(dep_h)

    al2 = al.rename(columns={"IATA_CODE":"AIRLINE","AIRLINE":"AIRLINE_NAME"})
    fl = fl.merge(al2, on="AIRLINE", how="left")
    fl["AIRLINE_NAME"] = fl["AIRLINE_NAME"].fillna(fl["AIRLINE"])
    return fl, al, ap

with st.spinner("🛫 Loading Emirates Aviation Intelligence Platform…"):
    df, airlines_raw, airports_raw = load_data()

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.4rem 1rem 1rem;text-align:center;border-bottom:1px solid rgba(200,16,46,0.2);margin-bottom:1rem;">
      <div style="font-size:2.5rem;margin-bottom:6px;">✈️</div>
      <div style="font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:900;color:#fff;">Emirates Aviation</div>
      <div style="font-family:'Playfair Display',serif;font-size:.82rem;color:#D4AF37;margin-bottom:4px;">Intelligence Platform</div>
      <div style="font-size:.6rem;color:#4B5563;text-transform:uppercase;letter-spacing:.18em;">U.S. Analytics · 2015</div>
    </div>
    <div style="font-size:.63rem;color:#4B5563;text-transform:uppercase;letter-spacing:.14em;padding:0 1rem .5rem;">Navigation</div>
    """, unsafe_allow_html=True)

    PAGE = st.radio("nav", [
        "✈️  Executive Overview",
        "🏢  Airline Performance",
        "🛬  Airport Performance",
        "⏱️  Delay Analytics",
        "❌  Cancellation Analytics",
        "🗺️  Route Intelligence",
        "📅  Time Trend Analysis",
        "🌎  Geographic Intelligence",
        "🤖  AI Insights",
        "📥  Download Center",
    ], label_visibility="collapsed")

    st.markdown("""
    <div style="margin-top:1.5rem;padding:1rem;border-top:1px solid rgba(255,255,255,.06);
    font-size:.63rem;color:#374151;text-align:center;line-height:2;">
      5,819,079 Flights · 14 Airlines<br>322 Airports · Year 2015<br>
      <span style="color:#C8102E;font-weight:600;">Emirates Aviation Intelligence</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════
if "Executive" in PAGE:
    pg("✈️","Executive Overview","Real-time U.S. domestic aviation performance intelligence — 2015")

    total   = len(df)
    cancel  = int(df["CANCELLED"].sum())
    divert  = int(df["DIVERTED"].sum())
    on_time = int(df["OTP_FLAG"].sum())
    delayed = int(((df["CANCELLED"]==0) & (df["ARRIVAL_DELAY"]>15)).sum())
    otp_r   = round(on_time/total*100, 2)
    can_r   = round(cancel/total*100, 2)
    div_r   = round(divert/total*100, 2)
    avg_arr = round(df.loc[df["CANCELLED"]==0,"ARRIVAL_DELAY"].mean(), 1)
    avg_dep = round(df.loc[df["CANCELLED"]==0,"DEPARTURE_DELAY"].mean(), 1)

    # KPI row using st.metric
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("✈️  Total Flights", f"{total:,}", "2015 Full Year")
    with c2: st.metric("🏢  Airlines", str(df["AIRLINE"].nunique()))
    with c3: st.metric("🛬  Airports", str(df["ORIGIN_AIRPORT"].nunique()))
    with c4: st.metric("🎯  On-Time Performance", f"{otp_r}%", "OTP Rate")

    c5,c6,c7,c8 = st.columns(4)
    with c5: st.metric("⏱️  Avg Arrival Delay", f"{avg_arr} min")
    with c6: st.metric("🛫  Avg Departure Delay", f"{avg_dep} min")
    with c7: st.metric("❌  Cancellation Rate", f"{can_r}%", f"-{cancel:,} flights")
    with c8: st.metric("🔄  Diversion Rate", f"{div_r}%")

    div()

    # Row: Gauge + Status Donut + Monthly Trend
    g1,g2,g3 = st.columns([1,1,2])

    with g1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=otp_r,
            number=dict(suffix="%", font=dict(color="#fff", size=36, family="Playfair Display")),
            title=dict(text="On-Time Performance", font=dict(color="#9CA3AF", size=13)),
            gauge=dict(
                axis=dict(range=[0,100], tickfont=dict(color=MUTED)),
                bar=dict(color="#16A34A"),
                bgcolor="rgba(0,0,0,0)", borderwidth=1, bordercolor="#374151",
                steps=[dict(range=[0,60], color="rgba(200,16,46,.1)"),
                       dict(range=[60,80], color="rgba(234,88,12,.1)"),
                       dict(range=[80,100], color="rgba(22,163,74,.1)")],
                threshold=dict(line=dict(color=GOLD, width=3), thickness=.75, value=otp_r)
            )
        ))
        fig.update_layout(**BASE, height=260)
        fig.update_layout(margin=dict(l=10,r=10,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with g2:
        labels = ["On Time","Delayed","Cancelled","Diverted"]
        vals   = [on_time, delayed, cancel, divert]
        fig2 = go.Figure(go.Pie(
            labels=labels, values=vals, hole=.55,
            marker=dict(colors=[PALETTE[3],PALETTE[0],PALETTE[4],PALETTE[1]],
                        line=dict(color="#0B0F19", width=2)),
            textinfo="percent", textfont=dict(size=11, color="#fff"),
        ))
        fig2.update_layout(**BASE, height=260, title=dict(text="Flight Status", font=dict(size=13,color="#fff")))
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    with g3:
        mth = df.groupby("MONTH").agg(
            Flights=("OTP_FLAG","count"), OTP=("OTP_FLAG","mean"),
            AvgDelay=("ARRIVAL_DELAY","mean")).reset_index()
        mth["Month"] = mth["MONTH"].map(MONTH_MAP)
        mth["OTP_Pct"] = mth["OTP"] * 100
        fig3 = go.Figure()
        fig3.add_bar(x=mth["Month"], y=mth["Flights"], name="Flights",
                     marker_color=PALETTE[2], marker_line_width=0, yaxis="y1")
        fig3.add_scatter(x=mth["Month"], y=mth["OTP_Pct"], name="OTP %", yaxis="y2",
                         line=dict(color=PALETTE[1], width=2.5), mode="lines+markers", marker=dict(size=6))
        fig3.add_scatter(x=mth["Month"], y=mth["AvgDelay"], name="Avg Delay (min)", yaxis="y3",
                         line=dict(color=PALETTE[0], width=2, dash="dash"), mode="lines")
        fig3.update_layout(**BASE, height=260,
                           title=dict(text="Monthly Volume · OTP · Delay", font=dict(size=14,color="#fff")),
                           xaxis=AX, yaxis=AX,
                           yaxis2=dict(overlaying="y", side="right", color=PALETTE[1],
                                       gridcolor="rgba(0,0,0,0)", ticksuffix="%", range=[60,100]),
                           yaxis3=dict(overlaying="y", side="right", position=.97,
                                       color=PALETTE[0], gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True, config=CFG)

    div()

    c4a, c4b = st.columns(2)
    with c4a:
        sec("Airline OTP Leaderboard","RANKING")
        al_otp = df.groupby("AIRLINE_NAME").agg(T=("OTP_FLAG","count"), OTP=("OTP_FLAG","sum")).reset_index()
        al_otp["OTP%"] = (al_otp["OTP"]/al_otp["T"]*100).round(1)
        al_otp = al_otp.sort_values("OTP%", ascending=True)
        fig4 = go.Figure(go.Bar(
            x=al_otp["OTP%"], y=al_otp["AIRLINE_NAME"], orientation="h",
            marker=dict(color=[PALETTE[1] if v>=80 else PALETTE[0] for v in al_otp["OTP%"]],
                        line=dict(width=0)),
            text=[f"{v:.1f}%" for v in al_otp["OTP%"]],
            textposition="outside", textfont=dict(color="#D1D5DB", size=11),
        ))
        fig4.add_vline(x=80, line_dash="dash", line_color=PALETTE[0],
                       annotation_text="80% Target", annotation_font_color=PALETTE[0])
        fig4.update_layout(**BASE, height=380, xaxis=dict(**AX, range=[0,105], ticksuffix="%"), yaxis=AX)
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    with c4b:
        sec("Delay Category Distribution","ANALYSIS")
        cat_order = ["On Time","Minor 1-15m","Moderate 16-60m","Severe 61-120m","Critical >120m"]
        cat_c = df[df["CANCELLED"]==0]["DELAY_CAT"].value_counts().reindex(cat_order, fill_value=0)
        fig5 = go.Figure(go.Bar(
            x=cat_c.index, y=cat_c.values,
            marker=dict(color=[PALETTE[3],PALETTE[1],PALETTE[4],PALETTE[0],PALETTE[0]],
                        line=dict(width=0)),
            text=[f"{v:,}" for v in cat_c.values],
            textposition="outside", textfont=dict(color="#D1D5DB", size=11),
        ))
        fig5.update_layout(**BASE, height=380, xaxis=dict(**AX, tickangle=-15), yaxis=AX)
        st.plotly_chart(fig5, use_container_width=True, config=CFG)

    div()
    sec("Executive Summary","AI GENERATED")
    best_al  = al_otp.iloc[-1]["AIRLINE_NAME"]
    worst_al = al_otp.iloc[0]["AIRLINE_NAME"]
    pk_mth   = mth.loc[mth["AvgDelay"].idxmax(),"Month"]
    e1, e2 = st.columns(2)
    with e1:
        ins(1,"Network OTP", f"U.S. aviation achieved <b>{otp_r}%</b> OTP across {total:,} flights. <b>{best_al}</b> leads with the highest on-time rate.")
        ins(2,"Delay Landscape", f"{delayed/total*100:.1f}% of flights experienced >15 min arrival delays. Avg delay: <b>{avg_arr} min</b>. Peak month: <b>{pk_mth}</b>.")
        ins(3,"Cancellation Impact", f"{cancel:,} cancellations ({can_r}%) network-wide. Weather and carrier disruptions dominate. Buffering can cut this by 20–30%.")
    with e2:
        ins(4,"Performance Gap", f"Significant OTP gap separates top performers from <b>{worst_al}</b>. Targeted carrier intervention programmes are recommended.")
        ins(5,"Seasonal Risk", f"Summer (Jun–Aug) and winter holidays drive peak delay periods. Proactive capacity planning is critical for these windows.")
        ins(6,"Strategic Priority", f"Late aircraft cascade is the #1 delay driver. Buffer optimization and real-time recovery scheduling can yield <b>15–25% OTP improvement</b>.")

# ══════════════════════════════════════════════════════════════════
# PAGE 2 — AIRLINE PERFORMANCE
# ══════════════════════════════════════════════════════════════════
elif "Airline" in PAGE:
    pg("🏢","Airline Performance","Carrier benchmarking — reliability, delay, and operational efficiency")

    al = df.groupby("AIRLINE_NAME").agg(
        Flights=("OTP_FLAG","count"), OTP=("OTP_FLAG","sum"), Cancelled=("CANCELLED","sum"),
        AvgArr=("ARRIVAL_DELAY","mean"), AvgDep=("DEPARTURE_DELAY","mean"),
        AlDelay=("AIRLINE_DELAY","mean"), WxDelay=("WEATHER_DELAY","mean"),
        LaDelay=("LATE_AIRCRAFT_DELAY","mean"), NaDelay=("AIR_SYSTEM_DELAY","mean"),
        SeDelay=("SECURITY_DELAY","mean"),
    ).reset_index()
    al["OTP%"]      = (al["OTP"]/al["Flights"]*100).round(1)
    al["Cancel%"]   = (al["Cancelled"]/al["Flights"]*100).round(2)
    al["ReliScore"] = (al["OTP%"]*0.5 - al["AvgArr"].clip(0)*0.3 - al["Cancel%"]*2).round(1)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("🥇  Best OTP", al.loc[al["OTP%"].idxmax(),"AIRLINE_NAME"].split()[0], f"{al['OTP%'].max():.1f}% OTP")
    with c2: st.metric("⚠️  Lowest OTP", al.loc[al["OTP%"].idxmin(),"AIRLINE_NAME"].split()[0], f"{al['OTP%'].min():.1f}% OTP")
    with c3: st.metric("📊  Network Avg OTP", f"{al['OTP%'].mean():.1f}%")
    with c4: st.metric("⏱️  Network Avg Delay", f"{al['AvgArr'].mean():.1f} min")
    with c5: st.metric("✈️  Total Flights", f"{al['Flights'].sum():,}")

    div()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        sec("OTP Rate — All Carriers","RANKING")
        s = al.sort_values("OTP%", ascending=True)
        fig = go.Figure(go.Bar(
            x=s["OTP%"], y=s["AIRLINE_NAME"], orientation="h",
            marker=dict(color=[PALETTE[1] if v>=80 else PALETTE[0] for v in s["OTP%"]], line=dict(width=0)),
            text=[f"{v:.1f}%" for v in s["OTP%"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11),
        ))
        fig.add_vline(x=80, line_dash="dash", line_color=PALETTE[0])
        fig.update_layout(**BASE, height=440, xaxis=dict(**AX, range=[0,105], ticksuffix="%"), yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with r1c2:
        sec("Average Arrival Delay","DELAY")
        s2 = al.sort_values("AvgArr", ascending=False)
        fig2 = go.Figure(go.Bar(
            x=s2["AIRLINE_NAME"], y=s2["AvgArr"],
            marker=dict(color=PALETTE[0], line=dict(width=0)),
            text=[f"{v:.1f}" for v in s2["AvgArr"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11),
        ))
        fig2.update_layout(**BASE, height=440, xaxis=dict(**AX, tickangle=-25), yaxis=AX)
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()
    sec("Delay Type Heatmap — Carrier vs Delay Category","HEATMAP")
    dcols = {"AlDelay":"Airline","WxDelay":"Weather","LaDelay":"Late Aircraft",
             "NaDelay":"Air System","SeDelay":"Security"}
    hmap = al.set_index("AIRLINE_NAME")[[*dcols]].rename(columns=dcols).round(1)
    fig3 = go.Figure(go.Heatmap(
        z=hmap.values, x=list(hmap.columns), y=list(hmap.index),
        colorscale=[[0,"#0B0F19"],[0.5,"#7B0A16"],[1,"#C8102E"]],
        showscale=True,
        text=hmap.values.round(1), texttemplate="%{text}", textfont=dict(color="#fff",size=11),
        hovertemplate="<b>%{y}</b> — %{x}<br>Avg Min: <b>%{z:.1f}</b><extra></extra>",
    ))
    fig3.update_layout(**BASE, height=400, xaxis=AX, yaxis=AX)
    st.plotly_chart(fig3, use_container_width=True, config=CFG)

    div()
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        sec("Stacked Delay by Carrier","BREAKDOWN")
        fig4 = go.Figure()
        for raw,name,color in [("AlDelay","Airline",PALETTE[0]),("WxDelay","Weather",PALETTE[2]),
                                ("LaDelay","Late Aircraft",PALETTE[1]),("NaDelay","Air System",PALETTE[3]),
                                ("SeDelay","Security",PALETTE[4])]:
            fig4.add_bar(x=al["AIRLINE_NAME"], y=al[raw], name=name,
                         marker_color=color, marker_line_width=0)
        fig4.update_layout(**BASE, barmode="stack", height=400, xaxis=dict(**AX, tickangle=-25), yaxis=AX)
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    with r2c2:
        sec("OTP % vs Cancellation Rate — Bubble","SCATTER")
        fig5 = go.Figure(go.Scatter(
            x=al["Cancel%"], y=al["OTP%"], mode="markers+text",
            marker=dict(size=al["Flights"]/al["Flights"].max()*40+8,
                        color=PALETTE[2], opacity=.8, line=dict(width=1,color="#fff")),
            text=al["AIRLINE_NAME"].str.split().str[0],
            textposition="top center", textfont=dict(size=9,color="#D1D5DB"),
            hovertext=al["AIRLINE_NAME"], hoverinfo="text",
        ))
        fig5.update_layout(**BASE, height=400,
                           xaxis=dict(**AX, title="Cancellation Rate (%)"),
                           yaxis=dict(**AX, title="OTP Rate (%)"))
        st.plotly_chart(fig5, use_container_width=True, config=CFG)

    div()
    sec("Complete Airline Rankings Table","ALL CARRIERS")
    tbl = al[["AIRLINE_NAME","Flights","OTP%","AvgArr","AvgDep","Cancel%","ReliScore"]].copy()
    tbl = tbl.sort_values("OTP%", ascending=False).reset_index(drop=True)
    tbl.index += 1
    tbl.columns = ["Airline","Flights","OTP %","Avg Arr Delay","Avg Dep Delay","Cancel %","Reliability Score"]
    tbl["OTP %"]          = tbl["OTP %"].map("{:.1f}%".format)
    tbl["Avg Arr Delay"]  = tbl["Avg Arr Delay"].map("{:.1f} min".format)
    tbl["Avg Dep Delay"]  = tbl["Avg Dep Delay"].map("{:.1f} min".format)
    tbl["Cancel %"]       = tbl["Cancel %"].map("{:.2f}%".format)
    tbl["Reliability Score"] = tbl["Reliability Score"].map("{:.1f}".format)
    tbl["Flights"]        = tbl["Flights"].map("{:,}".format)
    st.dataframe(tbl, use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════
# PAGE 3 — AIRPORT PERFORMANCE
# ══════════════════════════════════════════════════════════════════
elif "Airport" in PAGE:
    pg("🛬","Airport Performance","Hub efficiency, delay hotspots, and operational benchmarking")

    ap = df.groupby("ORIGIN_AIRPORT").agg(
        Deps=("OTP_FLAG","count"), OTP=("OTP_FLAG","sum"),
        Cancelled=("CANCELLED","sum"), AvgDep=("DEPARTURE_DELAY","mean"),
    ).reset_index().rename(columns={"ORIGIN_AIRPORT":"IATA_CODE"})
    ap["OTP%"]    = (ap["OTP"]/ap["Deps"]*100).round(1)
    ap["Cancel%"] = (ap["Cancelled"]/ap["Deps"]*100).round(2)
    ap = ap.merge(airports_raw[["IATA_CODE","AIRPORT","CITY","STATE","LATITUDE","LONGITUDE"]],
                  on="IATA_CODE", how="left").dropna(subset=["AvgDep"])

    mn = st.slider("Minimum departures threshold", 100, 5000, 500, 100)
    ap = ap[ap["Deps"] >= mn]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("🛬  Airports", f"{len(ap):,}")
    with c2: st.metric("🏆  Best OTP", ap.loc[ap["OTP%"].idxmax(),"IATA_CODE"], f"{ap['OTP%'].max():.1f}% OTP")
    with c3: st.metric("⚠️  Highest Delay", ap.loc[ap["AvgDep"].idxmax(),"IATA_CODE"], f"{ap['AvgDep'].max():.1f} min")
    with c4: st.metric("📊  Avg Airport OTP", f"{ap['OTP%'].mean():.1f}%")
    with c5: st.metric("✈️  Total Departures", f"{ap['Deps'].sum():,}")

    div()

    rc1,rc2 = st.columns(2)
    with rc1:
        sec("Top 15 Lowest Delay Airports","BEST")
        t15 = ap.nsmallest(15,"AvgDep").sort_values("AvgDep")
        fig = go.Figure(go.Bar(x=t15["AvgDep"], y=t15["IATA_CODE"], orientation="h",
            marker=dict(color=PALETTE[1], line=dict(width=0)),
            text=[f"{v:.1f}" for v in t15["AvgDep"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig.update_layout(**BASE, height=460, xaxis=dict(**AX, title="Avg Dep Delay (min)"), yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with rc2:
        sec("Top 15 Highest Delay Airports","WORST")
        b15 = ap.nlargest(15,"AvgDep").sort_values("AvgDep", ascending=False)
        fig2 = go.Figure(go.Bar(x=b15["IATA_CODE"], y=b15["AvgDep"],
            marker=dict(color=PALETTE[0], line=dict(width=0)),
            text=[f"{v:.1f}" for v in b15["AvgDep"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig2.update_layout(**BASE, height=460, xaxis=dict(**AX, tickangle=-30),
                           yaxis=dict(**AX, title="Avg Dep Delay (min)"))
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()
    sec("Top 20 Busiest Airports — OTP Rate","OTP")
    busy = ap.nlargest(20,"Deps").sort_values("OTP%", ascending=True)
    busy["Label"] = busy["IATA_CODE"] + " · " + busy["CITY"].fillna("")
    fig3 = go.Figure(go.Bar(x=busy["OTP%"], y=busy["Label"], orientation="h",
        marker=dict(color=[PALETTE[1] if v>=75 else PALETTE[0] for v in busy["OTP%"]], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in busy["OTP%"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
    fig3.add_vline(x=75, line_dash="dash", line_color=PALETTE[0])
    fig3.update_layout(**BASE, height=520, xaxis=dict(**AX, range=[0,105], ticksuffix="%"), yaxis=AX)
    st.plotly_chart(fig3, use_container_width=True, config=CFG)

    div()
    rc3,rc4 = st.columns(2)
    with rc3:
        sec("Volume vs Delay Scatter","CORRELATION")
        scat = ap.nlargest(60,"Deps").copy()
        scat["sz"] = scat["Deps"]/scat["Deps"].max()*40+5
        fig4 = go.Figure(go.Scatter(x=scat["Deps"], y=scat["AvgDep"], mode="markers+text",
            marker=dict(size=scat["sz"], color=PALETTE[2], opacity=.75, line=dict(width=.5,color="#fff")),
            text=scat["IATA_CODE"], textposition="top center", textfont=dict(size=8,color="#D1D5DB"),
            hovertext=scat["CITY"], hoverinfo="text+x+y"))
        fig4.update_layout(**BASE, height=400,
                           xaxis=dict(**AX, title="Total Departures"),
                           yaxis=dict(**AX, title="Avg Dep Delay (min)"))
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    with rc4:
        sec("Top 20 States — Avg Departure Delay","STATE")
        st_df = ap.dropna(subset=["STATE"]).groupby("STATE")["AvgDep"].mean().reset_index()
        st_df = st_df.sort_values("AvgDep", ascending=False).head(20)
        fig5 = go.Figure(go.Bar(x=st_df["STATE"], y=st_df["AvgDep"],
            marker=dict(color=PALETTE[0], line=dict(width=0)),
            text=[f"{v:.1f}" for v in st_df["AvgDep"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig5.update_layout(**BASE, height=400, xaxis=dict(**AX, tickangle=-30),
                           yaxis=dict(**AX, title="Avg Dep Delay (min)"))
        st.plotly_chart(fig5, use_container_width=True, config=CFG)

    div()
    sec("Airport Scorecard — Full Rankings","SCORECARD")
    sc = ap[["IATA_CODE","AIRPORT","CITY","STATE","Deps","OTP%","AvgDep","Cancel%"]].sort_values("OTP%", ascending=False).reset_index(drop=True)
    sc.index += 1
    sc.columns = ["Code","Airport","City","State","Departures","OTP %","Avg Dep Delay","Cancel %"]
    sc["Departures"]    = sc["Departures"].map("{:,}".format)
    sc["OTP %"]         = sc["OTP %"].map("{:.1f}%".format)
    sc["Avg Dep Delay"] = sc["Avg Dep Delay"].map("{:.1f} min".format)
    sc["Cancel %"]      = sc["Cancel %"].map("{:.2f}%".format)
    st.dataframe(sc, use_container_width=True, height=450)

# ══════════════════════════════════════════════════════════════════
# PAGE 4 — DELAY ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif "Delay" in PAGE:
    pg("⏱️","Delay Analytics","Root cause breakdown, severity mapping, and carrier-level delay intelligence")

    ddf = df[df["CANCELLED"]==0].copy()
    f1,f2 = st.columns(2)
    with f1:
        al_sel = st.selectbox("Airline",["All"]+sorted(ddf["AIRLINE_NAME"].unique()))
    with f2:
        mo_sel = st.selectbox("Month",["All"]+list(range(1,13)),
                              format_func=lambda x: MONTH_MAP[x] if x!="All" else "All")
    if al_sel!="All": ddf = ddf[ddf["AIRLINE_NAME"]==al_sel]
    if mo_sel!="All": ddf = ddf[ddf["MONTH"]==mo_sel]

    dcols = {"AIRLINE_DELAY":"Airline","WEATHER_DELAY":"Weather",
             "LATE_AIRCRAFT_DELAY":"Late Aircraft","AIR_SYSTEM_DELAY":"Air System","SECURITY_DELAY":"Security"}
    tot_d = {v: ddf[k].sum() for k,v in dcols.items()}
    grand = sum(tot_d.values()) or 1
    top_cause = max(tot_d, key=tot_d.get)

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.metric("⏱️  Avg Arrival Delay", f"{ddf['ARRIVAL_DELAY'].mean():.1f} min")
    with k2: st.metric("📊  Flights Delayed >15m", f"{(ddf['ARRIVAL_DELAY']>15).mean()*100:.1f}%")
    with k3: st.metric("🔴  Top Delay Cause", top_cause, f"{tot_d[top_cause]/grand*100:.1f}%")
    with k4: st.metric("📈  Total Delay Minutes", f"{grand/1e6:.1f}M min")
    with k5: st.metric("✈️  Flights Analyzed", f"{len(ddf):,}")

    div()

    dc1,dc2 = st.columns(2)
    with dc1:
        sec("Delay Root Cause — % Share","DONUT")
        pct_d = {k: v/grand*100 for k,v in tot_d.items()}
        fig = go.Figure(go.Pie(
            labels=list(pct_d.keys()), values=list(pct_d.values()), hole=.52,
            marker=dict(colors=PALETTE[:5], line=dict(color="#0B0F19",width=2)),
            textinfo="percent+label", textfont=dict(size=11,color="#fff"),
        ))
        fig.update_layout(**BASE, height=380, xaxis=AX, yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with dc2:
        sec("Pareto — Delay Hours by Cause","PARETO")
        vals_p = sorted([(k, tot_d[k]/3600) for k in tot_d], key=lambda x:-x[1])
        lbs = [x[0] for x in vals_p]; vls = [x[1] for x in vals_p]
        cum = np.cumsum(vls)/sum(vls)*100
        fig2 = go.Figure()
        fig2.add_bar(x=lbs, y=vls, name="Delay Hours", marker_color=PALETTE[0], marker_line_width=0)
        fig2.add_scatter(x=lbs, y=cum, name="Cumulative %", yaxis="y2",
                         line=dict(color=PALETTE[1],width=2.5), mode="lines+markers", marker=dict(size=7))
        fig2.update_layout(**BASE, height=380, xaxis=AX, yaxis=dict(**AX, title="Delay Hours (K)"),
                           yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                                       color=PALETTE[1], gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()
    sec("Stacked Delay by Airline","BREAKDOWN")
    al_d = ddf.groupby("AIRLINE_NAME")[list(dcols.keys())].mean().reset_index()
    fig3 = go.Figure()
    for raw,name,color in [("AIRLINE_DELAY","Airline",PALETTE[0]),("WEATHER_DELAY","Weather",PALETTE[2]),
                            ("LATE_AIRCRAFT_DELAY","Late Aircraft",PALETTE[1]),
                            ("AIR_SYSTEM_DELAY","Air System",PALETTE[3]),("SECURITY_DELAY","Security",PALETTE[4])]:
        fig3.add_bar(x=al_d["AIRLINE_NAME"], y=al_d[raw], name=name, marker_color=color, marker_line_width=0)
    fig3.update_layout(**BASE, barmode="stack", height=400, xaxis=dict(**AX, tickangle=-25), yaxis=AX)
    st.plotly_chart(fig3, use_container_width=True, config=CFG)

    div()
    dd1,dd2 = st.columns(2)
    with dd1:
        sec("Monthly Delay Trend by Type","TREND")
        md = ddf.groupby("MONTH")[list(dcols.keys())].mean().reset_index()
        md["Month"] = md["MONTH"].map(MONTH_MAP)
        fig4 = go.Figure()
        for raw,name,color in [("AIRLINE_DELAY","Airline",PALETTE[0]),("WEATHER_DELAY","Weather",PALETTE[2]),
                                ("LATE_AIRCRAFT_DELAY","Late Aircraft",PALETTE[1]),("AIR_SYSTEM_DELAY","Air System",PALETTE[3])]:
            fig4.add_scatter(x=md["Month"], y=md[raw], name=name,
                             line=dict(color=color,width=2.5), mode="lines+markers", marker=dict(size=6))
        fig4.update_layout(**BASE, height=380, xaxis=AX, yaxis=dict(**AX, title="Avg Delay (min)"))
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    with dd2:
        sec("Delay Intensity by Hour of Day","HOURLY")
        hr = ddf[ddf["DEP_HOUR"]>=0].groupby("DEP_HOUR").agg(
            AvgDelay=("ARRIVAL_DELAY","mean"), Flights=("OTP_FLAG","count")).reset_index()
        fig5 = go.Figure()
        fig5.add_bar(x=hr["DEP_HOUR"], y=hr["Flights"], name="Flights",
                     marker_color=PALETTE[2], marker_line_width=0, yaxis="y1")
        fig5.add_scatter(x=hr["DEP_HOUR"], y=hr["AvgDelay"], name="Avg Delay", yaxis="y2",
                         line=dict(color=PALETTE[0],width=2.5), mode="lines+markers", marker=dict(size=6))
        fig5.update_layout(**BASE, height=380,
                           xaxis=dict(**AX, title="Departure Hour"), yaxis=AX,
                           yaxis2=dict(overlaying="y", side="right", color=PALETTE[0],
                                       gridcolor="rgba(0,0,0,0)", title="Avg Delay (min)"))
        st.plotly_chart(fig5, use_container_width=True, config=CFG)

    div()
    sec("Delay Severity Index by Airline","DSI")
    dsi = ddf.groupby("AIRLINE_NAME").agg(
        AvgDelay=("ARRIVAL_DELAY","mean"),
        Pct15=("ARRIVAL_DELAY", lambda x:(x>15).mean()*100),
        Pct60=("ARRIVAL_DELAY", lambda x:(x>60).mean()*100),
        Pct120=("ARRIVAL_DELAY",lambda x:(x>120).mean()*100),
    ).reset_index()
    dsi["DSI"] = (dsi["AvgDelay"]*.4 + dsi["Pct15"]*.3 + dsi["Pct60"]*.2 + dsi["Pct120"]*.1).round(2)
    dsi = dsi.sort_values("DSI", ascending=False).reset_index(drop=True); dsi.index += 1
    dsi.columns = ["Airline","Avg Delay","% >15 min","% >60 min","% >120 min","DSI"]
    dsi["Avg Delay"] = dsi["Avg Delay"].map("{:.1f} min".format)
    for c in ["% >15 min","% >60 min","% >120 min"]: dsi[c] = dsi[c].map("{:.1f}%".format)
    st.dataframe(dsi, use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════
# PAGE 5 — CANCELLATION ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif "Cancellation" in PAGE:
    pg("❌","Cancellation Analytics","Root causes, trends, and carrier-level cancellation intelligence")

    cdf   = df[df["CANCELLED"]==1].copy()
    total = len(df); nc = len(cdf); cr = nc/total*100
    wx_pct = (cdf["CANCELLATION_REASON"]=="B").mean()*100
    ca_pct = (cdf["CANCELLATION_REASON"]=="A").mean()*100

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.metric("❌  Total Cancellations", f"{nc:,}")
    with k2: st.metric("📊  Cancel Rate", f"{cr:.2f}%")
    with k3: st.metric("🌩️  Weather-Caused", f"{wx_pct:.1f}%")
    with k4: st.metric("✈️  Carrier-Caused", f"{ca_pct:.1f}%")
    with k5: st.metric("📅  Worst Month", MONTH_MAP.get(int(cdf["MONTH"].value_counts().idxmax()),"N/A"))

    div()

    cc1,cc2 = st.columns(2)
    with cc1:
        sec("Cancellation Reason Distribution","ROOT CAUSE")
        rc = cdf["CANCELLATION_REASON"].map(CANCEL_MAP).value_counts()
        fig = go.Figure(go.Pie(labels=rc.index, values=rc.values, hole=.52,
            marker=dict(colors=PALETTE[:4], line=dict(color="#0B0F19",width=2)),
            textinfo="percent+label", textfont=dict(size=11,color="#fff")))
        fig.update_layout(**BASE, height=360, xaxis=AX, yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with cc2:
        sec("Cancellation Rate by Airline","CARRIER")
        al_c = df.groupby("AIRLINE_NAME").agg(T=("CANCELLED","count"),C=("CANCELLED","sum")).reset_index()
        al_c["Rate"] = (al_c["C"]/al_c["T"]*100).round(2)
        al_c = al_c.sort_values("Rate", ascending=True)
        fig2 = go.Figure(go.Bar(x=al_c["Rate"], y=al_c["AIRLINE_NAME"], orientation="h",
            marker=dict(color=PALETTE[0], line=dict(width=0)),
            text=[f"{v:.2f}%" for v in al_c["Rate"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig2.update_layout(**BASE, height=360, xaxis=dict(**AX, ticksuffix="%"), yaxis=AX)
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()
    sec("Monthly Cancellation Trend","TREND")
    mc = df.groupby("MONTH").agg(T=("CANCELLED","count"),C=("CANCELLED","sum")).reset_index()
    mc["Rate"] = (mc["C"]/mc["T"]*100).round(2)
    mc["Month"] = mc["MONTH"].map(MONTH_MAP)
    fig3 = go.Figure()
    fig3.add_bar(x=mc["Month"], y=mc["C"], name="Cancellations",
                 marker_color=PALETTE[0], marker_line_width=0)
    fig3.add_scatter(x=mc["Month"], y=mc["Rate"], name="Rate %", yaxis="y2",
                     line=dict(color=PALETTE[1],width=2.5), mode="lines+markers", marker=dict(size=7))
    fig3.update_layout(**BASE, height=360, xaxis=AX, yaxis=AX,
                       yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                                   color=PALETTE[1], gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig3, use_container_width=True, config=CFG)

    div()
    cc3,cc4 = st.columns(2)
    with cc3:
        sec("Cancellation Treemap — Airline × Reason","TREEMAP")
        tm = cdf.copy(); tm["Reason"] = tm["CANCELLATION_REASON"].map(CANCEL_MAP).fillna("Other")
        tm["Count"] = 1
        tma = tm.groupby(["AIRLINE_NAME","Reason"])["Count"].sum().reset_index()
        fig4 = px.treemap(tma, path=["AIRLINE_NAME","Reason"], values="Count",
                          color_discrete_sequence=PALETTE)
        fig4.update_traces(textinfo="label+percent parent", marker=dict(line=dict(width=1,color="#0B0F19")))
        fig4.update_layout(**BASE, height=420, xaxis=AX, yaxis=AX)
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    with cc4:
        sec("Day-of-Week Cancellation Pattern","WEEKLY")
        dc = df.groupby("DAY_OF_WEEK").agg(T=("CANCELLED","count"),C=("CANCELLED","sum")).reset_index()
        dc["Rate"] = (dc["C"]/dc["T"]*100).round(2)
        dc["Day"] = dc["DAY_OF_WEEK"].map(DOW_MAP)
        fig5 = go.Figure(go.Bar(x=dc["Day"], y=dc["Rate"],
            marker=dict(color=PALETTE[3], line=dict(width=0)),
            text=[f"{v:.2f}%" for v in dc["Rate"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig5.update_layout(**BASE, height=420, xaxis=AX, yaxis=dict(**AX, ticksuffix="%"))
        st.plotly_chart(fig5, use_container_width=True, config=CFG)

    div()
    sec("Airline × Month Cancellation Heatmap","HEATMAP")
    ml = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    hm = df.groupby(["AIRLINE_NAME","MONTH"])["CANCELLED"].mean().unstack(fill_value=0)*100
    hm.index = hm.index.str.split().str[0]
    hm.columns = [ml[m-1] for m in hm.columns]
    fig6 = go.Figure(go.Heatmap(z=hm.values.round(2), x=list(hm.columns), y=list(hm.index),
        colorscale=[[0,"#0B0F19"],[0.5,"#7B0A16"],[1,"#C8102E"]], showscale=True,
        text=hm.values.round(2), texttemplate="%{text}%", textfont=dict(color="#fff",size=10),
        hovertemplate="<b>%{y}</b> — %{x}<br>Cancel Rate: <b>%{z:.2f}%</b><extra></extra>"))
    fig6.update_layout(**BASE, height=400, xaxis=AX, yaxis=AX)
    st.plotly_chart(fig6, use_container_width=True, config=CFG)

# ══════════════════════════════════════════════════════════════════
# PAGE 6 — ROUTE INTELLIGENCE
# ══════════════════════════════════════════════════════════════════
elif "Route" in PAGE:
    pg("🗺️","Route Intelligence","Origin–destination performance, reliability scoring, and corridor analysis")

    mn = st.slider("Min flights per route", 10, 500, 50, 10)
    rs = df.groupby(["ORIGIN_AIRPORT","DESTINATION_AIRPORT","ROUTE"]).agg(
        Flights=("OTP_FLAG","count"), OTP=("OTP_FLAG","sum"), Cancelled=("CANCELLED","sum"),
        AvgArr=("ARRIVAL_DELAY","mean"), AvgDist=("DISTANCE","mean"),
    ).reset_index()
    rs["OTP%"]    = (rs["OTP"]/rs["Flights"]*100).round(1)
    rs["Cancel%"] = (rs["Cancelled"]/rs["Flights"]*100).round(2)
    rs["RRI"]     = (rs["OTP%"]*0.6 - rs["Cancel%"]*3 - rs["AvgArr"].clip(0)*0.2).round(1)
    rs = rs[rs["Flights"] >= mn]

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.metric("🗺️  Active Routes", f"{len(rs):,}")
    with k2: st.metric("🏆  Best OTP Route", rs.loc[rs["OTP%"].idxmax(),"ROUTE"], f"{rs['OTP%'].max():.1f}%")
    with k3: st.metric("⚠️  Most Delayed", rs.loc[rs["AvgArr"].idxmax(),"ROUTE"], f"{rs['AvgArr'].max():.1f} min")
    with k4: st.metric("📏  Avg Distance", f"{rs['AvgDist'].mean():.0f} mi")

    div()

    rc1,rc2 = st.columns(2)
    with rc1:
        sec("Top 15 Most Reliable Routes","BEST OTP")
        tr = rs.nlargest(15,"OTP%").sort_values("OTP%", ascending=True)
        fig = go.Figure(go.Bar(x=tr["OTP%"], y=tr["ROUTE"], orientation="h",
            marker=dict(color=PALETTE[1], line=dict(width=0)),
            text=[f"{v:.1f}%" for v in tr["OTP%"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig.update_layout(**BASE, height=480, xaxis=dict(**AX, range=[0,110], ticksuffix="%"), yaxis=AX)
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with rc2:
        sec("Top 15 Most Delayed Routes","WORST")
        wd = rs.nlargest(15,"AvgArr").sort_values("AvgArr", ascending=False)
        fig2 = go.Figure(go.Bar(x=wd["ROUTE"], y=wd["AvgArr"],
            marker=dict(color=PALETTE[0], line=dict(width=0)),
            text=[f"{v:.1f}" for v in wd["AvgArr"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig2.update_layout(**BASE, height=480, xaxis=dict(**AX, tickangle=-30),
                           yaxis=dict(**AX, title="Avg Arr Delay (min)"))
        st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()

    rc3,rc4 = st.columns(2)
    with rc3:
        sec("Top 15 Busiest Routes","VOLUME")
        bz = rs.nlargest(15,"Flights").sort_values("Flights", ascending=False)
        fig3 = go.Figure(go.Bar(x=bz["ROUTE"], y=bz["Flights"],
            marker=dict(color=PALETTE[2], line=dict(width=0)),
            text=[f"{v:,}" for v in bz["Flights"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
        fig3.update_layout(**BASE, height=420, xaxis=dict(**AX, tickangle=-30), yaxis=AX)
        st.plotly_chart(fig3, use_container_width=True, config=CFG)

    with rc4:
        sec("Distance vs Avg Arrival Delay","CORRELATION")
        samp = rs.sample(min(200,len(rs)), random_state=42)
        fig4 = go.Figure(go.Scatter(x=samp["AvgDist"], y=samp["AvgArr"], mode="markers",
            marker=dict(size=samp["Flights"]/samp["Flights"].max()*20+4,
                        color=PALETTE[2], opacity=.75, line=dict(width=.5,color="#fff")),
            hovertext=samp["ROUTE"], hoverinfo="text+x+y"))
        fig4.update_layout(**BASE, height=420,
                           xaxis=dict(**AX, title="Avg Route Distance (mi)"),
                           yaxis=dict(**AX, title="Avg Arrival Delay (min)"))
        st.plotly_chart(fig4, use_container_width=True, config=CFG)

    div()
    sec("Route Reliability Index — Top 50","SCORECARD")
    disp = rs.sort_values("RRI", ascending=False).head(50)[
        ["ROUTE","Flights","OTP%","AvgArr","Cancel%","AvgDist","RRI"]].reset_index(drop=True)
    disp.index += 1
    disp.columns = ["Route","Flights","OTP %","Avg Arr Delay","Cancel %","Avg Dist (mi)","RRI"]
    disp["OTP %"]         = disp["OTP %"].map("{:.1f}%".format)
    disp["Avg Arr Delay"] = disp["Avg Arr Delay"].map("{:.1f} min".format)
    disp["Cancel %"]      = disp["Cancel %"].map("{:.2f}%".format)
    disp["Avg Dist (mi)"] = disp["Avg Dist (mi)"].map("{:.0f}".format)
    disp["Flights"]       = disp["Flights"].map("{:,}".format)
    st.dataframe(disp, use_container_width=True, height=440)

# ══════════════════════════════════════════════════════════════════
# PAGE 7 — TIME TREND ANALYSIS  (xaxis bug fixed here)
# ══════════════════════════════════════════════════════════════════
elif "Time" in PAGE:
    pg("📅","Time Trend Analysis","Monthly, quarterly, daily, and hourly performance pattern intelligence")

    tab1,tab2,tab3,tab4,tab5 = st.tabs(["📆 Monthly","📊 Quarterly","📅 Day of Week","🕐 Hourly","🍂 Seasonal"])

    with tab1:
        mth = df.groupby("MONTH").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
            C=("CANCELLED","sum"),D=("ARRIVAL_DELAY","mean")).reset_index()
        mth["OTP%"] = (mth["OTP"]/mth["T"]*100).round(1)
        mth["CR"]   = (mth["C"]/mth["T"]*100).round(2)
        mth["Month"]= mth["MONTH"].map(MONTH_MAP)

        t1,t2 = st.columns(2)
        with t1:
            fig = go.Figure()
            fig.add_bar(x=mth["Month"], y=mth["T"], name="Flights",
                        marker_color=PALETTE[2], marker_line_width=0)
            fig.add_scatter(x=mth["Month"], y=mth["OTP%"], name="OTP %", yaxis="y2",
                            line=dict(color=PALETTE[1],width=2.5), mode="lines+markers", marker=dict(size=7))
            fig.update_layout(**BASE, height=360, title=dict(text="Monthly Flights & OTP",font=dict(size=14,color="#fff")),
                              xaxis=AX, yaxis=AX,
                              yaxis2=dict(overlaying="y",side="right",ticksuffix="%",
                                          color=PALETTE[1],gridcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, use_container_width=True, config=CFG)

        with t2:
            fig2 = go.Figure()
            fig2.add_bar(x=mth["Month"], y=mth["D"], name="Avg Delay",
                         marker_color=PALETTE[0], marker_line_width=0)
            fig2.add_scatter(x=mth["Month"], y=mth["CR"], name="Cancel %", yaxis="y2",
                             line=dict(color=PALETTE[3],width=2.5), mode="lines+markers", marker=dict(size=7))
            fig2.update_layout(**BASE, height=360, title=dict(text="Monthly Avg Delay & Cancellations",font=dict(size=14,color="#fff")),
                               xaxis=AX, yaxis=dict(**AX, title="Avg Delay (min)"),
                               yaxis2=dict(overlaying="y",side="right",ticksuffix="%",
                                           color=PALETTE[3],gridcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig2, use_container_width=True, config=CFG)

    with tab2:
        qt = df.groupby("QUARTER").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
            C=("CANCELLED","sum"),D=("ARRIVAL_DELAY","mean")).reset_index()
        qt["OTP%"] = (qt["OTP"]/qt["T"]*100).round(1)
        qt["CR"]   = (qt["C"]/qt["T"]*100).round(2)
        t1,t2 = st.columns(2)
        with t1:
            fig = go.Figure()
            for i,row in qt.iterrows():
                fig.add_bar(x=[row["QUARTER"]], y=[row["T"]], name=row["QUARTER"],
                            marker_color=PALETTE[i], marker_line_width=0)
            fig.update_layout(**BASE, height=360, showlegend=False,
                              title=dict(text="Quarterly Flight Volume",font=dict(size=14,color="#fff")),
                              xaxis=AX, yaxis=AX)
            st.plotly_chart(fig, use_container_width=True, config=CFG)
        with t2:
            fig2 = go.Figure()
            fig2.add_scatter(x=qt["QUARTER"], y=qt["OTP%"], name="OTP %",
                             line=dict(color=PALETTE[1],width=3), mode="lines+markers+text",
                             text=[f"{v:.1f}%" for v in qt["OTP%"]], textposition="top center")
            fig2.add_scatter(x=qt["QUARTER"], y=qt["CR"], name="Cancel %",
                             line=dict(color=PALETTE[0],width=3,dash="dash"), mode="lines+markers+text",
                             text=[f"{v:.2f}%" for v in qt["CR"]], textposition="bottom center")
            fig2.update_layout(**BASE, height=360,
                               title=dict(text="Quarterly OTP & Cancellation",font=dict(size=14,color="#fff")),
                               xaxis=AX, yaxis=AX)
            st.plotly_chart(fig2, use_container_width=True, config=CFG)

    with tab3:
        dow = df.groupby("DAY_OF_WEEK").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
            C=("CANCELLED","sum"),D=("ARRIVAL_DELAY","mean")).reset_index()
        dow["OTP%"] = (dow["OTP"]/dow["T"]*100).round(1)
        dow["Day"]  = dow["DAY_OF_WEEK"].map({1:"Monday",2:"Tuesday",3:"Wednesday",
                                               4:"Thursday",5:"Friday",6:"Saturday",7:"Sunday"})
        t1,t2 = st.columns(2)
        with t1:
            fig = go.Figure(go.Bar(x=dow["Day"], y=dow["D"],
                marker=dict(color=PALETTE[0], line=dict(width=0)),
                text=[f"{v:.1f}" for v in dow["D"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
            fig.update_layout(**BASE, height=380, title=dict(text="Avg Arrival Delay by Day",font=dict(size=14,color="#fff")),
                              xaxis=AX, yaxis=dict(**AX, title="Avg Delay (min)"))
            st.plotly_chart(fig, use_container_width=True, config=CFG)
        with t2:
            fig2 = go.Figure(go.Bar(x=dow["Day"], y=dow["OTP%"],
                marker=dict(color=[PALETTE[1] if v>=75 else PALETTE[0] for v in dow["OTP%"]], line=dict(width=0)),
                text=[f"{v:.1f}%" for v in dow["OTP%"]], textposition="outside", textfont=dict(color="#D1D5DB",size=11)))
            fig2.update_layout(**BASE, height=380, title=dict(text="OTP Rate by Day of Week",font=dict(size=14,color="#fff")),
                               xaxis=AX, yaxis=dict(**AX, ticksuffix="%", range=[0,105]))
            st.plotly_chart(fig2, use_container_width=True, config=CFG)

    with tab4:
        hr2 = df[df["DEP_HOUR"]>=0].groupby("DEP_HOUR").agg(
            T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),D=("ARRIVAL_DELAY","mean")).reset_index()
        hr2["OTP%"] = (hr2["OTP"]/hr2["T"]*100).round(1)
        fig = go.Figure()
        fig.add_bar(x=hr2["DEP_HOUR"], y=hr2["T"], name="Flights",
                    marker_color=PALETTE[2], marker_line_width=0, yaxis="y1")
        fig.add_scatter(x=hr2["DEP_HOUR"], y=hr2["D"], name="Avg Delay", yaxis="y2",
                        line=dict(color=PALETTE[0],width=2.5), mode="lines+markers", marker=dict(size=6))
        fig.add_scatter(x=hr2["DEP_HOUR"], y=hr2["OTP%"], name="OTP %", yaxis="y3",
                        line=dict(color=PALETTE[1],width=2,dash="dash"), mode="lines")
        fig.update_layout(**BASE, height=420,
                          title=dict(text="Hourly Flight Operations (0–23h)",font=dict(size=14,color="#fff")),
                          xaxis=dict(**AX, title="Departure Hour",
                                     tickmode="array", tickvals=list(range(0,24))),
                          yaxis=AX,
                          yaxis2=dict(overlaying="y",side="right",color=PALETTE[0],
                                      gridcolor="rgba(0,0,0,0)",title="Avg Delay"),
                          yaxis3=dict(overlaying="y",side="right",position=.95,
                                      color=PALETTE[1],gridcolor="rgba(0,0,0,0)",ticksuffix="%"))
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    with tab5:
        seas = df.groupby("SEASON").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
            C=("CANCELLED","sum"),D=("ARRIVAL_DELAY","mean")).reset_index()
        seas["OTP%"] = (seas["OTP"]/seas["T"]*100).round(1)
        seas["CR"]   = (seas["C"]/seas["T"]*100).round(2)
        seas = seas.set_index("SEASON").reindex(["Winter","Spring","Summer","Fall"]).reset_index()
        t1,t2 = st.columns(2)
        with t1:
            fig = go.Figure(go.Bar(x=seas["SEASON"], y=seas["D"],
                marker=dict(color=PALETTE[0], line=dict(width=0)),
                text=[f"{v:.1f}" for v in seas["D"]], textposition="outside", textfont=dict(color="#D1D5DB",size=12)))
            fig.update_layout(**BASE, height=360, title=dict(text="Avg Arrival Delay by Season",font=dict(size=14,color="#fff")),
                              xaxis=AX, yaxis=dict(**AX, title="Avg Delay (min)"))
            st.plotly_chart(fig, use_container_width=True, config=CFG)
        with t2:
            fig2 = go.Figure(go.Bar(x=seas["SEASON"], y=seas["OTP%"],
                marker=dict(color=[PALETTE[1] if v>=75 else PALETTE[0] for v in seas["OTP%"]], line=dict(width=0)),
                text=[f"{v:.1f}%" for v in seas["OTP%"]], textposition="outside", textfont=dict(color="#D1D5DB",size=12)))
            fig2.update_layout(**BASE, height=360, title=dict(text="OTP Rate by Season",font=dict(size=14,color="#fff")),
                               xaxis=AX, yaxis=dict(**AX, ticksuffix="%", range=[0,105]))
            st.plotly_chart(fig2, use_container_width=True, config=CFG)

    div()
    sec("Month × Day-of-Week Delay Heatmap","CROSS-DIMENSIONAL")
    pv = df.pivot_table(values="ARRIVAL_DELAY", index="MONTH", columns="DAY_OF_WEEK", aggfunc="mean")
    pv.index = [MONTH_MAP[i] for i in pv.index]
    pv.columns = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    fig3 = go.Figure(go.Heatmap(z=pv.values.round(1), x=list(pv.columns), y=list(pv.index),
        colorscale=[[0,"#0B0F19"],[0.5,"#7B0A16"],[1,"#C8102E"]], showscale=True,
        text=pv.values.round(1), texttemplate="%{text}", textfont=dict(color="#fff",size=11),
        hovertemplate="<b>%{y} — %{x}</b><br>Avg Delay: <b>%{z:.1f} min</b><extra></extra>"))
    fig3.update_layout(**BASE, height=400, xaxis=AX, yaxis=AX)
    st.plotly_chart(fig3, use_container_width=True, config=CFG)

# ══════════════════════════════════════════════════════════════════
# PAGE 8 — GEOGRAPHIC INTELLIGENCE
# ══════════════════════════════════════════════════════════════════
elif "Geographic" in PAGE:
    pg("🌎","Geographic Intelligence","Interactive U.S. maps — delay hotspots, hub density, route corridors")

    ap = df.groupby("ORIGIN_AIRPORT").agg(
        Deps=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
        C=("CANCELLED","sum"),AvgDep=("DEPARTURE_DELAY","mean")).reset_index()
    ap.columns = ["IATA_CODE","Deps","OTP","C","AvgDep"]
    ap["OTP%"] = (ap["OTP"]/ap["Deps"]*100).round(1)
    ap["CR"]   = (ap["C"]/ap["Deps"]*100).round(2)
    ap = ap.merge(airports_raw[["IATA_CODE","AIRPORT","CITY","STATE","LATITUDE","LONGITUDE"]],
                  on="IATA_CODE", how="inner").dropna(subset=["LATITUDE","LONGITUDE"])
    ap = ap[(ap["LATITUDE"].between(15,75)) & (ap["LONGITUDE"].between(-180,-50))]

    met = st.selectbox("Map Metric",["Avg Departure Delay","OTP Rate","Cancellation Rate","Total Departures"])
    mn2 = st.slider("Min departures", 50, 2000, 200, 50)
    gdf = ap[ap["Deps"]>=mn2].copy()
    gdf["sz"] = gdf["Deps"]/gdf["Deps"].max()*45+5
    col_map   = {"Avg Departure Delay":"AvgDep","OTP Rate":"OTP%","Cancellation Rate":"CR","Total Departures":"Deps"}
    scale_map = {"Avg Departure Delay":"Reds","OTP Rate":"RdYlGn","Cancellation Rate":"Reds","Total Departures":"Blues"}
    col = col_map[met]; scale = scale_map[met]

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.metric("🛬  Airports Mapped", f"{len(gdf):,}")
    with k2: st.metric("📍  Worst Delay Hub", gdf.loc[gdf["AvgDep"].idxmax(),"IATA_CODE"], f"{gdf['AvgDep'].max():.1f} min")
    with k3: st.metric("🏆  Best OTP Hub", gdf.loc[gdf["OTP%"].idxmax(),"IATA_CODE"], f"{gdf['OTP%'].max():.1f}%")
    with k4: st.metric("✈️  Busiest Airport", gdf.loc[gdf["Deps"].idxmax(),"IATA_CODE"], f"{gdf['Deps'].max():,}")

    sec(f"U.S. Airport Map — {met}","INTERACTIVE")
    fig = px.scatter_geo(gdf, lat="LATITUDE", lon="LONGITUDE", color=col, size="sz",
                         hover_name="IATA_CODE", scope="usa", color_continuous_scale=scale,
                         hover_data={"CITY":True,"STATE":True,"AvgDep":":.1f","OTP%":":.1f","Deps":":,","LATITUDE":False,"LONGITUDE":False,"sz":False})
    fig.update_geos(bgcolor="#0B0F19",landcolor="#111827",
                    showcoastlines=True,coastlinecolor="#374151",
                    showsubunits=True,subunitcolor="#1F2937",
                    projection_type="albers usa")
    fig.update_layout(**BASE, height=560,
                       margin=dict(l=0,r=0,t=20,b=0),
                      coloraxis_colorbar=dict(tickfont=dict(color="#D1D5DB"),
                                              title_font=dict(color="#D1D5DB"),
                                              bgcolor="rgba(0,0,0,0.5)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":True})

    div()
    sec("State-Level Choropleth","STATE MAP")
    st_df = gdf.groupby("STATE").agg(Airports=("IATA_CODE","count"),
        AvgDelay=("AvgDep","mean"),AvgOTP=("OTP%","mean"),TotalDep=("Deps","sum")).reset_index().dropna()
    cm2 = st.selectbox("Choropleth Metric",["AvgDelay","AvgOTP","TotalDep"],
                       format_func=lambda x:{"AvgDelay":"Avg Delay","AvgOTP":"OTP Rate","TotalDep":"Departures"}[x])
    fig2 = px.choropleth(st_df, locations="STATE", locationmode="USA-states", color=cm2,
                         scope="usa", color_continuous_scale="Reds" if cm2=="AvgDelay" else "Blues",
                         hover_data={"STATE":True,"Airports":True,"AvgDelay":":.1f","AvgOTP":":.1f"})
    fig2.update_geos(bgcolor="#0B0F19",landcolor="#111827",showcoastlines=True,coastlinecolor="#374151")
    fig2.update_layout(**BASE, height=480,
                    margin=dict(l=0,r=0,t=20,b=0),
                       coloraxis_colorbar=dict(tickfont=dict(color="#D1D5DB")))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":True})

    div()
    sec("Top 30 Route Corridors","ROUTE MAP")
    rv  = df.groupby(["ORIGIN_AIRPORT","DESTINATION_AIRPORT"]).size().reset_index(name="Cnt")
    top30 = rv.nlargest(30,"Cnt")
    coord = gdf.set_index("IATA_CODE")[["LATITUDE","LONGITUDE","CITY"]].to_dict("index")
    fig3 = go.Figure()
    for _,row in top30.iterrows():
        o,d = row["ORIGIN_AIRPORT"],row["DESTINATION_AIRPORT"]
        if o not in coord or d not in coord: continue
        op = 0.15 + 0.65*(row["Cnt"]/top30["Cnt"].max())
        fig3.add_scattergeo(lat=[coord[o]["LATITUDE"],coord[d]["LATITUDE"],None],
                            lon=[coord[o]["LONGITUDE"],coord[d]["LONGITUDE"],None],
                            mode="lines",line=dict(width=1.4,color=RED),
                            opacity=op,showlegend=False,hoverinfo="skip")
    ra   = set(top30["ORIGIN_AIRPORT"])|set(top30["DESTINATION_AIRPORT"])
    dots = gdf[gdf["IATA_CODE"].isin(ra)]
    fig3.add_scattergeo(lat=dots["LATITUDE"],lon=dots["LONGITUDE"],mode="markers+text",
                        marker=dict(size=7,color=GOLD,line=dict(width=.5,color="#fff")),
                        text=dots["IATA_CODE"],textposition="top right",
                        textfont=dict(size=8,color=GOLD),hovertext=dots["CITY"],
                        hoverinfo="text",name="Airport")
    fig3.update_geos(scope="usa",bgcolor="#0B0F19",landcolor="#111827",
                     showcoastlines=True,coastlinecolor="#374151",
                     showsubunits=True,subunitcolor="#1F2937",
                     projection_type="albers usa")
    fig3.update_layout(**BASE, height=500, showlegend=False)
    fig3.update_layout(margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":True})

# ══════════════════════════════════════════════════════════════════
# PAGE 9 — AI INSIGHTS
# ══════════════════════════════════════════════════════════════════
elif "AI" in PAGE:
    pg("🤖","AI Insights & Recommendations","Automated executive intelligence — strategic findings and action plans")

    total  = len(df); cancel = int(df["CANCELLED"].sum()); on_time = int(df["OTP_FLAG"].sum())
    otp_r  = round(on_time/total*100,2); can_r = round(cancel/total*100,2)
    avg_arr= round(df.loc[df["CANCELLED"]==0,"ARRIVAL_DELAY"].mean(),1)

    al2 = df.groupby("AIRLINE_NAME").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum")).reset_index()
    al2["OTP%"] = (al2["OTP"]/al2["T"]*100).round(1)
    best_al  = al2.loc[al2["OTP%"].idxmax(),"AIRLINE_NAME"]
    worst_al = al2.loc[al2["OTP%"].idxmin(),"AIRLINE_NAME"]
    gap = al2["OTP%"].max() - al2["OTP%"].min()

    dt = {"Late Aircraft":df["LATE_AIRCRAFT_DELAY"].sum(),"Air System":df["AIR_SYSTEM_DELAY"].sum(),
          "Carrier":df["AIRLINE_DELAY"].sum(),"Weather":df["WEATHER_DELAY"].sum(),"Security":df["SECURITY_DELAY"].sum()}
    top_d = max(dt, key=dt.get)
    top_pct = dt[top_d]/sum(dt.values())*100
    mth2 = df.groupby("MONTH")["ARRIVAL_DELAY"].mean()
    pk_m = MONTH_MAP.get(int(mth2.idxmax()),"N/A")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(200,16,46,.1),rgba(212,175,55,.06));
    border:1px solid rgba(212,175,55,.3);border-radius:16px;padding:1.6rem 2rem;margin-bottom:2rem;">
      <div style="font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:900;color:#fff;margin-bottom:.4rem;">
        📋 Executive Aviation Intelligence Report — 2015
      </div>
      <div style="font-size:.72rem;color:#6B7280;letter-spacing:.12em;text-transform:uppercase;margin-bottom:1rem;">
        Emirates Aviation Intelligence Platform · Auto-Generated
      </div>
      <div style="font-size:.88rem;color:#D1D5DB;line-height:1.85;">
        Analyzed <b style="color:#D4AF37">{total:,}</b> flights ·
        <b style="color:#D4AF37">{df["AIRLINE"].nunique()}</b> carriers ·
        <b style="color:#D4AF37">{df["ORIGIN_AIRPORT"].nunique()}</b> airports ·
        OTP <b style="color:#D4AF37">{otp_r}%</b> ·
        Cancel rate <b style="color:#C8102E">{can_r}%</b> ·
        Avg delay <b style="color:#D4AF37">{avg_arr} min</b>
      </div>
    </div>""", unsafe_allow_html=True)

    sec("🔍 Key Findings","AUTOMATED")
    e1,e2 = st.columns(2)
    with e1:
        ins(1,"Carrier Performance Gap",f"A <b>{gap:.1f}-point</b> OTP gap exists between <b>{best_al}</b> ({al2['OTP%'].max():.1f}%) and <b>{worst_al}</b> ({al2['OTP%'].min():.1f}%). Targeted intervention required.")
        ins(2,"Primary Delay Driver",f"<b>{top_d}</b> delays account for <b>{top_pct:.1f}%</b> of total delay minutes, cascading across the network.")
        ins(3,"Seasonal Vulnerability",f"<b>{pk_m}</b> records peak average delay. Summer and winter drive the dominant risk windows.")
    with e2:
        ins(4,"Peak Hour Congestion","Evening departure slots accumulate cascading delay debt from morning disruptions. Flights at 17:00–21:00 record the highest average delays.")
        ins(5,"Cancellation Pattern",f"Weather (B) and Carrier (A) causes drive {can_r:.2f}% cancellations. Pre-cancellation protocols can cut this by 20–30%.")
        ins(6,"Route Opportunity","High-frequency routes show the greatest delay concentration. Buffer scheduling on top-10 delayed routes could recover 8–12% OTP.")

    div()
    sec("⚠️ Risk Analysis Matrix","RISK")
    risks = pd.DataFrame([
        {"Risk":"Late Aircraft Cascade","L":9,"I":9,"Cat":"Operational"},
        {"Risk":"Weather Disruption","L":7,"I":8,"Cat":"External"},
        {"Risk":"NAS Congestion","L":8,"I":7,"Cat":"Systemic"},
        {"Risk":"Carrier Under-performance","L":6,"I":7,"Cat":"Performance"},
        {"Risk":"Security Delay","L":2,"I":5,"Cat":"Regulatory"},
        {"Risk":"Seasonal Demand Surge","L":9,"I":6,"Cat":"Strategic"},
        {"Risk":"Route Congestion","L":7,"I":6,"Cat":"Network"},
    ])
    cat_colors = {"Operational":PALETTE[0],"External":PALETTE[2],"Systemic":PALETTE[3],
                  "Performance":PALETTE[1],"Regulatory":PALETTE[4],"Strategic":PALETTE[5],"Network":PALETTE[6]}
    figr = go.Figure()
    for cat in risks["Cat"].unique():
        sub = risks[risks["Cat"]==cat]
        figr.add_scatter(x=sub["L"],y=sub["I"],mode="markers+text",name=cat,
                         marker=dict(size=sub["L"]*sub["I"]/10*6,color=cat_colors.get(cat,PALETTE[0]),
                                     opacity=.85,line=dict(width=1,color="#fff")),
                         text=sub["Risk"],textposition="top center",textfont=dict(size=9,color="#D1D5DB"))
    figr.add_shape(type="rect",x0=7,y0=7,x1=10,y1=10,
                   fillcolor="rgba(200,16,46,.08)",line_color="rgba(200,16,46,.3)")
    figr.add_annotation(x=8.5,y=9.7,text="HIGH RISK ZONE",font=dict(color="#ff6b7a",size=10),showarrow=False)
    figr.update_layout(**BASE,height=460,
                       xaxis=dict(**AX,title="Likelihood (1–10)",range=[0,11]),
                       yaxis=dict(**AX,title="Impact (1–10)",range=[0,11]))
    st.plotly_chart(figr, use_container_width=True, config=CFG)

    div()
    sec("🎯 Strategic Recommendations","ACTION PLAN")
    recs = [
        ("#C8102E","CRITICAL","1. Late Aircraft Cascade Prevention",
         ["10–15 min buffer scheduling on morning high-frequency rotations",
          "Real-time aircraft tracking dashboards for ground operations",
          "Dedicated maintenance recovery slots at hub airports",
          "Target: 25% reduction in late aircraft delays within 6 months"]),
        ("#EA580C","HIGH",f"2. Carrier Performance Intervention",
         ["Performance improvement programme for bottom-tier carriers",
          "Monthly OTP KPI reviews with carrier operational heads",
          "Incentive-based on-time completion bonuses",
          "Target: Close performance gap to <10 points within 12 months"]),
        ("#EA580C","HIGH",f"3. Seasonal Capacity Optimization",
         [f"Increased schedule buffers during {pk_m} and summer peak",
          "Additional ground handling resources at high-delay airports",
          "FAA coordination for ATC slot management during peaks",
          "Target: 15–20% reduction in peak-season delay average"]),
        ("#D4AF37","MEDIUM","4. Weather Resilience Program",
         ["Predictive weather analytics integrated with ops control",
          "Pre-cancellation protocols for severe weather (>80% probability)",
          "Automated passenger re-accommodation to reduce disruption impact",
          "Target: 20% reduction in weather-related cancellations"]),
        ("#2563EB","STRATEGIC","5. Technology & Data Infrastructure",
         ["Real-time intelligence platform across all hubs",
          "ML-based delay prediction 12 hours ahead for proactive recovery",
          "Cross-carrier data sharing for NAS delay coordination",
          "Target: Network OTP above 82% by end of next fiscal year"]),
    ]
    for color,priority,title,actions in recs:
        acts = "".join([f"<li style='margin-bottom:5px;color:#D1D5DB;font-size:.82rem;'>{a}</li>" for a in actions])
        st.markdown(f"""
        <div class="rec-card" style="border-left:4px solid {color};">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:.8rem;">
            <span style="background:{color};color:#fff;font-size:.62rem;padding:3px 9px;border-radius:20px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">{priority}</span>
            <span style="font-family:'Playfair Display',serif;font-size:.98rem;font-weight:700;color:#fff;">{title}</span>
          </div>
          <ul style="margin:0;padding-left:1.2rem;line-height:1.9;">{acts}</ul>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE 10 — DOWNLOAD CENTER
# ══════════════════════════════════════════════════════════════════
elif "Download" in PAGE:
    pg("📥","Download Center","Export platform analytics in enterprise-ready formats")

    st.markdown("""
    <div style="background:rgba(255,255,255,.03);border:1px solid rgba(200,16,46,.25);
    border-radius:14px;padding:1.3rem 1.8rem;margin-bottom:1.8rem;">
      <div style="font-family:'Playfair Display',serif;font-size:1.1rem;color:#fff;margin-bottom:.4rem;">📋 Export Configuration</div>
      <div style="font-size:.8rem;color:#9CA3AF;">Select dataset and format. All exports include engineered features and cleaned data.</div>
    </div>""", unsafe_allow_html=True)

    dl1,dl2 = st.columns(2)
    with dl1:
        ds   = st.selectbox("Dataset",["Airline Performance","Airport Performance","Route Intelligence",
                                        "Delay Analytics","Cancellation Report","Monthly Trends"])
        rows = st.slider("Max rows (0=all)", 0, 200000, 0, 10000)
    with dl2:
        fmt = st.selectbox("Format",["CSV","Excel (.xlsx)","JSON"])

    def make_df(name):
        if name=="Airline Performance":
            r = df.groupby(["AIRLINE","AIRLINE_NAME"]).agg(
                Flights=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),Cancelled=("CANCELLED","sum"),
                AvgArr=("ARRIVAL_DELAY","mean"),AvgDep=("DEPARTURE_DELAY","mean"),
                AlDelay=("AIRLINE_DELAY","mean"),WxDelay=("WEATHER_DELAY","mean"),
                LaDelay=("LATE_AIRCRAFT_DELAY","mean"),NaDelay=("AIR_SYSTEM_DELAY","mean")).reset_index()
            r["OTP%"]=(r["OTP"]/r["Flights"]*100).round(2)
            r["Cancel%"]=(r["Cancelled"]/r["Flights"]*100).round(2)
            return r
        elif name=="Airport Performance":
            r = df.groupby("ORIGIN_AIRPORT").agg(Deps=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),
                C=("CANCELLED","sum"),AvgDep=("DEPARTURE_DELAY","mean")).reset_index()
            r["OTP%"]=(r["OTP"]/r["Deps"]*100).round(2)
            r["CR"]=(r["C"]/r["Deps"]*100).round(2)
            return r.merge(airports_raw[["IATA_CODE","AIRPORT","CITY","STATE"]],
                           left_on="ORIGIN_AIRPORT",right_on="IATA_CODE",how="left")
        elif name=="Route Intelligence":
            r = df.groupby(["ORIGIN_AIRPORT","DESTINATION_AIRPORT","ROUTE"]).agg(
                Flights=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),C=("CANCELLED","sum"),
                AvgArr=("ARRIVAL_DELAY","mean"),Dist=("DISTANCE","mean")).reset_index()
            r["OTP%"]=(r["OTP"]/r["Flights"]*100).round(2)
            r["CR"]=(r["C"]/r["Flights"]*100).round(2)
            return r.sort_values("Flights",ascending=False)
        elif name=="Delay Analytics":
            return df[df["CANCELLED"]==0].groupby(["AIRLINE_NAME","MONTH"]).agg(
                Flights=("OTP_FLAG","count"),AvgArr=("ARRIVAL_DELAY","mean"),
                AvgDep=("DEPARTURE_DELAY","mean"),AlDelay=("AIRLINE_DELAY","mean"),
                WxDelay=("WEATHER_DELAY","mean"),LaDelay=("LATE_AIRCRAFT_DELAY","mean"),
                NaDelay=("AIR_SYSTEM_DELAY","mean"),SeDelay=("SECURITY_DELAY","mean")).reset_index()
        elif name=="Cancellation Report":
            r = df[df["CANCELLED"]==1].groupby(
                ["AIRLINE_NAME","ORIGIN_AIRPORT","MONTH","CANCEL_DESC"]).size().reset_index(name="Cancellations")
            return r.sort_values("Cancellations",ascending=False)
        else:
            r = df.groupby(["YEAR","MONTH","MONTH_NAME","SEASON","QUARTER"]).agg(
                Flights=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum"),C=("CANCELLED","sum"),
                D=("ARRIVAL_DELAY","mean"),Dep=("DEPARTURE_DELAY","mean")).reset_index()
            r["OTP%"]=(r["OTP"]/r["Flights"]*100).round(2)
            r["CR"]=(r["C"]/r["Flights"]*100).round(2)
            return r

    edf = make_df(ds)
    if rows > 0: edf = edf.head(rows)

    sec(f"Preview — {ds}","DATA")
    st.info(f"📊  {len(edf):,} rows × {len(edf.columns)} columns")
    st.dataframe(edf.head(100), use_container_width=True, height=340)

    div()
    sec("Download","EXPORT")
    fn = ds.replace(" ","_")
    co1,co2,co3 = st.columns(3)
    with co1:
        st.download_button("⬇️ Download CSV", edf.to_csv(index=False).encode(),
                           f"Emirates_{fn}.csv","text/csv",use_container_width=True)
    with co2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w: edf.to_excel(w,index=False,sheet_name="Emirates")
        st.download_button("⬇️ Download Excel",buf.getvalue(),f"Emirates_{fn}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    with co3:
        st.download_button("⬇️ Download JSON",edf.to_json(orient="records",indent=2).encode(),
                           f"Emirates_{fn}.json","application/json",use_container_width=True)

    div()
    al3 = df.groupby("AIRLINE_NAME").agg(T=("OTP_FLAG","count"),OTP=("OTP_FLAG","sum")).reset_index()
    al3["OTP%"] = al3["OTP"]/al3["T"]*100
    pk = MONTH_MAP.get(int(df.groupby("MONTH")["ARRIVAL_DELAY"].mean().idxmax()),"N/A")
    report = f"""EMIRATES AVIATION INTELLIGENCE PLATFORM
U.S. Airline Performance & Delay Analytics — 2015
Executive Summary Report
{'='*60}

NETWORK OVERVIEW
Total Flights           : {len(df):,}
Airlines                : {df["AIRLINE"].nunique()}
Airports                : {df["ORIGIN_AIRPORT"].nunique()}

PERFORMANCE KPIs
On-Time Performance     : {df["OTP_FLAG"].mean()*100:.2f}%
Avg Arrival Delay       : {df.loc[df["CANCELLED"]==0,"ARRIVAL_DELAY"].mean():.2f} min
Avg Departure Delay     : {df.loc[df["CANCELLED"]==0,"DEPARTURE_DELAY"].mean():.2f} min
Cancellation Rate       : {df["CANCELLED"].mean()*100:.2f}%

KEY INSIGHTS
Best carrier  : {al3.loc[al3["OTP%"].idxmax(),"AIRLINE_NAME"]}
Worst carrier : {al3.loc[al3["OTP%"].idxmin(),"AIRLINE_NAME"]}
Peak delay month: {pk}
Primary delay cause: Late Aircraft cascade

{'='*60}
Generated by Emirates Aviation Intelligence Platform
"""
    st.download_button("⬇️ Download Executive Report (.txt)", report.encode(),
                       "Emirates_Executive_Report_2015.txt","text/plain",use_container_width=True)
