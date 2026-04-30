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
    
   # model/audio_model.py

    def segment_novelty(self):
        """Метод 1: Аналіз новизни (Novelty Analysis)"""
        # Твій старий алгоритм по енергії або спектральній новизні
        self._run_structural_segmentation(k=6, prefix="Section")

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