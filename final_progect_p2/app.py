# app.py
import streamlit as st
import sqlite3
import polars as pl
import plotly.express as px
from datetime import date
import os
from pathlib import Path

# Путь к базе данных
DB_PATHS = [
    "data/weather.db",
    "weather.db",
    "/opt/airflow/data/weather.db",
    "../data/weather.db",
]

DB_PATH = None
for path in DB_PATHS:
    if os.path.exists(path):
        DB_PATH = path
        break

if DB_PATH is None:
    DB_PATH = "data/weather.db"
    os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="WeatherInsight", layout="wide")
st.title("🌦️ WeatherInsight: Погодные тренды и комфорт")

@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weather'")
        if not cursor.fetchone():
            st.error("❌ Таблица 'weather' не найдена. Запустите DAG Airflow.")
            conn.close()
            return None

        df = pl.read_database("SELECT * FROM weather ORDER BY date", conn)
        conn.close()

        if df.is_empty():
            st.warning("⚠️ База данных пуста. Запустите DAG Airflow.")
            return None

        return df
    except Exception as e:
        st.error(f"❌ Ошибка загрузки: {str(e)}")
        return None

df = load_data()

if df is None:
    st.stop()

# Статистика
st.subheader("📊 Общая статистика")
total_records = len(df)
unique_cities = df["city"].n_unique()
col1, col2, col3 = st.columns(3)
col1.metric("Всего записей", total_records)
col2.metric("Уникальных городов", unique_cities)
if "comfort_index" in df.columns:
    col3.metric("Средний комфорт", f"{df['comfort_index'].mean():.1f}")

# Выбор города
cities = sorted(df["city"].unique().to_list())
selected_city = st.selectbox("Выберите город", cities)

city_data = df.filter(pl.col("city") == selected_city)

# Разделение на историю и прогноз
today = date.today()
today_str = str(today)
historical_data = city_data.filter(pl.col("date") < today_str)
forecast_data = city_data.filter(pl.col("date") >= today_str)

# === ГРАФИК ТЕМПЕРАТУРЫ ===
if not historical_data.is_empty():
    st.subheader(f"📈 Исторические данные: {selected_city}")
    fig_temp_hist = px.line(
        historical_data.to_pandas(),
        x="date",
        y="avg_temp",
        title=f"Средняя температура в {selected_city} (история)",
        labels={"avg_temp": "Температура (°C)", "date": "Дата"}
    )
    st.plotly_chart(fig_temp_hist, use_container_width=True)

if not forecast_data.is_empty():
    st.subheader(f"🔮 Прогноз: {selected_city}")
    fig_temp_forecast = px.line(
        forecast_data.to_pandas(),
        x="date",
        y="avg_temp",
        title=f"Средняя температура в {selected_city} (прогноз)",
        labels={"avg_temp": "Температура (°C)", "date": "Дата"}
    )
    st.plotly_chart(fig_temp_forecast, use_container_width=True)

# === НОВОЕ: ГРАФИК ИНДЕКСА КОМФОРТА ===
if "comfort_index" in city_data.columns:
    st.subheader(f"😊 Индекс комфорта: {selected_city}")

    # Исторический комфорт
    if not historical_data.is_empty():
        fig_comfort_hist = px.line(
            historical_data.to_pandas(),
            x="date",
            y="comfort_index",
            title=f"Индекс комфорта в {selected_city} (история, выше = лучше)",
            labels={"comfort_index": "Индекс комфорта", "date": "Дата"},
            color_discrete_sequence=["#2ecc71"]
        )
        st.plotly_chart(fig_comfort_hist, use_container_width=True)

    # Прогноз комфорта
    if not forecast_data.is_empty():
        fig_comfort_forecast = px.line(
            forecast_data.to_pandas(),
            x="date",
            y="comfort_index",
            title=f"Индекс комфорта в {selected_city} (прогноз, выше = лучше)",
            labels={"comfort_index": "Индекс комфорта", "date": "Дата"},
            color_discrete_sequence=["#e67e22"]
        )
        st.plotly_chart(fig_comfort_forecast, use_container_width=True)

# Статистика по выбранному городу
st.subheader(f"📊 Статистика для {selected_city}")
rainy_days = city_data["is_rainy"].sum()
avg_temp = city_data["avg_temp"].mean()
if "comfort_index" in city_data.columns:
    avg_comfort = city_data["comfort_index"].mean()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Средняя температура", f"{avg_temp:.1f}°C")
    col2.metric("Дождливых дней", int(rainy_days))
    col3.metric("Всего дней", len(city_data))
    col4.metric("Средний комфорт", f"{avg_comfort:.1f}")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Средняя температура", f"{avg_temp:.1f}°C")
    col2.metric("Дождливых дней", int(rainy_days))
    col3.metric("Всего дней", len(city_data))

# Аномалии
st.subheader("⚠️ Анализ аномалий")
if not city_data.is_empty():
    mean_temp = city_data["avg_temp"].mean()
    std_temp = city_data["avg_temp"].std()
    anomalies = city_data.filter(
        (pl.col("avg_temp") > mean_temp + 2 * std_temp) |
        (pl.col("avg_temp") < mean_temp - 2 * std_temp)
    )
    if not anomalies.is_empty():
        st.warning(f"Найдено {len(anomalies)} температурных аномалий")
        st.dataframe(anomalies.select(["date", "avg_temp", "is_rainy"]).to_pandas())
    else:
        st.success("✅ Аномалии не обнаружены")

# Таблица последних данных
st.subheader("📋 Последние 20 записей")
columns = ["date", "avg_temp", "total_precip", "avg_wind", "is_rainy"]
if "comfort_index" in city_data.columns:
    columns.append("comfort_index")
display_df = city_data.tail(20).select(columns).to_pandas()
st.dataframe(display_df, use_container_width=True)

# Информация
st.sidebar.header("ℹ️ Информация")
st.sidebar.info(
    f"""
    **База данных:** {DB_PATH}
    **Городов:** {unique_cities}
    **Записей:** {total_records}
    **Последнее обновление:** {df['date'].max()}
    """
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Индекс комфорта учитывает:**
- 🌡️ Отклонение от 20°C
- 🌧️ Количество осадков
- 💨 Силу ветра
""")
