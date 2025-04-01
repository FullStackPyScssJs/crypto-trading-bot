import tkinter as tk
from tkinter import ttk

class Dashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#2E3440')
        self.label = tk.Label(self, text="Dashboard", fg='#D8DEE9', bg='#2E3440', font=('Arial', 24))
        self.label.pack(pady=20)

        # Signals frame
        self.signals_frame = tk.Frame(self, bg='#3B4252')
        self.signals_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Load signals button
        self.load_button = tk.Button(self.signals_frame, text="Load Signals", bg='#4C566A', fg='#D8DEE9', font=('Arial', 12), command=self.load_signals)
        self.load_button.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.signals_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=10)

        # Placeholder for signals
        self.placeholder_label = tk.Label(self.signals_frame, text="Signals will appear here", fg='#D8DEE9', bg='#3B4252', font=('Arial', 16))
        self.placeholder_label.pack(pady=50)

    def load_signals(self):
        # Reset progress bar and simulate loading
        self.progress['value'] = 0
        self._simulate_loading()

    def _simulate_loading(self):
        current_value = self.progress['value']
        if current_value < 100:
            new_value = current_value + 10  # Increase progress
            self.progress['value'] = new_value
            self.after(500, self._simulate_loading)  # Repeat until progress reaches 100
        else:
            self.progress.stop()
            self.placeholder_label.config(text="Signals loaded successfully!")
