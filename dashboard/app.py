import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = "data/finance.duckdb"

st.set_page_config(
    page_title="Yahoo Finance Dashboard",
    page_icon="📈",
    layout="wide"
)


@st.cache_data
def cargar_datos():
    conn = duckdb.connect(DB_PATH)
    precios = conn.execute("SELECT * FROM silver_prices ORDER BY ticker, date").df()
    resumen = conn.execute("SELECT * FROM gold_ticker_summary ORDER BY ticker").df()
    conn.close()
    return precios, resumen


# Cargar datos
precios, resumen = cargar_datos()

# Header
st.title("📈 Yahoo Finance Pipeline Dashboard")
st.markdown("Análisis de mercado — AAPL, MSFT, GOOGL, NVDA, JPM, BAC, SPY, QQQ")
st.divider()

# Sidebar
st.sidebar.header("Filtros")
tickers = sorted(precios["ticker"].unique().tolist())
ticker_sel = st.sidebar.selectbox("Seleccioná un activo", tickers)
fecha_min = precios["date"].min()
fecha_max = precios["date"].max()
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=[fecha_min, fecha_max],
    min_value=fecha_min,
    max_value=fecha_max
)

# Filtrar datos
df_filtrado = precios[
    (precios["ticker"] == ticker_sel) &
    (precios["date"] >= pd.Timestamp(fecha_inicio)) &
    (precios["date"] <= pd.Timestamp(fecha_fin))
]

# Fila 1 — Métricas
col1, col2, col3, col4 = st.columns(4)
ultimo = df_filtrado.iloc[-1]
primero = df_filtrado.iloc[0]
retorno_total = round((ultimo["close"] - primero["close"]) / primero["close"] * 100, 2)

col1.metric("Precio actual", f"${ultimo['close']:.2f}")
col2.metric("Retorno en período", f"{retorno_total}%")
col3.metric("Volatilidad promedio", f"{df_filtrado['daily_return_pct'].std():.2f}%")
col4.metric("Volumen promedio", f"{df_filtrado['volume'].mean():,.0f}")

st.divider()

# Fila 2 — Precio + SMA
st.subheader(f"Precio histórico — {ticker_sel}")
fig_precio = go.Figure()
fig_precio.add_trace(go.Scatter(
    x=df_filtrado["date"], y=df_filtrado["close"],
    name="Precio", line=dict(color="#2196F3", width=1.5)
))
fig_precio.add_trace(go.Scatter(
    x=df_filtrado["date"], y=df_filtrado["sma_20"],
    name="SMA 20", line=dict(color="#FF9800", width=1, dash="dash")
))
fig_precio.add_trace(go.Scatter(
    x=df_filtrado["date"], y=df_filtrado["sma_50"],
    name="SMA 50", line=dict(color="#E91E63", width=1, dash="dash")
))
fig_precio.update_layout(height=400, template="plotly_dark")
st.plotly_chart(fig_precio, use_container_width=True)

# Fila 3 — RSI y MACD
col_rsi, col_macd = st.columns(2)

with col_rsi:
    st.subheader("RSI 14")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df_filtrado["date"], y=df_filtrado["rsi_14"],
        name="RSI", line=dict(color="#9C27B0", width=1.5)
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecomprada")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobrevendida")
    fig_rsi.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

with col_macd:
    st.subheader("MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(
        x=df_filtrado["date"], y=df_filtrado["macd"],
        name="MACD", line=dict(color="#00BCD4", width=1.5)
    ))
    fig_macd.add_trace(go.Scatter(
        x=df_filtrado["date"], y=df_filtrado["macd_signal"],
        name="Signal", line=dict(color="#FF5722", width=1, dash="dash")
    ))
    fig_macd.add_bar(
        x=df_filtrado["date"], y=df_filtrado["macd_hist"],
        name="Histograma", marker_color="#4CAF50"
    )
    fig_macd.update_layout(height=300, template="plotly_dark")
    st.plotly_chart(fig_macd, use_container_width=True)

st.divider()

# Fila 4 — Resumen comparativo
st.subheader("Comparación de activos")
fig_resumen = px.bar(
    resumen,
    x="ticker",
    y="avg_daily_return",
    color="volatility",
    color_continuous_scale="RdYlGn",
    title="Retorno diario promedio vs Volatilidad",
    labels={"avg_daily_return": "Retorno diario promedio (%)", "volatility": "Volatilidad"}
)
fig_resumen.update_layout(template="plotly_dark")
st.plotly_chart(fig_resumen, use_container_width=True)