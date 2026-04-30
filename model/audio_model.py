from model.segment import Segment


class AudioModel:
    def __init__(self):
        self.signal = None        # аудіосигнал
        self.sr = None            # sample rate
        self.segments = []        # список сегментів

    def has_audio(self):
        return self.signal is not None

    def set_audio(self, signal, sr):
        self.signal = signal
        self.sr = sr
        self.segments = []        # очищаємо старі сегменти

    def set_segments(self, segments):
        self.segments = segments

    def load_from_file(self, path):
            from .audio_loader import load_audio
            signal, sr = load_audio(path)
            if signal is not None:
                self.set_audio(signal, sr)
                return True
            return False
    
    def segment_audio(self):
        from .segmentation import energy_based_segmentation
        if self.signal is not None:
            self.segments = energy_based_segmentation(self.signal, self.sr)
            return True
        return False
    
    def segment_novelty(self):
        """Сегментація на основі новизни з обмеженням до 10 сегментів"""
        import librosa
        import numpy as np

        # 1. Параметри для пошуку великих структур (великий hop_length)
        hop_length = 2048  # Збільшуємо, щоб ігнорувати дрібні деталі
        
        # Обчислюємо функцію новизни на основі спектрального потоку
        onset_env = librosa.onset.onset_strength(y=self.signal, sr=self.sr, hop_length=hop_length)
        
        # 2. Сильне згладжування кривої новизни
        onset_env = librosa.util.normalize(onset_env)
        
        # 3. Шукаємо піки, але з великим "вікном очікування" (wait), щоб межі не були надто близько
        peaks = librosa.util.peak_pick(
            onset_env, 
            pre_max=100, post_max=100, 
            pre_avg=100, post_avg=100, 
            delta=0.1, wait=200 # wait=200 кадрів (~9 секунд мінімальний сегмент)
        )
        
        # Конвертуємо у час
        times = librosa.frames_to_time(peaks, sr=self.sr, hop_length=hop_length)
        
        # 4. ОБМЕЖЕННЯ: Якщо піків більше 9 (щоб разом з останнім було 10), беремо найсильніші
        if len(times) > 9:
            # Сортуємо піки за їх "силою" (значенням на кривій новизни)
            peak_strengths = onset_env[peaks]
            strongest_indices = np.argsort(peak_strengths)[-9:] # Беремо 9 найпотужніших
            times = np.sort(times[strongest_indices])

        # 5. Створення сегментів з музичними мітками
        self.segments = []
        labels = ["INTRO", "VERSE 1", "CHORUS 1", "VERSE 2", "CHORUS 2", "BRIDGE", "CHORUS 3", "OUTRO", "END"]
        
        start_time = 0.0
        for i, end_time in enumerate(times):
            label = labels[i] if i < len(labels) else f"PART {i+1}"
            self.segments.append(Segment(start=start_time, end=float(end_time), label=label))
            start_time = float(end_time)
        
        # Додаємо фінальний сегмент
        total_duration = len(self.signal) / self.sr
        if start_time < total_duration:
            label = labels[len(self.segments)] if len(self.segments) < len(labels) else "OUTRO"
            self.segments.append(Segment(start=start_time, end=total_duration, label=label))

    def segment_librosa_onset(self):
        """Метод 2: Librosa (Structure/Laplacian)"""
        import librosa
        import numpy as np
        from .segment import Segment

        # Витягуємо гармонічні ознаки (chroma)
        chroma = librosa.feature.chroma_cqt(y=self.signal, sr=self.sr)
        # k=8 зазвичай достатньо для стандартної пісні (Intro, Verse, Chorus...)
        boundary_frames = librosa.segment.agglomerative(chroma, k=8)
        boundary_times = librosa.frames_to_time(boundary_frames, sr=self.sr)

        # Твій бажаний список назв
        labels = ["Intro", "Verse 1", "Chorus 1", "Verse 2", "Chorus 2", "Bridge", "Chorus 3", "Outro"]

        self.segments = []
        for i in range(len(boundary_times) - 1):
            label = labels[i] if i < len(labels) else f"Part {i+1}"
            self.segments.append(Segment(boundary_times[i], boundary_times[i+1], label))

    def segment_ml(self):
        """Метод 3: Machine Learning (CNN/Salami)"""
        # Тут буде виклик нейронки, поки можеш залишити заглушку
        pass