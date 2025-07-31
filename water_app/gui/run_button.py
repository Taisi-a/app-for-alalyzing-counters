
import tkinter as tk
from tkinter import ttk, scrolledtext


import visualization.pdf_report
from core.data_processing import filter_data
from core.analysis import perform_analysis
from core.technical_analysis import perform_technical_analysis
import core.comparison

import gui
import gui.utils
import gui.graps


def run_analysis(tab_name, filtered_data, selected_modes=None, selected_graphs=None, save_format=None, filtered_data2=None):  # Добавляем параметр filtered_data
    """Функция для выполнения анализа с учётом отфильтрованных данных"""

    print(f"Режимы для анализа: {selected_modes}")  # Проверка
    print(f"Выбранные графики: {selected_graphs}")  # Логируем выбор графиков

    # Вывод результатов
    gui.result_text.config(state='normal')
    gui.result_text.insert(tk.END, f"\n=== Результаты анализа ({tab_name}) ===\n")

    if tab_name == "Сравнение":
        stats = core.comparison.perform_comparison(filtered_data, selected_modes, df2=filtered_data2)
        gui.result_text.insert(tk.END, stats)

    elif tab_name == "Анализ данных":
        stats = perform_analysis(filtered_data, selected_modes)
        gui.result_text.insert(tk.END, stats)
    else:
        stats = perform_technical_analysis(filtered_data, selected_modes)
        gui.result_text.insert(tk.END, stats)

    gui.result_text.config(state='disabled')

    gui.graps.update_graphs(filtered_data, selected_graphs, tab_name, save_format)


def create_action_buttons(parent, tab_name, filters, filter_widgets=None, comparison_filters=None):
    frame = ttk.Frame(parent)
    frame.pack(padx=10, pady=10, fill="x")

    def get_selected_values(widgets):
        """Получает выбранные значения из виджетов"""
        values = {
            'start_date': widgets['date_from'].get(),
            'end_date': widgets['date_to'].get(),
            'cities': [widgets['city'].get(i) for i in widgets['city'].curselection()],
            'usage_types': [widgets['usage_type'].get(i) for i in widgets['usage_type'].curselection()],
            'meter_ids': [widgets['meter_id'].get(i) for i in widgets['meter_id'].curselection()],
            'meter_types': [widgets['meter_type'].get(i) for i in widgets['meter_type'].curselection()]
        }
        print(values)
        return values

    def generate_report():
        selected_modes = []
        selected_graphs = []
        save_format = "PNG"

        for child in parent.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if child["text"] == "Опции отчёта" and hasattr(child, 'checkbox_vars'):
                    selected_modes = [int(mode) for mode, var in child.checkbox_vars.items() if var.get() == 1]
                elif child["text"] == "Выбор графиков":
                    if hasattr(child, 'graph_vars'):
                        selected_graphs = [graph for graph, var in child.graph_vars.items() if var.get() == 1]
                    if hasattr(child, 'format_var'):
                        save_format = child.format_var.get() or "PNG"

        print(f"Выбранные режимы: {selected_modes}")
        print(f"Выбранные графики: {selected_graphs}")
        print(f"Формат сохранения: {save_format}")

        if filter_widgets:
            filtered_data = filter_data(gui.df, get_selected_values(filter_widgets))
            run_analysis(tab_name, filtered_data, selected_modes, selected_graphs, save_format)
        elif comparison_filters:
            print(comparison_filters)
            filtered_data2 = filter_data(gui.df, get_selected_values(comparison_filters[1]))
            filtered_data = filter_data(gui.df, get_selected_values(comparison_filters[0]))
            run_analysis(tab_name, filtered_data, selected_modes, selected_graphs, save_format, filtered_data2)
        elif tab_name == "Сравнение данных":
            filtered_data2 = gui.df
            filtered_data = gui.df
            run_analysis(tab_name, filtered_data, selected_modes, selected_graphs, save_format, filtered_data2)
        else:
            filtered_data = gui.df
            run_analysis(tab_name, filtered_data, selected_modes, selected_graphs, save_format)



    def generate_file():
        selected_modes = []
        selected_graphs = []
        for child in parent.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if child["text"] == "Опции отчёта" and hasattr(child, 'checkbox_vars'):
                    selected_modes = [int(mode) for mode, var in child.checkbox_vars.items() if var.get() == 1]
                elif child["text"] == "Выбор графиков":
                    if hasattr(child, 'graph_vars'):
                        selected_graphs = [graph for graph, var in child.graph_vars.items() if var.get() == 1]

        print(f"Выбранные режимы: {selected_modes}")
        print(f"Выбранные графики: {selected_graphs}")

        if filter_widgets:
            filtered_data = filter_data(gui.df, get_selected_values(filter_widgets))
            visualization.pdf_report.perform_analysis_with_pdf(filtered_data,"report.pdf", selected_modes, selected_graphs, tab_name)
        elif comparison_filters:
            print(comparison_filters)
            filtered_data2 = filter_data(gui.df, get_selected_values(comparison_filters[1]))
            filtered_data = filter_data(gui.df, get_selected_values(comparison_filters[0]))
            visualization.pdf_report.perform_analysis_with_pdf(filtered_data,"report.pdf", selected_modes, selected_graphs, tab_name, filtered_data2)
        elif tab_name == "Сравнение данных":
            filtered_data2 = gui.df
            filtered_data = gui.df
            visualization.pdf_report.perform_analysis_with_pdf(filtered_data,"report.pdf", selected_modes, selected_graphs, tab_name, filtered_data2)
        else:
            filtered_data = gui.df
            visualization.pdf_report.perform_analysis_with_pdf(filtered_data,"report.pdf", selected_modes, selected_graphs, tab_name)


    ttk.Button(
        frame,
        text="Сгенерировать отчет",
        command=generate_report  # Передаём функцию без вызова ()
    ).pack(side="left", padx=5)

    ttk.Button(frame, text="Экспортировать данные", command=generate_file).pack(side="left", padx=5)
    ttk.Button(frame, text="Очистить фильтры").pack(side="right", padx=5)
