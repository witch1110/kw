import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

# Налаштування стилю
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AudioUploadWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grab_set()

        self.title("Завантаження аудіо для сегментації")
        self.geometry("600x600")

        window_width = 600
        window_height = 600
        
        # Отримуємо розміри екрана користувача
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Обчислюємо координати для центру
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Встановлюємо розмір і позицію
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Змінна для зберігання шляху до файлу
        self.selected_file_path = None

        # --- Головний контейнер ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20)
        self.main_frame.pack(padx=40, pady=40, fill="both", expand=True)

        self.label = ctk.CTkLabel(
            self.main_frame, 
            text="Крок 1: Оберіть аудіофайл", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label.pack(pady=(30, 20))

        # --- Кнопка вибору файлу ---
        self.upload_btn = ctk.CTkButton(
            self.main_frame,
            text="📁 ОБРАТИ ФАЙЛ",
            height=50,
            width=200,
            fg_color="#1f6aa5",
            command=self.choose_file
        )
        self.upload_btn.pack(pady=10)

        # Мітка для відображення назви обраного файлу
        self.file_label = ctk.CTkLabel(
            self.main_frame, 
            text="Файл не обрано", 
            text_color="gray",
            wraplength=350 # щоб довга назва не вилазила за межі
        )
        self.file_label.pack(pady=10)

       # --- Вибір методу ---
        self.method_label = ctk.CTkLabel(
            self.main_frame, 
            text="Крок 2: Оберіть метод сегментації", 
            font=ctk.CTkFont(size=16)
        )
        self.method_label.pack(pady=(20, 10))

        # ДОДАЄМО ЗМІННУ ДЛЯ КОНТРОЛЕРА
        self.method_var = ctk.StringVar(value="Novelty Analysis") 

        self.method_menu = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Novelty Analysis", "Librosa (Onset)", "Machine Learning (CNN)"],
            width=250,
            variable=self.method_var # ПРИВ'ЯЗУЄМО ЗМІННУ ТУТ
        )
        self.method_menu.pack(pady=10)

        # --- Кнопка запуску ---
        # ВАЖЛИВО: Контролер шукає self.run_btn
        self.run_btn = ctk.CTkButton(
            self.main_frame,
            text="🚀 СЕГМЕНТУВАТИ",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=60,
            width=300,
            fg_color="green",
            hover_color="#050"
            # Прибираємо command тут, бо її призначить Контролер
        )
        self.run_btn.pack(pady=(30, 15))

        # --- Кнопка Назад ---
        self.back_btn = ctk.CTkButton(
            self.main_frame,
            text="← На головну",
            font=ctk.CTkFont(size=14),
            height=40,
            width=300,
            fg_color="transparent",
            border_width=2,
            border_color="gray",
            command=self.go_back
        )
        
        self.back_btn.pack(pady=10)

    def choose_file(self):
        # Відкриваємо діалогове вікно для вибору файлу
        file_path = filedialog.askopenfilename(
            title="Оберіть аудіофайл",
            filetypes=(("Audio Files", "*.mp3 *.wav *.ogg *.flac"), ("All Files", "*.*"))
        )
        
        if file_path:
            self.selected_file_path = file_path
            # Показуємо тільки ім'я файлу без повного шляху для краси
            filename = os.path.basename(file_path)
            self.file_label.configure(text=f"Обрано: {filename}", text_color="white")
            print(f"Обрано файл: {file_path}")

    def start_segmentation(self):
        if not self.selected_file_path:
            messagebox.showwarning("Помилка", "Будь ласка, спочатку оберіть аудіофайл!")
            return

        method = self.method_menu.get()
        file = os.path.basename(self.selected_file_path)
        
        # Тут зазвичай йде перехід до вікна з результатом або запуск алгоритму
        messagebox.showinfo(
            "Процес розпочато", 
            f"Запуск сегментації...\nФайл: {file}\nМетод: {method}"
        )
        print(f"Запуск алгоритму {method} для {file}")

    def go_back(self):
        self.destroy()
        self.parent.deiconify()

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()  # ховаємо головне
    app = AudioUploadWindow(root)
    app.mainloop()