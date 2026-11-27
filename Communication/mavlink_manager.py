import time
import threading
import queue
from pymavlink import mavutil
class MAVLinkManager:

    def __init__(self, event_bus=None):

        self.event_bus = event_bus

        self.connection = None
        self.command_connection = None

        self.target_system = None
        self.target_component = None

        self.connected = False
        self.armed = False
        self.current_mode = None
        self.depth = None

        
        self.surface_pressure = 1013.25 #in hpa

        self.stop_event = threading.Event()
        self.monitor_thread = None

        self.ack_queue = queue.Queue()

        self.last_heartbeat_time = 0

    
    def connect(self, connection_string):

        print("Connecting to vehicle...")

        self.connection = mavutil.mavlink_connection(
            connection_string
        )

        self.command_connection = mavutil.mavlink_connection(
            "udpout:127.0.0.1:14601"
        )

        heartbeat = self.connection.wait_heartbeat(timeout=10)

        if heartbeat is None:

            print("No heartbeat received.")

            self.connection.close()
            self.command_connection.close()

            self.connection = None
            self.command_connection = None

            return False

        self.target_system = self.connection.target_system
        self.target_component = self.connection.target_component

        self.connected = True
        self.last_heartbeat_time = time.time()

        self.armed = bool(
            heartbeat.base_mode
            & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        )

        self.current_mode = heartbeat.custom_mode

        print("Connected successfully!")
        print("Vehicle system:", self.target_system)
        print("Vehicle component:", self.target_component)

        self.stop_event.clear()

        self.monitor_thread = threading.Thread(
            target=self.monitor_messages,
            daemon=True
        )

        self.monitor_thread.start()

        return True

    
    def calculate_depth(self, pressure):

        pressure_difference = (
            pressure - self.surface_pressure
        )

        depth = (
            pressure_difference * 100
        ) / (1025 * 9.80665)

        return round(depth, 2)

   
    def publish_telemetry(self):

        if self.event_bus is None:
            return

        telemetry = {
            "connected": self.connected,
            "armed": self.armed,
            "flight_mode": self.current_mode,
            "depth": self.depth
        }

        self.event_bus.publish(
            "telemetry_updated",
            telemetry
        )

    
    def monitor_messages(self):

        while not self.stop_event.is_set():

            message = self.connection.recv_match(
                blocking=True,
                timeout=1
            )

            if message is not None:

                
                if message.get_type() == "HEARTBEAT":

                    self.last_heartbeat_time = time.time()

                    if not self.connected:
                        self.connected = True
                        print("Vehicle connection restored!")

                    self.armed = bool(
                        message.base_mode
                        & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                    )

                    self.current_mode = message.custom_mode

                    self.publish_telemetry()

                
                elif message.get_type() == "SCALED_PRESSURE2":

                    self.depth = self.calculate_depth(
                        message.press_abs
                    )

                    self.publish_telemetry()

                
                elif message.get_type() == "COMMAND_ACK":

                    self.ack_queue.put(message)

            
            if time.time() - self.last_heartbeat_time > 3:

                if self.connected:

                    self.connected = False

                    print("WARNING: Vehicle connection lost!")

                    self.publish_telemetry()

   
    def arm(self):
        return self.send_arm_command(1)

    
    def disarm(self):
        return self.send_arm_command(0)

    
    def send_arm_command(self, value):

        if not self.connected:
            print("Cannot send command: vehicle is disconnected.")
            return False

        self.command_connection.mav.command_long_send(
            self.target_system,
            self.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            value,
            0, 0, 0, 0, 0, 0
        )

        print("Waiting for vehicle confirmation...")

        try:
            ack = self.ack_queue.get(timeout=5)

        except queue.Empty:
            print("No command confirmation received.")
            return False

        if ack.command != mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            print("Received confirmation for a different command.")
            return False

        if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:

            if value == 1:
                print("ARM command accepted!")

            else:
                print("DISARM command accepted!")

            return True

        print("Vehicle rejected the command.")
        return False

    
    def set_mode(self, mode_number):

        if not self.connected:
            print("Cannot change mode: vehicle is disconnected.")
            return False

        self.command_connection.mav.command_long_send(
            self.target_system,
            self.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_number,
            0, 0, 0, 0, 0
        )

        print("Waiting for mode confirmation...")

        try:
            ack = self.ack_queue.get(timeout=5)

        except queue.Empty:
            print("No command confirmation received.")
            return False

        if ack.command != mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            print("Received confirmation for a different command.")
            return False

        if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("Flight mode change accepted!")
            return True

        print("Vehicle rejected the mode change.")
        return False

    
    def send_movement(self, x, y, z, r):

        if not self.connected:
            return False

        self.command_connection.mav.manual_control_send(
            self.target_system,
            x,
            y,
            z,
            r,
            0
        )

        return True

   
    def disconnect(self):

        self.stop_event.set()

        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=2)

        if self.connection is not None:
            self.connection.close()
            self.connection = None

        if self.command_connection is not None:
            self.command_connection.close()
            self.command_connection = None

        self.connected = False
        self.armed = False
        self.current_mode = None
        self.depth = None

        self.publish_telemetry()

        print("Disconnected from vehicle.")
