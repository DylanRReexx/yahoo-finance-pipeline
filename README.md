# 📈 Yahoo Finance Pipeline

End-to-end data pipeline para análisis de mercados financieros usando datos reales de Yahoo Finance.

## 🏗️ Arquitectura

yfinance API → Bronze → Silver → Gold → Dashboard / ML Model

| Capa       | Descripción                                             |
|------------|---------------------------------------------------------|
| **Bronze** | Datos crudos descargados de Yahoo Finance               |
| **Silver** | Datos limpios con indicadores técnicos (SMA, RSI, MACD) |
| **Gold**   | Métricas de negocio agregadas y features para ML        |

## 🛠️ Stack tecnológico

| Herramienta  | Uso                           |
|--------------|-------------------------------|
| Python 3.11  | Lenguaje base                 |
| yfinance     | Fuente de datos financieros   |
| DuckDB       | Base de datos analítica local |
| pandas       | Transformación de datos       |
| XGBoost      | Modelo de clasificación ML    |
| scikit-learn | Evaluación del modelo         |
| Streamlit    | Dashboard interactivo         |
| Plotly       | Visualizaciones               |

## 📊 Activos analizados

`AAPL` `MSFT` `GOOGL` `NVDA` `JPM` `BAC` `SPY` `QQQ`

Datos históricos desde 2018 hasta la fecha actual.

## 🤖 Modelo ML

Clasificador XGBoost que predice si el precio de un activo subirá o bajará al día siguiente.

**Features utilizados:**
- Retorno diario
- Rango diario
- Volumen promedio 20 días
- Distancia porcentual a SMA 20 y SMA 50
- RSI 14
- MACD, Signal y Histograma

**Resultado:** ~52% accuracy con balance de clases corregido mediante `scale_pos_weight`.
El modelo detecta correctamente el 44% de las bajadas vs 8% sin balanceo.

## 🚀 Cómo ejecutar el proyecto

### 1. Clonar el repositorio
```bash
git clone git@github.com:DylanRReexx/yahoo-finance-pipeline.git
cd yahoo-finance-pipeline
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
venv\Scripts\Activate  # Windows
pip install -r requirements.txt
```

### 3. Correr el pipeline completo
```bash
python src/ingestion/downloader.py
python src/transformation/silver.py
python src/transformation/gold.py
```

### 4. Entrenar el modelo
```bash
python src/models/train.py
```

### 5. Correr el dashboard
```bash
streamlit run dashboard/app.py
```

## 📁 Estructura del proyecto

yahoo-finance-pipeline/
├── data/                   # Base de datos DuckDB
├── notebooks/              # Exploración y análisis
├── src/
│   ├── ingestion/          # Descarga de datos con yfinance
│   ├── transformation/     # Capas Silver y Gold
│   └── models/             # Modelo XGBoost
├── dashboard/              # App Streamlit
├── requirements.txt        # Dependencias
└── README.md

## 👤 Autor

**Dylan Rangel Valencia** — Systems Engineering Student @ ULATINA  
[GitHub](https://github.com/DylanRReexx)
