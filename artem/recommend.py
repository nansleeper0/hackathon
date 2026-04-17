import pandas as pd
import os

def recommend_brands(
    gender: str,
    category: str,
    n: int = 5,
    sort_type: str = "actual",
    risk_level: str = "medium",
    path: str = "results",
    full: bool = False
):
    """
    Рекомендация брендов по категории и полу.

    risk_level:
    - "low"    -> минимальный учет возвратов, alpha = 0.9
    - "medium" -> баланс маржи и риска, alpha = 0.5
    - "high"   -> сильный учет риска возврата, alpha = 0.1
    """

    gender_map = {
        'M': 'male',
        'F': 'female'
    }

    risk_map = {
        'low': 'low_risk',
        'medium': 'medium_risk',
        'high': 'high_risk'
    }

    valid_sorts = [
        'actual',
        'price_desc',
        'price_asc',
        'popularity',
        'rating'
    ]

    if gender not in gender_map:
        raise ValueError("gender должен быть 'M' или 'F'")

    if sort_type not in valid_sorts:
        raise ValueError(f"sort_type должен быть из {valid_sorts}")

    if risk_level not in risk_map:
        raise ValueError("risk_level должен быть 'low', 'medium' или 'high'")

    # -------------------------
    # ВЫБОР ФАЙЛА
    # -------------------------
    if sort_type == "actual":
        filename = f"{gender_map[gender]}_actual_{risk_map[risk_level]}.csv"
    else:
        filename = f"{gender_map[gender]}_{sort_type}.csv"

    filepath = os.path.join(path, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    df = pd.read_csv(filepath)

    # -------------------------
    # ФИЛЬТР ПО КАТЕГОРИИ
    # -------------------------
    df = df[df['category'] == category].copy()

    if df.empty:
        return pd.DataFrame()

    # -------------------------
    # ТОП-N
    # -------------------------
    df = df.head(n)

    # -------------------------
    # ЧИСТКА NaN
    # -------------------------
    text_cols = [
        'brand',
        'product_1',
        'product_2',
        'product_name_1',
        'product_name_2'
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)

    numeric_cols = [
        'rating',
        'price_1',
        'price_2',
        'actual_score',
        'buyout_rate',
        'buyout_smooth',
        'avg_margin',
        'avg_price',
        'purchases'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # -------------------------
    # SHORT MODE
    # -------------------------
    if not full:
        visible_cols = [
            'brand',
            'rating',

            'product_1',
            'product_name_1',
            'price_1',

            'product_2',
            'product_name_2',
            'price_2'
        ]

        if sort_type == 'actual':
            visible_cols += [
                'actual_score',
                'buyout_smooth'
            ]

        visible_cols = [c for c in visible_cols if c in df.columns]
        df = df[visible_cols]

    return df.reset_index(drop=True)