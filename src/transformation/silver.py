import duckdb
import pandas as pd

DB_PATH = "data/finance.duckdb"


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula RSI y MACD por ticker en pandas."""
    resultados = []

    for ticker, grupo in df.groupby("ticker"):
        grupo = grupo.sort_values("date").copy()

        # RSI 14 días
        delta = grupo["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        grupo["rsi_14"] = round(100 - (100 / (1 + rs)), 4)

        # MACD (12, 26, 9)
        ema12 = grupo["close"].ewm(span=12, adjust=False).mean()
        ema26 = grupo["close"].ewm(span=26, adjust=False).mean()
        grupo["macd"] = round(ema12 - ema26, 4)
        grupo["macd_signal"] = round(
            grupo["macd"].ewm(span=9, adjust=False).mean(), 4
        )
        grupo["macd_hist"] = round(grupo["macd"] - grupo["macd_signal"], 4)

        resultados.append(grupo)

    return pd.concat(resultados).sort_values(["ticker", "date"]).reset_index(drop=True)


def crear_silver(conn: duckdb.DuckDBPyConnection):
    """Crea la capa Silver con datos limpios y métricas básicas."""

    # Cargar bronze
    df = conn.execute("SELECT * FROM bronze_prices ORDER BY ticker, date").df()

    # Calcular indicadores
    df = calcular_indicadores(df)

    # Crear tabla silver con SQL
    conn.execute("DROP TABLE IF EXISTS silver_prices")
    conn.execute("""
        CREATE TABLE silver_prices AS
        SELECT
            date,
            ticker,
            open,
            high,
            low,
            close,
            volume,

            -- Retorno diario
            ROUND(
                (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date))
                / LAG(close) OVER (PARTITION BY ticker ORDER BY date) * 100, 4
            ) AS daily_return_pct,

            -- Rango diario
            ROUND(high - low, 4) AS daily_range,

            -- Volumen promedio 20 días
            ROUND(
                AVG(volume) OVER (
                    PARTITION BY ticker ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ), 2
            ) AS avg_volume_20d,

            -- SMA 20 y 50
            ROUND(
                AVG(close) OVER (
                    PARTITION BY ticker ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ), 4
            ) AS sma_20,
            ROUND(
                AVG(close) OVER (
                    PARTITION BY ticker ORDER BY date
                    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
                ), 4
            ) AS sma_50,

            -- Indicadores calculados en pandas
            rsi_14,
            macd,
            macd_signal,
            macd_hist

        FROM df
        WHERE close IS NOT NULL
        ORDER BY ticker, date
    """)

    total = conn.execute("SELECT COUNT(*) FROM silver_prices").fetchone()[0]
    print(f"Silver creado: {total} filas")


if __name__ == "__main__":
    conn = duckdb.connect(DB_PATH)
    crear_silver(conn)
    conn.close()
    print("Transformación Silver completada.")