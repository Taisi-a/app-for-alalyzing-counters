import pandas as pd
import numpy as np


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Финальная оптимизированная версия с сохранением всех правил"""
    if df is None or df.empty:
        return pd.DataFrame()

    # Оптимизированные параметры для разных счетчиков
    config = {
        'P1': {
            'window': 144,  # 36 часов (было 96)
            'z_threshold': 15.0,  # Было 9.69
            'extreme_threshold': 1500,  # Было 1000
            'min_flow': 0.8,  # Было 0.5
            'max_flow': 25,  # Было 20
            'min_duration': 6,  # Было 4 (1.5 часа)
            'night_hours': range(0, 6),
            'min_night_flow': 1.2  # Новый параметр
        },
        '10266_1': {
            'window': 72,  # 36 часов (было 48)
            'z_threshold': 12.0,  # Было 8.5
            'extreme_threshold': 2500,  # Было 2000
            'min_flow': 1.2,  # Было 1.0
            'max_flow': 35,  # Было 30
            'min_duration': 3,  # Было 2 (1.5 часа)
            'night_hours': range(0, 5),
            'min_night_flow': 2.0  # Новый параметр
        }
    }

    anomalies = []

    # Обработка P1 счетчиков (полностью сохранена логика)
    if all(col in df.columns for col in ['Series', 'Value', 'time', 'ManagedObjectid']):
        p1_data = df[df['Series'] == 'P1'].copy()
        p1_data['Value'] = pd.to_numeric(p1_data['Value'], errors='coerce')
        p1_data = p1_data.dropna(subset=['Value'])
        if not p1_data.empty:
            anomalies.extend(_process_meter_data(p1_data, config['P1'], 'P1'))

    # Обработка 10266/1 счетчиков (полностью сохранена логика)
    if all(col in df.columns for col in ['typeM', 'Series', 'Value', 'time', 'ManagedObjectid']):
        mtype_data = df[(df['typeM'] == '/10266/1') & (df['Series'] == '1')].copy()
        mtype_data['Value'] = pd.to_numeric(mtype_data['Value'], errors='coerce')
        mtype_data = mtype_data.dropna(subset=['Value'])
        if not mtype_data.empty:
            anomalies.extend(_process_meter_data(mtype_data, config['10266_1'], '10266_1'))

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def _process_meter_data(data: pd.DataFrame, params: dict, meter_type: str) -> list:
    """Оптимизированная обработка данных с более строгими условиями обнаружения аномалий"""
    results = []
    try:
        data['time'] = pd.to_datetime(data['time'])
        data = data.sort_values(['ManagedObjectid', 'time'])

        for meter_id, group in data.groupby('ManagedObjectid'):
            group = group.drop_duplicates('time').set_index('time').sort_index()
            values = group['Value'].astype(float)

            # 1. Экстремальные значения - более строгая проверка
            if len(values) > 10:  # Только если есть достаточная история
                extreme_mask = values > params['extreme_threshold']
                # Исключаем повторяющиеся экстремальные значения
                extreme_mask = extreme_mask & ~extreme_mask.shift(1, fill_value=False)
                extreme_values = values[extreme_mask]

                for ts, val in extreme_values.items():
                    # Проверяем контекст - должно быть значительное падение после скачка
                    next_values = values[ts:ts + pd.Timedelta(hours=3)]
                    if len(next_values) > 1 and (val - next_values[-1] < val * 0.5):
                        continue

                    results.append({
                        'meter_id': str(meter_id),
                        'time': ts,
                        'value': val,
                        'anomaly_type': 'extreme_value',
                        'description': f"Экстремальное значение: {val:.2f} л (порог: {params['extreme_threshold']} л)",
                        'meter_type': meter_type
                    })

            # 2. Статистические аномалии - более строгие условия
            if len(values) >= params['window']:
                # Используем медиану и MAD для устойчивости к выбросам
                median = values.rolling(params['window'], min_periods=24).median()
                mad = (values - median).abs().rolling(params['window'], min_periods=24).median().clip(lower=0.1)
                modified_z = 0.6745 * (values - median) / mad

                # Условие 1: Очень высокая Z-оценка
                high_z = modified_z > params['z_threshold'] * 1.5  # Повысили порог

                # Условие 2: Значение выше 99.5% перцентиля
                roll_upper = values.rolling(params['window']).quantile(0.995)
                high_percentile = values > roll_upper * 1.5

                # Условие 3: Резкий рост по сравнению с историей
                prev_median = values.rolling(24).median().shift(1)
                sudden_jump = (values > prev_median * 3) & (values.diff() > prev_median * 2)

                # Комбинированная проверка (должны выполняться ВСЕ условия)
                anomaly_mask = high_z & high_percentile & sudden_jump

                # Требуем подтверждения в соседних точках
                anomaly_mask = anomaly_mask.rolling(3, center=True).min().astype(bool)

                # Исключаем аномалии в начале/конце ряда и кластеры аномалий
                anomaly_mask = anomaly_mask & ~anomaly_mask.shift(1, fill_value=False)
                anomaly_mask = anomaly_mask & ~anomaly_mask.shift(-1, fill_value=False)

                final_anomalies = values[anomaly_mask]

                for ts in final_anomalies.index:
                    # Дополнительная проверка на окружение
                    window = values[ts - pd.Timedelta(hours=6):ts + pd.Timedelta(hours=6)]
                    if len(window) < 5 or window.isna().any():
                        continue

                    # Значение должно быть изолированным (не частью кластера)
                    if (values[ts - pd.Timedelta(hours=1):ts + pd.Timedelta(hours=1)] > median[ts]).sum() > 3:
                        continue

                    results.append({
                        'meter_id': str(meter_id),
                        'time': ts,
                        'value': float(values[ts]),
                        'anomaly_type': 'z_score',
                        'description': f"Стат. аномалия: {float(values[ts]):.2f} л (медиана: {float(median[ts]):.2f}, MAD: {float(mad[ts]):.2f})",
                        'meter_type': meter_type
                    })

            # 3. Ночные протечки - более строгие критерии
            night_mask = group.index.hour.isin(params['night_hours'])
            flow_mask = (values > params['min_night_flow']) & (values < params['max_flow'] * 0.7)  # Уже верхняя граница
            night_flow = values[night_mask & flow_mask]

            if not night_flow.empty:
                # Группируем последовательные значения с более строгим условием
                changes = ((night_flow.diff().abs() > params['min_night_flow'] * 0.5) |
                           (night_flow.diff().abs() / night_flow.shift(1) > 0.3)).cumsum()

                for _, seq in night_flow.groupby(changes):
                    if len(seq) >= params['min_duration'] * 2:  # Удвоили минимальную длительность
                        # Требуем высокой стабильности
                        cv = seq.std() / seq.mean()
                        if cv > 0.2:  # Более строгий коэффициент вариации
                            continue

                        # Проверяем контекст - до и после должны быть низкие значения
                        prev_6h = values[seq.index[0] - pd.Timedelta(hours=6):seq.index[0]]
                        next_6h = values[seq.index[-1]:seq.index[-1] + pd.Timedelta(hours=6)]

                        if not prev_6h.empty and prev_6h.max() > params['max_flow'] * 0.8:
                            continue
                        if not next_6h.empty and next_6h.max() > params['max_flow'] * 0.8:
                            continue

                        duration = (seq.index[-1] - seq.index[0]).total_seconds() / 3600
                        avg_flow = seq.mean()

                        results.append({
                            'meter_id': str(meter_id),
                            'time': seq.index[0],
                            'end_time': seq.index[-1],
                            'value': avg_flow,
                            'anomaly_type': 'night_leak',
                            'description': f"Ночная протечка: {duration:.2f} ч, средний расход: {avg_flow:.2f} л (CV: {cv:.2f})",
                            'meter_type': meter_type
                        })

    except Exception as e:
        print(f"Ошибка обработки {meter_type}: {str(e)}")

    return results
def format_anomalies(anomalies_df: pd.DataFrame) -> str:
    """Форматирование отчета об аномалиях в строку"""
    if anomalies_df.empty:
        return "\nАномалии не обнаружены\n"

    anomaly_counts = anomalies_df['anomaly_type'].value_counts()

    print("Количество аномалий по типам:")
    print(anomaly_counts)

    output = ["\n=== ОБНАРУЖЕННЫЕ АНОМАЛИИ ==="]
    output.append(f"Всего аномалий: {len(anomalies_df)}")

    for _, row in anomalies_df.iterrows():
        output.append(f"\nСчетчик: {row.get('meter_id', 'N/A')} ({row.get('meter_type', 'N/A')})")
        output.append(f"Время: {row.get('time', 'N/A')}")

        if 'end_time' in row and pd.notna(row['end_time']):
            output.append(f"Период: {row['time']} - {row['end_time']}")

        output.append(f"Тип: {str(row.get('anomaly_type', 'N/A')).capitalize()}")
        output.append(f"Значение: {float(row.get('value', 0)):.2f} л")
        output.append(f"Описание: {row.get('description', 'N/A')}")
        output.append("-" * 50)

    return "\n".join(output)