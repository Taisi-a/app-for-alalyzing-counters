import pandas as pd
from datetime import datetime, timedelta

def load_data(file_path):
    """Загружает данные из CSV-файла с автоматическим определением разделителя"""
    try:
        # Автоматическое определение разделителя
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(2048)
            delimiter = ',' if ',' in sample else ';' if ';' in sample else '\t'

        df = pd.read_csv(file_path, sep=delimiter, low_memory=False)

        # Преобразование времени
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)

        print(f"Загружено {len(df)} строк из {file_path}")
        return df

    except Exception as e:
        print(f"Ошибка при загрузке {file_path}: {str(e)}")
        return None


def merge_datasets(meter_data, location_data):
    """Объединяет данные показаний счетчиков с метаданными"""
    if meter_data is None:
        return None

    try:
        # Автоматическое определение ID колонок
        meter_id_col = 'ManagedObjectid'
        loc_id_col = 'managedObjects_id' if 'managedObjects_id' in location_data.columns else 'ManagedObjectid'

        merged = pd.merge(
            meter_data,
            location_data,
            left_on=meter_id_col,
            right_on=loc_id_col,
            how='left'
        )

        # Стандартизация названий колонок
        if 'Suburb' in merged.columns:
            merged.rename(columns={'Suburb': 'suburb'}, inplace=True)
        if 'Meter Type' in merged.columns:
            merged.rename(columns={'Meter Type': 'meter_type'}, inplace=True)
        if 'Usage Type' in merged.columns:
            merged.rename(columns={'Usage Type': 'usage_type'}, inplace=True)

        return merged

    except Exception as e:
        print(f"Ошибка при объединении данных: {e}")
        return meter_data

def initialization_data():
    METER_DATA_FILE = 'dataset/combined_data.csv'
    LOCATION_DATA_FILE = 'dataset/managedobject_details.csv'

    # 1. Загрузка данных
    print("Загрузка данных...")
    meter_data = load_data(METER_DATA_FILE)
    location_data = load_data(LOCATION_DATA_FILE)

    # 2. Объединение данных
    combined_data = merge_datasets(meter_data, location_data)
    if combined_data is None:
        print("Не удалось объединить данные")
            #return

    filter_options = {
        'available_meters': combined_data[
            'ManagedObjectid'].unique().tolist() if 'ManagedObjectid' in combined_data.columns else [],
        'available_cities': combined_data[
            'suburb'].dropna().unique().tolist() if 'suburb' in combined_data.columns else [],
        'available_meter_types': combined_data[
            'typeM'].dropna().unique().tolist() if 'typeM' in combined_data.columns else [],
    }

    filters = {
        'start_date': None,
        'end_date': None,
        'meter_ids': None,
        'cities': None,
        'meter_types': None,
        'usage_types': None
    }

    return combined_data, filter_options, filters

def filter_data(df, filters):
    """Применяет все фильтры к данным"""
    if df is None:
        return None

    filtered = df.copy()

    # Фильтр по дате
    if filters.get('start_date') or filters.get('end_date'):
        filtered = filter_by_date(filtered, filters['start_date'], filters['end_date'])

    # Фильтр по счетчикам
    if filters.get('meter_ids'):
        filtered = filter_by_meters(filtered, filters['meter_ids'])

    # Фильтр по городам
    if filters.get('cities') and 'suburb' in filtered.columns:
        filtered = filter_by_city(filtered, filters['cities'])

    # Фильтр по типам счетчиков
    if filters.get('meter_types') and 'meter_type' in filtered.columns:
        filtered = filter_by_meter_type(filtered, filters['meter_types'])

    # Фильтр по типу использования
    if filters.get('usage_types') and 'usage_type' in filtered.columns:
        filtered = filter_by_usage_type(filtered, filters['usage_types'])

    print(filtered)

    return filtered


def filter_by_date(df, start_date=None, end_date=None):
    """Фильтрация по диапазону дат с обработкой временных зон UTC"""
    if df is None or df.empty or 'time' not in df.columns:
        return df

    try:
        # Убедимся, что столбец времени в UTC
        if not pd.api.types.is_datetime64tz_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'], utc=True)

        # Преобразуем входные даты в UTC
        start_date = pd.to_datetime(start_date, utc=True) if start_date else df['time'].min()
        end_date = pd.to_datetime(end_date, utc=True) if end_date else df['time'].max()

        # Добавляем 1 день к конечной дате для включения всех записей за последний день
        end_date = end_date + pd.Timedelta(days=1)

        # Применяем фильтр
        mask = (df['time'] >= start_date) & (df['time'] < end_date)
        return df[mask]

    except Exception as e:
        print(f"Ошибка фильтрации по дате: {e}")
        return df

def filter_by_meters(df, meter_ids):
    """Фильтрация по ID счетчиков"""
    if df is None or not meter_ids:
        return df

    try:
        return df[df['ManagedObjectid'].astype(str).isin([str(mid) for mid in meter_ids])]
    except Exception as e:
        print(f"Ошибка фильтрации по счетчикам: {e}")
        return df


def filter_by_city(df, cities):
    """Фильтрация по городам"""
    if df is None or not cities or 'suburb' not in df.columns:
        return df

    try:
        cities = [city.strip().upper() for city in cities]
        return df[df['suburb'].str.upper().isin(cities)]
    except Exception as e:
        print(f"Ошибка фильтрации по городам: {e}")
        return df


def filter_by_meter_type(df, meter_types):
    """Фильтрация по типам счетчиков"""
    if df is None or not meter_types or 'meter_type' not in df.columns:
        return df

    try:
        meter_types = [mt.strip().lower() for mt in meter_types]
        return df[df['meter_type'].str.lower().isin(meter_types)]
    except Exception as e:
        print(f"Ошибка фильтрации по типам счетчиков: {e}")
        return df


def filter_by_usage_type(df, usage_types):
    """Фильтрация по типу использования (Non-Residential/Residential)"""
    if df is None or not usage_types or 'usage_type' not in df.columns:
        return df

    try:
        usage_types = [ut.strip().lower() for ut in usage_types]
        return df[df['usage_type'].str.lower().isin(usage_types)]
    except Exception as e:
        print(f"Ошибка фильтрации по типу использования: {e}")
        return df

def display_results(df):
    """Отображает результаты фильтрации"""
    if df is None or df.empty:
        print("\nНет данных для отображения.")
        return

    print("\n=== РЕЗУЛЬТАТЫ ФИЛЬТРАЦИИ ===")
    print(f"Всего записей: {len(df)}")

    if 'time' in df.columns:
        print(f"\nПериод данных:")
        print(f"  Начало: {df['time'].min()}")
        print(f"  Конец:  {df['time'].max()}")

    if 'ManagedObjectid' in df.columns:
        print(f"\nУникальных счетчиков: {len(df['ManagedObjectid'].unique())}")

    if 'suburb' in df.columns and df['suburb'].notna().any():
        print(f"\nГорода в выборке:")
        print(", ".join(df['suburb'].dropna().unique()))

    if 'typeM' in df.columns and df['typeM'].notna().any():
        print(f"\nТипы счетчиков в выборке:")
        print(", ".join(df['typeM'].dropna().unique()))

    print("\nПервые 10 записей:")
    print(df.head(10).to_string(index=False))

