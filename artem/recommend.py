import pandas as pd
import os

def recommend_brands(
    gender: str,
    category: str,
    n: int = 5,
    sort_type: str = "actual",
    path: str = "results",
    full: bool = False
):
    """
    Рекомендация брендов по категории и полу.

    Параметры:
    ----------
    gender : str
        'M' — мужчины
        'F' — женщины

    category : str
        Категория товара (например: 'Jeans', 'Dresses')

    n : int
        Количество брендов

    sort_type : str
        Тип сортировки:
        - 'actual'      — лучший баланс (маржа + выкуп + популярность)
        - 'price_asc'   — дешевые
        - 'price_desc'  — дорогие
        - 'popularity'  — самые популярные
        - 'rating'      — лучший выкуп

    path : str
        Путь до сохранённых таблиц

    full : bool
        True  — вернуть все колонки (для анализа)
        False — только пользовательские

    Возвращает:
    ----------
    DataFrame
    """

    gender_map = {'M': 'male', 'F': 'female'}

    if gender not in gender_map:
        raise ValueError("gender должен быть 'M' или 'F'")

    valid_sorts = ['actual', 'price_desc', 'price_asc', 'popularity', 'rating']
    if sort_type not in valid_sorts:
        raise ValueError(f"sort_type должен быть из {valid_sorts}")

    filepath = os.path.join(path, f"{gender_map[gender]}_{sort_type}.csv")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    df = pd.read_csv(filepath)

    # =========================
    # ФИЛЬТР ПО КАТЕГОРИИ
    # =========================
    df = df[df['category'] == category]

    if df.empty:
        return pd.DataFrame()

    # =========================
    # ТОП-N
    # =========================
    df = df.head(n)

    # =========================
    # FULL / SHORT MODE
    # =========================
    if not full:
        visible_cols = [
            'brand',
            'rating',
            'product_1',
            'price_1',
            'product_2',
            'price_2'
        ]
        visible_cols = [c for c in visible_cols if c in df.columns]
        df = df[visible_cols]

    # =========================
    # ЧИСТКА NaN (для UI)
    # =========================
    for col in ['product_1', 'product_2']:
        if col in df.columns:
            df[col] = df[col].fillna('')

    for col in ['price_1', 'price_2']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df.reset_index(drop=True)

matrix = recommend_brands(
    gender='F',
    category='Accessories',
    n=10,
    sort_type='actual',
    full=False
)
print(matrix)