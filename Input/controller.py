import threading
import pygame
class Controller:

    def __init__(self, dead_zone):
        pygame.init()
        pygame.joystick.init()

        self.joystick = None
        self.dead_zone = dead_zone
        self.lock = threading.Lock()
        self.connect()

    def connect(self):
        if pygame.joystick.get_count() == 0:
            print("No controller detected")
            return False

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        print("Controller connected:", self.joystick.get_name())

        return True

    def check_connection(self):
        with self.lock:
            count = pygame.joystick.get_count()

            if self.joystick is not None and count == 0:
                print("Controller disconnected")

                self.joystick.quit()
                self.joystick = None

            elif self.joystick is None and count > 0:
                print("Controller detected")
                self.connect()

    def read(self):
        with self.lock:

            if self.joystick is None:
                return None

            axes = []
            buttons = []
            hats = []

            for i in range(self.joystick.get_numaxes()):
                value = self.joystick.get_axis(i)

                if abs(value) < self.dead_zone:
                    value = 0.0

                axes.append(value)

            for i in range(self.joystick.get_numbuttons()):
                buttons.append(self.joystick.get_button(i))

            for i in range(self.joystick.get_numhats()):
                hats.append(self.joystick.get_hat(i))

            return {
                "axes": axes,
                "buttons": buttons,
                "hats": hats
        }
    def close(self):
        with self.lock:
            if self.joystick is not None:
                self.joystick.quit()
                self.joystick = None

            pygame.quit()

    def get_actions(self, profile, data):

        if data is None:
            return None

        mapping = profile["controller"]

        if mapping["forward_axis"] >= len(data["axes"]):
            return None

        if mapping["left_axis"] >= len(data["axes"]):
            return None

        if mapping["arm_button"] >= len(data["buttons"]):
            return None

        actions = {
            "forward": -data["axes"][mapping["forward_axis"]],
            "left": -data["axes"][mapping["left_axis"]],
            "arm": data["buttons"][mapping["arm_button"]] == 1
        }

        return actions
    def get_name(self):
        with self.lock:
            if self.joystick is None:
                return None

            return self.joystick.get_name()