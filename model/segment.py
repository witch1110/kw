class Segment:
    def __init__(self, start, end, label=None):
        self.start = start    # початок у секундах
        self.end = end        # кінець у секундах
        self.label = label   # куплет, приспів тощо
