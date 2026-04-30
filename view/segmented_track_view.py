import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Приховуємо вітання pygame в консолі
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

class SegmentedTrackView(ctk.CTkToplevel):
    def __init__(self, audio_path=None):
        super().__init__()

        self.title("AUDIO ANALYZER PRO - EDITOR")
        self.geometry("1250x900")
        
        # Колірна палітра "Cyber Dark"
        self.bg_color = "#0B0B0C"
        self.panel_color = "#161618"
        self.accent_main = "#00F2FF"
        self.accent_second = "#7000FF"
        self.text_color = "#E1E1E1"
        
        self.configure(fg_color=self.bg_color)
        
        # Початкові дані
        self.segments = []
        self.markers = []
        self.selected_marker = None

        self._setup_styles()
        self._create_widgets()
        
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview", 
            background=self.panel_color, 
            foreground=self.text_color, 
            fieldbackground=self.panel_color, 
            borderwidth=0, 
            font=("Segoe UI", 11), 
            rowheight=40)
        
        style.configure("Treeview.Heading", 
            background="#1F1F22", 
            foreground=self.accent_main, 
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0)

        style.map("Treeview.Heading",
            background=[('active', '#1F1F22'), ('pressed', '#1F1F22')],
            relief=[('active', 'flat'), ('pressed', 'flat')])
        
        style.map("Treeview", background=[('selected', self.accent_second)])

    def _create_widgets(self):
        # --- Sidebar (Панель керування - ЛІВА) ---
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=self.panel_color, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="CONTROLS", font=("Arial", 22, "bold"), text_color=self.accent_main).pack(pady=30)

        # Налаштування методу
        ctk.CTkLabel(self.sidebar, text="Segmentation Method:", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=25, pady=(15,0))
        self.method_var = ctk.StringVar(value="Novelty Analysis")
        self.method_menu = ctk.CTkOptionMenu(
            self.sidebar, values=["Novelty Analysis", "Librosa Onset", "ML Segmentation"],
            variable=self.method_var, fg_color="#2A2A2D", button_color="#333", width=210
        )
        self.method_menu.pack(pady=10, padx=20)

        self.recalc_btn = ctk.CTkButton(
            self.sidebar, text="RE-SEGMENT", fg_color="transparent", border_width=1,
            border_color=self.accent_main, text_color=self.accent_main, hover_color="#102025",
            command=self._run_resegmentation
        )
        self.recalc_btn.pack(pady=10, padx=20, fill="x")

        # Кнопки редагування
        ctk.CTkLabel(self.sidebar, text="Editor Actions:", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=25, pady=(20, 0))
        
        self.add_btn = ctk.CTkButton(
            self.sidebar, text="+ ADD SEGMENT", fg_color="#2A2A2D", hover_color="#3A3A3D",
            command=self._add_segment
        )
        self.add_btn.pack(pady=10, padx=20, fill="x")

        self.play_segment_btn = ctk.CTkButton(
            self.sidebar, text="▶ PLAY SELECTED", fg_color="#2ecc71", hover_color="#27ae60",
            text_color="white", font=("Arial", 13, "bold"),
            command=self._on_play_segment_click # Будемо прив'язувати в контролері
        )
        self.play_segment_btn.pack(pady=10, padx=20, fill="x")

        # Кнопка Назад (розміщуємо внизу сайдбару)
        self.back_to_menu_btn = ctk.CTkButton(
            self.sidebar, 
            text="⬅ НАЗАД", 
            fg_color="#333333", 
            hover_color="#444444",
            height=40
        )
        self.back_to_menu_btn.pack(side="bottom", pady=(10, 5), padx=20, fill="x")

        self.save_btn = ctk.CTkButton(
            self.sidebar, text="SAVE PROJECT", fg_color=self.accent_second, 
            height=45, font=("Arial", 13, "bold"), command=lambda: messagebox.showinfo("Saved", "Project updated successfully!")
        )
        self.save_btn.pack(side="bottom", pady=(20, 10), padx=20, fill="x")

        # --- Main Content Area (ЦЕНТРАЛЬНА ЧАСТИНА) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=30, pady=20)

        # Заголовок
        ctk.CTkLabel(self.main_container, text="VISUAL ANALYZER", 
                    font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(0, 20))

        # 1. Спектрограма
        self.graph_frame = ctk.CTkFrame(self.main_container, fg_color=self.panel_color, corner_radius=20, 
                                        border_width=1, border_color="#2A2A2D", height=320)
        self.graph_frame.pack(fill="x")
        self.graph_frame.pack_propagate(False)

        # 2. ПАНЕЛЬ ПЛЕЄРА (Прямо під спектрограмою)
        self.player_panel = ctk.CTkFrame(self.main_container, fg_color="#161618", corner_radius=15, height=60)
        self.player_panel.pack(fill="x", pady=15)

        # Кнопка Play/Pause
        self.play_pause_btn = ctk.CTkButton(
            self.player_panel, text="▶", width=50, height=40, corner_radius=10,
            fg_color=self.accent_main, text_color="black", font=("Arial", 18, "bold")
        )
        self.play_pause_btn.pack(side="left", padx=15, pady=10)

        # Поточний час
        self.current_time_label = ctk.CTkLabel(self.player_panel, text="0:00", text_color=self.text_color)
        self.current_time_label.pack(side="left", padx=5)

        # Слайдер прогресу (з командою перемотування)
        self.progress_slider = ctk.CTkSlider(
            self.player_panel, 
            from_=0, 
            to=100, 
            number_of_steps=1000,
            button_color=self.accent_main, 
            progress_color=self.accent_main,
            command=self._on_slider_drag  # <--- Додано команду для контролера
        )
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=15)
        self.progress_slider.set(0)

        # Загальний час
        self.total_time_label = ctk.CTkLabel(self.player_panel, text="0:00", text_color=self.text_color)
        self.total_time_label.pack(side="left", padx=10)

        # 3. Таблиця сегментів
        self.table_frame = ctk.CTkFrame(self.main_container, fg_color=self.panel_color, corner_radius=20, 
                                        border_width=1, border_color="#2A2A2D")
        self.table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        cols = ("start", "end", "label")
        self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
        self.table.heading("start", text="START (S)")
        self.table.heading("end", text="END (S)")
        self.table.heading("label", text="TAG")
        
        for c in cols: self.table.column(c, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=15)
        self.table.bind("<Double-1>", self._on_edit)

    def _plot_spectrogram(self, signal=None, sr=None):
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

        self.fig, self.ax = plt.subplots(figsize=(10, 3), facecolor=self.panel_color)
        self.fig.subplots_adjust(bottom=0.2, top=0.9, left=0.05, right=0.95)
        
        if signal is not None and sr is not None:
            import librosa.display
            import matplotlib.ticker as ticker
            
            D = librosa.amplitude_to_db(np.abs(librosa.stft(signal)), ref=np.max)
            # x_axis=None, щоб вручну керувати шкалою
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', ax=self.ax, cmap='magma')
            
            # --- ОЦЕЙ БЛОК РОБИТЬ СЕКУНДИ ---
            self.ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f')) # 2 знаки після коми
            self.ax.set_xlabel("Time (s)", color=self.text_color)
            # -------------------------------
            
            self.duration = len(signal) / sr
        else:
            self.ax.set_xlim(0, 100)
            self.duration = 100

        self.ax.set_facecolor(self.panel_color)
        self.ax.tick_params(colors='#888', labelsize=9)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        # Дозволяємо графіку реагувати на мишку
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.draw()

    def _refresh_all(self):
        for item in self.table.get_children(): self.table.delete(item)
        for seg in self.segments:
            self.table.insert("", "end", values=(f"{seg['start']:.2f}", f"{seg['end']:.2f}", seg['label']))
        
        for line in self.markers: line.remove()
        self.markers = []
        for seg in self.segments:
            line = self.ax.axvline(x=seg['end'], color=self.accent_main, linewidth=2, alpha=0.8, picker=5)
            self.markers.append(line)
        self.canvas.draw()

    def _add_segment(self):
        last_end = self.segments[-1]['end'] if self.segments else 0.0
        self.segments.append({"start": last_end, "end": last_end + 10.0, "label": "NEW"})
        self._refresh_all()

    def _run_resegmentation(self):
        # Логіка виклику через контролер
        pass

    def _on_edit(self, event):
        item_id = self.table.identify_row(event.y)
        if not item_id: return
        idx = self.table.index(item_id)
        
        dialog = ctk.CTkInputDialog(text="Enter Time (end) or Tag Name:", title="Editor")
        val = dialog.get_input()
        if val:
            try:
                new_time = float(val)
                self.segments[idx]['end'] = new_time
                if idx+1 < len(self.segments): self.segments[idx+1]['start'] = new_time
            except:
                self.segments[idx]['label'] = val.upper()
            self._refresh_all()

    def _on_click(self, event):
        if event.inaxes != self.ax: return
        for line in self.markers:
            cont, _ = line.contains(event)
            if cont: self.selected_marker = line; break

    def _on_release(self, event):
        if self.selected_marker:
            idx = self.markers.index(self.selected_marker)
            new_x = max(0, round(event.xdata, 2))
            self.segments[idx]['end'] = new_x
            if idx+1 < len(self.segments): self.segments[idx+1]['start'] = new_x
            self.selected_marker = None
            self._refresh_all()

    def _on_motion(self, event):
        if self.selected_marker and event.inaxes == self.ax:
            self.selected_marker.set_xdata([event.xdata])
            self.canvas.draw()

    def _on_slider_drag(self, value):
        pass

    def _on_play_segment_click(self):
        pass

    