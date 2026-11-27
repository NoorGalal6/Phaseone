import queue
import threading
import time
class InputManager:

    def __init__(self, controller, keyboard, sampling_rate, event_bus):

        if sampling_rate <= 0:
            raise ValueError("Sampling rate must be greater than zero")

        self.controller = controller
        self.keyboard = keyboard
        self.sampling_rate = sampling_rate
        self.event_bus = event_bus

        self.keyboard_queue = queue.Queue(maxsize=1)

        self.stop_event = threading.Event()
        self.input_thread = None

    def start(self):

        if self.input_thread is not None and self.input_thread.is_alive():
            return

        self.stop_event.clear()

        self.input_thread = threading.Thread(
            target=self._read_inputs,
            daemon=True
        )

        self.input_thread.start()

    def update_keyboard(self, keys):

        try:
            self.keyboard_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self.keyboard_queue.put_nowait(keys.copy())
        except queue.Full:
            pass

    def _read_inputs(self):

        interval = 1 / self.sampling_rate
        keyboard_keys = set()

        while not self.stop_event.is_set():

            start_time = time.perf_counter()

            self.controller.check_connection()
            controller_data = self.controller.read()

            try:
                keyboard_keys = self.keyboard_queue.get_nowait()
            except queue.Empty:
                pass

            data = {
                "controller": controller_data,
                "keyboard": keyboard_keys
            }

            self.event_bus.publish("input_updated", data)

            elapsed = time.perf_counter() - start_time

            self.stop_event.wait(max(0, interval - elapsed))

    def stop(self):

        self.stop_event.set()

        if self.input_thread is not None:
            self.input_thread.join()
            self.input_thread = None
