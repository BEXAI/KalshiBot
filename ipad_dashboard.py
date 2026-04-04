import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(
    page_title="KalshiBot Master Console",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS targeting iPad/M5 responsive structures
st.markdown("""
<style>
    .big-font { font-size:30px !important; font-weight: bold; }
    .stMetric { border-radius: 8px; box-shadow: 1px 1px 5px rgba(0,0,0,0.2); padding: 15px; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🤖 BEXAI / KalshiBot Autonomous Hub")
st.markdown("**(iPad M5 Local Stream Interface)**")

@st.cache_data(ttl=5) # 5-second aggressive cache pulling
def load_data():
    try:
        with open("kalshi_trades.jsonlines", "r") as f:
            lines = f.readlines()
            
        data = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            
            # Identify Strategy Route
            strategy = item.get("strategy_type", "llm_agentic_prediction")
            tick_market = item.get("market", "Unknown")
            ts = item.get("timestamp", time.time())
            
            # Format rows securely into Eastern Standard Time (EST)
            dt_est = pd.to_datetime(ts, unit='s').tz_localize('UTC').tz_convert('US/Eastern')
            
            row = {
                "Timestamp": dt_est.replace(tzinfo=None), # Render naive for clean Streamlit alignment
                "Market": tick_market,
                "Strategy": strategy.upper(),
            }
            
            # Fast-Path Weather Mapping
            if strategy == "hybrid_quant_weather":
                weather = item.get("weather_sweep", {})
                row["Status"] = weather.get("status", "skipped")
                row["Edge"] = round(weather.get("edge", 0) * 100, 2)
                row["Action"] = f"{weather.get('side', 'N/A').upper()} @ {weather.get('amount', 0)}"
                
            # LLM Debate Mapping
            else:
                debate = item.get("debate_inference", {})
                row["Status"] = debate.get("decision", "SKIP")
                row["Edge"] = round(debate.get("edge", 0) * 100, 2)
                row["Action"] = f"${debate.get('trade_amount', 0)}"
                
            data.append(row)
            
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values("Timestamp", ascending=False)
        return df
    except Exception as e:
        return pd.DataFrame()

# Natively read the data
df = load_data()

# Render High-Level Metics
col1, col2, col3 = st.columns(3)
if not df.empty:
    executions = df[df["Status"].isin(["TRADE", "PAPER_TRADE", "weather_trade_executed"])]
    col1.metric("Live Executions", len(executions))
    col2.metric("Total Events Evaluated", len(df))
    
    highest_edge = df["Edge"].max() if "Edge" in df else 0
    col3.metric("Highest Structural Edge", f"{highest_edge}%")
else:
    col1.metric("Live Executions", 0)
    col2.metric("Total Events Evaluated", 0)
    col3.metric("System Mode", "Connecting...")

st.divider()

# Rendering Live Stream Data Frame mapped natively for horizontal finger scrolling
st.subheader("📡 Live Pipeline Sequence")
if not df.empty:
    st.dataframe(
        df,
        column_config={
            "Timestamp": st.column_config.DatetimeColumn("EST Time", format="hh:mm:ss a"),
            "Edge": st.column_config.NumberColumn(format="%.2f%%")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Awaiting Kalshi Execution Pipeline Logs. Launch `bash start_daemon.sh`!")

# Provide simple auto-refresh mechanism for iPad Safari
st.button("🔄 Force Interface Sync")
