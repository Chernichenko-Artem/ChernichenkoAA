import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px


# Загрузка данных
@st.cache_data
def load_data():
    conn = sqlite3.connect("weather.db")
    df = pd.read_sql("SELECT * FROM weather", conn)
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

st.title("🌦️ Анализ метеоданных")


# Фильтры
st.sidebar.header("Фильтры")

cities = st.sidebar.multiselect(
    "Выберите город(а)",
    df["city"].unique(),
    default=df["city"].unique()
)

date_range = st.sidebar.date_input(
    "Выберите диапазон дат",
    [df["date"].min(), df["date"].max()]
)

# Фильтрация
try:
    filtered_df = df[
        (df["city"].isin(cities)) &
        (df["date"] >= pd.to_datetime(date_range[0])) &
        (df["date"] <= pd.to_datetime(date_range[1]))
    ]



    # Производные признаки
    def temp_category(temp):
        if temp < 10:
            return "Холодно"
        elif temp < 20:
            return "Умеренно"
        else:
            return "Жарко"

    def precip_category(p):
        if p == 0:
            return "Без осадков"
        elif p < 2:
            return "Небольшие"
        else:
            return "Сильные"

    def comfort(row):
        if row["avg_temp"] > 18 and row["avg_wind"] < 10:
            return "Комфортно"
        return "Некомфортно"

    filtered_df["temp_category"] = filtered_df["avg_temp"].apply(temp_category)
    filtered_df["precip_category"] = filtered_df["total_precip"].apply(precip_category)
    filtered_df["comfort"] = filtered_df.apply(comfort, axis=1)




    # Таблица данных
    st.subheader("📊 Данные")
    st.dataframe(filtered_df.sort_values("date"))




    # EDA
    st.subheader("📈 Разведочный анализ")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(filtered_df, x="avg_temp", color="city", title="Распределение температуры")
        st.plotly_chart(fig)

    with col2:
        fig = px.box(filtered_df, x="city", y="avg_wind", title="Скорость ветра по городам")
        st.plotly_chart(fig)

    fig = px.bar(
        filtered_df.groupby("city")[["avg_temp", "total_precip"]].mean().reset_index(),
        x="city",
        y=["avg_temp", "total_precip"],
        barmode="group",
        title="Средние показатели по городам"
    )
    st.plotly_chart(fig)


    # Временной ряд
    st.subheader("📅 Временной ряд")

    metric = st.selectbox(
        "Выберите показатель",
        ["avg_temp", "total_precip", "avg_wind"]
    )

    fig = px.line(filtered_df, x="date", y=metric, color="city", title=f"Динамика {metric}")
    st.plotly_chart(fig)


    # Прогноз (скользящее среднее)
    st.subheader("🔮 Прогноз (скользящее среднее)")

    window = st.slider("Размер окна (дни)", 3, 14, 7)

    forecast_df = filtered_df.copy()
    forecast_df = forecast_df.sort_values("date")

    forecast_df["forecast"] = forecast_df.groupby("city")[metric].transform(
        lambda x: x.rolling(window).mean()
    )

    fig = px.line(
        forecast_df,
        x="date",
        y=[metric, "forecast"],
        color="city",
        title="Реальные значения vs Прогноз"
    )

    st.plotly_chart(fig)


    # Дополнительно
    st.subheader("🌍 Доп. анализ")

    fig = px.pie(filtered_df, names="comfort", title="Комфортность погоды")
    st.plotly_chart(fig)
except Exception as e:
                    st.error(f'←←← Введите диапозон дат в поле "Выберите диапазон дат"')
