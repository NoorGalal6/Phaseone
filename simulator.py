
import time
import threading

from pymavlink import mavutil



heartbeat_connection = mavutil.mavlink_connection(
    "udpout:127.0.0.1:14600"
)


command_connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14601"
)


armed = False

flight_modes = {
    0: "MANUAL",
    1: "STABILIZE",
    2: "ALT_HOLD"
}

current_mode = 0


depth = 2.0


surface_pressure = 1013.25


pressure = surface_pressure + (depth * 100)


print("Simulator started!")
print("Waiting for GCS commands...")


def receive_commands():

    global armed, current_mode

    while True:

        message = command_connection.recv_match(
            blocking=True
        )

        if message is None:
            continue

        
        if message.get_type() == "MANUAL_CONTROL":

            print("\nMovement received!")
            print("Forward / Backward:", message.x)
            print("Left / Right:", message.y)
            print("Up / Down:", message.z)
            print("Rotation:", message.r)

            continue

        if message.get_type() != "COMMAND_LONG":
            continue

        
        if message.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:

            if message.param1 == 1:
                armed = True
                print("Vehicle ARMED!")

            elif message.param1 == 0:
                armed = False
                print("Vehicle DISARMED!")

        
        elif message.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:

            new_mode = int(message.param2)

            if new_mode in flight_modes:

                current_mode = new_mode

                print(
                    "Flight mode changed to:",
                    flight_modes[current_mode]
                )

            else:
                print("Unknown flight mode!")

        else:
            continue

        
        heartbeat_connection.mav.command_ack_send(
            message.command,
            mavutil.mavlink.MAV_RESULT_ACCEPTED
        )

        print("COMMAND_ACK sent!")



command_thread = threading.Thread(
    target=receive_commands,
    daemon=True
)

command_thread.start()



while True:

    base_mode = (
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
    )

    if armed:
        base_mode |= (
            mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        )

    
    heartbeat_connection.mav.heartbeat_send(
        mavutil.mavlink.MAV_TYPE_SUBMARINE,
        mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
        base_mode,
        current_mode,
        mavutil.mavlink.MAV_STATE_STANDBY
    )

    
    heartbeat_connection.mav.scaled_pressure2_send(
        int(time.time() * 1000) % 4294967296,
        pressure,
        0,
        2000
    )

    time.sleep(1)
