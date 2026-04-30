import numpy as np
import librosa  # для роботи з аудіо

def load_audio(path, sr=44100):
    """
    Завантажує аудіофайл WAV / MP3.
    Повертає сигнал та частоту дискретизації.
    """
    try:
        signal, sr = librosa.load(path, sr=sr, mono=True)
        return signal, sr
    except Exception as e:
        print(f"Помилка завантаження аудіо: {e}")
        return None, None
