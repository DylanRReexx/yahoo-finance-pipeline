import duckdb

DB_PATH = "data/finance.duckdb"


def crear_gold(conn: duckdb.DuckDBPyConnection):
    """Crea la capa Gold con métricas de negocio agregadas."""

    # Tabla 1: Resumen por ticker
    conn.execute("DROP TABLE IF EXISTS gold_ticker_summary")
    conn.execute("""
        CREATE TABLE gold_ticker_summary AS
        SELECT
            ticker,
            MIN(date)                                   AS first_date,
            MAX(date)                                   AS last_date,
            COUNT(*)                                    AS total_days,
            ROUND(MIN(close), 2)                        AS min_price,
            ROUND(MAX(close), 2)                        AS max_price,
            ROUND(AVG(close), 2)                        AS avg_price,
            ROUND(AVG(daily_return_pct), 4)             AS avg_daily_return,
            ROUND(STDDEV(daily_return_pct), 4)          AS volatility,
            ROUND(SUM(volume) / COUNT(*), 0)            AS avg_daily_volume
        FROM silver_prices
        WHERE daily_return_pct IS NOT NULL
        GROUP BY ticker
        ORDER BY ticker
    """)
    print("Gold ticker_summary creado.")

    # Tabla 2: Señales de trading para ML
    conn.execute("DROP TABLE IF EXISTS gold_ml_features")
    conn.execute("""
        CREATE TABLE gold_ml_features AS
        SELECT
            date,
            ticker,
            close,
            daily_return_pct,
            daily_range,
            avg_volume_20d,
            sma_20,
            sma_50,

            -- Señal: precio sobre o bajo SMA 20
            CASE WHEN close > sma_20 THEN 1 ELSE 0 END AS above_sma20,

            -- Señal: precio sobre o bajo SMA 50
            CASE WHEN close > sma_50 THEN 1 ELSE 0 END AS above_sma50,

            -- Distancia porcentual al SMA 20
            ROUND((close - sma_20) / sma_20 * 100, 4)  AS dist_sma20_pct,

            -- Distancia porcentual al SMA 50
            ROUND((close - sma_50) / sma_50 * 100, 4)  AS dist_sma50_pct,

            -- Target: subió al día siguiente? (1 = sí, 0 = no)
            CASE
                WHEN LEAD(close) OVER (PARTITION BY ticker ORDER BY date) > close
                THEN 1 ELSE 0
            END AS target_up_tomorrow

        FROM silver_prices
        WHERE sma_50 IS NOT NULL
        ORDER BY ticker, date
    """)
    print("Gold ml_features creado.")


if __name__ == "__main__":
    conn = duckdb.connect(DB_PATH)
    crear_gold(conn)
    conn.close()
    print("Transformación Gold completada.")