from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import tempfile
import os
import matplotlib.pyplot as plt
import core
import visualization.plots
from core import anomaly_detection, technical_analysis, analysis

pdfmetrics.registerFont(TTFont('DejaVu', 'visualization/DejaVuSans.ttf'))

# Стили для PDF
styles = getSampleStyleSheet()
style_title = ParagraphStyle(
    'Title',
    parent=styles['Heading1'],
    fontName='DejaVu',  # Используем шрифт DejaVu
    fontSize=16,
    alignment=1,
    spaceAfter=12
)
style_heading = ParagraphStyle(
    'Heading',
    parent=styles['Heading2'],
    fontName='DejaVu',  # Используем шрифт DejaVu
    fontSize=12,
    spaceAfter=6
)
style_body = ParagraphStyle(
    'Body',
    parent=styles['BodyText'],
    fontName='DejaVu',  # Используем шрифт DejaVu
    fontSize=10,
    spaceAfter=12
)

def generate_pdf_report(report_data, filename="water_consumption_report.pdf"):
    """Генерация PDF отчета с данными анализа"""
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    # Титульная страница
    elements.append(Paragraph("Отчет по анализу потребления воды", style_title))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"Период: {report_data.get('period', 'не указан')}", style_body))
    elements.append(Paragraph(f"Количество счетчиков: {report_data.get('meter_count', 0)}", style_body))
    elements.append(Spacer(1, 36))

    # Раздел статистики
    elements.append(Paragraph("Общая статистика потребления", style_heading))
    print("444444")

    stats_data = [
        ["Метрика", "Значение"],
        ["Средний расход", f"{report_data.get('avg_consumption', 0):.2f} л/15мин"],
        ["Максимальный расход", f"{report_data.get('max_consumption', 0):.2f} л/15мин"],
        ["Минимальный расход", f"{report_data.get('min_consumption', 0):.2f} л/15мин"],
        ["Медианный расход", f"{report_data.get('median_consumption', 0):.2f} л/15мин"],
        ["Общий объем", f"{report_data.get('total_consumption', 0):.2f} л"],
    ]
    print("444444")

    stats_table = Table(stats_data, colWidths=[2 * inch, 2 * inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 24))

    temp_files = []
    print("444444")

    # Графики
    if 'graphs' in report_data:
        elements.append(Paragraph("Визуализация данных", style_heading))

        for graph in report_data['graphs']:
            # Сохраняем временный файл с графиком
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                graph.savefig(tmpfile.name, dpi=300, bbox_inches='tight')
                img = Image(tmpfile.name, width=5 * inch, height=3 * inch)
                elements.append(img)
                elements.append(Spacer(1, 12))
                temp_files.append(tmpfile.name)
    print("444444")

    # Аномалии
    if 'anomalies' in report_data and not report_data['anomalies'].empty:
        elements.append(Paragraph("Обнаруженные аномалии", style_heading))

        anomaly_data = [["Счетчик", "Время", "Тип", "Значение", "Описание"]]
        for _, row in report_data['anomalies'].iterrows():
            anomaly_data.append([
                str(row['meter_id']),
                str(row['time']),
                row['anomaly_type'],
                f"{row['value']:.2f}",
                row['description'][:50] + "..." if len(row['description']) > 50 else row['description']
            ])

        anomaly_table = Table(anomaly_data, colWidths=[0.8 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 2 * inch])
        anomaly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.mistyrose),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(anomaly_table)
        elements.append(Spacer(1, 24))

    print("444444")
    # Техническое состояние
    if 'health_stats' in report_data:
        elements.append(Paragraph("Техническое состояние счетчиков", style_heading))

        health_data = []
        if 'temperature' in report_data['health_stats']:
            temp_stats = report_data['health_stats']['temperature']['stats']
            health_data.extend([
                ["Температура", "Значение"],
                ["Средняя", f"{temp_stats['mean']['mean']:.2f} °C"],
                ["Минимальная", f"{temp_stats['min']['min']:.2f} °C"],
                ["Максимальная", f"{temp_stats['max']['max']:.2f} °C"],
            ])

        if 'switches' in report_data['health_stats']:
            switch_stats = report_data['health_stats']['switches']['stats']
            health_data.extend([
                ["Переключатели", "Значение"],
                ["Активные", f"{len(report_data['health_stats']['switches']['active_switches'])} шт"],
            ])

        if health_data:
            health_table = Table(health_data, colWidths=[2 * inch, 2 * inch])
            health_table.setStyle(TableStyle([
                 ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                 ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
                 ('FONTSIZE', (0, 0), (-1, 0), 10),
                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                 ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(health_table)

            # Генерация PDF
    print("dddd")
    doc.build(elements)
    print(f"Отчет сохранен как {filename}")

    for filepath in temp_files:
        try:
            os.unlink(filepath)
        except Exception as e:
            print(f"Не удалось удалить {filepath}: {e}")


def perform_analysis_with_pdf(df, filename="report.pdf", modes=None, visualizations=None, tab=None, df2=None):
    """Выполняет анализ и генерирует PDF отчет"""
    if df is None or df.empty:
        print("Нет данных для анализа")
        return
    if tab == "Анализ данных":
        if modes:
            if 1 in modes:
                #здесь код чтобы при выбранном режиме 1 то что выводится на экран в графическом интерфейсе записывалось в пдф красиво
                print("режим 1")
            if 2 in modes:
                print("режим 2")

        if visualizations:
            if 1 in visualizations:
                #Здесь код чтобы график созданный ранее (ну или создавался заного) и тоже отправлялся в пдфку
                print("режим 1")
            if 2 in visualizations:
                #Здесь код чтобы график созданный ранее (ну или создавался заного) и тоже отправлялся в пдфку
                print("режим 1")
            if 3 in visualizations:
                #Здесь код чтобы график созданный ранее (ну или создавался заного) и тоже отправлялся в пдфку
                print("режим 1")



    if tab == "Сравнение":
        if modes:
            if 1 in modes:
                #здесь код чтобы при выбранном режиме 1 то что выводится на экран в графическом интерфейсе записывалось в пдф красиво
                print("режим 1")
            if 2 in modes:
                print("режим 2")

        if visualizations:
            if 1 in visualizations:
                #Здесь код чтобы график созданный ранее (ну или создавался заного) и тоже отправлялся в пдфку
                print("режим 1")
    #и здесь дальше для каждой вкладки и для каждого режима

    #то что написано ниже это просто общее сохдание пдф, это надо будет убрать

    # Выполняем анализ
    analysis = core.analysis.analyze_consumption(df)
    print("11111111")
    anomalies = core.anomaly_detection.detect_anomalies(df)
    print("22222")
    leaks = core.technical_analysis.detect_leaks(df)
    print("333333")
    health_stats = core.technical_analysis.analyze_meter_health(df)
    print("444444")

    # Собираем данные для отчета
    report_data = {
        'period': f"{df['time'].min()} - {df['time'].max()}",
        'meter_count': len(df['ManagedObjectid'].unique()),
        'avg_consumption': analysis.get('avg_consumption', 0),
        'max_consumption': analysis.get('max_consumption', 0),
        'min_consumption': analysis.get('min_consumption', 0),
        'median_consumption': analysis.get('median_consumption', 0),
        'total_consumption': analysis.get('total_consumption', 0),
        'anomalies': anomalies,
        'health_stats': health_stats,
        'graphs': []
    }

    print("55555")

    # Создаем графики для отчета
    if visualizations:
        if 1 in visualizations:
        # График потребления
            fig = visualization.plots.plot_consumption_trend(df)
            if fig:  # убедимся, что фигура действительно была построена
                report_data['graphs'].append(fig)
                plt.close(fig)  # закрываем именно её
        if 3 in visualizations:
            # Суточные паттерны
            fig = visualization.plots.plot_hourly_pattern(df)
            if fig:  # убедимся, что фигура действительно была построена
                report_data['graphs'].append(fig)
                plt.close(fig)  # закрываем именно её

        if 6 in visualizations:
            # Аномалии (если есть)
            if not anomalies.empty:
                fig = visualization.plots.plot_anomalies(df, anomalies)
                if fig:  # убедимся, что фигура действительно была построена
                    report_data['graphs'].append(fig)
                    plt.close(fig)  # закрываем именно её

    # Генерируем PDF
    generate_pdf_report(report_data, filename)

