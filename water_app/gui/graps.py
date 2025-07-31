import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd

import visualization.pdf_report

from core.analysis import perform_analysis

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from visualization import plots
import core.technical_analysis
import gui
import gui.utils
import gui.run_button
import gui.filters


def update_graphs(filtered_data, selected_graphs, tab_name, save_format="PNG"):
    """Обновление графиков с исправлением ошибок"""

    # Очистка предыдущих графиков
    for widget in gui.graph_container.winfo_children():
        widget.destroy()

    if not selected_graphs:
        return

    # Основной контейнер с двойной прокруткой
    container = ttk.Frame(gui.graph_container)
    container.pack(fill="both", expand=True)

    # Создаем холст с прокруткой по обеим осям
    tk_canvas = tk.Canvas(container)
    h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=tk_canvas.xview)
    v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=tk_canvas.yview)

    scroll_frame = ttk.Frame(tk_canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: tk_canvas.configure(scrollregion=tk_canvas.bbox("all"))
    )

    tk_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    tk_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

    # Размещаем элементы
    tk_canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # Размеры графиков
    GRAPH_WIDTH = 800
    GRAPH_HEIGHT = 400

    # Для технического анализа получаем данные заранее
    health_stats = {}
    leaks = pd.DataFrame()
    if tab_name == "Технический анализ":
        health_stats = core.technical_analysis.analyze_meter_health(filtered_data)
        leaks = core.technical_analysis.detect_leaks(filtered_data)

    for graph_id in selected_graphs:
        frame = ttk.Frame(scroll_frame,
                          width=GRAPH_WIDTH,
                          height=GRAPH_HEIGHT,
                          borderwidth=1,
                          relief="solid")
        frame.pack_propagate(False)
        frame.pack(fill="both", padx=5, pady=5)

        try:
            # Создание фигуры matplotlib
            fig = plt.figure(figsize=(GRAPH_WIDTH / 100, GRAPH_HEIGHT / 100), dpi=100)

            # Логика создания графиков
            if tab_name == "Анализ данных":
                if graph_id == 1:
                    fig = visualization.plots.plot_consumption_trend(filtered_data, save=False)
                elif graph_id == 2:
                    fig = visualization.plots.plot_hourly_pattern(filtered_data, save=False)
                elif graph_id == 3:
                    fig = visualization.plots.plot_НЕт_ЕЩЕ_ТАКОГО(filtered_data, save=False)
                elif graph_id == 4:
                    fig = visualization.plots.plot_predictions(filtered_data, save=False)
                elif graph_id == 5:
                    fig = visualization.plots.plot_anomalies(filtered_data, save=False)

            elif tab_name == "Сравнение":
                if graph_id == 1:
                    fig = visualization.plots.plot_meter_comparison(filtered_data, save=False)
                elif graph_id == 2:
                    fig = visualization.plots.plot_meter_type_comparison(filtered_data, save=False)
                elif graph_id == 3:
                    fig = visualization.plots.plot_city_comparison(filtered_data, save=False)
                elif graph_id == 4:
                    fig = visualization.plots.plot_date_comparison(filtered_data, save=False)

            elif tab_name == "Технический анализ":
                if graph_id == 1:
                    fig = visualization.plots.plot_leaks(filtered_data, leaks, save=False)
                elif graph_id == 2:
                    fig = visualization.plots.plot_meter_health_temp(filtered_data, health_stats, save=False)
                elif graph_id == 3:
                    fig = visualization.plots.plot_meter_health_sw(filtered_data, health_stats, save=False)

            if fig:
                fig.tight_layout()

                # Создание canvas для matplotlib
                mpl_canvas = FigureCanvasTkAgg(fig, master=frame)
                mpl_canvas.draw()

                # Настройка размеров виджета
                mpl_widget = mpl_canvas.get_tk_widget()
                mpl_widget.config(width=GRAPH_WIDTH - 10, height=GRAPH_HEIGHT - 50)
                mpl_widget.pack(fill="none", expand=False)

                # Кнопка сохранения (более заметная)
                btn_frame = ttk.Frame(frame)
                btn_frame.pack(side="bottom", fill="x", pady=(0, 5))

                save_btn = ttk.Button(
                    btn_frame,
                    text="💾 Сохранить график",
                    style="Accent.TButton",  # Используем стиль для выделения
                    command=lambda f=fig, fmt=save_format: visualization.plots.save_plot(f, format=fmt)
                )
                save_btn.pack(side="right", padx=5, ipadx=10, ipady=3)

        except Exception as e:
            error_label = ttk.Label(frame, text=f"Ошибка: {str(e)}", foreground="red")
            error_label.pack()
            continue

