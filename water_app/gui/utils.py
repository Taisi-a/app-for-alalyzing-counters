from tkinter import ttk
import gui

def show_loading_screen():
    gui.loading_frame = ttk.Frame(gui.root)
    gui.loading_frame.pack(fill="both", expand=True)

    ttk.Label(gui.loading_frame, text="Загрузка данных...", font=('Helvetica', 16)).pack(pady=50)
    progress = ttk.Progressbar(gui.loading_frame, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    gui.root.update()


def hide_loading_screen():
    gui.loading_frame.pack_forget()