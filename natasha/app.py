import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide")

# st.title("Хакатон")

# --- Навигация ---
page = st.sidebar.selectbox(
    "Выбери экран",
    ["Бизнес", "Клиенты", "Поведение", "Рекомендации"]
)

# --- Загрузка данных ---
@st.cache_data
def load_data():
    margin_df = pd.read_csv("margin.csv")
    categories_df = pd.read_csv("categories.csv")
    categories_no_return_df = pd.read_csv("category_no_returned.csv")
    forecast_df = pd.read_csv("forecast_margin_df_daily.csv")
    sankey_auth_df = pd.read_csv('sankey_links_authorized.csv')
    sankey_anon_df = pd.read_csv('sankey_links_anonymous.csv')
    intervals_complete = pd.read_csv("intervals_between_purchases_complete.csv")
    intervals_all = pd.read_csv("intervals_between_purchases_all.csv")
    traffic_df = pd.read_csv("total_margin_by_source.csv")
    weekly_margin_df = pd.read_csv("weekly_margin_analytics.csv")
    activity_df = pd.read_csv("activity_dynamics_data.csv")
    recommendations_df = pd.read_csv("top10_items_per_segment_no_age.csv")
    return margin_df, categories_df, categories_no_return_df, forecast_df, sankey_auth_df, sankey_anon_df, intervals_complete, intervals_all, traffic_df, weekly_margin_df, activity_df, recommendations_df

margin_df, categories_df, categories_no_return_df, forecast_df, sankey_auth_df, sankey_anon_df, intervals_complete, intervals_all, traffic_df, weekly_margin_df, activity_df, recommendations_df = load_data()

# --- ЭКРАН БИЗНЕС ---
if page == "Бизнес":
    st.header("Бизнес")

    # безопасный парсинг даты (ВАЖНО)
    margin_df["date"] = pd.to_datetime(
        margin_df["date"],
        utc=True,
        errors="coerce"
    )

    # =========================
    # 🔹 KPI блок
    # =========================

    total_margin = categories_df["margin"].sum()
    num_categories = categories_df["category"].nunique()
    avg_margin = categories_df["margin"].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("Полная прибыль", f"{total_margin:,.0f}")
    col2.metric("Категории", num_categories)
    col3.metric("Средняя прибыль", f"{avg_margin:,.2f}")

    st.divider()



    st.subheader("Топ категорий по прибыли: с возвратами vs без возвратов")

# Подготавливаем данные для графика с возвратами
    categories_sorted = categories_df.sort_values(
        by="margin",
        ascending=False
    ).reset_index(drop=True)

    total_margin = categories_sorted["margin"].sum()
    categories_sorted["cumulative_percent"] = (categories_sorted["margin"].cumsum() / total_margin) * 100
    top_80 = categories_sorted[categories_sorted["cumulative_percent"] <= 80].copy()
    top_80["type"] = "Все заказы"

# Подготавливаем данные для графика без возвратов
    categories_no_return_sorted = categories_no_return_df.sort_values(
        by="margin",
        ascending=False
    ).reset_index(drop=True)

    total_margin_no_return = categories_no_return_sorted["margin"].sum()
    categories_no_return_sorted["cumulative_percent"] = (categories_no_return_sorted["margin"].cumsum() / total_margin_no_return) * 100
    top_80_no_return = categories_no_return_sorted[categories_no_return_sorted["cumulative_percent"] <= 80].copy()
    top_80_no_return["type"] = "Только доставленные (без возвратов)"

# Объединяем оба датафрейма
# Нужно убедиться, что категории одинаковые в обоих файлах
    combined_df = pd.concat([top_80, top_80_no_return], ignore_index=True)

# Строим grouped bar chart
    fig = px.bar(
        combined_df,
        x="category",
        y="margin",
        color="type",
        barmode="group",  # группированные столбцы рядом
        title="Категории, которые дают 80% от всей прибыли",
        labels={"margin": "Прибыль (руб)", "category": "Категория", "type": "Тип"},
        text="margin",
        color_discrete_map={
            "Все заказы": "#1f77b4",  # синий
            "Только доставленные (без учета возвратов)": "#d62728"   # красный
        }
    )

# Настройка внешнего вида
    fig.update_layout(
        xaxis_title="Категория",
        yaxis_title="Прибыль в рублях",
        xaxis={'categoryorder': 'total descending'},  # сортируем по сумме
        height=550,
    # yaxis=dict(
    #     range=[0, combined_df["margin"].max() * 1.15]  # отступ сверху для текста
    # ),
        legend=dict(
            title="Тип данных",
            orientation="h",  # горизонтальная легенда
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

# Форматируем текст на столбцах
    fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        textfont=dict(size=10)
    )

    st.plotly_chart(fig, use_container_width=True)



    with st.sidebar:
        st.header("Настройки отображения")
        
        # Выбор гранулярности (применяется ко всем графикам)
        granularity = st.radio(
            "Агрегация по времени:",
            options=["День", "Неделя", "Месяц"],
            horizontal=False,
            key="global_granularity"
        )
        
        st.divider()
        
        # Тумблеры для выбора отображаемых данных
        st.subheader("Отображать на графиках")
        
        show_historical = st.checkbox(
            "Исторические данные",
            value=True,
            key="show_historical"
        )
        
        show_forecast = st.checkbox(
            "Прогноз",
            value=True,
            key="show_forecast"
        )
        
        st.divider()
        
        # Выбор периода времени
        st.subheader("Выбор периода")
        
        min_date = pd.to_datetime(forecast_df['date'].min()).date()
        max_date = pd.to_datetime(forecast_df['date'].max()).date()

        # Опции для быстрого выбора
        period_preset = st.selectbox(
            "Быстрый выбор:",
            options=["Весь период", "Последний месяц", "Последние 3 месяца", "Последний год", "Произвольный период"],
            key="period_preset"
        )
        
        if period_preset == "Произвольный период":
            date_range = st.date_input(
                "Выберите диапазон дат:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="custom_date_range"
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date
        else:
            end_date = max_date
            if period_preset == "Последний месяц":
                start_date = end_date - pd.Timedelta(days=30)
            elif period_preset == "Последние 3 месяца":
                start_date = end_date - pd.Timedelta(days=90)
            elif period_preset == "Последний год":
                start_date = end_date - pd.Timedelta(days=365)
            else:  # Весь период
                start_date = min_date


            st.caption(f"Период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')}")
        
        st.divider()
        
        # Кнопка сброса всех фильтров
        if st.button("Сбросить все фильтры", use_container_width=True):
            st.session_state.period_preset = "Весь период"
            st.session_state.global_granularity = "День"
            st.session_state.show_historical = True
            st.session_state.show_forecast = True
            st.rerun()

    # Функция для фильтрации по дате
    def filter_by_date_range(df, start_date, end_date):
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        return df[mask].copy()

    # Функция для агрегации данных по выбранной гранулярности (одиночная категория)
    def aggregate_by_granularity(df, granularity):
        df = df.copy()
        df = df.dropna(subset=['date'])
        
        if df.empty:
            return pd.DataFrame(columns=['date', 'margin'])
        
        df = df.set_index('date')
        
        if granularity == "Неделя":
            aggregated = df['margin'].resample('W').sum().reset_index()
        elif granularity == "Месяц":
            aggregated = df['margin'].resample('M').sum().reset_index()
        else:  # День
            aggregated = df['margin'].resample('D').sum().reset_index()
        
        aggregated.columns = ['date', 'margin']
        return aggregated

    # Функция для агрегации с группировкой по категориям
    def aggregate_categories_by_granularity(df, granularity):
        df = df.copy()
        df = df.dropna(subset=['date'])
        
        if df.empty:
            return pd.DataFrame(columns=['date', 'margin', 'category'])
        
        result_dfs = []
        
        for category in df['category'].unique():
            cat_df = df[df['category'] == category].copy()
            cat_df = cat_df.set_index('date')
            
            if granularity == "Неделя":
                agg = cat_df['margin'].resample('W').sum()
            elif granularity == "Месяц":
                agg = cat_df['margin'].resample('M').sum()
            else:  # День
                agg = cat_df['margin'].resample('D').sum()
            
            agg_df = agg.reset_index()
            agg_df['category'] = category
            result_dfs.append(agg_df)
        
        if result_dfs:
            result = pd.concat(result_dfs, ignore_index=True)
            result.columns = ['date', 'margin', 'category']
            return result
        else:
            return pd.DataFrame(columns=['date', 'margin', 'category'])

    # Применяем фильтр по дате ко всему датасету
    margin_df_filtered = filter_by_date_range(margin_df, start_date, end_date)

    # Убираем временную зону если она есть
    if margin_df['date'].dt.tz is not None:
        margin_df['date'] = margin_df['date'].dt.tz_localize(None)
        margin_df_filtered = filter_by_date_range(margin_df, start_date, end_date)

    # Подготавливаем forecast_df (колонка с прогнозом называется 'yhat')
    forecast_df_filtered = None
    if 'forecast_df' in globals() or 'forecast_df' in locals():
        # Оставляем только нужные колонки: date, category и yhat
        forecast_df_clean = forecast_df[['date', 'category', 'yhat']].copy()
        forecast_df_clean.columns = ['date', 'category', 'margin']
        forecast_df_clean['date'] = pd.to_datetime(forecast_df_clean['date'])
        
        # Убираем временную зону если она есть
        if forecast_df_clean['date'].dt.tz is not None:
            forecast_df_clean['date'] = forecast_df_clean['date'].dt.tz_localize(None)
        
        forecast_df_filtered = filter_by_date_range(forecast_df_clean, start_date, end_date)

    # Теперь основной контент страницы
    st.subheader("Прибыль по времени")

    # Получаем список всех категорий из ОТФИЛЬТРОВАННЫХ данных
    categories_list = sorted(margin_df_filtered["category"].unique())

    # Выпадающий список для выбора категории
    selected_category = st.selectbox(
        "Выберите категорию:",
        options=categories_list,
        key="margin_category_select"
    )

    # Фильтруем и агрегируем данные по выбранной категории
    category_data = margin_df_filtered[margin_df_filtered["category"] == selected_category].copy()
    category_data = category_data.sort_values("date")

    if not category_data.empty:
        # Применяем агрегацию к историческим данным
        plot_data = aggregate_by_granularity(category_data, granularity)
        
        # Убираем временную зону из дат в plot_data если есть
        if not plot_data.empty and plot_data['date'].dt.tz is not None:
            plot_data['date'] = plot_data['date'].dt.tz_localize(None)
        
        # Применяем агрегацию к прогнозным данным
        forecast_plot_data = None
        if show_forecast and forecast_df_filtered is not None and selected_category in forecast_df_filtered["category"].unique():
            forecast_cat_data = forecast_df_filtered[forecast_df_filtered["category"] == selected_category].copy()
            forecast_plot_data = aggregate_by_granularity(forecast_cat_data, granularity)
            
            # Убираем временную зону из дат в forecast_plot_data если есть
            if forecast_plot_data is not None and not forecast_plot_data.empty:
                if forecast_plot_data['date'].dt.tz is not None:
                    forecast_plot_data['date'] = forecast_plot_data['date'].dt.tz_localize(None)
        
        if not plot_data.empty:
            # Создаем комбинированный DataFrame в зависимости от выбранных опций
            combined_data = pd.DataFrame()
            
            if show_historical:
                plot_data_indexed = plot_data.set_index("date")[["margin"]]
                plot_data_indexed.columns = ["История"]
                combined_data = plot_data_indexed
            
            if show_forecast and forecast_plot_data is not None and not forecast_plot_data.empty:
                forecast_indexed = forecast_plot_data.set_index("date")[["margin"]]
                forecast_indexed.columns = ["Прогноз"]
                if combined_data.empty:
                    combined_data = forecast_indexed
                else:
                    combined_data = combined_data.join(forecast_indexed, how='outer')
            
            if not combined_data.empty:
                st.line_chart(
                    combined_data,
                    use_container_width=True
                )
                
                # Формируем текст подписи
                caption_text = f"Данные за период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')} | Агрегация: {granularity}"
                if show_historical and show_forecast:
                    caption_text += " | 🔵 История | 🔴 Прогноз"
                elif show_historical:
                    caption_text += " | 🔵 Только история"
                elif show_forecast:
                    caption_text += " | 🔴 Только прогноз"
                st.caption(caption_text)

                if show_forecast and forecast_df_clean is not None:
                    st.divider()
                    st.subheader("Прогнозные метрики")
                    
                    # Получаем данные для выбранной категории из forecast_df (оригинальные, без фильтра по датам)
                    forecast_cat_full = forecast_df_clean[forecast_df_clean['category'] == selected_category].copy()
                    
                    if not forecast_cat_full.empty:
                        # Находим последнюю дату в исторических данных
                        last_historical_date = category_data['date'].max()
                        
                        # Находим прогноз на последнюю историческую дату
                        forecast_on_last_date = forecast_cat_full[forecast_cat_full['date'] == last_historical_date]
                        
                        # Находим прогноз через год
                        date_after_year = last_historical_date + pd.Timedelta(days=365)
                        forecast_after_year = forecast_cat_full[
                            forecast_cat_full['date'] <= date_after_year
                        ].sort_values('date', ascending=False)
                        
                        if not forecast_on_last_date.empty and not forecast_after_year.empty:
                            value_last = forecast_on_last_date['margin'].values[0]
                            value_year = forecast_after_year['margin'].values[0]
                            
                            # Расчет процента изменения
                            if value_last > 0:
                                daily_pct_change = ((value_year - value_last) / value_last) * 100
                            else:
                                daily_pct_change = 0
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    label=f"Прогноз на {last_historical_date.strftime('%d.%m.%Y')}",
                                    value=f"{value_last:,.0f} ₽".replace(",", " "),
                                    delta=None
                                )
                            
                            with col2:
                                st.metric(
                                    label=f"Прогноз на {forecast_after_year['date'].values[0].strftime('%d.%m.%Y')}",
                                    value=f"{value_year:,.0f} ₽".replace(",", " "),
                                    delta=f"{daily_pct_change:+.1f}%"
                                )
                        
                        # --- ГОДОВЫЕ МЕТРИКИ ---
                        st.subheader("Годовые показатели")
                        
                        # Исторические данные за последний год
                        year_ago = last_historical_date - pd.Timedelta(days=365)
                        historical_last_year = category_data[
                            (category_data['date'] >= year_ago) & 
                            (category_data['date'] <= last_historical_date)
                        ]
                        historical_sum = historical_last_year['margin'].sum()
                        
                        # Прогноз на следующий год
                        next_year_end = last_historical_date + pd.Timedelta(days=365)
                        forecast_next_year = forecast_cat_full[
                            (forecast_cat_full['date'] > last_historical_date) & 
                            (forecast_cat_full['date'] <= next_year_end)
                        ]
                        forecast_sum = forecast_next_year['margin'].sum()
                        
                        # Расчет процента изменения
                        if historical_sum > 0:
                            yearly_pct_change = ((forecast_sum - historical_sum) / historical_sum) * 100
                        else:
                            yearly_pct_change = 0
                        
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            st.metric(
                                label=f"Суммарная прибыль за последний год ({year_ago.strftime('%d.%m.%Y')} — {last_historical_date.strftime('%d.%m.%Y')})",
                                value=f"{historical_sum:,.0f} ₽".replace(",", " "),
                                delta=None
                            )
                        
                        with col4:
                            st.metric(
                                label=f"Прогноз на следующий год ({last_historical_date.strftime('%d.%m.%Y')} — {next_year_end.strftime('%d.%m.%Y')})",
                                value=f"{forecast_sum:,.0f} ₽".replace(",", " "),
                                delta=f"{yearly_pct_change:+.1f}%"
                            )
                    else:
                        st.info("Нет прогнозных данных для выбранной категории")
                # ========== КОНЕЦ БЛОКА С ПРОГНОЗНЫМИ МЕТРИКАМИ ==========
                
            else:
                st.info("Выберите хотя бы один тип данных для отображения")
        else:
            st.info("Нет данных для отображения с выбранной агрегацией")
    else:
        st.info("Нет данных для выбранной категории в указанном периоде")

    st.subheader("Сравнение категорий по прибыли")
    # Мультиселект для сравнения нескольких категорий
    compare_categories = st.multiselect(
        "Сравнить категории (выберите 2-5):",
        options=sorted(margin_df_filtered["category"].unique()),
        default=sorted(margin_df_filtered["category"].unique())[:min(3, len(margin_df_filtered["category"].unique()))],
        key="compare_multiselect"
    )

    if len(compare_categories) >= 2:
        filtered_df = margin_df_filtered[margin_df_filtered["category"].isin(compare_categories)]
        aggregated_df = aggregate_categories_by_granularity(filtered_df, granularity)
        
        if not aggregated_df.empty:
            # Убираем временную зону если есть
            if aggregated_df['date'].dt.tz is not None:
                aggregated_df['date'] = aggregated_df['date'].dt.tz_localize(None)
            
            # Создаем pivot table для исторических данных
            pivot = pd.DataFrame()
            
            if show_historical:
                pivot = aggregated_df.pivot_table(
                    index="date",
                    columns="category",
                    values="margin",
                    aggfunc="sum"
                )
            
            # Добавляем прогнозные данные если нужно
            if show_forecast and forecast_df_filtered is not None:
                forecast_filtered = forecast_df_filtered[forecast_df_filtered["category"].isin(compare_categories)]
                if not forecast_filtered.empty:
                    forecast_aggregated = aggregate_categories_by_granularity(forecast_filtered, granularity)
                    
                    # Убираем временную зону если есть
                    if forecast_aggregated['date'].dt.tz is not None:
                        forecast_aggregated['date'] = forecast_aggregated['date'].dt.tz_localize(None)
                    
                    forecast_pivot = forecast_aggregated.pivot_table(
                        index="date",
                        columns="category",
                        values="margin",
                        aggfunc="sum"
                    )
                    # Добавляем суффикс '_прогноз' к колонкам
                    forecast_pivot.columns = [f"{col}_прогноз" for col in forecast_pivot.columns]
                    
                    # Объединяем с историческими данными
                    if pivot.empty:
                        pivot = forecast_pivot
                    else:
                        pivot = pivot.join(forecast_pivot, how='outer')
            
            if not pivot.empty:
                st.line_chart(pivot, use_container_width=True)
                
                # Формируем текст подписи
                caption_text = f"Сравнение динамики разных категорий | Период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')} | Агрегация: {granularity}"
                if show_historical and show_forecast:
                    caption_text += " | 🔵 История | 🔴 Прогноз"
                elif show_historical:
                    caption_text += " | 🔵 Только история"
                elif show_forecast:
                    caption_text += " | 🔴 Только прогноз"
                st.caption(caption_text)
            else:
                st.info("Выберите хотя бы один тип данных для отображения")
        else:
            st.info("Нет данных для выбранных категорий в указанном периоде")
            
    elif len(compare_categories) == 1:
        st.info("Выберите ещё хотя бы одну категорию для сравнения")
    else:
        st.info("Выберите 2-5 категорий для сравнения")


# --- ЭКРАН КЛИЕНТЫ ---
elif page == "Клиенты":
    st.header("Клиенты")

    st.subheader("Интервалы между покупками")
    # --- COMPLETE ORDERS ---
    st.subheader("Complete Orders")
    st.caption("Только завершенные заказы")
    
    fig_complete = go.Figure()
    fig_complete.add_trace(go.Histogram(
        x=intervals_complete['days_between'],
        nbinsx=60,
        marker_color='#1f77b4',
        marker_line=dict(color='white', width=0.5),
        opacity=0.85,
        name='Complete Orders'
    ))
    
    fig_complete.update_layout(
        title="Интервалы между покупками (Complete Orders)",
        xaxis_title="Дней между покупками",
        yaxis_title="Количество интервалов",
        bargap=0.05,
        height=450,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    fig_complete.update_xaxes(
        showgrid=False,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)',
        tickformat='d'
    )
    
    fig_complete.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)'
    )
    
    st.plotly_chart(fig_complete, use_container_width=True)
    
    # --- ALL ORDERS ---
    st.subheader("All Orders")
    st.caption("Все заказы (включая незавершенные)")
    
    fig_all = go.Figure()
    fig_all.add_trace(go.Histogram(
        x=intervals_all['days_between'],
        nbinsx=60,
        marker_color='#ff7f0e',
        marker_line=dict(color='white', width=0.5),
        opacity=0.85,
        name='All Orders'
    ))
    
    fig_all.update_layout(
        title="Интервалы между покупками (All Orders)",
        xaxis_title="Дней между покупками",
        yaxis_title="Количество интервалов",
        bargap=0.05,
        height=450,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    fig_all.update_xaxes(
        showgrid=False,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)',
        tickformat='d'
    )
    
    fig_all.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)'
    )
    
    st.plotly_chart(fig_all, use_container_width=True)


# --- ЭКРАН ПОВЕДЕНИЕ ---
elif page == "Поведение":
    st.header("Поведение пользователей")
    
    # Функция для создания Sankey диаграммы
    def create_sankey(df):
        # Задаем желаемый порядок узлов
        desired_order = ['home', 'department', 'product', 'cart', 'purchase']
        
        # Получаем все уникальные узлы из данных
        all_nodes_set = set(df['source'].unique()) | set(df['target'].unique())
        
        # Сортируем узлы согласно желаемому порядку
        all_nodes = []
        for node in desired_order:
            if node in all_nodes_set:
                all_nodes.append(node)
        
        # Добавляем остальные узлы, которых нет в desired_order (если есть)
        for node in all_nodes_set:
            if node not in all_nodes:
                all_nodes.append(node)
        
        # Создаем словарь для маппинга названий в индексы
        node_dict = {node: i for i, node in enumerate(all_nodes)}
        
        source_indices = [node_dict[src] for src in df['source']]
        target_indices = [node_dict[tgt] for tgt in df['target']]
        values = df['value'].tolist()
        
        
        colors = [
            'rgba(31, 119, 180, 0.8)',
            'rgba(255, 127, 14, 0.8)',
            'rgba(44, 160, 44, 0.8)',
            'rgba(214, 39, 40, 0.8)',
            'rgba(148, 103, 189, 0.8)',
            'rgba(140, 86, 75, 0.8)',
            'rgba(227, 119, 194, 0.8)',
            'rgba(127, 127, 127, 0.8)',
            'rgba(188, 189, 34, 0.8)',
            'rgba(23, 190, 207, 0.8)'
        ]
        
        node_colors = [colors[i % len(colors)] for i in range(len(all_nodes))]
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                hovertemplate='%{source.label} → %{target.label}<br>Вероятность: %{value:.2%}<extra></extra>'
            )
        )])
        
        fig.update_layout(
            font=dict(size=12),
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig

    # --- АВТОРИЗОВАННЫЕ ПОЛЬЗОВАТЕЛИ ---
    st.subheader("Авторизованные пользователи")
    st.caption("Вероятности переходов между категориями")
    
    fig_auth = create_sankey(sankey_auth_df)
    st.plotly_chart(fig_auth, use_container_width=True)
    
    # Статистика для авторизованных
    st.write("**Топ-3 вероятных переходов:**")
    top_auth = sankey_auth_df.nlargest(3, 'value')[['source', 'target', 'value']]

    col_a1, col_a2, col_a3 = st.columns(3)

    for i, (col, (_, row)) in enumerate(zip([col_a1, col_a2, col_a3], top_auth.iterrows())):
        with col:
            st.markdown(
                f"<div style='text-align: center; padding: 15px; border-radius: 8px; "
                f"border: 1px solid #000000; background-color: #ffffff;'>"
                f"<div style='font-size: 14px; color: #666666; margin-bottom: 8px;'>#{i+1}</div>"
                f"<div style='font-size: 16px; color: #000000; margin-bottom: 8px;'>{row['source']} → {row['target']}</div>"
                f"<div style='font-size: 22px; font-weight: bold; color: #000000;'>{row['value']:.1%}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    st.divider()
    
    # --- НЕАВТОРИЗОВАННЫЕ ПОЛЬЗОВАТЕЛИ ---
    st.subheader("Неавторизованные пользователи")
    st.caption("Вероятности переходов между категориями")
    
    fig_anon = create_sankey(sankey_anon_df)
    st.plotly_chart(fig_anon, use_container_width=True)
    
    # Статистика для неавторизованных
    st.write("**Топ-3 вероятных переходов:**")
    top_anon = sankey_anon_df.nlargest(3, 'value')[['source', 'target', 'value']]

    col_u1, col_u2, col_u3 = st.columns(3)

    for i, (col, (_, row)) in enumerate(zip([col_u1, col_u2, col_u3], top_anon.iterrows())):
        with col:
            st.markdown(
                f"<div style='text-align: center; padding: 15px; border-radius: 8px; "
                f"border: 1px solid #000000; background-color: #ffffff;'>"
                f"<div style='font-size: 14px; color: #666666; margin-bottom: 8px;'>#{i+1}</div>"
                f"<div style='font-size: 16px; color: #000000; margin-bottom: 8px;'>{row['source']} → {row['target']}</div>"
                f"<div style='font-size: 22px; font-weight: bold; color: #000000;'>{row['value']:.1%}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.subheader("Распределение прибыли по источникам трафика")

    # Создаем две колонки
    col_pie, col_info = st.columns([1.5, 1])

    with col_pie:
        # Создаем pie chart через Plotly
        fig_pie = go.Figure(data=[go.Pie(
            labels=traffic_df['traffic_source'],
            values=traffic_df['absolute_margin'],
            textinfo='percent',  # показываем только проценты на графике
            textposition='inside',
            hole=0.0,
            marker=dict(
                colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
                line=dict(color='white', width=1.5)
            ),
            hovertemplate='<b>%{label}</b><br>Прибыль: %{value:,.0f} ₽<br>Доля: %{percent}<extra></extra>',
            sort=False  # сохраняем порядок из данных
        )])
        
        fig_pie.update_layout(
            title="Распределение абсолютной прибыли по источникам",
            height=400,
            showlegend=False,  # убираем легенду, так как информация будет справа
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_info:
        st.write("**Источники трафика**")
        
        # Сортируем по убыванию маржи
        display_df = traffic_df.sort_values('absolute_margin', ascending=False).copy()
        
        # Рассчитываем проценты
        total = display_df['absolute_margin'].sum()
        display_df['percentage'] = (display_df['absolute_margin'] / total * 100).round(1)
        
        # Цвета для источников
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        # Выводим каждый источник отдельной строкой
        for i, (_, row) in enumerate(display_df.iterrows()):
            color = colors[i % len(colors)]
            margin_formatted = f"{row['absolute_margin']:,.0f}".replace(",", " ")
            
            st.markdown(
                f"<div style='display: flex; align-items: center; margin-bottom: 15px;'>"
                f"<div style='width: 12px; height: 12px; background-color: {color}; "
                f"border-radius: 3px; margin-right: 10px;'></div>"
                f"<div style='flex: 1;'>"
                f"<div style='font-weight: bold;'>{row['traffic_source']}</div>"
                f"<div style='font-size: 12px; color: #666;'>{margin_formatted} ₽</div>"
                f"</div>"
                f"<div style='font-size: 18px; font-weight: bold;'>{row['percentage']:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        # Итого
        total_formatted = f"{total:,.0f}".replace(",", " ")
        st.divider()
        st.markdown(
            f"<div style='display: flex; justify-content: space-between;'>"
            f"<span style='font-weight: bold;'>Итого</span>"
            f"<span style='font-weight: bold;'>{total_formatted} ₽</span>"
            f"</div>",
            unsafe_allow_html=True
        )


### НЕДЕЛЬНАЯ МАРЖА ПО ИСТОЧНИКАМ
    weekly_margin_df['created_at'] = pd.to_datetime(weekly_margin_df['created_at'])
    weekly_margin_df = weekly_margin_df.rename(columns={
        'created_at': 'date',
        'traffic_source': 'source',
        'smoothed_margin': 'margin'
    })
    
    # Убираем временную зону если есть
    if weekly_margin_df['date'].dt.tz is not None:
        weekly_margin_df['date'] = weekly_margin_df['date'].dt.tz_localize(None)
    
    # Боковое меню с настройками
    with st.sidebar:
        st.header("Настройки отображения")
        
        # Выбор гранулярности
        granularity = st.radio(
            "Агрегация по времени:",
            options=["Неделя", "Месяц"],
            horizontal=False,
            key="behavior_granularity"
        )
        
        st.divider()
        
        # Выбор периода времени
        st.subheader("Выбор периода")
        
        min_date = weekly_margin_df['date'].min().date()
        max_date = weekly_margin_df['date'].max().date()
        
        period_preset = st.selectbox(
            "Быстрый выбор:",
            options=["Весь период", "Последний месяц", "Последние 3 месяца", "Последний год", "Произвольный период"],
            key="behavior_period_preset"
        )
        
        if period_preset == "Произвольный период":
            date_range = st.date_input(
                "Выберите диапазон дат:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="behavior_custom_date_range"
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date
        else:
            end_date = max_date
            if period_preset == "Последний месяц":
                start_date = end_date - pd.Timedelta(days=30)
            elif period_preset == "Последние 3 месяца":
                start_date = end_date - pd.Timedelta(days=90)
            elif period_preset == "Последний год":
                start_date = end_date - pd.Timedelta(days=365)
            else:
                start_date = min_date
            
            st.caption(f"Период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')}")
        
        st.divider()
        
        # Кнопка сброса
        if st.button("Сбросить все фильтры", use_container_width=True):
            st.session_state.behavior_period_preset = "Весь период"
            st.session_state.behavior_granularity = "Неделя"
            st.rerun()
    
    # Функция для фильтрации по дате
    def filter_by_date_range(df, start_date, end_date):
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        return df[mask].copy()
    
    # Функция для агрегации данных
    def aggregate_source_by_granularity(df, granularity):
        df = df.copy()
        df = df.dropna(subset=['date', 'margin'])
        
        if df.empty:
            return pd.DataFrame(columns=['date', 'margin', 'source'])
        
        result_dfs = []
        
        for source in df['source'].unique():
            source_df = df[df['source'] == source].copy()
            source_df = source_df.set_index('date')
            
            if granularity == "Неделя":
                agg = source_df['margin'].resample('W').mean()
            elif granularity == "Месяц":
                agg = source_df['margin'].resample('M').mean()
            else:  # День
                agg = source_df['margin'].resample('D').mean()
            
            agg_df = agg.reset_index()
            agg_df['source'] = source
            result_dfs.append(agg_df)
        
        if result_dfs:
            result = pd.concat(result_dfs, ignore_index=True)
            result.columns = ['date', 'margin', 'source']
            return result
        else:
            return pd.DataFrame(columns=['date', 'margin', 'source'])
    
    # Применяем фильтр по дате
    weekly_margin_filtered = filter_by_date_range(weekly_margin_df, start_date, end_date)
    
    # --- GRAFIK MARZHI PO ISTOCHNIKAM ---
    st.subheader("Динамика сглаженной прибыли по источникам трафика")
    
    # Получаем список источников
    sources_list = sorted(weekly_margin_filtered['source'].unique())
    
    # Выпадающий список для выбора источника
    selected_source = st.selectbox(
        "Выберите источник трафика:",
        options=sources_list,
        key="source_select"
    )
    
    # Фильтруем данные по выбранному источнику
    source_data = weekly_margin_filtered[weekly_margin_filtered['source'] == selected_source].copy()
    source_data = source_data.sort_values("date")
    
    if not source_data.empty:
        # Применяем агрегацию
        plot_data = aggregate_source_by_granularity(source_data, granularity)
        plot_data = plot_data[plot_data['source'] == selected_source]
        
        if not plot_data.empty:
            # Используем st.line_chart вместо Plotly для единого стиля
            chart_data = plot_data.set_index('date')[['margin']]
            chart_data.columns = [selected_source]
            
            st.line_chart(
                chart_data,
                use_container_width=True
            )
            
            # Статистика
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Средняя прибыль", f"{plot_data['margin'].mean():,.0f} ₽")
            with col2:
                st.metric("Максимальная прибыль", f"{plot_data['margin'].max():,.0f} ₽")
            with col3:
                st.metric("Минимальная прибыль", f"{plot_data['margin'].min():,.0f} ₽")
            
            st.caption(f"Данные за период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')} | Агрегация: {granularity}")
        else:
            st.info("Нет данных для отображения с выбранной агрегацией")
    else:
        st.info("Нет данных для выбранного источника в указанном периоде")
    
    st.divider()
    
    # --- SRAVNENIE ISTOCHNIKOV ---
    st.subheader("Сравнение источников трафика")
    
    compare_sources = st.multiselect(
        "Сравнить источники (выберите 2-5):",
        options=sources_list,
        default=sources_list[:min(3, len(sources_list))],
        key="compare_sources_multiselect"
    )
    
    if len(compare_sources) >= 2:
        filtered_df = weekly_margin_filtered[weekly_margin_filtered['source'].isin(compare_sources)]
        aggregated_df = aggregate_source_by_granularity(filtered_df, granularity)
        
        if not aggregated_df.empty:
            # Создаем pivot table для st.line_chart
            pivot = aggregated_df.pivot_table(
                index='date',
                columns='source',
                values='margin',
                aggfunc='mean'
            )
            
            st.line_chart(
                pivot,
                use_container_width=True
            )
            
            st.caption(f"Сравнение источников | Период: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')} | Агрегация: {granularity}")
        else:
            st.info("Нет данных для выбранных источников в указанном периоде")
            
    elif len(compare_sources) == 1:
        st.info("Выберите ещё хотя бы один источник для сравнения")
    else:
        st.info("Выберите 2-5 источников для сравнения")
    
    st.divider()

    st.subheader("Динамика активности пользователей")
    st.caption("Количество действий по датам")
    activity_df['date'] = pd.to_datetime(activity_df['date'])

    # Убираем временную зону если есть
    if activity_df['date'].dt.tz is not None:
        activity_df['date'] = activity_df['date'].dt.tz_localize(None)

    # Функция для агрегации активности по выбранной гранулярности
    def aggregate_activity_by_granularity(df, granularity):
        df = df.copy()
        df = df.dropna(subset=['date', 'actions_count'])
        
        if df.empty:
            return pd.DataFrame(columns=['date', 'actions_count'])
        
        df = df.set_index('date')
        
        if granularity == "Неделя":
            aggregated = df['actions_count'].resample('W').sum().reset_index()
        elif granularity == "Месяц":
            aggregated = df['actions_count'].resample('M').sum().reset_index()
        else:  # День
            aggregated = df['actions_count'].resample('D').sum().reset_index()
        
        aggregated.columns = ['date', 'actions_count']
        return aggregated

    # Применяем фильтр по дате (используем те же start_date и end_date из бокового меню)
    activity_filtered = filter_by_date_range(activity_df, start_date, end_date)

    if not activity_filtered.empty:
        # Применяем агрегацию
        activity_plot = aggregate_activity_by_granularity(activity_filtered, granularity)
        
        if not activity_plot.empty:
            # Создаем красивый график через Plotly
            fig_activity = go.Figure()
            
            fig_activity.add_trace(go.Scatter(
                x=activity_plot['date'],
                y=activity_plot['actions_count'],
                mode='lines+markers',
                name='Активность',
                line=dict(width=3, color='#2ca02c'),
                marker=dict(size=6, color='#2ca02c'),
                fill='tozeroy',
                fillcolor='rgba(44, 160, 44, 0.1)',
                hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Действий: %{y:,.0f}<extra></extra>'
            ))
            
            fig_activity.update_layout(
                # title="Динамика активности пользователей",
                xaxis_title="Дата",
                yaxis_title="Количество действий",
                height=450,
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                showlegend=False
            )
            
            fig_activity.update_xaxes(
                showgrid=False,
                tickformat='%d.%m.%Y'
            )
            
            fig_activity.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(211,211,211,0.3)'
            )
            
            st.plotly_chart(fig_activity, use_container_width=True)
    

    st.subheader("Распределение прибыли по городам")
    
    # Загружаем данные по континентам
    africa_df = pd.read_csv("Africa_map.csv")
    asia_df = pd.read_csv("Asia_map.csv")
    europe_df = pd.read_csv("Europe_map.csv")
    north_america_df = pd.read_csv("North_America_map.csv")
    oceania_df = pd.read_csv("Oceania_map.csv")
    south_america_df = pd.read_csv("South_America_map.csv")
    
    # Убираем строки с null в названии города
    south_america_df = south_america_df[south_america_df['city'].notna()]
    
    # Добавляем колонку с континентом
    africa_df['continent'] = 'Africa'
    asia_df['continent'] = 'Asia'
    europe_df['continent'] = 'Europe'
    north_america_df['continent'] = 'North America'
    oceania_df['continent'] = 'Oceania'
    south_america_df['continent'] = 'South America'
    
    # Объединяем все данные
    all_cities_df = pd.concat([
        africa_df, asia_df, europe_df, 
        north_america_df, oceania_df, south_america_df
    ], ignore_index=True)
    
    # Выбор режима отображения
    map_mode = st.radio(
        "Выберите режим отображения:",
        options=["Весь мир", "По континентам"],
        horizontal=True,
        key="map_mode"
    )
    
    if map_mode == "Весь мир":
        st.subheader("Мировая карта прибыли")
        
        # Создаем мировую карту
        fig_world = go.Figure()
        
        # Добавляем точки для всех городов
        fig_world.add_trace(go.Scattergeo(
            lon=all_cities_df['lon'],
            lat=all_cities_df['lat'],
            text=all_cities_df['city'] + '<br>Прибыль: ' + all_cities_df['total_margin'].round(0).astype(int).astype(str) + ' ₽<br>Заказов: ' + all_cities_df['orders_count'].astype(str),
            mode='markers',
            marker=dict(
                size=all_cities_df['total_margin'] / all_cities_df['total_margin'].max() * 30 + 5,
                color=all_cities_df['total_margin'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Прибыль (₽)",
                    tickformat=",.0f"
                ),
                line=dict(width=0.5, color='white')
            ),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        
        fig_world.update_layout(
            title=dict(
                text="Распределение прибыли по городам мира",
                font=dict(size=20)
            ),
            geo=dict(
                projection_type='natural earth',
                showland=True,
                landcolor='rgb(243, 243, 243)',
                coastlinecolor='rgb(204, 204, 204)',
                showocean=True,
                oceancolor='rgb(230, 245, 255)',
                showcountries=True,
                countrycolor='rgb(204, 204, 204)',
                countrywidth=0.5,
                showframe=False
            ),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        st.plotly_chart(fig_world, use_container_width=True)
        
        # Статистика по миру
        st.subheader("Мировая статистика")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Всего городов",
                len(all_cities_df)
            )
        
        with col2:
            total_margin = all_cities_df['total_margin'].sum()
            st.metric(
                "Общая прибыль",
                f"{total_margin:,.0f} ₽".replace(",", " ")
            )
        
        with col3:
            total_orders = all_cities_df['orders_count'].sum()
            st.metric(
                "Всего заказов",
                f"{total_orders:,}".replace(",", " ")
            )
        
        with col4:
            avg_margin = all_cities_df['total_margin'].mean()
            st.metric(
                "Средняя прибыль",
                f"{avg_margin:,.0f} ₽".replace(",", " ")
            )

        with col5:
            top10_margin = all_cities_df.nlargest(10, 'total_margin')['total_margin'].sum()
            top10_share = (top10_margin / total_margin) * 100
            st.metric(
                "Доля топ-10 городов",
                f"{top10_share:.1f}%"
            )    
        
        # # Топ-10 городов по марже
        # st.subheader("Топ-10 городов по прибыли")
        
        # top_cities = all_cities_df.nlargest(10, 'total_margin')[
        #     ['city', 'continent', 'total_margin', 'orders_count']
        # ]
        
        # st.dataframe(
        #     top_cities,
        #     use_container_width=True,
        #     hide_index=True,
        #     column_config={
        #         "city": "Город",
        #         "continent": "Континент",
        #         "total_margin": st.column_config.NumberColumn(
        #             "Прибыль",
        #             format="%,.0f ₽"
        #         ),
        #         "orders_count": st.column_config.NumberColumn(
        #             "Заказов",
        #             format="%d"
        #         )
        #     }
        # )
    
    else:  # По континентам
        # Выбор континента
        continent = st.selectbox(
            "Выберите континент:",
            options=['Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America'],
            format_func=lambda x: {
                'Africa': 'Африка',
                'Asia': 'Азия',
                'Europe': 'Европа',
                'North America': 'Северная Америка',
                'Oceania': 'Австралия',
                'South America': 'Южная Америка'
            }[x],
            key="continent_select"
        )
        
        # Выбираем данные для континента
        continent_df = all_cities_df[all_cities_df['continent'] == continent]
        
        # Определяем центр карты для каждого континента
        continent_centers = {
            'Africa': dict(lat=0, lon=20),
            'Asia': dict(lat=35, lon=100),
            'Europe': dict(lat=50, lon=10),
            'North America': dict(lat=40, lon=-100),
            'Oceania': dict(lat=-25, lon=135),
            'South America': dict(lat=-15, lon=-60)
        }
        
        # Создаем карту континента
        fig_continent = go.Figure()
        
        fig_continent.add_trace(go.Scattergeo(
            lon=continent_df['lon'],
            lat=continent_df['lat'],
            text=continent_df['city'] + '<br>Прибыль: ' + continent_df['total_margin'].round(0).astype(int).astype(str) + ' ₽<br>Заказов: ' + continent_df['orders_count'].astype(str),
            mode='markers',
            marker=dict(
                size=continent_df['total_margin'] / continent_df['total_margin'].max() * 40 + 8,
                color=continent_df['total_margin'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Прибыль (₽)",
                    tickformat=",.0f"
                ),
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        
        continent_names = {
            'Africa': 'Африка',
            'Asia': 'Азия',
            'Europe': 'Европа',
            'North America': 'Северная Америка',
            'Oceania': 'Австралия',
            'South America': 'Южная Америка'
        }
        
        fig_continent.update_layout(
            title=dict(
                text=f"Распределение прибыли по городам - {continent_names[continent]}",
                font=dict(size=20)
            ),
            geo=dict(
                projection_type='natural earth',
                center=continent_centers[continent],
                projection_scale=1.5 if continent in ['Europe', 'Oceania'] else 1,
                showland=True,
                landcolor='rgb(243, 243, 243)',
                coastlinecolor='rgb(204, 204, 204)',
                showocean=True,
                oceancolor='rgb(230, 245, 255)',
                showcountries=True,
                countrycolor='rgb(204, 204, 204)',
                countrywidth=0.5,
                showframe=False
            ),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        st.plotly_chart(fig_continent, use_container_width=True)
        
        # Статистика по континенту
        st.subheader(f"Статистика - {continent_names[continent]}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Всего городов",
                len(continent_df)
            )
        
        with col2:
            total_margin = continent_df['total_margin'].sum()
            st.metric(
                "Общая прибыль",
                f"{total_margin:,.0f} ₽".replace(",", " ")
            )
        
        with col3:
            total_orders = continent_df['orders_count'].sum()
            st.metric(
                "Всего заказов",
                f"{total_orders:,}".replace(",", " ")
            )
        
        with col4:
            avg_margin = continent_df['total_margin'].mean()
            st.metric(
                "Средняя прибыль",
                f"{avg_margin:,.0f} ₽".replace(",", " ")
            )
        
        # # Топ-10 городов континента
        # st.subheader(f"Топ-10 городов - {continent_names[continent]}")
        
        # top_continent = continent_df.nlargest(10, 'total_margin')[
        #     ['city', 'total_margin', 'orders_count']
        # ]
        
        # st.dataframe(
        #     top_continent,
        #     use_container_width=True,
        #     hide_index=True,
        #     column_config={
        #         "city": "Город",
        #         "total_margin": st.column_config.NumberColumn(
        #             "Прибыль",
        #             format="%,.0f ₽"
        #         ),
        #         "orders_count": st.column_config.NumberColumn(
        #             "Заказов",
        #             format="%d"
        #         )
        #     }
        # )

    st.subheader("Распределение прибыли по континентам")

    # Загружаем данные
    continent_df = pd.read_csv("continent_margin_summary.csv")

    # Создаем две колонки
    col_pie, col_info = st.columns([1.5, 1])

    with col_pie:
        # Цвета для континентов
        continent_colors = {
            'Asia': '#1f77b4',
            'North_America': '#ff7f0e', 
            'Europe': '#2ca02c',
            'South_America': '#d62728',
            'Oceania': '#9467bd',
            'Africa': '#8c564b'
        }
        
        # Создаем список цветов в порядке континентов
        colors_list = [continent_colors[cont] for cont in continent_df['continent']]
        
        # Создаем pie chart через Plotly
        fig_pie = go.Figure(data=[go.Pie(
            labels=continent_df['continent'].map({
                'Asia': 'Азия',
                'North_America': 'Северная Америка',
                'Europe': 'Европа',
                'South_America': 'Южная Америка',
                'Oceania': 'Австралия',
                'Africa': 'Африка'
            }),
            values=continent_df['total_margin'],
            textinfo='percent',
            textposition='inside',
            hole=0.0,
            marker=dict(
                colors=colors_list,
                line=dict(color='white', width=1.5)
            ),
            hovertemplate='<b>%{label}</b><br>Прибыль: %{value:,.0f} ₽<br>Доля: %{percent}<extra></extra>',
            sort=False
        )])
        
        fig_pie.update_layout(
            # title="Распределение абсолютной прибыли по континентам",
            height=400,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_info:
        st.write("**Континенты**")
        
        # Сортируем по убыванию маржи
        display_df = continent_df.sort_values('total_margin', ascending=False).copy()
        
        # Рассчитываем проценты
        total = display_df['total_margin'].sum()
        display_df['percentage'] = (display_df['total_margin'] / total * 100).round(1)
        
        # Цвета для континентов
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Названия континентов на русском
        continent_names = {
            'Asia': 'Азия',
            'North_America': 'Северная Америка',
            'Europe': 'Европа',
            'South_America': 'Южная Америка',
            'Oceania': 'Австралия',
            'Africa': 'Африка'
        }
        
        # Выводим каждый континент отдельной строкой
        for i, (_, row) in enumerate(display_df.iterrows()):
            color = colors[i % len(colors)]
            margin_formatted = f"{row['total_margin']:,.0f}".replace(",", " ")
            
            st.markdown(
                f"<div style='display: flex; align-items: center; margin-bottom: 15px;'>"
                f"<div style='width: 12px; height: 12px; background-color: {color}; "
                f"border-radius: 3px; margin-right: 10px;'></div>"
                f"<div style='flex: 1;'>"
                f"<div style='font-weight: bold;'>{continent_names[row['continent']]}</div>"
                f"<div style='font-size: 12px; color: #666;'>{margin_formatted} ₽</div>"
                f"<div style='font-size: 12px; color: #999;'>{row['cities_covered']} городов, {row['orders_count']:,} заказов</div>"
                f"</div>"
                f"<div style='font-size: 18px; font-weight: bold;'>{row['percentage']:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        # # Итого
        # total_formatted = f"{total:,.0f}".replace(",", " ")
        # total_cities = display_df['cities_covered'].sum()
        # total_orders = display_df['orders_count'].sum()
        
        # st.divider()
        # st.markdown(
        #     f"<div style='display: flex; justify-content: space-between;'>"
        #     f"<span style='font-weight: bold;'>Итого</span>"
        #     f"<span style='font-weight: bold;'>{total_formatted} ₽</span>"
        #     f"</div>",
        #     unsafe_allow_html=True
        # )
        # st.caption(f"Всего городов: {total_cities}, всего заказов: {total_orders:,}".replace(",", " "))

    # --- ТОП-30 ГОРОДОВ ПО СУММАРНОЙ МАРЖЕ ---
    st.subheader("Топ-30 городов по суммарной прибыли")

    # Загружаем данные
    city_margin_df = pd.read_csv("city_margin_distribution.csv")

    # Берем топ-30 городов
    top_30_cities = city_margin_df.nlargest(30, 'total_margin')

    # Сортируем по убыванию для отображения (слева направо от большего к меньшему)
    top_30_cities = top_30_cities.sort_values('total_margin', ascending=False)

    # Создаем вертикальный bar chart
    fig_top_cities = go.Figure()

    fig_top_cities.add_trace(go.Bar(
        x=top_30_cities['city'],
        y=top_30_cities['total_margin'],
        marker=dict(
            color=top_30_cities['total_margin'],
            colorscale='Plasma',  # от фиолетового через красный к желтому
            showscale=True,
            colorbar=dict(
                title="Прибыль (₽)",
                tickformat=",.0f"
            ),
            line=dict(width=0)
        ),
        text=top_30_cities['total_margin'].apply(lambda x: f'{x:,.0f} ₽'.replace(',', ' ')),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Прибыль: %{y:,.0f} ₽<br>Доля от общей: %{customdata:.2f}%<extra></extra>',
        customdata=top_30_cities['margin_share'] * 100
    ))

    fig_top_cities.update_layout(
        # title="Топ-30 городов по суммарной прибыли",
        xaxis_title="",
        yaxis_title="Суммарная прибыль (₽)",
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        margin=dict(l=20, r=20, t=40, b=80),
        showlegend=False
    )

    fig_top_cities.update_xaxes(
        showgrid=False,
        tickangle=45,
        tickfont=dict(size=10)
    )

    fig_top_cities.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)',
        tickformat=',.0f'
    )

    st.plotly_chart(fig_top_cities, use_container_width=True)

    # Дополнительная информация
    col1, col2, col3 = st.columns(3)

    with col1:
        total_top30_margin = top_30_cities['total_margin'].sum()
        st.metric(
            "Суммарная прибыль топ-30",
            f"{total_top30_margin:,.0f} ₽".replace(',', ' ')
        )

    with col2:
        total_top30_share = top_30_cities['margin_share'].sum() * 100
        st.metric(
            "Доля от общей прибыли",
            f"{total_top30_share:.1f}%"
        )

    with col3:
        avg_top30_margin = top_30_cities['total_margin'].mean()
        st.metric(
            "Средняя прибыль в топ-30",
            f"{avg_top30_margin:,.0f} ₽".replace(',', ' ')
        )   

    # --- СРАВНЕНИЕ ИНТЕНСИВНОСТИ ВОЗВРАТОВ ПО МАКРО-РЕГИОНАМ ---
    st.subheader("Сравнение интенсивности возвратов по макро-регионам")

    # Загружаем данные
    return_rates_df = pd.read_csv("continent_return_rates.csv")

    # Сортируем по убыванию return rate
    return_rates_df = return_rates_df.sort_values('avg_return_rate', ascending=False)

    # Названия континентов на русском
    continent_names = {
        'Africa': 'Африка',
        'Europe': 'Европа',
        'South_America': 'Южная Америка',
        'Asia_Japan_Australia': 'Азия, Япония, Австралия',
        'North_America': 'Северная Америка'
    }

    # Создаем столбец с русскими названиями
    return_rates_df['continent_ru'] = return_rates_df['continent'].map(continent_names)

    # Создаем вертикальный bar chart
    fig_returns = go.Figure()

    fig_returns.add_trace(go.Bar(
        x=return_rates_df['continent_ru'],
        y=return_rates_df['avg_return_rate'],
        marker=dict(
            color=return_rates_df['avg_return_rate'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(
                title="Доля возвратов",
                tickformat='.1%'
            ),
            line=dict(width=0)
        ),
        text=return_rates_df['avg_return_rate'].apply(lambda x: f'{x:.2%}'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Доля возвратов: %{y:.2%}<br>Возвратов: %{customdata[0]:,}<br>Заказов: %{customdata[1]:,}<extra></extra>',
        customdata=return_rates_df[['total_returns', 'total_orders']].values
    ))

    fig_returns.update_layout(
        # title="Сравнение интенсивности возвратов по макро-регионам",
        xaxis_title="",
        yaxis_title="Доля возвратов",
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        margin=dict(l=20, r=20, t=40, b=60),
        showlegend=False
    )

    fig_returns.update_xaxes(
        showgrid=False,
        tickangle=0,
        tickfont=dict(size=11)
    )

    fig_returns.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211,211,211,0.3)',
        tickformat='.1%'
    )

    st.plotly_chart(fig_returns, use_container_width=True)

    # Дополнительная информация
    # col1, col2 = st.columns(2)

    # with col1:
    #     st.write("**Статистика по континентам:**")
    #     display_df = return_rates_df[['continent_ru', 'total_returns', 'total_orders', 'avg_return_rate']].copy()
    #     display_df['avg_return_rate'] = display_df['avg_return_rate'] * 100
        
    #     st.dataframe(
    #         display_df,
    #         use_container_width=True,
    #         hide_index=True,
    #         column_config={
    #             "continent_ru": "Континент",
    #             "total_returns": st.column_config.NumberColumn("Возвратов", format="%d"),
    #             "total_orders": st.column_config.NumberColumn("Заказов", format="%d"),
    #             "avg_return_rate": st.column_config.NumberColumn("Доля возвратов", format="%.2f%%")
    #         }
    #     )

    # with col2:
    #     st.write("**Ключевые выводы:**")
        
    #     max_rate = return_rates_df.loc[return_rates_df['avg_return_rate'].idxmax()]
    #     min_rate = return_rates_df.loc[return_rates_df['avg_return_rate'].idxmin()]
    #     avg_rate = return_rates_df['avg_return_rate'].mean()
        
    #     st.metric(
    #         "Максимальная доля возвратов",
    #         f"{max_rate['avg_return_rate']:.2%}",
    #         f"{continent_names[max_rate['continent']]}"
    #     )
        
    #     st.metric(
    #         "Минимальная доля возвратов",
    #         f"{min_rate['avg_return_rate']:.2%}",
    #         f"{continent_names[min_rate['continent']]}"
    #     )
        
    #     st.metric(
    #         "Средняя доля возвратов",
    #         f"{avg_rate:.2%}"
    #     )
        
    #     st.caption("💡 Африка имеет самую высокую долю возвратов, Северная Америка — самую низкую")    

# --- ЭКРАН РЕКОМЕНДАЦИИ ---
elif page == "Рекомендации":
    st.header("Рекомендации")
    st.subheader("Топ-10 категорий по вероятности покупки")
    
    # Получаем все уникальные категории и назначаем им цвета
    all_categories = recommendations_df['category'].unique()
    
    # Цветовая палитра
    colors_palette = [
        "#2380c2", '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
        '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173'
    ]
    
    # Создаем словарь цветов для категорий
    category_colors = {}
    for i, category in enumerate(sorted(all_categories)):
        category_colors[category] = colors_palette[i % len(colors_palette)]
    
    # Функция для создания вертикального bar chart с цветами по категориям
    def create_colored_bar_chart(df, gender, is_loyal, title, max_y=None):
        # Фильтруем данные
        segment_df = df[(df['gender'] == gender) & (df['is_loyal'] == is_loyal)].copy()
        
        # Берем топ-10 по вероятности
        segment_df = segment_df.nlargest(10, 'prob')
        
        # Сортируем по убыванию вероятности
        segment_df = segment_df.sort_values('prob', ascending=False)
        
        # Получаем цвета для категорий в порядке отображения
        bar_colors = [category_colors[cat] for cat in segment_df['category']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=segment_df['category'],
            y=segment_df['prob'],
            marker_color=bar_colors,
            text=segment_df['prob'].apply(lambda x: f'{x:.1%}'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Вероятность: %{y:.1%}<extra></extra>'
        ))
        
        # Определяем максимальное значение для оси Y
        if max_y is None:
            y_max = segment_df['prob'].max() * 1.15
        else:
            y_max = max_y
        
        fig.update_layout(
            title=title,
            xaxis_title="",
            yaxis_title="Вероятность покупки",
            height=400,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        fig.update_xaxes(
            showgrid=False,
            tickangle=45,
            tickfont=dict(size=10)
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211,211,211,0.3)',
            tickformat='.0%',
            range=[0, y_max]
        )
        
        return fig, segment_df['prob'].max()
    
    st.markdown("### Лояльные клиенты")
    
    women_loyal_df = recommendations_df[(recommendations_df['gender'] == 'F') & (recommendations_df['is_loyal'] == True)]
    men_loyal_df = recommendations_df[(recommendations_df['gender'] == 'M') & (recommendations_df['is_loyal'] == True)]
    
    women_max_loyal = women_loyal_df.nlargest(10, 'prob')['prob'].max() if not women_loyal_df.empty else 0
    men_max_loyal = men_loyal_df.nlargest(10, 'prob')['prob'].max() if not men_loyal_df.empty else 0
    global_max = max(women_max_loyal, men_max_loyal) * 1.15
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        if not women_loyal_df.empty:
            fig_f_true, _ = create_colored_bar_chart(
                recommendations_df, gender='F', is_loyal=True, 
                title="Женщины", max_y=global_max
            )
            st.plotly_chart(fig_f_true, use_container_width=True)
        else:
            st.info("Нет данных для лояльных женщин")
    
    with col_f2:
        if not men_loyal_df.empty:
            fig_m_true, _ = create_colored_bar_chart(
                recommendations_df, gender='M', is_loyal=True,
                title="Мужчины", max_y=global_max
            )
            st.plotly_chart(fig_m_true, use_container_width=True)
        else:
            st.info("Нет данных для лояльных мужчин")
    
    st.divider()

    st.subheader("Ключевые инсайты")
    
    # Расчет влияния лояльности
    loyal_f = recommendations_df[(recommendations_df['gender'] == 'F') & (recommendations_df['is_loyal'] == True)]['prob'].mean()
    not_loyal_f = recommendations_df[(recommendations_df['gender'] == 'F') & (recommendations_df['is_loyal'] == False)]['prob'].mean()
    loyal_m = recommendations_df[(recommendations_df['gender'] == 'M') & (recommendations_df['is_loyal'] == True)]['prob'].mean()
    not_loyal_m = recommendations_df[(recommendations_df['gender'] == 'M') & (recommendations_df['is_loyal'] == False)]['prob'].mean()
    
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    
    with col_i1:
        lift_f = ((loyal_f - not_loyal_f) / not_loyal_f * 100) if not_loyal_f > 0 else 0
        st.metric(
            "Рост вероятности у женщин",
            f"{loyal_f:.1%}",
            delta=None
        )
        st.caption("Лояльные vs нелояльные")
    
    with col_i2:
        lift_m = ((loyal_m - not_loyal_m) / not_loyal_m * 100) if not_loyal_m > 0 else 0
        st.metric(
            "Рост вероятности у мужчин",
            f"{loyal_m:.1%}",
            delta=None
        )
        st.caption("Лояльные vs нелояльные")
    
    with col_i3:
        top_category_f = women_loyal_df.nlargest(1, 'prob').iloc[0] if not women_loyal_df.empty else None
        if top_category_f is not None:
            st.metric(
                "Топ категория (женщины)",
                top_category_f['category'],
                delta=None
            )
    
    with col_i4:
        top_category_m = men_loyal_df.nlargest(1, 'prob').iloc[0] if not men_loyal_df.empty else None
        if top_category_m is not None:
            st.metric(
                "Топ категория (мужчины)",
                top_category_m['category'],
                delta=None
            )
    
    st.divider()
    

    # ДАШБОРД 2: РЕКОМЕНДАЦИИ ТОВАРОВ
    # ============================================
    st.subheader("Рекомендованные бренды")
    st.caption("Выберите пол и категорию для получения рекомендаций")
    
    # Функция для рекомендаций (адаптированная под Streamlit)
    def recommend_brands_streamlit(gender: str, category: str, n: int = 20, sort_type: str = "actual", path: str = "results"):
        gender_map = {'M': 'male', 'F': 'female'}
        
        if gender not in gender_map:
            st.error("Некорректный пол")
            return pd.DataFrame()
        
        valid_sorts = ['actual', 'price_desc', 'price_asc', 'popularity', 'rating']
        if sort_type not in valid_sorts:
            st.error("Некорректный тип сортировки")
            return pd.DataFrame()
        
        filepath = os.path.join(path, f"{gender_map[gender]}_{sort_type}.csv")
        
        if not os.path.exists(filepath):
            st.warning(f"Файл не найден: {filepath}")
            return pd.DataFrame()
        
        df = pd.read_csv(filepath)
        df = df[df['category'] == category]
        
        if df.empty:
            return pd.DataFrame()
        
        df = df.head(n).reset_index(drop=True)
        
        # Отбираем колонки для отображения
        display_cols = ['brand', 'rating', 'product_1', 'price_1', 'product_2', 'price_2']
        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()
        
        # Чистка NaN
        for col in ['product_1', 'product_2']:
            if col in df_display.columns:
                df_display[col] = df_display[col].fillna('—')
        
        for col in ['price_1', 'price_2']:
            if col in df_display.columns:
                df_display[col] = df_display[col].fillna(0)
        
        return df_display
    
    # Фильтры
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        selected_gender = st.selectbox(
            "Выберите пол:",
            options=['F', 'M'],
            format_func=lambda x: 'Женщины' if x == 'F' else 'Мужчины',
            key="rec_gender"
        )
    
    with col_f2:
        # Получаем список категорий для выбранного пола
        gender_categories = sorted(recommendations_df[recommendations_df['gender'] == selected_gender]['category'].unique())
        selected_category = st.selectbox(
            "Выберите категорию:",
            options=gender_categories,
            key="rec_category"
        )
    
    with col_f3:
        sort_options = {
            'actual': 'По актуальности',
            'popularity': 'По популярности',
            'rating': 'По рейтингу',
            'price_desc': 'Дорогие сначала',
            'price_asc': 'Дешевые сначала'
        }
        selected_sort = st.selectbox(
            "Сортировка:",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            key="rec_sort"
        )
    
    # Количество товаров
    n_items = st.slider("Количество товаров:", min_value=5, max_value=50, value=20, step=5, key="rec_n_items")
    
    # Кнопка для получения рекомендаций
    if st.button("Получить рекомендации", use_container_width=True, key="rec_button"):
        result_df = recommend_brands_streamlit(
            gender=selected_gender,
            category=selected_category,
            n=n_items,
            sort_type=selected_sort,
            path="."
        )
        
        if not result_df.empty:
            st.success(f"Найдено {len(result_df)} брендов")
            
            # Форматируем для отображения
            styled_df = result_df.copy()
            
            # Переименовываем колонки
            column_names = {
                'brand': 'Бренд',
                'rating': 'Рейтинг',
                'product_1': 'ID, Товар 1',
                'price_1': 'Цена 1 (₽)',
                'product_2': 'ID, Товар 2',
                'price_2': 'Цена 2 (₽)'
            }
            styled_df = styled_df.rename(columns={k: v for k, v in column_names.items() if k in styled_df.columns})

            # Настраиваем форматирование колонок
            column_config = {}
            for col in styled_df.columns:
                if 'Цена' in col:
                    column_config[col] = st.column_config.NumberColumn(col, format="%.0f ₽")
                elif 'Рейтинг' in col:
                    column_config[col] = st.column_config.NumberColumn(col, format="%.2f")
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )

        else:
            st.warning("Нет данных для выбранных параметров")
    else:
        st.info("Нажмите кнопку, чтобы получить рекомендации")