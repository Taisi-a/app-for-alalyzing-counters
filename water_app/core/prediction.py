import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from datetime import timedelta


def predict_consumption(df, forecast_hours=24, min_history_days=7):
    """Устойчивая функция прогнозирования с полной обработкой ошибок"""
    if df is None or df.empty:
        return pd.DataFrame()

    # Проверка обязательных колонок
    required_cols = ['time', 'ManagedObjectid', 'Value']
    if not all(col in df.columns for col in required_cols):
        missing = set(required_cols) - set(df.columns)
        print(f"Отсутствуют обязательные колонки: {missing}")
        return pd.DataFrame()

    try:
        # Предобработка данных
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        df = df.sort_values(['ManagedObjectid', 'time'])

        # Обработка значений
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Value'])
        df = df[df['Value'].between(0, 1000)]  # Фильтр нереалистичных значений

        predictions = []

        for meter_id, group in df.groupby('ManagedObjectid'):
            try:
                # Проверка достаточности данных
                if len(group) < min_history_days * 24:
                    continue

                # Определение частоты данных с защитой от деления на ноль
                try:
                    freq = group['time'].diff().mode()[0] if len(group) > 1 else pd.Timedelta(hours=1)
                    if pd.isna(freq) or freq == pd.Timedelta(0):
                        freq = pd.Timedelta(hours=1)
                except:
                    freq = pd.Timedelta(hours=1)

                # Создание временного ряда с защитой от ошибок
                try:
                    ts = group.set_index('time')['Value'].resample(freq).mean().ffill()
                    if len(ts) < 24:  # Минимум 1 день данных
                        continue
                except:
                    continue

                # Создание признаков без скользящих статистик
                features = pd.DataFrame({
                    'value': ts,
                    'hour': ts.index.hour,
                    'day_of_week': ts.index.dayofweek,
                    'is_weekend': ts.index.dayofweek.isin([5, 6]).astype(int)
                })

                # Добавление лаговых признаков
                for lag in [1, 2, 3, 24]:
                    features[f'lag_{lag}'] = ts.shift(lag)

                # Удаление строк с пропусками
                features = features.dropna()
                if len(features) < 24:
                    continue

                # Разделение на признаки и целевую переменную
                X = features.drop(columns=['value'])
                y = features['value']

                # Простая модель с явным преобразованием в dense
                numeric_features = X.select_dtypes(include=np.number).columns.tolist()
                categorical_features = ['hour', 'day_of_week', 'is_weekend']

                preprocessor = ColumnTransformer([
                    ('num', SimpleImputer(strategy='median'), numeric_features),
                    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
                ])

                model = Pipeline([
                    ('preprocessor', preprocessor),
                    ('regressor', HistGradientBoostingRegressor(
                        max_iter=100,
                        random_state=42,
                        scoring='neg_mean_absolute_error'
                    ))
                ])

                # Обучение модели
                model.fit(X, y)

                # Прогнозирование
                last_date = features.index[-1]
                future_dates = pd.date_range(
                    start=last_date + freq,
                    periods=forecast_hours,
                    freq=freq
                )

                # Пошаговое прогнозирование
                predicted_values = []
                for i, date in enumerate(future_dates):
                    try:
                        # Подготовка признаков для прогноза
                        future_features = {
                            'hour': date.hour,
                            'day_of_week': date.dayofweek,
                            'is_weekend': int(date.dayofweek in [5, 6]),
                            'lag_1': predicted_values[-1] if i > 0 else ts.iloc[-1],
                            'lag_2': predicted_values[-2] if i > 1 else ts.iloc[-1],
                            'lag_3': predicted_values[-3] if i > 2 else ts.iloc[-1],
                            'lag_24': predicted_values[-24] if i > 23 else ts.iloc[-24] if len(ts) >= 24 else ts.iloc[
                                -1]
                        }

                        # Преобразование в DataFrame и прогноз
                        future_df = pd.DataFrame([future_features])
                        pred = model.predict(future_df)[0]
                        predicted_values.append(max(0, pred))
                    except:
                        predicted_values.append(np.nan)
                        continue

                # Удаление NaN из прогнозов
                predicted_values = [x for x in predicted_values if not np.isnan(x)]
                if not predicted_values:
                    continue

                # Сохранение результатов
                result = pd.DataFrame({
                    'time': future_dates[:len(predicted_values)],
                    'meter_id': meter_id,
                    'predicted': predicted_values,
                    'freq_minutes': freq.total_seconds() / 60
                })
                predictions.append(result)

            except Exception as e:
                print(f"Ошибка прогноза для {meter_id}: {str(e)}")
                continue

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        return pd.DataFrame()

    return pd.concat(predictions) if predictions else pd.DataFrame()

def format_predictions(predictions_df: pd.DataFrame) -> str:
    """Форматирование отчета о предсказаниях в строку"""
    if predictions_df.empty:
        return "\nНет данных для прогнозирования или не удалось сделать прогноз\n"

    # Группировка по счетчикам
    meter_counts = predictions_df['meter_id'].value_counts()

    output = ["\n=== ПРОГНОЗ ПОТРЕБЛЕНИЯ ==="]
    output.append(f"Всего прогнозов: {len(predictions_df)}")
    output.append(f"Уникальных счетчиков: {len(meter_counts)}")
    output.append(
        f"Горизонт прогнозирования: {predictions_df['freq_minutes'].iloc[0] * len(predictions_df) / 60:.1f} часов")

    output.append("\nКоличество прогнозов по счетчикам:")
    for meter_id, count in meter_counts.items():
        output.append(f"- {meter_id}: {count} прогнозов")

    # Добавляем детали по первым нескольким прогнозам для каждого счетчика
    output.append("\n=== ДЕТАЛИ ПРОГНОЗОВ ===")
    for meter_id, group in predictions_df.groupby('meter_id'):
        output.append(f"\nСчетчик: {meter_id}")
        output.append(f"Частота данных: {group['freq_minutes'].iloc[0]:.0f} минут")

        first_pred = group.iloc[0]
        last_pred = group.iloc[-1]

        output.append(f"Период прогноза: {first_pred['time']} - {last_pred['time']}")
        output.append(f"Среднее прогнозируемое значение: {group['predicted'].mean():.2f} л/ч")

        for _, row in group.iterrows():
            output.append(f"- {row['time']}: {row['predicted']:.2f} л")

    return "\n".join(output)