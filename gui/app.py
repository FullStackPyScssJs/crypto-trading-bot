import tkinter as tk
from tkinter import ttk
from components.dashboard import Dashboard
from components.logs_viewer import LogsViewer
from components.notifications import Notifications
from components.settings import Settings

class TradingBotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("  TitanFlow")
        self.geometry("1200x800")  # Standard window size
        self.configure(bg='#2E3440')
        self.fullscreen = False

        # Title bar (dark gray)
        self.title_bar = tk.Frame(self, bg='#2E3440', height=30)
        self.title_bar.pack(fill=tk.X)

        self.title_label = tk.Label(self.title_bar, text="  TitanFlow", bg='#2E3440', fg='#D8DEE9', font=('Arial', 12))
        self.title_label.pack(side=tk.LEFT, padx=10)

        self.close_button = tk.Button(self.title_bar, text="X", bg='#2E3440', fg='#D8DEE9', relief=tk.FLAT, command=self.destroy)
        self.close_button.pack(side=tk.RIGHT, padx=10)

        self.fullscreen_button = tk.Button(self.title_bar, text="⛶", bg='#2E3440', fg='#D8DEE9', relief=tk.FLAT, command=self.toggle_fullscreen)
        self.fullscreen_button.pack(side=tk.RIGHT, padx=10)

        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)

        # Sidebar state
        self.sidebar_expanded = False
        self.sidebar_width_collapsed = 50
        self.sidebar_width_expanded = 200  # Adjusted width to match the title length

        # Sidebar
        self.sidebar = tk.Frame(self, bg='#3B4252', width=self.sidebar_width_collapsed, height=800)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Hamburger icon for sidebar toggle
        self.hamburger_icon = tk.Label(self.sidebar, text="☰", bg='#3B4252', fg='#D8DEE9', font=('Arial', 20))
        self.hamburger_icon.pack(pady=20)
        self.hamburger_icon.bind("<Button-1>", self.toggle_sidebar)
        self.hamburger_icon.bind("<Enter>", lambda e: self.hamburger_icon.config(fg='#88C0D0'))
        self.hamburger_icon.bind("<Leave>", lambda e: self.hamburger_icon.config(fg='#D8DEE9'))

        # Button container in sidebar
        self.button_container = tk.Frame(self.sidebar, bg='#3B4252')
        self.button_container.pack(fill=tk.X, padx=5, pady=5)

        # Buttons for sidebar
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Logs", self.show_logs),
            ("Notifications", self.show_notifications),
            ("Settings", self.show_settings)
        ]
        for text, command in buttons:
            button = tk.Button(self.button_container, text=text, bg='#3B4252', fg='#D8DEE9', relief=tk.FLAT, font=('Arial', 12), command=command)
            button.pack(fill=tk.X, pady=10, ipady=10)
            button.bind("<Enter>", lambda e, b=button: b.config(bg='#4C566A'))
            button.bind("<Leave>", lambda e, b=button: b.config(bg='#3B4252'))

        # Main content container
        self.container = tk.Frame(self, bg='#2E3440')
        self.container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Views initialization
        self.dashboard = Dashboard(self.container)
        self.logs_viewer = LogsViewer(self.container)
        self.notifications = Notifications(self.container)
        self.settings = Settings(self.container)

        # Set default view to Dashboard
        self.show_dashboard()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.overrideredirect(True)  # Hide title bar in fullscreen
            self.attributes("-fullscreen", True)
        else:
            self.overrideredirect(False)  # Restore title bar
            self.attributes("-fullscreen", False)
            self.geometry("1200x800")  # Reset window size after fullscreen

    def toggle_sidebar(self, event=None):
        """ Toggle the sidebar visibility without delay. """
        if self.sidebar_expanded:
            self.sidebar.config(width=self.sidebar_width_collapsed)
            self.button_container.pack_forget()  # Hide buttons when collapsing
        else:
            self.sidebar.config(width=self.sidebar_width_expanded)
            self.button_container.pack(fill=tk.X, padx=5, pady=5)  # Show buttons when expanding
        self.sidebar_expanded = not self.sidebar_expanded

    def show_dashboard(self):
        self.hide_all_frames()
        self.dashboard.pack(fill=tk.BOTH, expand=True)

    def show_logs(self):
        self.hide_all_frames()
        self.logs_viewer.pack(fill=tk.BOTH, expand=True)

    def show_notifications(self):
        self.hide_all_frames()
        self.notifications.pack(fill=tk.BOTH, expand=True)

    def show_settings(self):
        self.hide_all_frames()
        self.settings.pack(fill=tk.BOTH, expand=True)

    def hide_all_frames(self):
        self.dashboard.pack_forget()
        self.logs_viewer.pack_forget()
        self.notifications.pack_forget()
        self.settings.pack_forget()

if __name__ == "__main__":
    app = TradingBotApp()
    app.mainloop()

