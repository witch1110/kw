import customtkinter as ctk
import pygame
import sys
import os  
from tkinter import messagebox

# Імпорт ваших класів
from model.audio_model import AudioModel
from view.home_view import MainMenu 
from controller.main_controller import MainController

def main():
    # 1. Ініціалізація логіки
    model = AudioModel()

    # 2. Створення головного вікна
    app = MainMenu() 

    # 3. Підключення контролера
    controller = MainController(model, app)

    # 4. Функція для повного та чистого закриття програми
    def on_closing():
        try:
            # Зупиняємо аудіо-двигун
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            
            # Закриваємо вікна Tkinter
            app.quit()
            app.destroy()
        except:
            pass
        finally:
            # Жорстке завершення процесу, щоб прибрати помилки bgerror
            os._exit(0)

    # Прив'язуємо обробник закриття до головного вікна
    app.protocol("WM_DELETE_WINDOW", on_closing)

    # 5. Запуск циклу програми
    app.mainloop()

if __name__ == "__main__":
    main()