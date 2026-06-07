#Credit Calculator
import streamlit as st
import pandas as pd
import datetime
import math

# Настройка страницы
st.set_page_config(page_title="Кредитный калькулятор", layout="wide")
st.title("Кредитный калькулятор 🖩 ")
st.markdown("---")

if "calculated" not in st.session_state:
    st.session_state.calculated = False

# Функция для ввода
def validate_inputs(amount, rate, term, payment_type, start_date=None):
    errors = []
    if amount <= 0:
        errors.append("Сумма кредита должна быть положительным числом.")
    if rate <= 0 or rate > 100:
        errors.append("Процентная ставка должна быть в диапазоне (0, 100].")
    if term <= 0 or term > 600:  #  до 600 месяцев
        errors.append("Срок кредита должен быть в диапазоне от 1 до 600 месяцев.")
    if payment_type not in ["Аннуитетный", "Дифференциальный"]:
        errors.append("Выберите корректный тип платежа.")
    if start_date:
        if start_date < datetime.date.today():
            errors.append("Дата первого платежа не может быть в прошлом.")
    return errors

# Функция для расчета аннуитетного платежа
def calculate_annuity_payment(amount, annual_rate, months):
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return amount / months
    annuity_factor = (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return amount * annuity_factor

# Функция для расчета графика аннуитетных платежей
def calculate_annuity_schedule(amount, annual_rate, months, start_date=None):
    schedule = []
    balance = amount
    monthly_payment = calculate_annuity_payment(amount, annual_rate, months)
    monthly_rate = annual_rate / 100 / 12

    for i in range(1, months + 1):
        interest_part = balance * monthly_rate
        debt_part = monthly_payment - interest_part

        # Корректировка последнего платежа
        if i == months:
            debt_part = balance
            monthly_payment = debt_part + interest_part

        balance -= debt_part
        # Защита от отрицательного остатка
        balance = max(0, balance)

        payment_date = None
        if start_date:
            # Прибавляем месяцы к дате первого платежа
            year = start_date.year + (start_date.month + i - 2) // 12
            month = (start_date.month + i - 2) % 12 + 1
            try:
                payment_date = datetime.date(year, month, start_date.day)
            except ValueError:
                # Если дня нет в месяце , берем последний день месяца
                next_month = datetime.date(year, month, 1)
                last_day = next_month.replace(day=28) + datetime.timedelta(days=4)
                payment_date = last_day - datetime.timedelta(days=last_day.day - 1)

        schedule.append({
            "Период": i,
            "Дата платежа": payment_date.strftime("%d.%m.%Y") if payment_date else "-",
            "Остаток долга на начало периода": round(balance + debt_part, 2),
            "Ежемесячный платеж": round(monthly_payment, 2),
            "Процентная часть": round(interest_part, 2),
            "Долговая часть": round(debt_part, 2),
            "Остаток долга на конец периода": round(balance, 2)
        })

    return schedule

# Функция для расчета дифференцированных платежей
def calculate_differentiated_schedule(amount, annual_rate, months, start_date=None):
    schedule = []
    balance = amount
    monthly_rate = annual_rate / 100 / 12
    debt_part_fixed = amount / months

    for i in range(1, months + 1):
        interest_part = balance * monthly_rate
        monthly_payment = debt_part_fixed + interest_part

        # Для последнего месяца корректируем, чтобы остаток стал точно 0
        if i == months:
            debt_part_fixed = balance
            monthly_payment = debt_part_fixed + interest_part

        balance -= debt_part_fixed
        balance = max(0, balance)

        payment_date = None
        if start_date:
            year = start_date.year + (start_date.month + i - 2) // 12
            month = (start_date.month + i - 2) % 12 + 1
            try:
                payment_date = datetime.date(year, month, start_date.day)
            except ValueError:
                # Если дня нет в месяце, берем последний день месяца
                next_month = datetime.date(year, month, 1)
                last_day = next_month.replace(day=28) + datetime.timedelta(days=4)
                payment_date = last_day - datetime.timedelta(days=last_day.day - 1)

        schedule.append({
            "Период": i,
            "Дата платежа": payment_date.strftime("%d.%m.%Y") if payment_date else "-",
            "Остаток долга на начало периода": round(balance + debt_part_fixed, 2),
            "Ежемесячный платеж": round(monthly_payment, 2),
            "Процентная часть": round(interest_part, 2),
            "Долговая часть": round(debt_part_fixed, 2),
            "Остаток долга на конец периода": round(balance, 2)
        })

    return schedule

# Блок ввода данных с обработкой ошибок
with st.expander("Введите параметры кредита", expanded=not st.session_state.calculated):
    col1, col2 = st.columns(2)

    with col1:
        loan_amount = st.number_input(
            "Сумма кредита (руб.)",
            min_value=0.01,
            step=10000.0,
            format="%.2f",
            key="loan_amount_input",
            value=100000.0  # Значение по умолчанию
        )

        interest_rate = st.number_input(
            "Процентная ставка (% годовых)",
            min_value=0.01,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            key="interest_rate_input",
            value=10.0  # Значение по умолчанию
        )

        loan_term = st.number_input(
            "Срок кредита (месяцев)",
            min_value=1,
            max_value=600,
            step=1,
            key="loan_term_input",
            value=6  # Значение по умолчанию
        )

    with col2:
        payment_type = st.radio(
            "Тип платежа",
            options=["Аннуитетный", "Дифференциальный"],
            horizontal=True,
            key="payment_type_input"
        )

        include_dates = st.checkbox("Добавить даты платежей", key="include_dates")

        first_payment_date = None
        if include_dates:
            first_payment_date = st.date_input(
                "Дата первого платежа",
                min_value=datetime.date.today(),
                value=datetime.date.today().replace(day=1) + datetime.timedelta(days=32),
                key="first_payment_date_input"
            )

    # Кнопка расчета с условным рендерингом
    if st.button("Рассчитать кредит", type="primary"):
        errors = validate_inputs(loan_amount, interest_rate, loan_term, payment_type, first_payment_date if include_dates else None)

        if errors:
            for error in errors:
                st.error(f"Ошибка: {error}")
            st.session_state.calculated = False
            st.stop()  # Использование st.stop() для прекращения выполнения при ошибках
        else:
            st.session_state.calculated = True
            st.session_state.loan_amount = loan_amount
            st.session_state.interest_rate = interest_rate
            st.session_state.loan_term = loan_term
            st.session_state.payment_type = payment_type
            st.session_state.first_payment_date = first_payment_date if include_dates else None
            st.rerun()  # Использование st.rerun() для обновления интерфейса

# Условный рендеринг результатов
if st.session_state.calculated:
    if all(key in st.session_state for key in ['loan_amount', 'interest_rate', 'loan_term', 'payment_type']):
        # Извлекаем данные из состояния сессии
        loan_amount = st.session_state.loan_amount
        interest_rate = st.session_state.interest_rate
        loan_term = st.session_state.loan_term
        payment_type = st.session_state.payment_type
        first_payment_date = st.session_state.get('first_payment_date', None)

        st.markdown("---")
        st.subheader("Результаты расчёта")

        # Расчет графика платежей в зависимости от типа платежа
        if payment_type == "Аннуитетный":
            monthly_payment = calculate_annuity_payment(loan_amount, interest_rate, loan_term)
            schedule = calculate_annuity_schedule(loan_amount, interest_rate, loan_term, first_payment_date)

            # Вывод общей информации
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ежемесячный платеж", f"{monthly_payment:,.2f} ₽")
            with col2:
                total_payment = sum(payment["Ежемесячный платеж"] for payment in schedule)
                st.metric("Общая сумма выплат", f"{total_payment:,.2f} ₽")
            with col3:
                overpayment = total_payment - loan_amount
                st.metric("Переплата по кредиту", f"{overpayment:,.2f} ₽", delta=f"{(overpayment/loan_amount)*100:.1f}%")
        else:  # Дифференциальный
            schedule = calculate_differentiated_schedule(loan_amount, interest_rate, loan_term, first_payment_date)

            col1, col2, col3 = st.columns(3)
            with col1:
                first_payment = schedule[0]["Ежемесячный платеж"]
                last_payment = schedule[-1]["Ежемесячный платеж"]
                st.metric("Первый платеж", f"{first_payment:,.2f} ₽")
                st.caption(f"Последний платеж: {last_payment:,.2f} ₽")
            with col2:
                total_payment = sum(payment["Ежемесячный платеж"] for payment in schedule)
                st.metric("Общая сумма выплат", f"{total_payment:,.2f} ₽")
            with col3:
                overpayment = total_payment - loan_amount
                st.metric("Переплата по кредиту", f"{overpayment:,.2f} ₽", delta=f"{(overpayment/loan_amount)*100:.1f}%")

        st.markdown("---")

        # Отображение графика платежей в виде таблицы
        st.subheader("График платежей")

        # Создание DataFrame
        df = pd.DataFrame(schedule)

        # Форматирование числовых столбцов
        numeric_cols = ["Остаток долга на начало периода", "Ежемесячный платеж",
                        "Процентная часть", "Долговая часть", "Остаток долга на конец периода"]
        for col in numeric_cols:
            df[col] = df[col].apply(lambda x: f"{x:,.2f} ₽")

        # Использование st.expander() для сворачивания таблицы
        with st.expander("Показать полный график платежей", expanded=True):
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Период": st.column_config.NumberColumn("№ платежа", format="%d"),
                    "Дата платежа": st.column_config.TextColumn("Дата"),
                    "Остаток долга на начало периода": st.column_config.TextColumn("Остаток на начало", width="medium"),
                    "Ежемесячный платеж": st.column_config.TextColumn("Платёж", width="medium"),
                    "Процентная часть": st.column_config.TextColumn("Проценты", width="medium"),
                    "Долговая часть": st.column_config.TextColumn("Основной долг", width="medium"),
                    "Остаток долга на конец периода": st.column_config.TextColumn("Остаток на конец", width="medium")
                }
            )

        # Кнопка для сброса и нового расчета
        if st.button("Новый расчёт", type="secondary"):
            st.session_state.calculated = False
            st.rerun()
    else:
        # Если данных нет, сбрасываем состояние
        st.session_state.calculated = False
        st.rerun()
else:
    # Отображение, если данные еще не введены.
    st.info('↑ Заполните параметры кредита в форме выше и нажмите "Рассчитать кредит".')
