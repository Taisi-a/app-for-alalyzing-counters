import pandas as pd
import core.anomaly_detection
from typing import Dict, Any, List, Optional, Union


def analyze_meter_health(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ технического состояния счетчиков воды"""
    health_stats = {}

    if df is None or df.empty:
        return health_stats

    # Разделение данных по типам счетчиков
    digital_meters = df[~df['typeM'].str.startswith('/')]
    integrated_meters = df[df['typeM'].str.startswith('/')]

    # Анализ Digital Meters
    if not digital_meters.empty:
        health_stats['digital'] = {
            'flow': _analyze_flow(digital_meters),
            'switches': _analyze_switches(digital_meters),
            'temperature': _analyze_temperature(digital_meters),
            'battery': _analyze_battery(digital_meters),
            'signal': _analyze_signal(digital_meters)
        }

    # Анализ Integrated Meters
    if not integrated_meters.empty:
        health_stats['integrated'] = {
            'flow': _analyze_integrated_flow(integrated_meters),
            'temperature': _analyze_integrated_temp(integrated_meters),
            'pressure': _analyze_pressure(integrated_meters)
        }

    return health_stats


def _analyze_flow(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ показаний расхода воды"""
    stats = {}
    flow_data = df[df['Series'].isin(['P1', 'T1'])]

    if not flow_data.empty:
        # Анализ интервальных показаний (P1)
        p1_stats = flow_data[flow_data['Series'] == 'P1'].groupby('ManagedObjectid')['Value'].agg(
            ['sum', 'mean', 'max', 'count'])
        stats['interval'] = {
            'stats': p1_stats.describe().to_dict(),
            'high_flow': p1_stats[p1_stats['max'] > 500].index.tolist(),  # >500 л/интервал
            'zero_flow': p1_stats[p1_stats['sum'] == 0].index.tolist()
        }

        # Анализ суммарных показаний (T1)
        t1_stats = flow_data[flow_data['Series'] == 'T1'].groupby('ManagedObjectid')['Value'].agg(
            ['min', 'max', 'last'])
        stats['total'] = {
            'stats': t1_stats.describe().to_dict(),
            'max_values': t1_stats.sort_values('max', ascending=False).head(10).to_dict()
        }

    return stats


def _analyze_switches(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ состояния переключателей"""
    stats = {}
    switch_data = df[df['Series'] == 'SW2']

    if not switch_data.empty:
        switch_stats = switch_data.groupby('ManagedObjectid')['Value'].agg(['count', 'mean'])
        stats['status'] = {
            'active': switch_stats[switch_stats['mean'] > 0].index.tolist(),
            'inactive': switch_stats[switch_stats['mean'] == 0].index.tolist()
        }

    return stats


def _analyze_temperature(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ температуры для Digital Meters"""
    stats = {}
    temp_data = df[df['Series'].isin(['T', 'Median', 'Min', 'Max'])]

    if not temp_data.empty:
        temp_stats = temp_data.pivot_table(index='ManagedObjectid', columns='Series', values='Value', aggfunc='mean')
        stats['readings'] = {
            'stats': temp_stats.describe().to_dict(),
            'high_temp': temp_stats[temp_stats['Max'] > 50].index.tolist(),
            'low_temp': temp_stats[temp_stats['Min'] < -10].index.tolist()
        }

    return stats


def _analyze_battery(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ состояния батареи"""
    stats = {}
    battery_data = df[df['Series'] == 'V']

    if not battery_data.empty:
        battery_stats = battery_data.groupby('ManagedObjectid')['Value'].agg(['min', 'mean', 'max'])
        stats['readings'] = {
            'stats': battery_stats.describe().to_dict(),
            'low_battery': battery_stats[battery_stats['min'] < 3.0].index.tolist()  # <3V
        }

    return stats


def _analyze_signal(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ качества сигнала"""
    stats = {}
    signal_data = df[df['Series'].isin(['RSRP', 'SINR', 'RSRQ', 'RSSI'])]

    if not signal_data.empty:
        signal_stats = signal_data.pivot_table(index='ManagedObjectid', columns='Series', values='Value',
                                               aggfunc='mean')
        stats['readings'] = {
            'stats': signal_stats.describe().to_dict(),
            'poor_signal': signal_stats[signal_stats['RSRP'] < -100].index.tolist()  # Плохой сигнал
        }

    return stats


def _analyze_integrated_flow(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ расхода для Integrated Meters"""
    stats = {}
    flow_data = df[df['typeM'].str.startswith('/10266')]

    if not flow_data.empty:
        flow_stats = flow_data.groupby(['ManagedObjectid', 'Series'])['Value'].agg(['sum', 'mean', 'max'])
        stats['readings'] = {
            'stats': flow_stats.describe().to_dict(),
            'high_flow': flow_stats[flow_stats['max'] > 100].index.tolist()  # >100 л/интервал
        }

    return stats


def _analyze_integrated_temp(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ температуры для Integrated Meters"""
    stats = {}
    temp_data = df[df['typeM'].str.startswith('/10268')]

    if not temp_data.empty:
        temp_stats = temp_data.groupby('ManagedObjectid')['Value'].agg(['min', 'mean', 'max'])
        stats['readings'] = {
            'stats': temp_stats.describe().to_dict(),
            'high_temp': temp_stats[temp_stats['max'] > 30].index.tolist(),  # >30°C
            'low_temp': temp_stats[temp_stats['min'] < 5].index.tolist()  # <5°C
        }

    return stats


def _analyze_pressure(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ давления для Integrated Meters"""
    stats = {}
    pressure_data = df[df['typeM'].str.startswith('/10269')]

    if not pressure_data.empty:
        pressure_stats = pressure_data.groupby('ManagedObjectid')['Value'].agg(['min', 'mean', 'max'])
        stats['readings'] = {
            'stats': pressure_stats.describe().to_dict(),
            'high_pressure': pressure_stats[pressure_stats['max'] > 10].index.tolist(),  # >10 бар
            'low_pressure': pressure_stats[pressure_stats['min'] < 1].index.tolist()  # <1 бар
        }

    return stats


def detect_leaks(df: pd.DataFrame) -> pd.DataFrame:
    """Обнаружение потенциальных протечек"""
    leaks = []

    # Анализ непрерывного расхода в ночное время
    night_flow = df[(df['time'].dt.hour >= 0) & (df['time'].dt.hour <= 5) &
                    (df['Series'] == 'P1') & (df['Value'] > 0)]

    if not night_flow.empty:
        continuous_flow = night_flow.groupby('ManagedObjectid').filter(
            lambda x: x['Value'].sum() > 50)  # Более 50 литров за ночь

        if not continuous_flow.empty:
            leaks.append(continuous_flow)

    # Анализ необычно высокого расхода
    high_flow = df[(df['Series'] == 'P1') & (df['Value'] > 300)]  # Более 300 литров за интервал

    if not high_flow.empty:
        leaks.append(high_flow)

    # Анализ расхождения между P1 и T1
    flow_comparison = df[df['Series'].isin(['P1', 'T1'])].pivot_table(
        index=['ManagedObjectid', 'time'], columns='Series', values='Value')

    if not flow_comparison.empty:
        flow_comparison['diff'] = flow_comparison['T1'] - flow_comparison['P1']
        abnormal_diff = flow_comparison[abs(flow_comparison['diff']) > 100]  # Разница более 100 литров

        if not abnormal_diff.empty:
            leaks.append(abnormal_diff)

    # Объединение всех обнаруженных протечек
    if leaks:
        return pd.concat(leaks).drop_duplicates()
    return pd.DataFrame()


def print_leaks(leaks: pd.DataFrame) -> str:
    """Форматирование информации о протечках для вывода"""
    output = ""

    if 'P1' in leaks.columns:  # Для данных о расходе
        leak_stats = leaks.groupby('ManagedObjectid')['P1'].agg(['sum', 'count'])
        output += "Протечки по расходу воды:\n"
        for meter_id, row in leak_stats.iterrows():
            output += f"Счетчик {meter_id}: {row['sum']} литров за {row['count']} интервалов\n"

    elif 'diff' in leaks.columns:  # Для расхождений между P1 и T1
        output += "\nРасхождения в показаниях:\n"
        for meter_id, group in leaks.groupby('ManagedObjectid'):
            output += f"Счетчик {meter_id}: среднее расхождение {group['diff'].mean():.2f} литров\n"

    return output


def generate_recommendations(health_stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Генерация рекомендаций по обслуживанию"""
    recommendations = []

    # Digital Meters рекомендации
    if 'digital' in health_stats:
        digital = health_stats['digital']

        # Высокий расход
        if 'flow' in digital and 'high_flow' in digital['flow'].get('interval', {}):
            for meter_id in digital['flow']['interval']['high_flow']:
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Высокий расход воды (>500 л/интервал)',
                    'recommendation': 'Проверить на утечки или несанкционированный расход'
                })

        # Нулевой расход
        if 'flow' in digital and 'zero_flow' in digital['flow'].get('interval', {}):
            for meter_id in digital['flow']['interval']['zero_flow']:
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Нулевой расход воды',
                    'recommendation': 'Проверить работоспособность счетчика'
                })

        # Температура
        if 'temperature' in digital:
            temp_stats = digital['temperature'].get('readings', {})
            for meter_id in temp_stats.get('high_temp', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Высокая температура (>50°C)',
                    'recommendation': 'Проверить условия эксплуатации'
                })
            for meter_id in temp_stats.get('low_temp', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Низкая температура (<-10°C)',
                    'recommendation': 'Проверить защиту от замерзания'
                })

        # Батарея
        if 'battery' in digital:
            battery_stats = digital['battery'].get('readings', {})
            for meter_id in battery_stats.get('low_battery', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Низкий заряд батареи (<3V)',
                    'recommendation': 'Заменить батарею'
                })

        # Сигнал
        if 'signal' in digital:
            signal_stats = digital['signal'].get('readings', {})
            for meter_id in signal_stats.get('poor_signal', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Digital',
                    'issue': 'Плохой сигнал (RSRP < -100)',
                    'recommendation': 'Проверить антенну и местоположение'
                })

    # Integrated Meters рекомендации
    if 'integrated' in health_stats:
        integrated = health_stats['integrated']

        # Расход воды
        if 'flow' in integrated and 'high_flow' in integrated['flow'].get('readings', {}):
            for meter_id in integrated['flow']['readings']['high_flow']:
                recommendations.append({
                    'meter_id': meter_id[0],  # (ManagedObjectid, Series)
                    'type': 'Integrated',
                    'issue': f'Высокий расход воды (>100 л/интервал) в серии {meter_id[1]}',
                    'recommendation': 'Проверить систему на утечки'
                })

        # Температура
        if 'temperature' in integrated:
            temp_stats = integrated['temperature'].get('readings', {})
            for meter_id in temp_stats.get('high_temp', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Integrated',
                    'issue': 'Высокая температура (>30°C)',
                    'recommendation': 'Проверить систему охлаждения'
                })
            for meter_id in temp_stats.get('low_temp', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Integrated',
                    'issue': 'Низкая температура (<5°C)',
                    'recommendation': 'Проверить защиту от замерзания'
                })

        # Давление
        if 'pressure' in integrated:
            pressure_stats = integrated['pressure'].get('readings', {})
            for meter_id in pressure_stats.get('high_pressure', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Integrated',
                    'issue': 'Высокое давление (>10 бар)',
                    'recommendation': 'Проверить систему на перегрузки'
                })
            for meter_id in pressure_stats.get('low_pressure', []):
                recommendations.append({
                    'meter_id': meter_id,
                    'type': 'Integrated',
                    'issue': 'Низкое давление (<1 бар)',
                    'recommendation': 'Проверить систему на утечки'
                })

    return recommendations


def perform_technical_analysis(df, modes=None):
    """Основная функция анализа данных"""
    if df is None or df.empty:
        return "Нет данных для анализа\n"

    if not modes:
        return "Не выбраны режимы анализа\n"

    output = ""
    health_stats = analyze_meter_health(df)

    # 1. Поиск протечек
    if 1 in modes:
        output += "\n=== РЕЗУЛЬТАТЫ ПОИСКА ПРОТЕЧЕК ===\n"
        flow_data = df[df['Series'].isin(['P1', 'T1'])]
        if not flow_data.empty:
            leaks = detect_leaks(flow_data)
            if not leaks.empty:
                output += f"Найдено {len(leaks.groupby('ManagedObjectid'))} потенциальных протечек:\n"
                output += print_leaks(leaks)
            else:
                output += "Протечки не обнаружены\n"
        else:
            output += "Нет данных о расходе воды для анализа протечек\n"

    # 2. Анализ температуры
    if 2 in modes:
        output += _format_temperature_analysis(health_stats)

    # 3. Анализ переключателей
    if 3 in modes:
        output += "\n=== АНАЛИЗ ПЕРЕКЛЮЧАТЕЛЕЙ ===\n"
        if 'digital' in health_stats and 'switches' in health_stats['digital']:
            switches = health_stats['digital']['switches']
            output += f"Активных переключателей: {len(switches.get('status', {}).get('active', []))}\n"
            output += f"Неактивных переключателей: {len(switches.get('status', {}).get('inactive', []))}\n"
        else:
            output += "Данные о переключателях отсутствуют\n"

    # 4. Статистика неисправностей
    if 4 in modes:
        output += "\n=== СТАТИСТИКА НЕИСПРАВНОСТЕЙ ===\n"

        # Анализ батареи
        if 'digital' in health_stats and 'battery' in health_stats['digital']:
            battery = health_stats['digital']['battery']
            output += "\nСостояние батарей:\n"
            output += f"Средний заряд: {battery['readings']['stats']['mean']['mean']:.2f} V\n"
            output += f"Минимальный заряд: {battery['readings']['stats']['min']['min']:.2f} V\n"
            if battery['readings'].get('low_battery'):
                output += f"Счетчиков с низким зарядом (<3V): {len(battery['readings']['low_battery'])}\n"
                output += "ID проблемных счетчиков: " + ", ".join(map(str, battery['readings']['low_battery'])) + "\n"
            else:
                output += "Проблем с батареями не обнаружено\n"
        else:
            output += "\nДанные о батареях отсутствуют\n"

        # Анализ сигнала
        if 'digital' in health_stats and 'signal' in health_stats['digital']:
            signal = health_stats['digital']['signal']
            output += "\nКачество сигнала:\n"
            output += f"Средний уровень сигнала (RSRP): {signal['readings']['stats']['mean']['RSRP']:.2f} dB\n"
            if signal['readings'].get('poor_signal'):
                output += f"Счетчиков с плохим сигналом (<-100 dB): {len(signal['readings']['poor_signal'])}\n"
                output += "ID проблемных счетчиков: " + ", ".join(map(str, signal['readings']['poor_signal'])) + "\n"
            else:
                output += "Проблем с сигналом не обнаружено\n"
        else:
            output += "\nДанные о сигнале отсутствуют\n"

        # Анализ передачи данных
        log_data = df[df['Series'].isin(['Stored', 'Sent'])]
        if not log_data.empty:
            log_stats = log_data.pivot_table(index='ManagedObjectid', columns='Series', values='Value', aggfunc='max')
            transmission_issues = log_stats[log_stats['Stored'] - log_stats['Sent'] > 10]

            output += "\nПередача данных:\n"
            output += f"Всего счетчиков с данными: {len(log_stats)}\n"
            output += f"Счетчиков с проблемами передачи: {len(transmission_issues)}\n"
            if not transmission_issues.empty:
                output += "ID проблемных счетчиков: " + ", ".join(map(str, transmission_issues.index)) + "\n"
        else:
            output += "\nДанные о передаче данных отсутствуют\n"

    # 5. Рекомендации по замене
    if 5 in modes:
        recommendations = generate_recommendations(health_stats)
        output += "\n=== РЕКОМЕНДАЦИИ ПО ОБСЛУЖИВАНИЮ ===\n"
        if recommendations:
            for rec in recommendations:
                output += f"[{rec['type']}] Счетчик {rec['meter_id']}: {rec['issue']}\n"
                output += f"Рекомендация: {rec['recommendation']}\n\n"
        else:
            output += "Критических проблем не обнаружено\n"

    print(output)
    return output


def _format_temperature_analysis(health_stats: Dict[str, Any]) -> str:
    """Форматирование анализа температуры"""
    output = "\n=== АНАЛИЗ ТЕМПЕРАТУРЫ ===\n"
    has_data = False

    # Digital Meters
    if 'digital' in health_stats and 'temperature' in health_stats['digital']:
        temp_stats = health_stats['digital']['temperature'].get('readings', {})
        if temp_stats:
            output += "\nDigital Meters:\n"
            stats = temp_stats.get('stats', {})
            output += f"Средняя температура: {stats.get('mean', {}).get('Mean', 'N/A')} °C\n"
            output += f"Минимальная температура: {stats.get('min', {}).get('Min', 'N/A')} °C\n"
            output += f"Максимальная температура: {stats.get('max', {}).get('Max', 'N/A')} °C\n"

            if temp_stats.get('high_temp'):
                output += f"\nСчетчики с высокой температурой (>50°C):\n"
                output += ", ".join(str(x) for x in temp_stats['high_temp']) + "\n"

            if temp_stats.get('low_temp'):
                output += f"\nСчетчики с низкой температурой (<-10°C):\n"
                output += ", ".join(str(x) for x in temp_stats['low_temp']) + "\n"

            has_data = True

    # Integrated Meters
    if 'integrated' in health_stats and 'temperature' in health_stats['integrated']:
        temp_stats = health_stats['integrated']['temperature'].get('readings', {})
        if temp_stats:
            output += "\nIntegrated Meters:\n"
            stats = temp_stats.get('stats', {})
            output += f"Средняя температура: {stats.get('mean', {}).get('mean', 'N/A')} °C\n"
            output += f"Минимальная температура: {stats.get('min', {}).get('min', 'N/A')} °C\n"
            output += f"Максимальная температура: {stats.get('max', {}).get('max', 'N/A')} °C\n"

            if temp_stats.get('high_temp'):
                output += f"\nСчетчики с высокой температурой (>30°C):\n"
                output += ", ".join(str(x) for x in temp_stats['high_temp']) + "\n"

            if temp_stats.get('low_temp'):
                output += f"\nСчетчики с низкой температурой (<5°C):\n"
                output += ", ".join(str(x) for x in temp_stats['low_temp']) + "\n"

            has_data = True

    if not has_data:
        output += "Данные о температуре отсутствуют\n"

    return output


def print_health_stats(health_stats: Dict[str, Any]) -> None:
    """Вывод статистики в консоль"""
    if not health_stats:
        print("Нет данных для отображения")
        return

    print("\n=== ОБЩАЯ СТАТИСТИКА СОСТОЯНИЯ СЧЕТЧИКОВ ===")

    # Digital Meters
    if 'digital' in health_stats:
        print("\nDIGITAL METERS:")
        digital = health_stats['digital']

        if 'flow' in digital:
            print("\nРасход воды:")
            flow = digital['flow']
            if 'interval' in flow:
                print(f"Макс. расход: {flow['interval']['stats']['max']['max']:.2f} л")
                print(f"Средний расход: {flow['interval']['stats']['mean']['mean']:.2f} л")

            if 'total' in flow:
                print(f"\nСуммарный расход:")
                print(f"Макс. значение: {flow['total']['stats']['max']['max']:.2f} л")

        if 'temperature' in digital:
            print("\nТемпература:")
            temp = digital['temperature']['readings']
            print(f"Макс. температура: {temp['stats']['max']['Max']:.2f} °C")
            print(f"Мин. температура: {temp['stats']['min']['Min']:.2f} °C")

        if 'battery' in digital:
            print("\nБатарея:")
            battery = digital['battery']['readings']
            print(f"Средний заряд: {battery['stats']['mean']['mean']:.2f} V")
            print(f"Мин. заряд: {battery['stats']['min']['min']:.2f} V")

        if 'signal' in digital:
            print("\nСигнал:")
            signal = digital['signal']['readings']
            print(f"Средний уровень сигнала (RSRP): {signal['stats']['mean']['RSRP']:.2f} dB")

    # Integrated Meters
    if 'integrated' in health_stats:
        print("\nINTEGRATED METERS:")
        integrated = health_stats['integrated']

        if 'flow' in integrated:
            print("\nРасход воды:")
            flow = integrated['flow']['readings']
            print(f"Макс. расход: {flow['stats']['max']['max']:.2f} л")

        if 'temperature' in integrated:
            print("\nТемпература:")
            temp = integrated['temperature']['readings']
            print(f"Макс. температура: {temp['stats']['max']['max']:.2f} °C")

        if 'pressure' in integrated:
            print("\nДавление:")
            pressure = integrated['pressure']['readings']
            print(f"Макс. давление: {pressure['stats']['max']['max']:.2f} бар")