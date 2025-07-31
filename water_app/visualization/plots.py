import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

# Поддерживаемые форматы изображений
SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'svg', 'pdf']


def save_plot(fig, filename='plot', format='png', directory='plots'):
    """
    Сохраняет график в файл с указанным форматом.

    Параметры:
        fig: matplotlib figure объект
        filename: имя файла (без расширения)
        format: формат файла (png, jpg, svg, pdf)
        directory: директория для сохранения
    """
    # Создаем директорию, если ее нет
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Формируем полный путь к файлу
    filepath = os.path.join(directory, f"{filename}.{format.lower()}")

    # Сохраняем в выбранном формате
    fig.savefig(filepath, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"График сохранен как: {filepath}")


def plot_consumption_trend(df, meter_id=None, save=False, format='png'):
    """Визуализация трендов потребления"""
    if df is None or df.empty:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(15, 6))

    if meter_id:
        meter_data = flow_data[flow_data['ManagedObjectid'] == meter_id]
        sns.lineplot(data=meter_data, x='time', y='Value', label=f'Счетчик {meter_id}')
        plt.title(f'Потребление воды - счетчик {meter_id}')
    else:
        sns.lineplot(data=flow_data, x='time', y='Value', label='Все счетчики')
        plt.title('Потребление воды - все счетчики')

    plt.xlabel('Время')
    plt.ylabel('Расход воды (л)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save:
        name_suffix = f"_meter_{meter_id}" if meter_id else ""
        save_plot(fig, f"consumption_trend{name_suffix}", format)
    else:
        plt.show()
        return fig


def plot_hourly_pattern(df, save=False, format='png'):
    """Визуализация суточных паттернов потребления"""
    if df is None or df.empty:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    flow_data['hour'] = flow_data['time'].dt.hour
    hourly_stats = flow_data.groupby('hour')['Value'].mean().reset_index()

    fig = plt.figure(figsize=(12, 6))
    sns.barplot(data=hourly_stats, x='hour', y='Value')
    plt.title('Средний расход воды по часам суток')
    plt.xlabel('Час дня')
    plt.ylabel('Средний расход (л)')
    plt.grid(True)

    if save:
        save_plot(fig, "hourly_pattern", format)
    else:
        plt.show()
        return fig


def plot_anomalies(df, anomalies, save=False, format='png'):
    """Визуализация аномалий"""
    if df is None or anomalies.empty:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(15, 8))

    # График потребления
    for meter_id, group in flow_data.groupby('ManagedObjectid'):
        plt.plot(group['time'], group['Value'], alpha=0.3, label=f'Счетчик {meter_id}')

    # Аномалии
    for _, row in anomalies.iterrows():
        plt.scatter(row['time'], row['value'], color='red', s=100, alpha=0.7)

    plt.title('Аномалии в потреблении воды')
    plt.xlabel('Время')
    plt.ylabel('Расход воды (л)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save:
        save_plot(fig, "anomalies", format)
    else:
        plt.show()
        return fig


def plot_leaks(df, leaks, save=False, format='png'):
    """Визуализация протечек"""
    if df is None or leaks.empty:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(15, 8))

    # График потребления
    for meter_id, group in flow_data.groupby('ManagedObjectid'):
        plt.plot(group['time'], group['Value'], alpha=0.3, label=f'Счетчик {meter_id}')

    # Протечки
    for _, row in leaks.iterrows():
        plt.axvspan(row['start_time'], row['end_time'], color='red', alpha=0.2)
        plt.text(row['start_time'], row['max_flow'],
                 f"Протечка ({row['leak_type']})",
                 bbox=dict(facecolor='white', alpha=0.8))

    plt.title('Потенциальные протечки воды')
    plt.xlabel('Время')
    plt.ylabel('Расход воды (л)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save:
        save_plot(fig, "leaks", format)
    else:
        plt.show()
        return fig

def plot_meter_health_sw(df, health_stats, save=False, format='png'):
    """Визуализация технического состояния счетчиков"""
    if df is None or not health_stats:
        return

    # График состояния переключателей
    if 'switches' in health_stats and 'stats' in health_stats['switches']:
        switch_data = df[df['Series'] == 'SW2'].copy()
        if not switch_data.empty:
            fig = plt.figure(figsize=(12, 6))
            sns.countplot(data=switch_data, x='ManagedObjectid', hue='Value')
            plt.title('Состояние переключателей')
            plt.xlabel('ID счетчика')
            plt.ylabel('Количество показаний')
            plt.xticks(rotation=90)
            plt.grid(True)
            plt.tight_layout()

            if save:
                save_plot(fig, "meter_switches", format)
            else:
                plt.show()
                return fig

def plot_meter_health_temp(df, health_stats, save=False, format='png'):
    """Визуализация технического состояния счетчиков"""
    if df is None or not health_stats:
        return

    # График температуры
    if 'temperature' in health_stats and 'stats' in health_stats['temperature']:
        temp_data = df[df['Series'] == 'Max'].copy()
        if not temp_data.empty:
            fig = plt.figure(figsize=(12, 6))
            sns.boxplot(data=temp_data, x='ManagedObjectid', y='Value')
            plt.axhline(y=50, color='r', linestyle='--', label='Высокая температура')
            plt.axhline(y=-10, color='b', linestyle='--', label='Низкая температура')
            plt.title('Температура счетчиков')
            plt.xlabel('ID счетчика')
            plt.ylabel('Температура (°C)')
            plt.xticks(rotation=90)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            if save:
                save_plot(fig, "meter_temperature", format)
            else:
                plt.show()
                return fig



def plot_meter_type_comparison(df, save=False, format='png'):
    """Визуализация сравнения типов счетчиков"""
    if df is None or df.empty or 'typeM' not in df.columns:
        return

    flow_data = df[(df['Series'] == 'P1') | (df['typeM'] == '/10266/1')].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(12, 6))
    sns.boxplot(data=flow_data, x='typeM', y='Value')
    plt.title('Сравнение показаний разных типов счетчиков')
    plt.xlabel('Тип счетчика')
    plt.ylabel('Расход воды (л)')
    plt.grid(True)

    if save:
        save_plot(fig, "meter_type_comparison", format)
    else:
        plt.show()
        return fig


def plot_predictions(df, predictions, save=False, format='png'):
    """Визуализация прогноза потребления"""
    if df is None or predictions.empty:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(15, 6))

    # Исторические данные
    for meter_id, group in flow_data.groupby('ManagedObjectid'):
        plt.plot(group['time'], group['Value'], label=f'Счетчик {meter_id} (история)')

    # Прогноз
    for meter_id, group in predictions.groupby('meter_id'):
        plt.plot(group['time'], group['predicted'], '--', label=f'Счетчик {meter_id} (прогноз)')

    plt.title('Прогноз потребления воды')
    plt.xlabel('Время')
    plt.ylabel('Расход воды (л)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save:
        save_plot(fig, "consumption_predictions", format)
    else:
        plt.show()
        return fig


def plot_city_comparison(df, save=False, format='png'):
    """Визуализация сравнения городов"""
    if df is None or df.empty or 'suburb' not in df.columns:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    fig = plt.figure(figsize=(12, 6))
    sns.boxplot(data=flow_data, x='suburb', y='Value')
    plt.title('Сравнение потребления воды по городам')
    plt.xlabel('Город')
    plt.ylabel('Расход воды (л)')
    plt.xticks(rotation=45)
    plt.grid(True)

    if save:
        save_plot(fig, "city_comparison", format)
    else:
        plt.show()
        return fig


def plot_date_comparison(df, save=False, format='png'):
    """Визуализация сравнения по датам"""
    if df is None or df.empty or 'time' not in df.columns:
        return

    flow_data = df[df['Series'] == 'P1'].copy()
    if flow_data.empty:
        return

    flow_data['date'] = flow_data['time'].dt.date
    date_stats = flow_data.groupby('date')['Value'].mean().reset_index()

    fig = plt.figure(figsize=(15, 6))
    sns.lineplot(data=date_stats, x='date', y='Value')
    plt.title('Среднее потребление воды по дням')
    plt.xlabel('Дата')
    plt.ylabel('Средний расход (л)')
    plt.grid(True)

    if save:
        save_plot(fig, "date_comparison", format)
    else:
        plt.show()
        return fig