import tkinter as tk

class Notifications(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#2E3440')
        self.label = tk.Label(self, text="Notifications", fg='#D8DEE9', bg='#2E3440', font=('Arial', 24))
        self.label.pack(pady=20)

        # Notifications list
        self.notifications_list = tk.Listbox(self, bg='#3B4252', fg='#D8DEE9', font=('Arial', 12))
        self.notifications_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Sample notifications
        self.notifications_list.insert(0, "New signal: BTC/USD")
        self.notifications_list.insert(1, "Error: API connection lost")