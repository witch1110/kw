import customtkinter as ctk

class CustomInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.result = None
        self.after(10, self._center_window)


        # Робимо вікно модальним
        self.grab_set()
        self.focus_set()
        self.resizable(False, False)
        
        self.label = ctk.CTkLabel(self, text=text, font=("Arial", 14))
        self.label.pack(pady=(20, 10))
        
        self.entry = ctk.CTkEntry(self, width=300, placeholder_text="Введіть назву тут...")
        self.entry.pack(pady=10)
        self.entry.focus()
        
        self.btn_ok = ctk.CTkButton(self, text="ОК", width=100, command=self.on_ok)
        self.btn_ok.pack(pady=20)
        
        # Закриття на клавішу Enter
        self.bind("<Return>", lambda e: self.on_ok())

    def on_ok(self):
        self.result = self.entry.get()
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.result
    
    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Отримуємо координати і розміри головного вікна
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        # Обчислюємо центр
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.geometry(f'{width}x{height}+{x}+{y}')