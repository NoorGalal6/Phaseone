
import queue
import time

from config.config_manager import ConfigManager
from Core.event_bus import EventBus
from Input.controller import Controller
from Input.input_manager import InputManager
from Input.keyboard import Keyboard
from Communication.mavlink_manager import MAVLinkManager
from Admin.admin_manager import AdminManager
from utils.logger import setup_logger


def admin_command_menu(admin_manager, allowed_services):

    print("\n--- ADMIN COMMAND MENU ---")
    print("1 - Get bottomside status")
    print("2 - Restart a service")
    print("3 - Reboot bottomside")
    print("4 - Power off bottomside")
    print("5 - Continue to ROV controls")

    while True:

        choice = input("\nChoose an admin command: ").strip()

        if choice == "1":
            response = admin_manager.send_request("status")
            print("Server response:", response)

        elif choice == "2":
            print("Allowed services:", allowed_services)
            service = input("Enter service name: ").strip()

            response = admin_manager.send_request(
                "restart", service=service
            )
            print("Server response:", response)

        elif choice == "3":
            confirm = input(
                "Are you sure you want to reboot? (yes/no): "
            ).strip().lower()

            if confirm == "yes":
                response = admin_manager.send_request(
                    "reboot", confirm=True
                )
                print("Server response:", response)
            else:
                print("Reboot cancelled.")

        elif choice == "4":
            confirm = input(
                "Are you sure you want to power off? (yes/no): "
            ).strip().lower()

            if confirm == "yes":
                response = admin_manager.send_request(
                    "poweroff", confirm=True
                )
                print("Server response:", response)
            else:
                print("Poweroff cancelled.")

        elif choice == "5":
            print("Starting ROV controls...")
            break

        else:
            print("Invalid choice. Try again.")


def main():

    logger = setup_logger()

    config = ConfigManager()
    event_bus = EventBus()
    input_queue = queue.Queue(maxsize=1)

    admin_settings = config.settings["admin"]

    admin_manager = AdminManager(
        admin_settings["host"],
        admin_settings["port"]
    )

    admin_command_menu(
        admin_manager,
        admin_settings["allowed_services"]
    )

    last_telemetry_print = 0

    def receive_input(data):

        try:
            input_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            input_queue.put_nowait(data)
        except queue.Full:
            pass

    event_bus.subscribe("input_updated", receive_input)

    def receive_telemetry(data):

        nonlocal last_telemetry_print

        if time.time() - last_telemetry_print < 2:
            return

        last_telemetry_print = time.time()

        print("\n--- VEHICLE TELEMETRY ---")
        print("Connected:", data["connected"])
        print("Armed:", data["armed"])
        print("Flight mode:", data["flight_mode"])
        print("Depth:", data["depth"])

    event_bus.subscribe("telemetry_updated", receive_telemetry)

    profile = config.get_active_profile()
    settings = config.get_input_settings()

    controller = Controller(settings["dead_zone"])
    keyboard = Keyboard()

    input_manager = InputManager(
        controller,
        keyboard,
        settings["sampling_rate"],
        event_bus
    )

    connection_string = config.settings["mavlink"]["connection"]

    gcs = MAVLinkManager(event_bus)

    if not gcs.connect(connection_string):
        logger.error("Vehicle connection failed.")
        keyboard.close()
        controller.close()
        return

    last_controller_name = None
    input_lost = False
    previous_arm_pressed = False

    vehicle_link_available = gcs.connected

    try:

        input_manager.start()

        while True:

            controller.check_connection()

            link_restored = False

            if gcs.connected != vehicle_link_available:

                vehicle_link_available = gcs.connected

                if not vehicle_link_available:
                    print("Vehicle link lost!")

                else:
                    print("Vehicle link restored!")
                    link_restored = True

            name = controller.get_name()

            if name != last_controller_name:

                if name is not None:
                    if config.load_controller_profile(name):
                        profile = config.get_active_profile()

                last_controller_name = name

            new_profile = keyboard.get_profile_selection()

            if new_profile is not None:
                if config.switch_profile(new_profile):
                    profile = config.get_active_profile()

            try:
                data = input_queue.get_nowait()
            except queue.Empty:
                data = None

            keyboard_available = keyboard.listener.is_alive()
            controller_available = controller.get_name() is not None

            input_available = (
                keyboard_available or controller_available
            )

            if not input_available:

                if not input_lost:
                    print("WARNING: Input lost! Sending neutral movement.")

                input_lost = True

            else:

                if input_lost:
                    print("Input restored!")

                input_lost = False

            x, y, z, r = 0, 0, 500, 0

            controller_actions = None

            if data is not None:

                controller_actions = controller.get_actions(
                    profile,
                    data["controller"]
                )

            arm_pressed = False

            if controller_actions is not None:
                arm_pressed = controller_actions["arm"]

            if arm_pressed and not previous_arm_pressed:

                if gcs.armed:
                    gcs.disarm()
                else:
                    gcs.arm()

            previous_arm_pressed = arm_pressed

            if not input_lost:

                keys = keyboard.get_actions(profile)

                x += 1000 * (
                    int(keys["forward"]) - int(keys["backward"])
                )

                y += 1000 * (
                    int(keys["right"]) - int(keys["left"])
                )

                z += 500 * (
                    int(keys["up"]) - int(keys["down"])
                )

                r += 1000 * (
                    int(keys["yaw_right"]) - int(keys["yaw_left"])
                )

                if controller_actions is not None:

                    x += int(controller_actions["forward"] * 1000)
                    y -= int(controller_actions["left"] * 1000)

            x = max(-1000, min(1000, x))
            y = max(-1000, min(1000, y))
            z = max(0, min(1000, z))
            r = max(-1000, min(1000, r))

            if link_restored:
                x, y, z, r = 0, 0, 500, 0

            if gcs.connected:
                gcs.send_movement(x, y, z, r)

            time.sleep(1 / settings["sampling_rate"])

    except KeyboardInterrupt:
        logger.info("Stopping application")

    finally:

        if gcs.connected:
            gcs.send_movement(0, 0, 500, 0)

        input_manager.stop()
        keyboard.close()
        controller.close()
        gcs.disconnect()


if __name__ == "__main__":
    main()
