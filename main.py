import queue
import time
from config.config_manager import ConfigManager
from Core.event_bus import EventBus
from Input.controller import Controller
from Input.input_manager import InputManager
from Input.keyboard import Keyboard
from utils.logger import setup_logger
def main():

    logger = setup_logger()
    logger.info("ROV application started")

    config = ConfigManager()
    event_bus = EventBus()
    event_input_queue = queue.Queue(maxsize=1)

    def receive_input(data):
        try:
            event_input_queue.get_nowait()
        except queue.Empty:
            pass

        event_input_queue.put_nowait(data)

    event_bus.subscribe("input_updated", receive_input)

    profile = config.get_active_profile()
    last_controller_name = None

    input_settings = config.get_input_settings()

    controller = Controller(
        dead_zone=input_settings["dead_zone"]
    )

    keyboard = Keyboard()

    input_manager = InputManager(
        controller,
        keyboard,
        sampling_rate=input_settings["sampling_rate"],
        event_bus=event_bus
    )

    try:
        input_manager.start()

        while True:
            controller.check_connection()

            controller_name = controller.get_name()

            if controller_name != last_controller_name:
                if controller_name is not None and config.load_controller_profile(controller_name):
                    profile = config.get_active_profile()
                    logger.info("Loaded profile for: %s", controller_name)

                last_controller_name = controller_name

            keys = keyboard.read()
            input_manager.update_keyboard(keys)

            new_profile = keyboard.get_profile_selection()

            if new_profile is not None and config.switch_profile(new_profile):
                profile = config.get_active_profile()
                logger.info("Switched to profile: %s", new_profile)

            try:
                input_data = event_input_queue.get_nowait()
            except queue.Empty:
                input_data = None

            if input_data is not None:
                controller_data = input_data["controller"]

                controller_actions = controller.get_actions(
                    profile, controller_data
                )
            else:
                controller_actions = None

            keyboard_actions = keyboard.get_actions(profile)

            logger.info("ROV Keyboard Actions: %s", keyboard_actions)
            logger.info("ROV Controller Actions: %s", controller_actions)

            if keys:
                logger.debug("Pressed keys: %s", keys)

            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Stopping application")

    finally:
        input_manager.stop()
        keyboard.close()
        controller.close()
        logger.info("ROV application stopped")


if __name__ == "__main__":
    main()

