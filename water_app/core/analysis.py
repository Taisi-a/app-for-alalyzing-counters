import pandas as pd
from scipy import stats
import core
from core import prediction
from core.anomaly_detection import detect_anomalies, format_anomalies


def analyze_consumption(df):
    """Анализ потребления воды с учетом двух типов счетчиков (P1 и 10266/1)"""
    analysis = {
        'p1_meters': {},
        'mtype_10266_1': {},
        'common_stats': {
            'total_meters': 0,
            'data_points_count': 0,
            'first_date': 'нет данных',
            'last_date': 'нет данных',
            'consumption_stats': {},
            'meter_types_distribution': {},
            'suburb_distribution': {},
            'usage_type_distribution': {},
            'readings_distribution': {},
            'meter_readings_count': {}
        }
    }

    if df is None or df.empty:
        return analysis

    # Проверка обязательных колонок
    required_columns = ['time', 'ManagedObjectid', 'Value']
    if 'Series' in df.columns or 'typeM' in df.columns:
        pass
    else:
        print("Предупреждение: Отсутствуют колонки Series или typeM")
        return analysis

    try:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        if df.empty:
            print("Предупреждение: Нет корректных данных времени")
            return analysis
    except Exception as e:
        print(f"Ошибка преобразования времени: {e}")
        return analysis

    # Заполняем common_stats
    analysis['common_stats']['total_meters'] = df['ManagedObjectid'].nunique()
    analysis['common_stats']['data_points_count'] = len(df)
    analysis['common_stats']['first_date'] = df['time'].min().strftime('%Y-%m-%d')
    analysis['common_stats']['last_date'] = df['time'].max().strftime('%Y-%m-%d')

    # Добавляем расширенную статистику по расходам
    if 'Value' in df.columns:
        # Для P1 счетчиков
        p1_data = df[df['Series'] == 'P1'].copy() if 'Series' in df.columns else pd.DataFrame()
        # Для 10266/1 счетчиков
        mtype_data = df[df['typeM'] == '/10266/1'].copy() if 'typeM' in df.columns else pd.DataFrame()

        # Объединенные данные для общей статистики
        combined_flow = pd.concat([p1_data, mtype_data])

        if not combined_flow.empty:
            analysis['common_stats']['consumption_stats'] = {
                'total': combined_flow['Value'].sum(),
                'average': combined_flow['Value'].mean(),
                'median': combined_flow['Value'].median(),
                'min': combined_flow['Value'].min(),
                'max': combined_flow['Value'].max(),
                'peak': combined_flow['Value'].quantile(0.95),
                'std_dev': combined_flow['Value'].std(),
                'q1': combined_flow['Value'].quantile(0.25),
                'q3': combined_flow['Value'].quantile(0.75),
                'zero_readings': int((combined_flow['Value'] == 0).sum()),
                'zero_percentage': (combined_flow['Value'] == 0).mean() * 100
            }

    # Остальная статистика
    if 'meter_type' in df.columns:
        analysis['common_stats']['meter_types_distribution'] = df.groupby('meter_type')[
            'ManagedObjectid'].nunique().to_dict()
        analysis['common_stats']['readings_distribution'] = df['meter_type'].value_counts().to_dict()
        analysis['common_stats']['meter_readings_count'] = df.groupby('meter_type')[
            'ManagedObjectid'].value_counts().groupby('meter_type').mean().to_dict()

    if 'suburb' in df.columns:
        analysis['common_stats']['suburb_distribution'] = df['suburb'].value_counts().to_dict()

    if 'usage_type' in df.columns:
        analysis['common_stats']['usage_type_distribution'] = df['usage_type'].value_counts().to_dict()

    # Анализ для P1 счетчиков
    if 'Series' in df.columns:
        p1_data = df[df['Series'] == 'P1'].copy()
        if not p1_data.empty:
            p1_data['hour'] = p1_data['time'].dt.hour
            p1_data['day_of_week'] = p1_data['time'].dt.dayofweek
            p1_data['day_name'] = p1_data['time'].dt.day_name()  # Добавляем названия дней

            analysis['p1_meters']['flow_stats'] = {
                'total_consumption': p1_data['Value'].sum(),
                'avg_consumption': p1_data['Value'].mean(),
                'max_consumption': p1_data['Value'].max(),
                'min_consumption': p1_data['Value'].min(),
                'hourly_pattern': p1_data.groupby('hour')['Value'].mean().to_dict(),
                'daily_pattern': p1_data.groupby('day_of_week')['Value'].mean().to_dict(),
                'daily_pattern_named': p1_data.groupby('day_name')['Value'].mean().to_dict(),
                'meter_stats': p1_data.groupby('ManagedObjectid')['Value'].agg(
                    ['sum', 'mean', 'max', 'min', 'std', 'count']
                ).to_dict('index')
            }

    # Анализ для 10266/1 счетчиков
    if 'typeM' in df.columns:
        mtype_data = df[df['typeM'] == '/10266/1'].copy()
        if not mtype_data.empty:
            mtype_data['hour'] = mtype_data['time'].dt.hour
            mtype_data['day_of_week'] = mtype_data['time'].dt.dayofweek
            mtype_data['day_name'] = mtype_data['time'].dt.day_name()  # Добавляем названия дней

            analysis['mtype_10266_1']['flow_stats'] = {
                'total_consumption': mtype_data['Value'].sum(),
                'avg_consumption': mtype_data['Value'].mean(),
                'hourly_pattern': mtype_data.groupby('hour')['Value'].mean().to_dict(),
                'daily_pattern': mtype_data.groupby('day_of_week')['Value'].mean().to_dict(),
                'daily_pattern_named': mtype_data.groupby('day_name')['Value'].mean().to_dict(),
                'meter_stats': mtype_data.groupby('ManagedObjectid')['Value'].agg(
                    ['sum', 'mean', 'max', 'min', 'std', 'count']
                ).to_dict('index')
            }

    return analysis


def perform_analysis(df, modes=None):
    """Функция для выполнения анализа с учетом двух типов счетчиков"""
    if df is None or df.empty:
        return "Нет данных для анализа\n"

    analysis = analyze_consumption(df)
    output = ""

    # 1. Общая статистика
    if 1 in modes:
        output += "\n=== ОБЩАЯ СТАТИСТИКА ===\n"
        output += f"Всего счетчиков: {analysis['common_stats']['total_meters']}\n"
        output += f"Всего показаний: {analysis['common_stats']['data_points_count']}\n"
        output += f"Период данных: с {analysis['common_stats']['first_date']} по {analysis['common_stats']['last_date']}\n"

        if 'consumption_stats' in analysis['common_stats']:
            stats = analysis['common_stats']['consumption_stats']
            output += "\nОбщая статистика потребления:\n"
            output += f"  Общий расход: {stats['total']:,.2f} л\n"
            output += f"  Средний расход: {stats['average']:,.2f} л/интервал\n"
            output += f"  Медианный расход: {stats['median']:,.2f} л/интервал\n"
            output += f"  Минимальный расход: {stats['min']:,.2f} л\n"
            output += f"  Максимальный расход: {stats['max']:,.2f} л\n"
            output += f"  Пиковый расход (95-й перцентиль): {stats['peak']:,.2f} л\n"
            output += f"  Стандартное отклонение: {stats['std_dev']:,.2f} л\n"

        if analysis['common_stats']['meter_types_distribution']:
            output += "\nРаспределение счетчиков по типам:\n"
            for meter_type, count in analysis['common_stats']['meter_types_distribution'].items():
                output += f"  {meter_type}: {count} счетчиков\n"

    # 2. Статистика по счетчикам
    if 2 in modes:
        output += "\n=== СТАТИСТИКА ПО СЧЕТЧИКАМ ===\n"

        # P1 счетчики
        if 'p1_meters' in analysis and 'flow_stats' in analysis['p1_meters']:
            stats = analysis['p1_meters']['flow_stats']
            output += "\n[Тип: P1 (интервалы 15 минут)]\n"
            output += f"Общий расход: {stats['total_consumption']:,.2f} л\n"
            output += f"Средний расход: {stats['avg_consumption']:,.2f} л/интервал\n"

            if 'meter_stats' in stats:
                output += "\nДетали по счетчикам:\n"
                for meter_id, meter_stats in sorted(stats['meter_stats'].items()):
                    output += f"\nСчетчик {meter_id}:\n"
                    output += f"  Суммарный расход: {meter_stats['sum']:,.2f} л\n"
                    output += f"  Средний расход: {meter_stats['mean']:,.2f} ± {meter_stats['std']:,.2f} л\n"
                    output += f"  Максимальный расход: {meter_stats['max']:,.2f} л\n"
                    output += f"  Минимальный расход: {meter_stats['min']:,.2f} л\n"
                    output += f"  Количество показаний: {meter_stats['count']}\n"

        # 10266/1 счетчики
        if 'mtype_10266_1' in analysis and 'flow_stats' in analysis['mtype_10266_1']:
            stats = analysis['mtype_10266_1']['flow_stats']
            output += "\n[Тип: 10266/1 (интервалы 30 минут)]\n"
            output += f"Общий расход: {stats['total_consumption']:,.2f} л\n"
            output += f"Средний расход: {stats['avg_consumption']:,.2f} л/интервал\n"

            if 'meter_stats' in stats:
                output += "\nДетали по счетчикам:\n"
                for meter_id, meter_stats in sorted(stats['meter_stats'].items()):
                    output += f"\nСчетчик {meter_id}:\n"
                    output += f"  Суммарный расход: {meter_stats['sum']:,.2f} л\n"
                    output += f"  Средний расход: {meter_stats['mean']:,.2f} ± {meter_stats['std']:,.2f} л\n"
                    output += f"  Максимальный расход: {meter_stats['max']:,.2f} л\n"
                    output += f"  Минимальный расход: {meter_stats['min']:,.2f} л\n"
                    output += f"  Количество показаний: {meter_stats['count']}\n"

    # Остальные режимы (3-6) остаются без изменений
    # 3. Статистика по районам
    if 3 in modes:
        output += "\n=== СТАТИСТИКА ПО РАЙОНАМ ===\n"
        if 'suburb' in df.columns:
            suburb_stats = df[df['Series'] == 'P1'].groupby('suburb')['Value'].agg(
                ['sum', 'mean', 'median', 'max', 'min', 'count'])
            for suburb, stats in suburb_stats.sort_values('sum', ascending=False).head(10).iterrows():
                output += f"\nРайон {suburb}:\n"
                output += f"  Суммарный расход: {stats['sum']:,.2f} л\n"
                output += f"  Средний расход: {stats['mean']:,.2f} л\n"
                output += f"  Медианный расход: {stats['median']:,.2f} л\n"
                output += f"  Максимальный расход: {stats['max']:,.2f} л\n"
                output += f"  Минимальный расход: {stats['min']:,.2f} л\n"
                output += f"  Количество показаний: {stats['count']}\n"
        else:
            output += "Данные по районам отсутствуют\n"

    # 4. Аномалии
    if 4 in modes:
        try:
            anomalies = detect_anomalies(df)
            output += format_anomalies(anomalies)
        except Exception as e:
            output += f"\nОшибка при обнаружении аномалий: {str(e)}\n"

    if 5 in modes:
        output += "\n=== СУТОЧНЫЕ И НЕДЕЛЬНЫЕ ПАТТЕРНЫ ПОТРЕБЛЕНИЯ ===\n"

        # Паттерны для P1
        if 'p1_meters' in analysis and 'flow_stats' in analysis['p1_meters']:
            p1_stats = analysis['p1_meters']['flow_stats']

            output += "\n[Тип: P1 - Часовые паттерны]\n"
            for hour, val in sorted(p1_stats['hourly_pattern'].items()):
                output += f"  {hour:02}:00 - {val:.2f} л\n"

            output += "\n[Тип: P1 - По дням недели]\n"
            for day, val in p1_stats['daily_pattern_named'].items():
                output += f"  {day[:3]}: {val:.2f} л\n"  # Сокращаем названия дней (Mon, Tue...)

        # Паттерны для 10266/1
        if 'mtype_10266_1' in analysis and 'flow_stats' in analysis['mtype_10266_1']:
            mtype_stats = analysis['mtype_10266_1']['flow_stats']

            output += "\n[Тип: 10266/1 - Часовые паттерны]\n"
            for hour, val in sorted(mtype_stats['hourly_pattern'].items()):
                output += f"  {hour:02}:00 - {val:.2f} л\n"

            output += "\n[Тип: 10266/1 - По дням недели]\n"
            for day, val in mtype_stats['daily_pattern_named'].items():
                output += f"  {day[:3]}: {val:.2f} л\n"

    # 6. Прогнозирование потребления
    if 6 in modes:
        predictions = core.prediction.predict_consumption(df, forecast_hours=24)
        if not predictions.empty:
            formatted_predictions = core.prediction.format_predictions(predictions)
            output += "\nПРОГНОЗ ПОТРЕБЛЕНИЯ:\n" + formatted_predictions + "\n"
            print(formatted_predictions)

    return output