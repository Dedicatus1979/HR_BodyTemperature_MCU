from ucollections import deque


class CircularBuffer(object):
    def __init__(self, max_size):
        self.data = deque((), max_size, True)
        self.max_size = max_size

    def __len__(self):
        return len(self.data)

    def append(self, item):
        try:
            self.data.append(item)
        except IndexError:
            self.data.popleft()
            self.data.append(item)

    def pop(self):
        return self.data.popleft()
