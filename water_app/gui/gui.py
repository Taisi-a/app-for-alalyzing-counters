import tkinter as tk
from tkinter import ttk, scrolledtext

import threading

from core.data_processing import initialization_data, filter_data

import gui
import gui.utils
import gui.run_button
import gui.filters
import gui.menu


def create_main_interface(filter_options, filters):

    # Главный контейнер с прокруткой
    main_frame = ttk.Frame(gui.root)
    main_frame.pack(fill="both", expand=True)

    # Холст и скроллбар
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Область результатов
    result_frame = ttk.LabelFrame(scrollable_frame, text="Результаты анализа")
    result_frame.pack(fill="x", padx=10, pady=5)

    gui.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10)
    gui.result_text.pack(fill="x", padx=5, pady=5)
    gui.result_text.config(state='disabled')

    # Область графиков
    graph_frame = ttk.LabelFrame(scrollable_frame, text="Графики")
    graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

    gui.graph_container = ttk.Frame(graph_frame)
    gui.graph_container.pack(fill="both", expand=True)

    # Вкладки
    tab_control = ttk.Notebook(scrollable_frame)

    tabs = [
        ("Анализ данных", "Анализ данных"),
        ("Сравнение", "Сравнение"),
        ("Тех состояние", "Технический анализ")
    ]

    for tab_text, tab_name in tabs:
        tab = ttk.Frame(tab_control)
        tab_control.add(tab, text=tab_text)

        if tab_name == "Сравнение":
            comparison_filters = gui.filters.create_comparison_filters(tab, filter_options)
            gui.run_button.create_action_buttons(tab, tab_name, filters, comparison_filters=comparison_filters)
        else:
            filter_widgets = gui.filters.create_filters_frame(tab, tab_name, filter_options)
            gui.run_button.create_action_buttons(tab, tab_name, filters, filter_widgets=filter_widgets)

        # Для всех вкладок одинаковый набор элементов
        gui.menu.create_graph_selector(tab, tab_name)
        gui.menu.create_report_options(tab, tab_name)

    tab_control.pack(fill="x", padx=10, pady=5)

def load_data():
    """Загрузка данных"""
    gui.utils.show_loading_screen()
    gui.df, filter_options, filters = initialization_data()
    gui.utils.hide_loading_screen()
    create_main_interface(filter_options, filters)


def grafic():
    gui.root = tk.Tk()
    gui.root.title("Анализ данных счетчиков")
    gui.root.geometry("1200x800")

    # Запуск загрузки данных в отдельном потоке
    threading.Thread(target=load_data, daemon=True).start()

    gui.root.mainloop()
