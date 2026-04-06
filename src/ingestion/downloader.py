import yfinance as yf
import duckdb
import pandas as pd
from datetime import datetime

# Activos a descargar
TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "JPM", "BAC", "SPY", "QQQ"]

# Configuración
DB_PATH = "data/finance.duckdb"
START_DATE = "2018-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")


def descargar_datos(tickers: list, start: str, end: str) -> pd.DataFrame:
    """Descarga datos históricos de Yahoo Finance."""
    print(f"Descargando datos para: {tickers}")
    df = yf.download(tickers, start=start, end=end, auto_adjust=True)
    df = df.stack(level=1).reset_index()
    df.columns = ["date", "ticker", "close", "high", "low", "open", "volume"]
    df = df[["date", "ticker", "open", "high", "low", "close", "volume"]]
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    print(f"Datos descargados: {len(df)} filas")
    return df


def guardar_bronze(df: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Guarda los datos crudos en la capa Bronze."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze_prices (
            date        DATE,
            ticker      VARCHAR,
            open        DOUBLE,
            high        DOUBLE,
            low         DOUBLE,
            close       DOUBLE,
            volume      BIGINT,
            loaded_at   TIMESTAMP DEFAULT current_timestamp
        )
    """)
    conn.execute("DELETE FROM bronze_prices")
    conn.execute("INSERT INTO bronze_prices SELECT *, current_timestamp FROM df")
    total = conn.execute("SELECT COUNT(*) FROM bronze_prices").fetchone()[0]
    print(f"Bronze cargado: {total} filas")


if __name__ == "__main__":
    conn = duckdb.connect(DB_PATH)
    df = descargar_datos(TICKERS, START_DATE, END_DATE)
    guardar_bronze(df, conn)
    conn.close()
    print("Ingesta completada.")