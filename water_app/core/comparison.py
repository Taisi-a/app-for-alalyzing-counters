import pandas as pd
from scipy import stats


def compare_basic_consumption_stats(df1, df2):
    """1. Сравнение основных статистик потребления"""
    output = "\n=== 1. Сравнение основных статистик потребления ===\n"

    def get_consumption_stats(df, df_name):
        stats = {}
        # Анализ для P1 счетчиков
        p1_data = df[df['Series'] == 'P1'].copy() if 'Series' in df.columns else pd.DataFrame()
        # Анализ для 10266/1 счетчиков
        mtype_data = df[df['typeM'] == '/10266/1'].copy() if 'typeM' in df.columns else pd.DataFrame()

        combined = pd.concat([p1_data, mtype_data])

        if not combined.empty:
            stats = {
                'total': combined['Value'].sum(),
                'mean': combined['Value'].mean(),
                'median': combined['Value'].median(),
                'min': combined['Value'].min(),
                'max': combined['Value'].max(),
                'std': combined['Value'].std(),
                'count': len(combined),
                'zero_readings': (combined['Value'] == 0).sum()
            }

        return stats

    stats1 = get_consumption_stats(df1, "Первый датафрейм")
    stats2 = get_consumption_stats(df2, "Второй датафрейм")

    output += "\nПервый датафрейм:\n"
    for k, v in stats1.items():
        output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    output += "\nВторой датафрейм:\n"
    for k, v in stats2.items():
        output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    # Сравнение
    if stats1 and stats2:
        output += "\nСравнение:\n"
        output += f"Разница общего расхода: {stats1['total'] - stats2['total']:.2f} л\n"
        output += f"Разница среднего расхода: {stats1['mean'] - stats2['mean']:.2f} л\n"
        if stats1['mean'] != 0:
            output += f"Относительная разница среднего: {(stats1['mean'] - stats2['mean']) / stats1['mean'] * 100:.1f}%\n"

    return output


def compare_meter_types_consumption(df1, df2):
    """2. Сравнение потребления по типам счетчиков"""
    output = "\n=== 2. Сравнение потребления по типам счетчиков ===\n"

    def analyze_meter_type(df, type_col, type_val, df_name):
        if type_col not in df.columns:
            return None

        data = df[df[type_col] == type_val].copy()
        if data.empty:
            return None

        return {
            'count': len(data),
            'mean': data['Value'].mean(),
            'median': data['Value'].median(),
            'total': data['Value'].sum(),
            'max': data['Value'].max(),
            'min': data['Value'].min()
        }

    # Анализ P1 в первом датафрейме
    p1_stats1 = analyze_meter_type(df1, 'Series', 'P1', "Первый датафрейм")
    # Анализ 10266/1 в первом датафрейме
    mtype_stats1 = analyze_meter_type(df1, 'typeM', '/10266/1', "Первый датафрейм")

    # Анализ P1 во втором датафрейме
    p1_stats2 = analyze_meter_type(df2, 'Series', 'P1', "Второй датафрейм")
    # Анализ 10266/1 во втором датафрейме
    mtype_stats2 = analyze_meter_type(df2, 'typeM', '/10266/1', "Второй датафрейм")

    # Вывод результатов
    if p1_stats1:
        output += "\nПервый датафрейм - P1 счетчики:\n"
        for k, v in p1_stats1.items():
            output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    if mtype_stats1:
        output += "\nПервый датафрейм - 10266/1 счетчики:\n"
        for k, v in mtype_stats1.items():
            output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    if p1_stats2:
        output += "\nВторой датафрейм - P1 счетчики:\n"
        for k, v in p1_stats2.items():
            output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    if mtype_stats2:
        output += "\nВторой датафрейм - 10266/1 счетчики:\n"
        for k, v in mtype_stats2.items():
            output += f"{k}: {v:.2f}\n" if isinstance(v, (float, int)) else f"{k}: {v}\n"

    # Сравнение P1
    if p1_stats1 and p1_stats2:
        output += "\nСравнение P1 счетчиков:\n"
        diff = p1_stats1['mean'] - p1_stats2['mean']
        output += f"Разница среднего расхода: {diff:.2f} л\n"
        if p1_stats1['mean'] != 0:
            output += f"Относительная разница: {diff / p1_stats1['mean'] * 100:.1f}%\n"

    # Сравнение 10266/1
    if mtype_stats1 and mtype_stats2:
        output += "\nСравнение 10266/1 счетчиков:\n"
        diff = mtype_stats1['mean'] - mtype_stats2['mean']
        output += f"Разница среднего расхода: {diff:.2f} л\n"
        if mtype_stats1['mean'] != 0:
            output += f"Относительная разница: {diff / mtype_stats1['mean'] * 100:.1f}%\n"

    return output


def compare_temporal_patterns(df1, df2):
    """3. Сравнение временных паттернов потребления"""
    output = "\n=== 3. Сравнение временных паттернов потребления ===\n"

    def get_temporal_stats(df, type_col, type_val, df_name):
        if type_col not in df.columns or 'time' not in df.columns:
            return None

        data = df[df[type_col] == type_val].copy()
        if data.empty:
            return None

        data['hour'] = data['time'].dt.hour
        data['day_of_week'] = data['time'].dt.dayofweek

        return {
            'hourly': data.groupby('hour')['Value'].mean().to_dict(),
            'daily': data.groupby('day_of_week')['Value'].mean().to_dict()
        }

    # Получаем временные паттерны для каждого типа счетчиков в обоих датафреймах
    p1_temp1 = get_temporal_stats(df1, 'Series', 'P1', "Первый датафрейм")
    mtype_temp1 = get_temporal_stats(df1, 'typeM', '/10266/1', "Первый датафрейм")
    p1_temp2 = get_temporal_stats(df2, 'Series', 'P1', "Второй датафрейм")
    mtype_temp2 = get_temporal_stats(df2, 'typeM', '/10266/1', "Второй датафрейм")

    # Сравнение P1 счетчиков
    if p1_temp1 and p1_temp2:
        output += "\nСравнение часовых паттернов P1:\n"
        for hour in range(24):
            val1 = p1_temp1['hourly'].get(hour, 0)
            val2 = p1_temp2['hourly'].get(hour, 0)
            output += f"{hour:02}:00 - {val1:.2f} vs {val2:.2f} л\n"

    # Сравнение 10266/1 счетчиков
    if mtype_temp1 and mtype_temp2:
        output += "\nСравнение часовых паттернов 10266/1:\n"
        for hour in range(24):
            val1 = mtype_temp1['hourly'].get(hour, 0)
            val2 = mtype_temp2['hourly'].get(hour, 0)
            output += f"{hour:02}:00 - {val1:.2f} vs {val2:.2f} л\n"

    return output


def perform_statistical_tests(df1, df2):
    """4. Статистические тесты для сравнения потребления"""
    output = "\n=== 4. Статистические тесты для сравнения потребления ===\n"

    def prepare_data(df, type_col, type_val):
        if type_col not in df.columns:
            return None
        return df[df[type_col] == type_val]['Value'].dropna().values

    # Подготовка данных для P1
    p1_data1 = prepare_data(df1, 'Series', 'P1')
    p1_data2 = prepare_data(df2, 'Series', 'P1')

    # Подготовка данных для 10266/1
    mtype_data1 = prepare_data(df1, 'typeM', '/10266/1')
    mtype_data2 = prepare_data(df2, 'typeM', '/10266/1')

    # Тесты для P1
    if p1_data1 is not None and p1_data2 is not None:
        if len(p1_data1) > 1 and len(p1_data2) > 1:
            _, p_val = stats.ttest_ind(p1_data1, p1_data2, equal_var=False)
            output += f"\nP1 счетчики - t-тест:\n"
            output += f"p-value: {p_val:.4f} {'(значимо)' if p_val < 0.05 else '(не значимо)'}\n"

    # Тесты для 10266/1
    if mtype_data1 is not None and mtype_data2 is not None:
        if len(mtype_data1) > 1 and len(mtype_data2) > 1:
            _, p_val = stats.ttest_ind(mtype_data1, mtype_data2, equal_var=False)
            output += f"\n10266/1 счетчики - t-тест:\n"
            output += f"p-value: {p_val:.4f} {'(значимо)' if p_val < 0.05 else '(не значимо)'}\n"

    return output


def perform_comparison(df1, modes, df2):
    """Основная функция сравнения двух датафреймов по потреблению воды"""
    if df1 is None or df2 is None:
        return "Ошибка: Один или оба датафрейма отсутствуют"

    if not modes:
        return "Ошибка: Не выбраны режимы сравнения"

    output = "=== СРАВНЕНИЕ ПОТРЕБЛЕНИЯ ВОДЫ ===\n"

    # 1. Основные статистики потребления
    if 1 in modes:
        output += compare_basic_consumption_stats(df1, df2)

    # 2. Сравнение по типам счетчиков
    if 2 in modes:
        output += compare_meter_types_consumption(df1, df2)

    # 3. Временные паттерны
    if 3 in modes:
        output += compare_temporal_patterns(df1, df2)

    # 4. Статистические тесты
    if 4 in modes:
        output += perform_statistical_tests(df1, df2)

    return output