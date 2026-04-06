import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Power Consumption Digital Twin", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

body, [class^="css"], [class*=" css"] {
    color: #cbd5e1 !important;
    background-color: #0b1120 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

section[data-testid="stSidebar"] {
    background: #09101f !important;
}

.stApp {
    background: linear-gradient(135deg, #08111f 0%, #0f172a 100%);
}

.metric-card {
    background: #111827;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 16px;
}

.metric-card .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-bottom: 8px;
}

.metric-card .value {
    font-size: 32px;
    font-weight: 700;
    line-height: 1;
    color: #f8fafc;
}

.metric-card .sub {
    color: #94a3b8;
    margin-top: 10px;
    font-size: 12px;
}

.metric-card .change {
    margin-top: 8px;
    font-size: 12px;
}

.card-panel {
    background: rgba(15, 23, 42, 0.82);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 22px;
    padding: 22px;
}

.section-title {
    font-size: 19px;
    font-weight: 700;
    margin-bottom: 6px;
}

.section-subtitle {
    color: #94a3b8;
    margin-bottom: 18px;
    font-size: 13px;
}

.toggle-box {
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 14px 16px;
    background: #0f172a;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    margin-bottom: 12px;
}

.toggle-label {
    color: #cbd5e1;
    font-size: 13px;
}

.factor-bar-wrap {
    width: 100%;
    height: 10px;
    background: rgba(148, 163, 184, 0.10);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 8px;
}

.factor-bar {
    height: 100%;
    border-radius: 999px;
}

.factor-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    margin-bottom: 14px;
}

.factor-title {
    color: #94a3b8;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

.log-card {
    background: #0f172a;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 20px;
    padding: 16px;
    max-height: 350px;
    overflow-y: auto;
}

.log-entry {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #cbd5e1;
    margin-bottom: 8px;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #7dd3fc;
    font-size: 0.85rem;
    font-weight: 600;
}

.separator {
    height: 1px;
    background: rgba(148, 163, 184, 0.10);
    margin: 24px 0;
}

</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

BUILDING_BASE = {
    "techpark": 820,
    "hospital": 960,
    "datacenter": 1180,
    "mall": 740,
    "office": 680,
}
DAY_FACTOR = {"weekday": 1.0, "weekend": 0.58, "holiday": 0.45, "peak": 1.18}
HOUR_CURVE = [0.55, 0.52, 0.50, 0.49, 0.50, 0.55, 0.65, 0.80, 0.92, 0.98, 1.02, 1.05, 1.04, 1.05, 1.08, 1.10, 1.15, 1.10, 1.02, 0.95, 0.88, 0.80, 0.72, 0.62]

DEFAULT_OVERVIEW = {
    "current_load": "847 kW",
    "hybrid_accuracy": "96.4%",
    "peak_forecast": "1.24 MW",
    "cost_saving": "₹3.1 L",
    "weather_contribution": "34%",
    "anomalies_today": "2",
}

OVERVIEW_SERIES = {
    "labels": [f"{str(i).zfill(2)}:00" for i in range(24)],
    "actual": [420, 395, 380, 370, 365, 385, 430, 540, 680, 760, 820, 870, 880, 875, 895, 910, 1050, 980, 920, 850, 770, 680, 580, 490],
    "hybrid": [415, 390, 378, 368, 362, 382, 428, 537, 676, 756, 816, 864, 876, 870, 890, 904, 1042, 974, 916, 844, 766, 675, 576, 486],
    "baseline": [440, 415, 400, 388, 380, 395, 450, 570, 710, 800, 870, 930, 950, 940, 970, 995, 1130, 1060, 990, 920, 840, 740, 640, 550],
}

ERROR_SERIES = lambda: {
    "days": [f"D{i+1}" for i in range(30)],
    "lstm": [14 + np.sin(i * 0.4) * 4 + np.random.rand() * 3 for i in range(30)],
    "arima": [10 + np.sin(i * 0.35) * 3 + np.random.rand() * 2 for i in range(30)],
    "xgb": [7 + np.sin(i * 0.3) * 2 + np.random.rand() * 1.5 for i in range(30)],
    "hybrid": [3 + np.sin(i * 0.25) * 0.8 + np.random.rand() * 0.6 for i in range(30)],
}

RADAR_SERIES = {
    "labels": ["Accuracy", "Weather", "Anomaly", "Speed", "Scalability", "Efficiency"],
    "baseline": [60, 30, 45, 85, 70, 75],
    "xgboost": [78, 68, 72, 92, 80, 82],
    "hybrid": [96, 90, 88, 72, 85, 80],
}

IMPORTANCE_SERIES = {
    "features": ["Temperature", "Hour-of-day", "Humidity", "Solar GHI", "Day-of-week", "Occupancy", "HDD/CDD", "Wind speed"],
    "scores": [34, 22, 14, 11, 9, 6, 3, 1],
}

GAP_SERIES = {
    "events": ["Normal", "Heatwave", "Monsoon", "Cold front", "Holiday", "Low GHI"],
    "baseline": [8.1, 24.3, 19.7, 14.2, 12.8, 18.5],
    "hybrid": [2.8, 4.1, 3.9, 3.2, 3.5, 4.8],
}

WEEKLY_SERIES = {
    "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "techpark": [820, 845, 860, 855, 830, 410, 290],
    "hospital": [960, 970, 955, 965, 960, 950, 940],
}

DISTRIBUTION_SERIES = {
    "labels": ["HVAC", "IT/Servers", "Lighting", "Elevators", "Misc"],
    "values": [42, 28, 12, 8, 10],
}

C = {
    "actual": "#38bdf8",
    "hybrid": "#c084fc",
    "baseline": "#64748b",
    "orange": "#fb923c",
    "green": "#34d399",
    "yellow": "#fbbf24",
    "purple": "#c084fc",
    "teal": "#2dd4bf",
    "red": "#f87171",
}

if "scenario_log" not in st.session_state:
    st.session_state.scenario_log = ["[--:--] Log initialised. Set a scenario and hit Run Scenario."]


def compute_load(
    building: str,
    day: str,
    temp: float,
    humid: float,
    wind: float,
    wind_dir: float,
    occ: float,
    solar: float,
    hour: int,
    hvac: bool,
    servers: bool,
    ev: bool,
    solar_online: bool,
):
    base = BUILDING_BASE[building] * DAY_FACTOR[day]
    base *= HOUR_CURVE[hour]

    if temp > 28:
        temp_effect = np.power(temp - 28, 1.6) * 9.5
    elif temp < 20:
        temp_effect = (20 - temp) * 5.0
    else:
        temp_effect = 0.0

    humid_effect = max(0.0, humid - 60.0) * 1.8
    wind_effect = -(min(18.0, (wind - 12.0) * 1.4) if wind > 12.0 else 0.0)
    wind_dir_effect = np.cos((wind_dir - 180.0) / 180.0 * np.pi) * 2.4
    occ_effect = base * (occ / 100.0) * 0.35
    solar_offset = solar * 0.18 if solar_online else 0.0
    ev_load = 85.0 if ev else 0.0
    hvac_mul = 1.0 if hvac else 0.45
    server_mul = 1.0 if servers else 0.3

    hvac_load = (base * 0.42 + temp_effect + humid_effect - wind_effect + wind_dir_effect) * hvac_mul
    it_load = base * 0.28 * server_mul
    light_load = base * 0.12 * (occ / 100.0)
    total = round(hvac_load + it_load + light_load + occ_effect * 0.15 + ev_load - solar_offset)

    power_lag_1 = max(80, round(base * 0.96))
    power_lag_24 = max(70, round(base * (0.92 if day == "weekday" else 0.84)))
    dayofweek = 3 if day == "weekday" else 5 if day == "weekend" else 6 if day == "holiday" else 2
    month = datetime.now().month

    baseline_pred = round(
        0.52 * power_lag_1
        + 0.27 * power_lag_24
        + 1.8 * hour
        + 4.5 * dayofweek
        + 2.1 * month
        + 0.13 * temp
        + 0.09 * humid
    )

    weather_adjust = (
        (temp - 28) * 2.3 if temp > 28 else (20 - temp) * 1.8 if temp < 20 else 0.0
    ) + max(0.0, (humid - 55.0) * 1.4) + max(0.0, (wind - 10.0) * 0.4)
    weather_adjust += 4.0 if abs((wind_dir + 180.0) % 360.0 - 180.0) < 45.0 else -1.0
    hybrid_pred = round(baseline_pred + weather_adjust * 0.83)

    return {
        "total": total,
        "hvac_load": round(hvac_load),
        "it_load": round(it_load),
        "light_load": round(light_load),
        "solar_offset": round(solar_offset),
        "ev_load": round(ev_load),
        "weather_stress": round(abs(temp_effect + humid_effect)),
        "baseline_pred": baseline_pred,
        "hybrid_pred": hybrid_pred,
        "power_lag_1": power_lag_1,
        "power_lag_24": power_lag_24,
        "hour": hour,
        "dayofweek": dayofweek,
        "month": month,
    }


def make_overview_chart():
    df = pd.DataFrame(OVERVIEW_SERIES)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["labels"], y=[v * 1.04 for v in df["hybrid"]], mode="lines", line=dict(color="rgba(56,189,248,0.0)"), showlegend=False, hoverinfo='skip', fill='tonexty', fillcolor='rgba(56,189,248,0.12)'))
    fig.add_trace(go.Scatter(x=df["labels"], y=[v * 0.96 for v in df["hybrid"]], mode="lines", line=dict(color="rgba(56,189,248,0.0)"), fill='tonexty', fillcolor='rgba(56,189,248,0.12)', showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=df["labels"], y=df["baseline"], mode="lines", line=dict(color=C["baseline"], dash='dash', width=1.8), name='Baseline'))
    fig.add_trace(go.Scatter(x=df["labels"], y=df["hybrid"], mode="lines", line=dict(color=C["hybrid"], width=2.5), name='Hybrid'))
    fig.add_trace(go.Scatter(x=df["labels"], y=df["actual"], mode="lines+markers", line=dict(color=C["actual"], width=2.8), marker=dict(size=5, color=C["actual"]), name='Actual'))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h', yanchor='bottom', y=1.02, x=0.01))
    fig.update_xaxes(showgrid=True, gridcolor='rgba(148,163,184,0.08)', tickfont=dict(color='#94a3b8'))
    fig.update_yaxes(showgrid=True, gridcolor='rgba(148,163,184,0.08)', tickfont=dict(color='#94a3b8'), tickformat='~s')
    return fig


def make_weekly_chart():
    df = pd.DataFrame(WEEKLY_SERIES)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["days"], y=df["techpark"], name="Tech Park", marker_color='rgba(56,189,248,0.7)', marker_line_width=0, width=0.4))
    fig.add_trace(go.Bar(x=df["days"], y=df["hospital"], name="Hospital", marker_color='rgba(192,132,252,0.7)', marker_line_width=0, width=0.4))
    fig.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    fig.update_yaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)', tickformat='~s')
    return fig


def make_breakdown_chart():
    fig = go.Figure(data=[go.Pie(labels=DISTRIBUTION_SERIES["labels"], values=DISTRIBUTION_SERIES["values"], hole=0.62, marker=dict(colors=[C["orange"], C["actual"], C["yellow"], C["teal"], C["baseline"]], line=dict(color='rgba(0,0,0,0)', width=0)))])
    fig.update_traces(textinfo='percent+label', textfont=dict(color='#e2e8f0', size=10))
    fig.update_layout(showlegend=True, legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h', y=-0.15), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=10))
    return fig


def make_error_chart():
    series = ERROR_SERIES()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series['days'], y=series['lstm'], mode='lines', line=dict(color=C['baseline'], dash='dash'), name='Baseline LSTM'))
    fig.add_trace(go.Scatter(x=series['days'], y=series['arima'], mode='lines', line=dict(color=C['yellow']), name='ARIMA + Weather'))
    fig.add_trace(go.Scatter(x=series['days'], y=series['xgb'], mode='lines', line=dict(color=C['orange']), name='XGBoost'))
    fig.add_trace(go.Scatter(x=series['days'], y=series['hybrid'], mode='lines', line=dict(color=C['actual'], width=2.5), name='Hybrid'))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    fig.update_yaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)', ticksuffix='%')
    return fig


def make_radar_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=RADAR_SERIES['baseline'], theta=RADAR_SERIES['labels'], fill='toself', name='Baseline LSTM', line=dict(color=C['baseline'])))
    fig.add_trace(go.Scatterpolar(r=RADAR_SERIES['xgboost'], theta=RADAR_SERIES['labels'], fill='toself', name='XGBoost', line=dict(color=C['orange'])))
    fig.add_trace(go.Scatterpolar(r=RADAR_SERIES['hybrid'], theta=RADAR_SERIES['labels'], fill='toself', name='Hybrid', line=dict(color=C['actual'])))
    fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(showline=False, gridcolor='rgba(148,163,184,0.08)', tickfont=dict(color='#94a3b8')),
                      angularaxis=dict(tickfont=dict(color='#94a3b8'))), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10))
    return fig


def make_temp_corr_chart():
    temps = np.arange(14, 49)
    load = [320 + (20 - t) * 8 + np.random.rand() * 20 if t < 20 else 380 + (t - 20) * 12 + np.random.rand() * 25 if t < 28 else 476 + np.power(t - 28, 1.8) * 18 + np.random.rand() * 30 for t in temps]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temps, y=load, mode='markers', marker=dict(color=C['actual'], size=7), name='Observed'))
    fig.add_trace(go.Scatter(x=temps, y=[round(v * 0.998) for v in load], mode='lines', line=dict(color=C['green'], width=2), name='Hybrid fit'))
    fig.add_trace(go.Scatter(x=temps, y=[round(v * 0.98 + 35) for v in load], mode='lines', line=dict(color=C['baseline'], dash='dash', width=1.7), name='Baseline fit'))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(title_text='Temperature (°C)', tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    fig.update_yaxes(title_text='Power Load (kW)', tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    return fig


def make_importance_chart():
    fig = go.Figure(go.Bar(x=IMPORTANCE_SERIES['scores'], y=IMPORTANCE_SERIES['features'], orientation='h', marker_color=['rgba(248,113,113,0.7)', 'rgba(56,189,248,0.7)', 'rgba(45,212,191,0.7)', 'rgba(251,191,36,0.7)', 'rgba(192,132,252,0.7)', 'rgba(52,211,153,0.7)', 'rgba(99,102,241,0.6)', 'rgba(71,85,105,0.5)']))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=10), showlegend=False)
    fig.update_xaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)', ticksuffix='%')
    fig.update_yaxes(tickfont=dict(color='#94a3b8'))
    return fig


def make_gap_chart():
    fig = go.Figure()
    fig.add_trace(go.Bar(x=GAP_SERIES['events'], y=GAP_SERIES['baseline'], name='Baseline error', marker_color='rgba(248,113,113,0.5)'))
    fig.add_trace(go.Bar(x=GAP_SERIES['events'], y=GAP_SERIES['hybrid'], name='Hybrid error', marker_color='rgba(56,189,248,0.6)'))
    fig.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    fig.update_yaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)', ticksuffix='%')
    return fig


def make_heatmap():
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    values = []
    for h in range(24):
        row = []
        for m in range(12):
            base = 400
            hour_factor = 1.5 + (0.5 if h in [14, 15] else 0) if 9 <= h <= 19 else 0.6
            month_factor = [0.7,0.75,0.85,1.0,1.2,1.4,1.45,1.4,1.15,0.95,0.8,0.7][m]
            row.append(round(base * hour_factor * month_factor + np.random.rand() * 50))
        values.append(row)
    fig = go.Figure(data=go.Heatmap(z=values, x=months, y=[f"{str(h).zfill(2)}:00" for h in range(24)], colorscale='Turbo', hoverongaps=False))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=60, r=20, t=20, b=20), xaxis_title='', yaxis_title='Hour')
    fig.update_xaxes(tickfont=dict(color='#94a3b8'))
    fig.update_yaxes(tickfont=dict(color='#94a3b8'))
    return fig


def make_twin_profile_chart(r):
    labels = [f"{str(i).zfill(2)}:00" for i in range(24)]
    scale_base = HOUR_CURVE[r['hour']]
    baseline_curve = [round(r['baseline_pred'] * (curve / scale_base)) for curve in HOUR_CURVE]
    hybrid_curve = [round(r['hybrid_pred'] * (curve / scale_base)) for curve in HOUR_CURVE]
    twin_curve = [round(r['total'] * (curve / scale_base)) for curve in HOUR_CURVE]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=baseline_curve, mode='lines', name='Baseline Model', line=dict(color=C['baseline'], width=2)))
    fig.add_trace(go.Scatter(x=labels, y=hybrid_curve, mode='lines', name='Hybrid Model', line=dict(color=C['hybrid'], width=2)))
    fig.add_trace(go.Scatter(x=labels, y=twin_curve, mode='lines', name='Current Twin', line=dict(color=C['actual'], width=2, dash='dash')))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=20), legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)')
    fig.update_yaxes(tickfont=dict(color='#94a3b8'), gridcolor='rgba(148,163,184,0.08)', tickformat='~s')
    return fig


def format_factor(text, value, total):
    width = min(100, int(abs(value) / total * 100)) if total > 0 else 0
    color = C['orange'] if text == 'HVAC Load' else C['actual'] if text == 'IT / Servers' else C['yellow'] if text == 'Lighting' else C['green'] if text == 'Solar Offset' else C['purple'] if text == 'EV Charging' else C['red']
    return f"<div class='factor-row'><div><div class='factor-title'>{text}</div><div class='factor-bar-wrap'><div class='factor-bar' style='width:{width}%;background:{color}'></div></div></div><div style='text-align:right;min-width:78px;color:#cbd5e1;font-size:12px'>{value:+d} kW</div></div>"


def render_metric_card(label, value, suffix='', sub='', change_text='', change_color='#94a3b8'):
    st.markdown(f"""
    <div class='metric-card'>
        <div class='label'>{label}</div>
        <div class='value'>{value}{suffix}</div>
        <div class='sub'>{sub}</div>
        <div class='change' style='color:{change_color}'>{change_text}</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.markdown("<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:22px'><div><h1 style='margin:0'>Power Consumption Intelligence Platform</h1><p style='margin:4px 0 0;color:#94a3b8'>Hybrid predictive model · Weather-aware · Digital twin simulation</p></div><div class='live-badge'>● LIVE MODEL</div></div>", unsafe_allow_html=True)

    tabs = st.tabs(["Overview", "Model Comparison", "Weather Impact", "Digital Twin"])

    with tabs[0]:
        cols = st.columns(3)
        with cols[0]:
            render_metric_card("Current Load", "847", " kW", "Tech park · Building A–D", "▲ +6.2% from yesterday", C['orange'])
            render_metric_card("Peak Forecast", "1.24", " MW", "Today 14:00–16:00", "▲ Heat wave effect", C['orange'])
        with cols[1]:
            render_metric_card("Hybrid Accuracy", "96.4", "%", "7-day rolling MAPE", "▼ Error reduced 41%", C['green'])
            render_metric_card("Cost Saving", "₹3.1", " L", "vs baseline model / mo", "▼ Optimised usage", C['green'])
        with cols[2]:
            render_metric_card("Weather Contribution", "34", "%", "Of current variance", "● Temp 33°C · Humid 74%", C['yellow'])
            render_metric_card("Anomalies Today", "2", "", "Unusual spikes detected", "▲ HVAC surge 09:15", C['orange'])

        st.markdown("<div class='card-panel'><div class='section-title'>24-Hour Power Consumption — Predicted vs Actual</div><div class='section-subtitle'>Baseline LSTM · Hybrid model · Actual readings · Weather-adjusted forecast</div>", unsafe_allow_html=True)
        st.plotly_chart(make_overview_chart(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<div class='card-panel'><div class='section-title'>Weekly Pattern</div><div class='section-subtitle'>Mon–Sun average by building type</div>", unsafe_allow_html=True)
            st.plotly_chart(make_weekly_chart(), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown("<div class='card-panel'><div class='section-title'>Consumption Breakdown</div><div class='section-subtitle'>By system category</div>", unsafe_allow_html=True)
            st.plotly_chart(make_breakdown_chart(), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            render_metric_card("Baseline LSTM", "82.1", "%", "Historical only", "", C['baseline'])
            render_metric_card("ARIMA + Weather", "87.5", "%", "Statistical + weather", "", C['yellow'])
        with col2:
            render_metric_card("XGBoost", "91.8", "%", "Multi-feature gradient", "", C['orange'])
            render_metric_card("Hybrid (LSTM+XGB+Weather)", "96.4", "%", "Full fusion model ✦", "", C['actual'])

        st.markdown("<div class='card-panel'><div class='section-title'>Prediction Error Comparison — MAPE Over 30 Days</div><div class='section-subtitle'>Lower is better. Hybrid model consistently outperforms individual approaches.</div>", unsafe_allow_html=True)
        st.plotly_chart(make_error_chart(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='card-panel'><div class='section-title'>Model Performance Radar</div><div class='section-subtitle'>Accuracy · Speed · Weather sensitivity · Anomaly detection</div>", unsafe_allow_html=True)
            st.plotly_chart(make_radar_chart(), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='card-panel'><div class='section-title'>Detailed Metrics</div><div class='section-subtitle'>MAPE · RMSE · R² · Inference time</div>", unsafe_allow_html=True)
            st.markdown("""
                <table style='width:100%; border-collapse:collapse; color:#cbd5e1;'>
                    <thead><tr><th style='text-align:left;padding:10px 0 8px 0;color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:1px'>Model</th><th style='text-align:right;padding:10px 0 8px 0;color:#94a3b8;font-size:11px'>MAPE</th><th style='text-align:right;padding:10px 0 8px 0;color:#94a3b8;font-size:11px'>RMSE</th><th style='text-align:right;padding:10px 0 8px 0;color:#94a3b8;font-size:11px'>R²</th><th style='text-align:right;padding:10px 0 8px 0;color:#94a3b8;font-size:11px'>Inference</th></tr></thead>
                    <tbody>
                        <tr><td style='padding:8px 0;'>Baseline LSTM</td><td style='padding:8px 0;text-align:right;color:#f87171'>17.9%</td><td style='padding:8px 0;text-align:right'>142 kW</td><td style='padding:8px 0;text-align:right'>0.81</td><td style='padding:8px 0;text-align:right'>12ms</td></tr>
                        <tr><td style='padding:8px 0;'>ARIMA + Weather</td><td style='padding:8px 0;text-align:right;color:#f87171'>12.5%</td><td style='padding:8px 0;text-align:right'>98 kW</td><td style='padding:8px 0;text-align:right'>0.87</td><td style='padding:8px 0;text-align:right'>8ms</td></tr>
                        <tr><td style='padding:8px 0;'>XGBoost Multi</td><td style='padding:8px 0;text-align:right;color:#38bdf8'>8.2%</td><td style='padding:8px 0;text-align:right'>73 kW</td><td style='padding:8px 0;text-align:right'>0.92</td><td style='padding:8px 0;text-align:right'>4ms</td></tr>
                        <tr><td style='padding:8px 0;'><strong>Hybrid Fusion</strong></td><td style='padding:8px 0;text-align:right;color:#34d399'>3.6%</td><td style='padding:8px 0;text-align:right'>31 kW</td><td style='padding:8px 0;text-align:right'>0.964</td><td style='padding:8px 0;text-align:right'>18ms</td></tr>
                    </tbody>
                </table>
                <div class='metric-card' style='margin-top:16px;'>The Hybrid model reduces MAPE by <strong>79.9%</strong> vs baseline and cuts RMSE from 142kW to 31kW — translating to significantly tighter peak load scheduling and grid optimisation.</div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("<div class='card-panel'><div class='section-title'>Temperature vs Power Consumption Correlation</div><div class='section-subtitle'>Cooling degree days drive HVAC load non-linearly above 28°C threshold</div>", unsafe_allow_html=True)
        st.plotly_chart(make_temp_corr_chart(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='card-panel'><div class='section-title'>Weather Features — Importance Score</div><div class='section-subtitle'>Impact contribution to prediction variance</div>", unsafe_allow_html=True)
            st.plotly_chart(make_importance_chart(), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='card-panel'><div class='section-title'>Prediction Gap: Baseline vs Hybrid</div><div class='section-subtitle'>Error during extreme weather events</div>", unsafe_allow_html=True)
            st.plotly_chart(make_gap_chart(), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-panel'><div class='section-title'>Seasonal & Hourly Weather-Load Heatmap</div><div class='section-subtitle'>Darker = higher load · Month (x) × Hour of day (y)</div>", unsafe_allow_html=True)
        st.plotly_chart(make_heatmap(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        left, right = st.columns([0.7, 1.3])
        with left:
            st.markdown("<div class='card-panel'><div class='section-title'>⚙ Scenario Parameters</div></div>", unsafe_allow_html=True)
            building = st.selectbox("Building / Facility type", ["techpark", "hospital", "datacenter", "mall", "office"], format_func=lambda v: {"techpark":"Tech Park (4 buildings)","hospital":"Hospital Complex","datacenter":"Data Centre","mall":"Shopping Mall","office":"Corporate Office Tower"}[v])
            day = st.selectbox("Day type", ["weekday", "weekend", "holiday", "peak"], format_func=lambda v: {"weekday":"Weekday (standard)","weekend":"Weekend","holiday":"Public holiday","peak":"Peak demand day"}[v])
            temp = st.slider("Temperature (°C)", 15, 48, 33)
            humid = st.slider("Humidity (%)", 10, 100, 74)
            wind = st.slider("Wind speed (m/s)", 0, 25, 8)
            wind_dir = st.slider("Wind direction (°)", 0, 360, 180)
            occ = st.slider("Occupancy (%)", 0, 100, 85)
            solar = st.slider("Solar irradiance (W/m²)", 0, 1000, 620)
            hour = st.slider("Hour of day", 0, 23, 14)
            hvac = st.checkbox("HVAC — full operation", True)
            servers = st.checkbox("Server rooms active", True)
            ev = st.checkbox("EV charging stations", False)
            solar_online = st.checkbox("Solar panels online", True)
            if st.button("▶ Run Scenario & Log"):
                scenario = compute_load(building, day, temp, humid, wind, wind_dir, occ, solar, hour, hvac, servers, ev, solar_online)
                ts = datetime.now().strftime("%H:%M")
                flags = " ".join(["HVAC" if hvac else "no-HVAC", "+EV" if ev else "", "solar" if solar_online else "no-solar"]).strip()
                st.session_state.scenario_log.insert(0, f"[{ts}] {building} · {scenario['total']} kW · baseline {scenario['baseline_pred']} kW · hybrid {scenario['hybrid_pred']} kW · {temp}°C · occ {occ}% · {str(hour).zfill(2)}:00 · {flags}")
            if st.button("✕ Clear Log"):
                st.session_state.scenario_log = ["[--:--] Log cleared."]

        scenario = compute_load(building, day, temp, humid, wind, wind_dir, occ, solar, hour, hvac, servers, ev, solar_online)
        with right:
            st.markdown("<div class='card-panel'><div class='section-title'>Hybrid AI Twin Prediction</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex;align-items:flex-end;gap:16px'><div style='font-size:48px;font-weight:700;color:#38bdf8'>{scenario['hybrid_pred']}</div><div style='color:#94a3b8'>kW instantaneous load</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='margin-top:10px;color:#94a3b8;font-size:13px'>Baseline model: <strong style='color:#f8fafc'>{scenario['baseline_pred']} kW</strong></div>")
            delta_pct = round((scenario['hybrid_pred'] - scenario['baseline_pred']) / max(1, scenario['baseline_pred']) * 100, 1)
            delta_color = '#f87171' if delta_pct > 4 else '#34d399' if delta_pct < -3 else '#fbbf24'
            st.markdown(f"<div style='margin-top:10px;color:{delta_color};font-size:13px'>{'▲' if delta_pct >= 0 else '▼'} {abs(delta_pct)}% from baseline model</div>", unsafe_allow_html=True)

            totals = [abs(scenario['hvac_load']), abs(scenario['it_load']), abs(scenario['light_load']), abs(scenario['solar_offset']), abs(scenario['ev_load']), abs(scenario['weather_stress'])]
            max_total = max(max(totals), 1)
            st.markdown(format_factor('HVAC Load', scenario['hvac_load'], max_total), unsafe_allow_html=True)
            st.markdown(format_factor('IT / Servers', scenario['it_load'], max_total), unsafe_allow_html=True)
            st.markdown(format_factor('Lighting', scenario['light_load'], max_total), unsafe_allow_html=True)
            st.markdown(format_factor('Solar Offset', -scenario['solar_offset'], max_total), unsafe_allow_html=True)
            st.markdown(format_factor('EV Charging', scenario['ev_load'], max_total), unsafe_allow_html=True)
            st.markdown(format_factor('Weather Stress', scenario['weather_stress'], max_total), unsafe_allow_html=True)

            st.markdown("<div class='card-panel'><div class='section-title'>Hourly Profile — Today's Scenario</div></div>", unsafe_allow_html=True)
            st.plotly_chart(make_twin_profile_chart(scenario), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-subtitle' style='margin-top:14px'>Scenario Log</div>", unsafe_allow_html=True)
            st.markdown("<div class='log-card'>" + "<br>".join([f"<div class='log-entry'>{entry}</div>" for entry in st.session_state.scenario_log[:12]]) + "</div>", unsafe_allow_html=True)


if __name__ == '__main__':
    main()
