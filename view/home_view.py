import customtkinter as ctk
from view.library_view import LibraryWindow
from view.segmentation_window import AudioUploadWindow

# Налаштування стилістики
ctk.set_appearance_mode("dark")  # Темна тема
ctk.set_default_color_theme("blue") # Синя колірна схема

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title("Audio Segmenter Pro")
        self.geometry("800x500")

        window_width = 800
        window_height = 500
        
        # Отримуємо розміри екрана користувача
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Обчислюємо координати для центру
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Встановлюємо розмір і позицію
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Робимо так, щоб вміст центрувався
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Створюємо основний контейнер
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0)

        # --- ЗАГОЛОВОК ---
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="AUDIO SEGMENTER", 
            font=ctk.CTkFont(family="Arial", size=42, weight="bold"),
            text_color="#1f6aa5"
        )
        self.title_label.pack(pady=(0, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame, 
            text="Система автоматичного аналізу та сегментації аудіофайлів", 
            font=ctk.CTkFont(size=15),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 40))

        # --- КОНТЕЙНЕР ДЛЯ КНОПОК-КАРТОК ---
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack()

        # Кнопка "СЕГМЕНТУВАТИ"
        self.btn_segment = ctk.CTkButton(
            self.button_frame,
            text="🔍\n\nСЕГМЕНТУВАТИ",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=260,
            height=200,
            corner_radius=20,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.on_segment_click
        )
        self.btn_segment.grid(row=0, column=0, padx=20)

        # Кнопка "БІБЛІОТЕКА"
        self.btn_library = ctk.CTkButton(
            self.button_frame,
            text="📚\n\nБІБЛІОТЕКА",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=260,
            height=200,
            corner_radius=20,
            fg_color="#333333",
            hover_color="#444444",
            command=self.on_library_click
        )
        self.btn_library.grid(row=0, column=1, padx=20)

        # --- ФУТЕР ---
        self.footer_label = ctk.CTkLabel(
            self, 
            text=" ", 
            font=ctk.CTkFont(size=12),
            text_color="#444444"
        )
        self.footer_label.place(relx=0.5, rely=0.95, anchor="center")

    # Методи для кнопок (
    def on_segment_click(self):
        # Імпортуємо тут, щоб уникнути циклічної помилки
        from view.segmentation_window import SegmentationWindow
        
        # Створюємо вікно вибору методу
        self.seg_window = SegmentationWindow(self)
        
        # Передаємо модель та контролер (вони будуть потрібні для кнопки завантаження)
        # Це вікно має «підчепити» логіку в контролері
        self.master.controller.setup_segmentation_events(self.seg_window)

    def on_library_click(self):
        self.withdraw()  # Ховаємо головне вікно
        self.library_window = LibraryWindow(self)

    

if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()