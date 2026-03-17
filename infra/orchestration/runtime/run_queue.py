from collections import deque


class RunQueue:
    def __init__(self):
        self._queue = deque()

    def enqueue(self, run_request):
        self._queue.append(run_request)

    def dequeue(self):
        if self.is_empty():
            return None
        return self._queue.popleft()

    def peek(self):
        if self.is_empty():
            return None
        return self._queue[0]

    def size(self):
        return len(self._queue)

    def is_empty(self):
        return len(self._queue) == 0
