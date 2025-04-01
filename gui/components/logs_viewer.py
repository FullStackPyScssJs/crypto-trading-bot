import tkinter as tk
from tkinter import ttk

class LogsViewer(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#2E3440')
        self.label = tk.Label(self, text="Logs Viewer", fg='#D8DEE9', bg='#2E3440', font=('Arial', 24))
        self.label.pack(pady=20)

        # Logs table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview", background='#4C566A', foreground='#D8DEE9', fieldbackground='#4C566A', font=('Arial', 12))
        style.configure("Custom.Treeview.Heading", background='#3B4252', foreground='#D8DEE9', font=('Arial', 14, 'bold'))
        style.map("Custom.Treeview", background=[('selected', '#88C0D0')])

        self.logs_table = ttk.Treeview(self, columns=("Date", "Message"), show="headings", style="Custom.Treeview")
        self.logs_table.heading("Date", text="Date")
        self.logs_table.heading("Message", text="Message")
        self.logs_table.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Sample logs
        self.logs_table.insert("", "end", values=("2023-10-01", "Sample log 1"))
        self.logs_table.insert("", "end", values=("2023-10-02", "Sample log 2"))