from tkinter import Tk, Button, filedialog
import customtkinter as ctk

class MainView(Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Segmentation")
        self.load_btn = ctk.CTkButton(self, text="Завантажити аудіо")
        self.load_btn.pack(pady=20)

    def ask_file(self):
        return filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
