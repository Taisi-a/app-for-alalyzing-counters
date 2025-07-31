import tkinter as tk
from tkinter import ttk, scrolledtext



def create_graph_selector(parent, tab_name):
    frame = ttk.LabelFrame(parent, text="Выбор графиков")
    frame.pack(padx=10, pady=5, fill="x")

    graphs_frame = ttk.Frame(frame)
    graphs_frame.pack(fill="x", padx=5, pady=5)

    # Разные графики для разных вкладок
    if tab_name == "Анализ данных":
        graphs = [
            (1, "График потребления"),
            (2, "Суточные паттерны"),
            (3, "Недельные паттерны"),
            (4, "Прогноз потребления"),
            (5, "График аномалий")
        ]
    elif tab_name == "Сравнение":
        graphs = [
            (1, "Сравнение счетчиков"),
            (2, "Сравнение типов счетчиков"),
            (3, "Сравнение городов"),
            (4, "Сравнение по датам")
        ]
    else:  # Технический анализ
        graphs = [
            (1, "График протечек"),
            (2, "График температуры"),
            (3, "График переключателей"),
        ]

    if not hasattr(frame, 'graph_vars'):
        frame.graph_vars = {}

    for i, (code, name) in enumerate(graphs):
        var = tk.IntVar()
        cb = ttk.Checkbutton(graphs_frame, text=name, variable=var)
        cb.grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)
        frame.graph_vars[code] = var

    # Добавляем выбор формата для всех вкладок
    format_frame = ttk.Frame(frame)
    format_frame.pack(fill="x", padx=5, pady=5)
    ttk.Label(format_frame, text="Формат:").pack(side="left")

    formats = ['png', 'jpg', 'jpeg', 'svg', 'pdf']
    frame.format_var = tk.StringVar(value=formats[0])

    for fmt in formats:
        ttk.Radiobutton(format_frame, text=fmt, value=fmt, variable=frame.format_var).pack(side="left", padx=5)

    return frame


def create_report_options(parent, tab_name):
    frame = ttk.LabelFrame(parent, text="Опции отчёта")
    frame.pack(padx=10, pady=5, fill="x")

    # Разные опции для разных вкладок
    if tab_name == "Анализ данных":
        options = [
            ("1", "1. Общая статистика"),
            ("2", "2. Статистика по счетчикам"),
            ("3", "3. Статистика по городам"),
            ("4", "4. Анализ аномалий"),
            ("5", "5. Суточные и недельные паттерны"),
            ("6", "6. Прогнозирование потребления")
        ]
    elif tab_name == "Сравнение":
        options = [
            ("1", "1. Сравнение основных статистических показателей"),
            ("2", "2. Сравнение показаний по типам счетчиков между датафреймами"),
            ("3", "3. Сравнение временных паттернов"),
            ("4", "4. Выполнение статистических тестов")
        ]
    else:  # Технический анализ
        options = [
            ("1", "1. Поиск протечек"),
            ("2", "2. Анализ температуры"),
            ("3", "3. Анализ переключателей"),
            ("4", "4. Статистика неисправностей"),
            ("5", "5. Рекомендации по замене")
        ]

    if not hasattr(frame, 'checkbox_vars'):
        frame.checkbox_vars = {}

    for i, (mode, text) in enumerate(options):
        var = tk.IntVar(value=0)
        cb = ttk.Checkbutton(
            frame,
            text=text,
            variable=var,
            onvalue=1,
            offvalue=0
        )
        cb.grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)
        frame.checkbox_vars[mode] = var

    return frame