import threading


class EventBus:

    def __init__(self):
        self.subscribers = {}
        self.lock = threading.Lock()

    def subscribe(self, event_name, callback):
        with self.lock:
            if event_name not in self.subscribers:
                self.subscribers[event_name] = []

            self.subscribers[event_name].append(callback)

    def publish(self, event_name, data):
        with self.lock:
            callbacks = self.subscribers.get(event_name, []).copy()

        for callback in callbacks:
            callback(data)
