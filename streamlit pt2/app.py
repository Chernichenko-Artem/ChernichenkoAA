import streamlit as st
import pandas as pd
import plotly.express as px

# Настройка страницы
st.set_page_config(page_title="CSV Аналитик", layout="wide")
st.title("📊 Аналитик CSV-файлов")
st.markdown("Загрузите ваш CSV-файл для просмотра, анализа и визуализации данных.")

# Кеширование для быстрой загрузки данных
@st.cache_data
def load_data(uploaded_file):
    """
    Загружает CSV файл, обрабатывает кодировки и пытается определить разделитель.
    """
    try:
        # Пробуем прочитать с разделителем ',' и кодировкой UTF-8
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        # Если не получилось, пробуем cp1251 (Windows)
        df = pd.read_csv(uploaded_file, encoding='cp1251')
    except Exception:
        # Если всё ещё ошибка, пробуем разделитель ';'
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

    # Определяем и преобразуем типы данных
    for col in df.columns:
        # Попытка преобразовать в datetime
        if df[col].dtype == 'object':
            # Проверяем на формат времени HH:MM:SS
            sample = df[col].dropna().head(10).astype(str)
            if len(sample) > 0 and sample.str.match(r'^\d{2}:\d{2}:\d{2}$').all():
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
            else:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except (ValueError, TypeError):
                    pass

        # Попытка преобразовать в numeric
        if df[col].dtype == 'object':
            try:
                # Убираем возможные пробелы и заменяем запятые на точки
                cleaned = df[col].astype(str).str.replace(',', '.').str.strip()
                df[col] = pd.to_numeric(cleaned, errors='coerce')
            except (ValueError, TypeError):
                pass

    return df

# Боковая панель для загрузки файла
with st.sidebar:
    st.header("📂 Загрузка данных")
    uploaded_file = st.file_uploader("Выберите CSV файл", type=["csv"])

    if uploaded_file is not None:
        st.success("Файл успешно загружен!")

         #Показываем информацию о файле
        file_details = {
            "Имя файла": uploaded_file.name,
            "Размер": f"{uploaded_file.size / 1024:.2f} KB"
        }
        #st.json(file_details)

# Основная логика приложения
if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Вкладки для организации интерфейса
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Данные", "📈 Визуализация", "📊 Статистика", "ℹ️ Инфо"])

    # Вкладка 1: Данные
    with tab1:
        st.subheader("Просмотр данных")
        st.dataframe(df, use_container_width=True, height=400)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Количество строк", df.shape[0])
        with col2:
            st.metric("Количество столбцов", df.shape[1])

    # Вкладка 2: Визуализация
    with tab2:
        st.subheader("Построение графиков")

        # Определяем типы столбцов
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()

        # Показываем типы столбцов для информации
        with st.expander("📋 Типы столбцов"):
            type_info = pd.DataFrame({
                "Столбец": all_cols,
                "Тип": [str(df[col].dtype) for col in all_cols],
                "Числовой": [col in numeric_cols for col in all_cols],
                "Пример значения": [str(df[col].iloc[0]) if len(df) > 0 else "Нет данных" for col in all_cols]
            })
            st.dataframe(type_info)

        #  Выбор типа графика
        chart_category = st.radio(
            "Выберите тип визуализации",
            ["📈 Линейный/Точечный", "🫧 Пузырьковая диаграмма", "📊 Гистограмма", "📦 Boxplot", "🎯 3D график"],
            horizontal=True
        )

        # ЛИНЕЙНЫЙ/ТОЧЕЧНЫЙ ГРАФИК
        if chart_category == "📈 Линейный/Точечный":
            st.markdown("### 📈 Линейный график или диаграмма рассеяния")

            if len(numeric_cols) >= 1:
                # Для оси X можно выбрать любой столбец (не только числовой)
                col_x = st.selectbox("Ось X", ["(Индекс)"] + all_cols, index=0)
                # Для оси Y только числовой
                col_y = st.selectbox("Ось Y (числовой показатель)", numeric_cols)

                # Тип графика
                chart_type = st.radio("Тип графика", ["Точечный (Scatter)", "Линейный (Line)"], horizontal=True)

                # Цветовая группировка (опционально)
                use_color = st.checkbox("Группировать по цвету")
                if use_color:
                    color_col = st.selectbox("Столбец для цвета", all_cols)
                else:
                    color_col = None

                try:
                    if col_x == "(Индекс)":
                        x_data = df.index
                        x_label = "Индекс строки"
                    else:
                        x_data = df[col_x]
                        x_label = col_x

                    if chart_type == "Точечный (Scatter)":
                        if color_col:
                            fig = px.scatter(df, x=x_data, y=col_y, color=color_col,
                                           title=f"Зависимость {col_y} от {x_label}",
                                           labels={col_y: col_y, 'x': x_label})
                        else:
                            fig = px.scatter(df, x=x_data, y=col_y,
                                           title=f"Зависимость {col_y} от {x_label}",
                                           labels={col_y: col_y, 'x': x_label})
                    else:  # Линейный
                        # Сортируем по X для линейного графика
                        if col_x == "(Индекс)":
                            df_sorted = df.sort_index()
                            x_sorted = df_sorted.index
                        else:
                            df_sorted = df.sort_values(by=col_x)
                            x_sorted = df_sorted[col_x]

                        if color_col:
                            fig = px.line(df_sorted, x=x_sorted, y=col_y, color=color_col,
                                        title=f"Изменение {col_y} по {x_label}",
                                        labels={col_y: col_y, 'x': x_label})
                        else:
                            fig = px.line(df_sorted, x=x_sorted, y=col_y,
                                        title=f"Изменение {col_y} по {x_label}",
                                        labels={col_y: col_y, 'x': x_label})

                    fig.update_layout(
                        xaxis_title=x_label,
                        yaxis_title=col_y,
                        hovermode='closest',
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Кнопка для скачивания
                    html_content = fig.to_html()
                    st.download_button(
                        label="💾 Скачать график (HTML)",
                        data=html_content,
                        file_name=f"plot_{col_y}.html",
                        mime="text/html"
                    )

                except Exception as e:
                    st.error(f"Ошибка при построении графика: {e}")
                    st.info("Попробуйте выбрать другие столбцы")
            else:
                st.warning("⚠️ Нет числовых столбцов для оси Y")

        #  ПУЗЫРЬКОВАЯ ДИАГРАММА
        elif chart_category == "🫧 Пузырьковая диаграмма":
            st.markdown("### 🫧 Пузырьковая диаграмма (Bubble Chart)")
            st.markdown("Размер пузырька показывает третий числовой параметр")

            if len(numeric_cols) >= 2:
                col_x = st.selectbox("Ось X", numeric_cols, key="bubble_x")
                col_y = st.selectbox("Ось Y", numeric_cols, key="bubble_y")
                col_size = st.selectbox("Размер пузырька", numeric_cols, key="bubble_size")
                col_color = st.selectbox("Цвет (опционально)", ["(Нет)"] + all_cols, key="bubble_color")

                try:
                    if col_color == "(Нет)":
                        fig = px.scatter(df, x=col_x, y=col_y, size=col_size,
                                        title=f"Пузырьковая диаграмма: {col_y} от {col_x}",
                                        labels={col_x: col_x, col_y: col_y, col_size: col_size})
                    else:
                        fig = px.scatter(df, x=col_x, y=col_y, size=col_size, color=col_color,
                                        title=f"Пузырьковая диаграмма: {col_y} от {col_x}",
                                        labels={col_x: col_x, col_y: col_y, col_size: col_size, col_color: col_color})

                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)

                    html_content = fig.to_html()
                    st.download_button("💾 Скачать пузырьковую диаграмму (HTML)", html_content, "bubble_chart.html", "text/html")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
            else:
                st.warning(f"⚠️ Нужно минимум 2 числовых столбца. Доступно: {len(numeric_cols)}")

        # ГИСТОГРАММА
        elif chart_category == "📊 Гистограмма":
            st.markdown("# 📊 Гистограмма распределения")

            if numeric_cols:
                hist_col = st.selectbox("Выберите столбец", numeric_cols, key="hist_select")
                if hist_col:
                    bins = st.slider("Количество интервалов (bins)", 10, 100, 50)
                    fig_hist = px.histogram(df, x=hist_col, nbins=bins,
                                            title=f"Распределение '{hist_col}'",
                                            marginal="box",
                                            opacity=0.7)
                    fig_hist.update_layout(xaxis_title=hist_col, yaxis_title="Частота", height=500)
                    st.plotly_chart(fig_hist, use_container_width=True)

                    html_content = fig_hist.to_html()
                    st.download_button("💾 Скачать гистограмму (HTML)", html_content, f"histogram_{hist_col}.html", "text/html")
            else:
                st.warning("⚠️ Нет числовых столбцов")

        # BOXPLOT
        elif chart_category == "📦 Boxplot":
            st.markdown("# 📦 Boxplot (ящик с усами)")
            st.markdown("Показывает медиану, квартили и выбросы")

            if numeric_cols:
                box_col = st.selectbox("Выберите столбец", numeric_cols, key="box_select")
                if box_col:
                    # Обычный boxplot
                    fig_box = px.box(df, y=box_col, title=f"Boxplot для '{box_col}'",
                                    points="all")
                    fig_box.update_layout(yaxis_title=box_col, height=500)
                    st.plotly_chart(fig_box, use_container_width=True)

                    # Скрипичный график
                    st.markdown("# Скрипичный график (Violin Plot) - более детальное распределение")
                    fig_violin = px.violin(df, y=box_col, title=f"Скрипичный график для '{box_col}'",
                                           box=True, points="all")
                    st.plotly_chart(fig_violin, use_container_width=True)

                    html_content = fig_box.to_html()
                    st.download_button("💾 Скачать boxplot (HTML)", html_content, f"boxplot_{box_col}.html", "text/html")
            else:
                st.warning("⚠️ Нет числовых столбцов")

        # 3D ГРАФИК
        elif chart_category == "🎯 3D график":
            st.markdown("# 🎯 3D график")
            st.markdown("Визуализация трех числовых переменных в 3D пространстве")

            if len(numeric_cols) >= 3:
                col_x = st.selectbox("Ось X", numeric_cols, key="3d_x")
                col_y = st.selectbox("Ось Y", numeric_cols, key="3d_y")
                col_z = st.selectbox("Ось Z", numeric_cols, key="3d_z")
                col_color = st.selectbox("Цвет (опционально)", ["(Нет)"] + numeric_cols, key="3d_color")

                try:
                    if col_color == "(Нет)":
                        fig = px.scatter_3d(df, x=col_x, y=col_y, z=col_z,
                                           title=f"3D график: {col_z} от {col_x} и {col_y}")
                    else:
                        fig = px.scatter_3d(df, x=col_x, y=col_y, z=col_z, color=col_color,
                                           title=f"3D график: {col_z} от {col_x} и {col_y}")

                    fig.update_layout(height=700)
                    st.plotly_chart(fig, use_container_width=True)

                    html_content = fig.to_html()
                    st.download_button("💾 Скачать 3D график (HTML)", html_content, "3d_plot.html", "text/html")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
            else:
                st.warning(f"⚠️ Для 3D графика нужно минимум 3 числовых столбца. Доступно: {len(numeric_cols)}")

    # Вкладка 3: Статистика
    with tab3:
        st.subheader("Статистический анализ")

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        if numeric_cols:
            selected_stat_col = st.selectbox("Выберите числовой столбец для анализа", numeric_cols)

            if selected_stat_col:
                data_series = df[selected_stat_col].dropna()

                if len(data_series) > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📈 Среднее", f"{data_series.mean():.4f}")
                    with col2:
                        st.metric("📉 Медиана", f"{data_series.median():.4f}")
                    with col3:
                        st.metric("🎲 Стд. Отклонение", f"{data_series.std():.4f}")

                    st.markdown("---")
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("Минимум", f"{data_series.min():.4f}")
                    with col5:
                        st.metric("Максимум", f"{data_series.max():.4f}")
                    with col6:
                        st.metric("Количество значений", len(data_series))

                    st.markdown("---")
                    st.subheader("Полная описательная статистика")
                    st.dataframe(df[selected_stat_col].describe().to_frame().T)

                    st.markdown("---")
                    st.subheader("Квартили")
                    quantiles = data_series.quantile([0.25, 0.5, 0.75, 0.9, 0.95])
                    quantiles_df = pd.DataFrame({
                        "Квартиль": ["25% (Q1)", "50% (Медиана)", "75% (Q3)", "90%", "95%"],
                        "Значение": quantiles.values
                    })
                    st.dataframe(quantiles_df)
        else:
            st.warning("⚠️ В загруженном файле нет числовых столбцов")

        # Корреляционная матрица
        if len(numeric_cols) >= 2:
            st.markdown("---")
            st.subheader("Корреляционный анализ")
            corr_matrix = df[numeric_cols].corr()
            fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                                 title="Матрица корреляции", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            st.plotly_chart(fig_corr, use_container_width=True)

        # Анализ категориальных данных
        st.markdown("---")
        st.subheader("Анализ категориальных данных")
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if categorical_cols:
            cat_col = st.selectbox("Выберите категориальный столбец", categorical_cols)
            if cat_col:
                value_counts = df[cat_col].value_counts().reset_index()
                value_counts.columns = [cat_col, "Количество"]

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(value_counts, use_container_width=True)
                with col2:
                    top10 = value_counts.head(10)
                    if len(top10) > 0:
                        fig_pie = px.pie(top10, values="Количество", names=cat_col, title=f"Топ-10 значений в '{cat_col}'")
                        st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Нет категориальных столбцов")

    # Вкладка 4: Инфо
    with tab4:
        st.subheader("Информация о типах данных")

        dtype_df = pd.DataFrame({
            "Столбец": df.columns,
            "Тип данных": [str(df[col].dtype) for col in df.columns],
            "Уникальных значений": [df[col].nunique() for col in df.columns],
            "Пропуски": [df[col].isnull().sum() for col in df.columns],
            "Процент пропусков": [f"{(df[col].isnull().sum() / len(df) * 100):.2f}%" for col in df.columns]
        })
        st.dataframe(dtype_df, use_container_width=True)

        st.subheader("Примеры первых строк")
        st.dataframe(df.head(10), use_container_width=True)

        st.subheader("Статистика по пропущенным значениям")
        missing_stats = dtype_df[dtype_df["Пропуски"] > 0]
        if len(missing_stats) > 0:
            st.dataframe(missing_stats, use_container_width=True)
        else:
            st.success("✅ Нет пропущенных значений!")

else:
    st.info("👈 Пожалуйста, загрузите CSV-файл с помощью боковой панели, чтобы начать.")


    st.markdown("""
    ### 🚀 Возможности приложения:

    #### Типы графиков:
    - **📈 Линейный/Точечный** - для анализа зависимостей (с поддержкой цветовой группировки)
    - **🫧 Пузырьковая диаграмма** - 3 переменные (X, Y, размер пузырька)
    - **📊 Гистограмма** - распределение данных
    - **📦 Boxplot** - ящик с усами + скрипичный график
    - **🎯 3D график** - визуализация трех переменных

    #### Анализ:
    - Среднее, медиана, стандартное отклонение
    - Квартили, минимум, максимум
    - Корреляционная матрица
    - Анализ категориальных данных
    """)
