import numpy as np
from .segment import Segment

def energy_based_segmentation(signal, sr, frame_size=1024, hop_size=512, threshold=0.01):
    """
    Проста сегментація по енергії сигналу.
    Повертає список об'єктів Segment(start, end, label)
    """
    # 1. Розрахунок енергії
    energy = np.array([
        np.sum(np.square(signal[i:i+frame_size]))
        for i in range(0, len(signal), hop_size)
    ])

    # 2. Нормалізація (щоб значення були від 0 до 1)
    if np.max(energy) > 0:
        energy = energy / np.max(energy)

    # 3. Знаходимо кадри, де звук голосніший за поріг
    frames = np.where(energy > threshold)[0]

    if len(frames) == 0:
        return [Segment(0, len(signal)/sr, label="SILENCE")]

    segments = []
    start_frame = frames[0]

    # 4. Групуємо кадри в неперервні сегменти
    for i in range(1, len(frames)):
        # Якщо між кадрами є розрив — значить, один сегмент закінчився, інший почався
        if frames[i] != frames[i-1] + 1:
            start_sec = start_frame * hop_size / sr
            end_sec = frames[i-1] * hop_size / sr
            
            # Додаємо сегмент і даємо йому ім'я (Label)
            segments.append(Segment(start_sec, end_sec, label=f"SEGMENT {len(segments)+1}"))
            
            start_frame = frames[i]

    # 5. Додаємо останній знайдений сегмент
    start_sec = start_frame * hop_size / sr
    end_sec = frames[-1] * hop_size / sr
    segments.append(Segment(start_sec, end_sec, label=f"SEGMENT {len(segments)+1}"))

    return segments