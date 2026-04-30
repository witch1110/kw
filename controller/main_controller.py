from view.segmented_track_view import SegmentedTrackView
from tkinter import messagebox
import pygame
import time
from view.dialogs import CustomInputDialog

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        if hasattr(self, 'view') and hasattr(self.view, 'btn_segment'):
            self.view.btn_segment.configure(command=self.open_segmentation_menu)

        if hasattr(self.view, 'btn_library'):
            self.view.btn_library.configure(command=self.open_library)

    def open_segmentation_menu(self):
        from view.segmentation_window import AudioUploadWindow
        self.seg_win = AudioUploadWindow(self.view)
        self.seg_win.run_btn.configure(command=self.handle_processing)

    def handle_processing(self):
        """Обробка вибору методу та запуск вікна редактора"""
        path = getattr(self.seg_win, 'selected_file_path', None)
        
        if not path:
            messagebox.showwarning("Помилка", "Ви не обрали файл!")
            return

        # ОТРИМУЄМО ОБРАНИЙ МЕТОД З МЕНЮ
        method = self.seg_win.method_var.get()
        print(f"Обрано метод: {method}") # Для самоперевірки в консолі

        self.seg_win.run_btn.configure(text="⏳ ОБРОБКА...", state="disabled")
        self.seg_win.update() 

        if self.model.load_from_file(path):
            self.model.current_path = path 
            
            # ВИБІР АЛГОРИТМУ
            if "Librosa" in method:
                self.model.segment_librosa_onset()
            elif "Novelty" in method:
                self.model.segment_novelty()
            else:
                # Поки ML не готовий, нехай буде novelty або повідомлення
                print("ML ще в розробці, запускаю Novelty за замовчуванням")
                self.model.segment_novelty()

            # Закриваємо допоміжні вікна та відкриваємо редактор
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

        self.editor.recalc_btn.configure(command=self.handle_resegmentation)

        self.editor.save_btn.configure(command=self.save_current_project)

    

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

    def handle_resegmentation(self):
        """Перерахунок сегментів іншим методом без закриття вікна"""
        # Зупиняємо плеєр перед перерахунком, щоб не було конфліктів
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.is_playing = False
        self.editor.play_pause_btn.configure(text="▶")

        method = self.editor.method_var.get()
        
        if "Librosa" in method:
            self.model.segment_librosa_onset()
        elif "Novelty" in method:
            self.model.segment_novelty()
        else:
            self.model.segment_novelty()

        self.editor.segments = [
            {"start": s.start, "end": s.end, "label": s.label}
            for s in self.model.segments
        ]
        
        self.editor._refresh_all()

    def save_current_project(self):
        """Зберігає поточні сегменти у JSON файл"""
        import json
        import os
        from tkinter import messagebox

        if not hasattr(self.model, 'current_path') or not self.model.current_path:
            messagebox.showwarning("Помилка", "Немає даних для збереження")
            return

        # Створюємо структуру даних
        data_to_save = {
            "project_name": os.path.basename(self.model.current_path),
            "audio_path": self.model.current_path,
            "segments": self.editor.segments,
            "last_modified": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Створюємо папку library, якщо її немає
        if not os.path.exists("library"):
            os.makedirs("library")

        # Формуємо шлях до файлу
        file_base = os.path.basename(self.model.current_path).rsplit('.', 1)[0]
        save_path = os.path.join("library", f"{file_base}_project.json")

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Успіх", f"Проект збережено в папку library!")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти: {e}")

    def open_library(self):
        """Зчитує JSON-файли та відкриває бібліотеку"""
        import os
        import json
        from view.library_view import LibraryWindow

        library_path = "library"
        real_saved_tracks = []

        # 1. Збираємо дані з папки
        if os.path.exists(library_path):
            files = [f for f in os.listdir(library_path) if f.endswith('.json')]
            for index, file_name in enumerate(files):
                try:
                    with open(os.path.join(library_path, file_name), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        real_saved_tracks.append({
                            "id": index,
                            "name": data.get("project_name", file_name),
                            "date": data.get("last_modified", "Невідомо"),
                            "segments": len(data.get("segments", [])),
                            "full_data": data 
                        })
                except Exception as e:
                    print(f"Помилка зчитування {file_name}: {e}")

        # 2. Створюємо вікно ОДИН раз
        self.lib_win = LibraryWindow(self.view)
        
        # 3. Передаємо дані
        self.lib_win.saved_tracks = real_saved_tracks
        self.lib_win.render_library() 
        
        # 4. Прив'язуємо функції (Зверни увагу на назви кнопок!)
        self.lib_win.load_project_to_editor = self.load_saved_project #
        self.lib_win.export_btn.configure(command=self.export_project_from_library) #
        
        self.view.withdraw()

    def load_saved_project(self, track_item):
        """Відкриває збережений проект з бібліотеки в редакторі"""
        import os
        from tkinter import messagebox
        from model.audio_model import Segment

        # Отримуємо ПОВНІ дані проекту з об'єкта, який передала бібліотека
        project_data = track_item.get("full_data")
        if not project_data:
            messagebox.showerror("Помилка", "Дані проекту не знайдено.")
            return

        # 1. Дістаємо шлях до аудіо
        audio_path = project_data.get("audio_path")
        
        if not audio_path or not os.path.exists(audio_path):
            messagebox.showerror("Помилка", f"Аудіофайл не знайдено за шляхом:\n{audio_path}")
            return

        # 2. Завантажуємо аудіо в модель
        if self.model.load_from_file(audio_path):
            self.model.current_path = audio_path
            
            # 3. Завантажуємо сегменти (тепер беремо СПИСОК із JSON)
            segments_list = project_data.get("segments", [])
            
            # Перетворюємо словники з JSON назад у об'єкти класу Segment
            self.model.segments = []
            for s in segments_list:
                # Перевірка на випадок, якщо дані збережені як об'єкти або словники
                start = float(s.get('start', 0)) if isinstance(s, dict) else float(s.start)
                end = float(s.get('end', 0)) if isinstance(s, dict) else float(s.end)
                label = s.get('label', "PART") if isinstance(s, dict) else s.label
                
                self.model.segments.append(Segment(start=start, end=end, label=label))
            
            # 4. Закриваємо вікно бібліотеки та відкриваємо редактор
            if hasattr(self, 'lib_win'):
                self.lib_win.destroy()
                
            self.view.withdraw() 
            self.open_editor()
        else:
            messagebox.showerror("Помилка", "Не вдалося завантажити аудіо.")

    def export_segments(self):
        """Нарізає аудіо на сегменти та зберігає у папку exports"""
        import os
        import csv
        from pydub import AudioSegment
        from tkinter import messagebox, filedialog

        # 1. Перевірки
        if not self.model.segments or not self.model.current_path:
            messagebox.showwarning("Експорт", "Немає сегментів для експорту!")
            return

        # 2. Вибір папки для збереження
        output_base_dir = filedialog.askdirectory(title="Оберіть папку для експорту датасету")
        if not output_base_dir:
            return

        # Створюємо підпапку з іменем треку
        track_name = os.path.basename(self.model.current_path).rsplit('.', 1)[0]
        export_path = os.path.join(output_base_dir, f"dataset_{track_name}")
        
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        try:
            # 3. Завантажуємо аудіо через pydub
            audio = AudioSegment.from_file(self.model.current_path)
            
            manifest_data = [] # Для CSV файлу з описом

            # 4. Процес нарізки
            for i, seg in enumerate(self.model.segments):
                # pydub працює в мілісекундах
                start_ms = seg.start * 1000
                end_ms = seg.end * 1000
                
                # Вирізаємо шматок
                chunk = audio[start_ms:end_ms]
                
                # Формуємо ім'я файлу (наприклад: 01_INTRO_trackname.wav)
                safe_label = "".join(x for x in seg.label if x.isalnum() or x in "._- ").strip()
                chunk_filename = f"{i+1:02d}_{safe_label}.wav"
                chunk_path = os.path.join(export_path, chunk_filename)
                
                # Зберігаємо сегмент у форматі WAV (найкраще для ML)
                chunk.export(chunk_path, format="wav")
                
                # Додаємо запис у маніфест
                manifest_data.append([chunk_filename, seg.label, seg.start, seg.end])

            # 5. Створюємо CSV файл з метаданими (Manifest)
            csv_path = os.path.join(export_path, "metadata.csv")
            with open(csv_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "label", "start_sec", "end_sec"])
                writer.writerows(manifest_data)

            messagebox.showinfo("Успіх", f"Датасет сформовано!\nЗбережено {len(self.model.segments)} сегментів у:\n{export_path}")

        except Exception as e:
            messagebox.showerror("Помилка експорту", f"Сталася помилка: {str(e)}")

    def export_project_from_library(self):
        """Масовий експорт: створення спільної папки датасету з підпапкою аудіо та CSV"""
        import os
        import csv
        import shutil
        from tkinter import messagebox, filedialog, simpledialog

        # 1. Знаходимо обрані проекти
        selected_projects = [
            t for t in self.lib_win.saved_tracks 
            if self.lib_win.check_vars[t['id']].get()
        ]

        if not selected_projects:
            messagebox.showwarning("Експорт", "Виберіть проекти галочкою!")
            return

        # 2. Питаємо назву для головної папки датасету
        dialog = CustomInputDialog(self.lib_win, "Створення датасету", "Введіть назву датасету:")
        dataset_name = dialog.get_input()
        if not dataset_name: return

        # 3. Вибір місця, де створити цю папку
        base_location = filedialog.askdirectory(title="Оберіть місце для збереження")
        if not base_location: return

        # Формуємо шлях до головної папки та підпапок
        root_dir = os.path.join(base_location, dataset_name)
        audio_dir = os.path.join(root_dir, "tracks")
        
        try:
            # Створюємо структуру
            os.makedirs(audio_dir, exist_ok=True)

            all_annotations = []

            for project in selected_projects:
                data = project['full_data']
                original_audio = data.get("audio_path")
                
                if original_audio and os.path.exists(original_audio):
                    file_name = os.path.basename(original_audio)
                    # Копіюємо трек у root_dir/tracks/
                    shutil.copy2(original_audio, os.path.join(audio_dir, file_name))
                    
                    # Додаємо всі сегменти цього треку до списку
                    for seg in data.get("segments", []):
                        all_annotations.append({
                            "file_name": file_name,
                            "label": seg.get('label', 'PART'),
                            "start": seg.get('start', 0),
                            "end": seg.get('end', 0)
                        })

            # 4. Створюємо CSV всередині головної папки
            csv_path = os.path.join(root_dir, "annotations.csv")
            with open(csv_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_name", "label", "start", "end"])
                writer.writeheader()
                writer.writerows(all_annotations)

            messagebox.showinfo("Успіх", f"Датасет '{dataset_name}' готовий!\nШлях: {root_dir}")

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося створити структуру датасету: {e}")