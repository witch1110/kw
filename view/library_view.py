import customtkinter as ctk
from tkinter import messagebox

class LibraryWindow(ctk.CTkToplevel):
    def __init__(self, parent): 
        super().__init__(parent)
        self.parent = parent
        self.grab_set() 

        self.title("Audio Archive - Library")
        self.geometry("950x700") 
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (950 // 2)
        y = (screen_height // 2) - (700 // 2)
        
        self.geometry(f"950x700+{x}+{y}")

        
        # Кольори
        self.bg_color = "#121212"
        self.sidebar_color = "#0a0a0a"
        self.card_color = "#1e1e1e"
        self.accent_color = "#1f6aa5"
        self.text_white = "#ffffff"
        self.text_gray = "#bbbbbb"
        
        self.configure(fg_color=self.bg_color)

        self.saved_tracks = [
            {"id": 1, "name": "Summer_Vibes_2026.mp3", "date": "12.02.2026", "segments": 6},
            {"id": 2, "name": "Podcast_Recording_01.wav", "date": "15.02.2026", "segments": 12},
            {"id": 3, "name": "Rock_Ballad_Guitar.flac", "date": "01.03.2026", "segments": 4},
            {"id": 4, "name": "Jazz_Improvisation.mp3", "date": "04.03.2026", "segments": 7},
            {"id": 5, "name": "Ambient_Background.wav", "date": "05.03.2026", "segments": 3},
        ]

        self.check_vars = {}

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar, text="МЕНЮ", 
            font=ctk.CTkFont(size=20, weight="bold"), text_color=self.accent_color
        ).pack(pady=30)

        self.select_all_btn = ctk.CTkButton(
            self.sidebar, text="✅ Обрати всі", 
            fg_color="transparent", border_width=1, border_color="#444444",
            command=self.select_all
        )
        self.select_all_btn.pack(pady=10, padx=20, fill="x")

        self.deselect_all_btn = ctk.CTkButton(
            self.sidebar, text="❌ Зняти вибір", 
            fg_color="transparent", border_width=1, border_color="#444444",
            command=self.deselect_all
        )
        self.deselect_all_btn.pack(pady=10, padx=20, fill="x")

        # ТУТ ЗАЛИШАЄМО ТІЛЬКИ ОДНУ КНОПКУ НАЗАД
        self.back_btn = ctk.CTkButton(
            self.sidebar, text="← На головну", 
            fg_color="#333333", hover_color="#444444",
            command=self.go_back 
        )
        self.back_btn.pack(side="bottom", pady=30, padx=20, fill="x")

        # --- Основна область ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=30, pady=20)

        self.top_label = ctk.CTkLabel(
            self.content_frame, text="Збережені результати", 
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.text_white
        )
        self.top_label.pack(anchor="w", pady=(0, 20))

        self.scrollable_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)

        self.action_bar = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_bar.pack(fill="x", side="bottom", pady=(20, 0))

        self.export_btn = ctk.CTkButton(
            self.action_bar, 
            text="📤 ЕКСПОРТУВАТИ ОБРАНІ", 
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#28a745", hover_color="#218838",
            height=50, width=250,
            command=self.export_selected
        )
        self.export_btn.pack(side="right")

        self.render_library()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.parent.deiconify() # Повертаємо головне вікно
        self.destroy()

    def render_library(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        if not self.saved_tracks:
            self.show_empty_state()
        else:
            for track in self.saved_tracks:
                self.create_track_card(track)

    def create_track_card(self, track):
        card = ctk.CTkFrame(self.scrollable_frame, fg_color=self.card_color, corner_radius=12)
        card.pack(fill="x", pady=5, padx=5)
        
        var = ctk.BooleanVar()
        self.check_vars[track['id']] = var
        
        checkbox = ctk.CTkCheckBox(card, text="", variable=var, width=20, fg_color=self.accent_color)
        checkbox.pack(side="left", padx=15)
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=10)
        
        ctk.CTkLabel(info_frame, text=track['name'], font=ctk.CTkFont(size=16, weight="bold"), text_color=self.text_white).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Дата: {track['date']} | Сегментів: {track['segments']}", font=ctk.CTkFont(size=12), text_color=self.text_gray).pack(anchor="w")
        
        # ОНОВЛЕНА КНОПКА: вона має викликати метод відкриття в контролері
        btn_view = ctk.CTkButton(
            card, 
            text="Відкрити", 
            width=100, 
            fg_color="#3d3d3d", 
            command=lambda t=track: self.load_project_to_editor(t)
        )
        btn_view.pack(side="right", padx=20)

    def load_project_to_editor(self, track_data):
        """Це заглушка, яку контролер замінить на реальний метод"""
        # Якщо контролер не підмінив цей метод, просто виведемо інфо
        print(f"Завантаження проекту: {track_data['name']}")

    def select_all(self):
        for var in self.check_vars.values(): var.set(True)

    def deselect_all(self):
        for var in self.check_vars.values(): var.set(False)

    def export_selected(self):
        selected = [t['name'] for t in self.saved_tracks if self.check_vars[t['id']].get()]
        if not selected:
            messagebox.showwarning("Експорт", "Жоден файл не обраний для експорту!")
        else:
            messagebox.showinfo("Експорт", f"Експортуємо {len(selected)} файл(ів)...")

    def show_empty_state(self):
        ctk.CTkLabel(self.scrollable_frame, text="Бібліотека порожня", text_color=self.text_gray).pack(pady=100)

    def go_back(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()

if __name__ == "__main__":
    # Виправлений запуск для тестування окремо від мейна
    root = ctk.CTk()
    root.withdraw() 
    app = LibraryWindow(root)
    app.mainloop()