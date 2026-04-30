from view.segmented_track_view import SegmentedTrackView
from tkinter import messagebox
import pygame
import time

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        if hasattr(self, 'view') and hasattr(self.view, 'btn_segment'):
            self.view.btn_segment.configure(command=self.open_segmentation_menu)

    def open_segmentation_menu(self):
        from view.segmentation_window import AudioUploadWindow
        self.seg_win = AudioUploadWindow(self.view)
        self.seg_win.run_btn.configure(command=self.handle_processing)

    def handle_processing(self):
        """Обробка натискання кнопки СЕГМЕНТУВАТИ"""
        path = getattr(self.seg_win, 'selected_file_path', None)
        
        if not path:
            messagebox.showwarning("Помилка", "Ви не обрали файл!")
            return

        method = self.seg_win.method_var.get()
        self.seg_win.run_btn.configure(text="⏳ ОБРОБКА...", state="disabled")
        self.seg_win.update() 

        if self.model.load_from_file(path):
            self.model.current_path = path 
            
            if "Librosa" in method:
                self.model.segment_librosa_onset()
            elif "Novelty" in method:
                self.model.segment_novelty()
            else:
                self.model.segment_ml()

            self.seg_win.withdraw() 
            self.view.withdraw()    
            self.open_editor()
            self.seg_win.after(100, self.seg_win.destroy) 
        else:
            messagebox.showerror("Помилка", "Не вдалося завантажити файл.")
            self.seg_win.run_btn.configure(text="🚀 СЕГМЕНТУВАТИ", state="normal")

    def open_editor(self):
        """Створює і наповнює вікно редактора з робочим плеєром та перемоткою"""
        import pygame
        
        # 1. Створюємо вікно редактора
        self.editor = SegmentedTrackView()
        
        # 2. Ініціалізуємо змінні стану плеєра для контролера
        self.is_playing = False
        self.current_seconds = 0.0  # Точка відліку (змінюється при паузі або перемотці)
        
        # 3. Передаємо сегменти з моделі в таблицю редактора
        self.editor.segments = [
            {"start": s.start, "end": s.end, "label": s.label}
            for s in self.model.segments
        ]
        
        # 4. Налаштовуємо аудіо-двигун
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # 5. Рахуємо тривалість треку для налаштування слайдера
        duration = len(self.model.signal) / self.model.sr
        self.editor.progress_slider.configure(to=duration)
        self.editor.total_time_label.configure(text=self.format_time(duration))
        
        # 6. ПРИВ'ЯЗУЄМО КНОПКИ ТА ПОДІЇ
        # Кнопка Play/Pause
        self.editor.play_pause_btn.configure(command=self.toggle_playback)
        
        # Кнопка Назад
        self.editor.back_to_menu_btn.configure(command=self.stop_and_close)
        
        # Перемотка слайдером (прив'язуємо команду до методу seek_audio)
        self.editor.progress_slider.configure(command=self.seek_audio)
        
        # 7. Візуалізація: малюємо спектрограму та заповнюємо таблицю
        self.editor._plot_spectrogram(signal=self.model.signal, sr=self.model.sr)
        self.editor._refresh_all()
        
        # 8. Повернення головного меню при закритті вікна (якщо натиснули хрестик)
        self.editor.bind("<Destroy>", lambda e: self.view.deiconify() if hasattr(self, 'view') else None)
        
        # 9. Запускаємо фоновий цикл оновлення слайдера
        self.update_slider_loop()

        self.editor.play_segment_btn.configure(command=self.play_selected_segment)

    def toggle_playback(self):
        import pygame
        if not self.is_playing:
            # Граємо з поточної позиції (current_seconds оновлюється при перемотці)
            pygame.mixer.music.load(self.model.current_path)
            pygame.mixer.music.play(start=self.current_seconds)
            self.editor.play_pause_btn.configure(text="⏸")
            self.is_playing = True
        else:
            # При натисканні на паузу:
            # 1. Запам'ятовуємо, де зупинилися, щоб наступний старт був з цього ж місця
            self.current_seconds += pygame.mixer.music.get_pos() / 1000.0
            # 2. Зупиняємо відтворення
            pygame.mixer.music.stop()
            self.editor.play_pause_btn.configure(text="▶")
            self.is_playing = False

    def update_slider_loop(self):
        """Оновлення слайдера з урахуванням перемотки та перевіркою на існування вікна"""
        # 1. ПЕРЕВІРКА: Якщо вікна немає або воно закривається — негайно зупиняємо цикл
        if not hasattr(self, 'editor') or not self.editor.winfo_exists():
            return 

        if self.is_playing:
            try:
                import pygame
                # Перевіряємо, чи працює міксер і чи грає музика
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    # actual_time = (час, з якого ми почали/перемотали) + (скільки секунд пройшло з того моменту)
                    # get_pos() повертає мс з моменту останнього виклику play()
                    pos_ms = pygame.mixer.music.get_pos()
                    
                    if pos_ms >= 0:
                        actual_time = self.current_seconds + (pos_ms / 1000.0)
                        
                        # Перевіряємо, чи віджет слайдера все ще існує (щоб не було bgerror)
                        if self.editor.progress_slider.winfo_exists():
                            self.editor.progress_slider.set(actual_time)
                            self.editor.current_time_label.configure(text=self.format_time(actual_time))
                else:
                    # Якщо музика сама дограла до кінця
                    self.is_playing = False
                    self.editor.play_pause_btn.configure(text="▶")
                    
            except Exception as e:
                print(f"Помилка оновлення слайдера: {e}")
                return 

        # 2. РЕКУРСІЯ: Тільки якщо вікно все ще живе, плануємо наступне оновлення через 100 мс
        try:
            if self.editor.winfo_exists():
                self.editor.after(100, self.update_slider_loop)
        except:
            pass # Вікно було знищено в момент перевірки

    def stop_and_close(self):
        """Повне очищення при закритті редактора"""
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() # Вивантажуємо файл з пам'яті
        
        self.is_playing = False
        self.current_seconds = 0
        
        if hasattr(self, 'editor') and self.editor.winfo_exists():
            # Спочатку знімаємо всі події, щоб не було bgerror
            self.editor.protocol("WM_DELETE_WINDOW", lambda: None)
            self.editor.destroy()
            
        if hasattr(self, 'view'):
            self.view.deiconify()

    def format_time(self, seconds):
        """Функція форматування, якої не вистачало"""
        mins = int(max(0, seconds) // 60)
        secs = int(max(0, seconds) % 60)
        return f"{mins}:{secs:02d}"
    
    def seek_audio(self, value):
        """Функція перемотування музики"""
        import pygame
        
        # 1. Оновлюємо накопичений час значенням зі слайдера
        self.current_seconds = float(value)
        
        # 2. Оновлюємо текстову мітку часу, щоб було видно куди мотаємо
        self.editor.current_time_label.configure(text=self.format_time(self.current_seconds))
        
        # 3. Якщо музика грає зараз — перезапускаємо її з нової позиції
        if self.is_playing:
            pygame.mixer.music.load(self.model.current_path)
            pygame.mixer.music.play(start=self.current_seconds)
        
    def play_selected_segment(self):
        """Грає тільки виділений у таблиці шматочок"""
        import pygame
        
        # 1. Отримуємо виділений рядок
        selected_item = self.editor.table.selection()
        if not selected_item:
            messagebox.showinfo("Інфо", "Спочатку виберіть сегмент у таблиці!")
            return
            
        # 2. Беремо дані сегмента (час початку та кінця)
        values = self.editor.table.item(selected_item)['values']
        start_s = float(values[0])
        end_s = float(values[1])
        duration_s = end_s - start_s
        
        if duration_s <= 0: return

        # 3. Зупиняємо все, що грало, і мотаємо на початок сегмента
        pygame.mixer.music.stop()
        self.current_seconds = start_s
        self.is_playing = True
        self.editor.play_pause_btn.configure(text="⏸")
        
        # 4. Запускаємо відтворення
        pygame.mixer.music.load(self.model.current_path)
        pygame.mixer.music.play(start=start_s)
        
        # 5. Створюємо таймер, який зупинить музику через duration_s секунд
        # Ми використовуємо after, щоб автоматично натиснути паузу в кінці сегмента
        self.editor.after(int(duration_s * 1000), self.stop_segment_playback)

    def stop_segment_playback(self):
        """Зупиняє програвання після завершення сегмента"""
        import pygame
        if self.is_playing: # Якщо користувач сам не натиснув паузу раніше
            pygame.mixer.music.stop()
            self.is_playing = False
            self.editor.play_pause_btn.configure(text="▶")
            # Оновлюємо current_seconds на кінець сегмента
            # (або можна лишити на початку - як тобі зручніше)