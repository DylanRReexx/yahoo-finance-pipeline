import duckdb
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DB_PATH = "data/finance.duckdb"


def cargar_features(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Carga los features desde la capa Gold."""
    df = conn.execute("""
        SELECT
            date,
            ticker,
            daily_return_pct,
            daily_range,
            avg_volume_20d,
            dist_sma20_pct,
            dist_sma50_pct,
            above_sma20,
            above_sma50,
            target_up_tomorrow
        FROM gold_ml_features
        WHERE target_up_tomorrow IS NOT NULL
    """).df()

    # Agregar RSI y MACD desde Silver
    df_silver = conn.execute("""
        SELECT date, ticker, rsi_14, macd, macd_signal, macd_hist
        FROM silver_prices
    """).df()

    df = df.merge(df_silver, on=["date", "ticker"], how="left")
    print(f"Features cargados: {len(df)} filas")
    return df


def preparar_datos(df: pd.DataFrame):
    """Prepara X e y para el modelo."""
    features = [
        "daily_return_pct",
        "daily_range",
        "avg_volume_20d",
        "dist_sma20_pct",
        "dist_sma50_pct",
        "above_sma20",
        "above_sma50",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_hist"
    ]

    df = df.dropna(subset=features)
    X = df[features]
    y = df["target_up_tomorrow"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    # Calcular balance de clases
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale = round(neg / pos, 2)
    print(f"Train: {len(X_train)} filas | Test: {len(X_test)} filas")
    print(f"Balance de clases — Baja: {neg} | Sube: {pos} | scale_pos_weight: {scale}")
    return X_train, X_test, y_train, y_test, scale


def entrenar_modelo(X_train, y_train, scale_pos_weight) -> XGBClassifier:
    """Entrena el modelo XGBoost con balance de clases corregido."""
    modelo = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42
    )
    modelo.fit(X_train, y_train)
    print("Modelo entrenado.")
    return modelo


def evaluar_modelo(modelo: XGBClassifier, X_test, y_test):
    """Evalúa el modelo y muestra métricas."""
    y_pred = modelo.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {round(acc * 100, 2)}%")
    print("\nReporte de clasificación:")
    print(classification_report(y_test, y_pred, target_names=["Baja", "Sube"]))


if __name__ == "__main__":
    conn = duckdb.connect(DB_PATH)
    df = cargar_features(conn)
    conn.close()

    X_train, X_test, y_train, y_test, scale = preparar_datos(df)
    modelo = entrenar_modelo(X_train, y_train, scale)
    evaluar_modelo(modelo, X_test, y_test)