import threading
from pynput import keyboard
class Keyboard:
    def __init__(self):
        self.pressed_keys = set()
        self.lock = threading.Lock()
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

    def on_press(self, key):
        try:
            key_name = key.char.lower()
        except AttributeError:
            key_name = str(key).replace("Key.", "")

        with self.lock:
            self.pressed_keys.add(key_name)

    def on_release(self, key):
        try:
            key_name = key.char.lower()
        except AttributeError:
            key_name = str(key).replace("Key.", "")

        with self.lock:
            self.pressed_keys.discard(key_name)

    def read(self):
        with self.lock:
            return self.pressed_keys.copy()

    def get_actions(self, profile):
        keys = self.read()
        actions = {}

        for action, key in profile["keyboard"].items():
            actions[action] = key in keys

        return actions

    def get_profile_selection(self):
        keys = self.read()

        if "1" in keys:
            return "default"
        elif "2" in keys:
            return "operator_2"

        return None

    def close(self):
        self.listener.stop()
