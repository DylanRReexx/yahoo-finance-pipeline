import duckdb

DB_PATH = "data/finance.duckdb"


def crear_silver(conn: duckdb.DuckDBPyConnection):
    """Crea la capa Silver con datos limpios y métricas básicas."""
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

            -- Precio promedio móvil 20 días
            ROUND(
                AVG(close) OVER (
                    PARTITION BY ticker ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ), 4
            ) AS sma_20,

            -- Precio promedio móvil 50 días
            ROUND(
                AVG(close) OVER (
                    PARTITION BY ticker ORDER BY date
                    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
                ), 4
            ) AS sma_50

        FROM bronze_prices
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