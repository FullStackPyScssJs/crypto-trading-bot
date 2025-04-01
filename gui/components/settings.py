import tkinter as tk

class Settings(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#2E3440')
        self.label = tk.Label(self, text="Settings", fg='#D8DEE9', bg='#2E3440', font=('Arial', 24))
        self.label.pack(pady=20)

        # Monthly access key
        self.access_key_label = tk.Label(self, text="Monthly Access Key:", fg='#D8DEE9', bg='#2E3440', font=('Arial', 12))
        self.access_key_label.pack(pady=5)
        self.access_key_entry = tk.Entry(self, bg='#4C566A', fg='#D8DEE9', font=('Arial', 12))
        self.access_key_entry.pack(fill=tk.X, padx=10, pady=5)

        # Submit button to confirm access key
        self.submit_button = tk.Button(self, text="Submit Access Key", bg='#5E81AC', fg='#D8DEE9', font=('Arial', 12), command=self.submit_access_key)
        self.submit_button.pack(pady=10)

        # Label for feedback
        self.feedback_label = tk.Label(self, fg='#D8DEE9', bg='#2E3440', font=('Arial', 12))
        self.feedback_label.pack(pady=5)

    def submit_access_key(self):
        # Capture the access key entered
        access_key = self.access_key_entry.get()

        # Treat every key as valid
        if access_key:
            # Clear the access key field after validation
            self.access_key_entry.delete(0, tk.END)
            self.feedback_label.config(text="Access Key is valid!", fg="#A3BE8C")  # Green success message
        else:
            # If the field is empty, show error
            self.feedback_label.config(text="Please enter an Access Key.", fg="#D08770")  # Red error message
