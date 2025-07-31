
from tkinter import ttk

from tkinter import Listbox, MULTIPLE, END  # Добавлен импорт



def create_filters_frame(parent, title, filter_options):
    frame = ttk.LabelFrame(parent, text=f"Фильтры ({title})")
    frame.pack(padx=10, pady=5, fill="x")

    # Словарь для хранения элементов интерфейса
    filter_widgets = {
        'date_from': ttk.Entry(frame),
        'date_to': ttk.Entry(frame)
    }

    # Временной промежуток
    ttk.Label(frame, text="Дата с:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    filter_widgets['date_from'].grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Дата по:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    filter_widgets['date_to'].grid(row=0, column=3, padx=5, pady=5)

    # Множественный выбор
    filters = [
        ("city", "Город:", filter_options.get('available_cities', [])),
        ("usage_type", "Тип помещения:", ["Residential", "Non-Residential"]),
        ("meter_id", "Номер счетчика:", filter_options.get('available_meters', [])),
        ("meter_type", "Тип счетчика:", ["c8y_lwm2m", "captis_pulse"])
    ]

    for i, (key, label, options) in enumerate(filters, start=1):
        ttk.Label(frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")

        listbox = Listbox(frame, selectmode=MULTIPLE, height=3, exportselection=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        for option in options:
            listbox.insert(END, option)

        if options:
            listbox.selection_set(0)

        listbox.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
        scrollbar.grid(row=i, column=2, sticky="ns")

        filter_widgets[key] = listbox

    return filter_widgets


def create_comparison_filters(parent, filter_options):
    frame = ttk.LabelFrame(parent, text="Сравнение: Фильтры для сравнения")
    frame.pack(padx=10, pady=5, fill="x")

    # Список для хранения двух наборов фильтров
    comparison_filters = []

    for col in [0, 1]:
        subframe = ttk.Frame(frame)
        subframe.grid(row=0, column=col, padx=10, pady=5, sticky="nsew")

        filter_widgets = {
            'date_from': ttk.Entry(subframe),
            'date_to': ttk.Entry(subframe)
        }

        ttk.Label(subframe, text=f"Набор {col + 1}").pack(anchor="w")

        # Временной промежуток
        ttk.Label(subframe, text="Дата с:").pack(anchor="w")
        filter_widgets['date_from'].pack(fill="x")

        ttk.Label(subframe, text="Дата по:").pack(anchor="w")
        filter_widgets['date_to'].pack(fill="x")

        # Множественный выбор
        filters = [
            ("city", "Город", filter_options.get('available_cities', [])),
            ("usage_type", "Тип помещения", ["Residential", "Non-Residential"]),
            ("meter_id", "Номер счетчика", filter_options.get('available_meters', [])),
            ("meter_type", "Тип счетчика", ["c8y_lwm2m", "captis_pulse"])
        ]

        for key, label, options in filters:
            ttk.Label(subframe, text=label).pack(anchor="w")

            listbox = Listbox(subframe, selectmode=MULTIPLE, height=2, exportselection=0)
            scrollbar = ttk.Scrollbar(subframe, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)

            for option in options:
                listbox.insert(END, option)

            if options:
                listbox.selection_set(0)

            listbox.pack(fill="x")
            scrollbar.pack(side="right", fill="y")

            filter_widgets[key] = listbox

        comparison_filters.append(filter_widgets)

    return comparison_filters
