import socket
import json
import platform
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "settings.json"


def load_admin_settings():

    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)

    return config["admin"]


def receive_message(client):

    data = b""

    while True:

        chunk = client.recv(1024)

        if not chunk:
            break

        data += chunk

        if b"\n" in data:
            break

    return json.loads(data.decode().strip())


def get_status():

    return {
        "server": "running",
        "operating_system": platform.system(),
        "hostname": platform.node()
    }


def handle_request(request, allowed_services):

    command = request.get("command")

    if command == "status":

        return {
            "status": "success",
            "data": get_status()
        }

    elif command == "restart":

        service = request.get("service")

        if service not in allowed_services:

            return {
                "status": "error",
                "message": "Service is not allowed"
            }

        return {
            "status": "success",
            "message": f"Restart request accepted for {service}",
            "simulated": True
        }

    elif command == "reboot":

        if request.get("confirm") is not True:

            return {
                "status": "error",
                "message": "Reboot confirmation required"
            }

        return {
            "status": "success",
            "message": "Reboot request accepted",
            "simulated": True
        }

    elif command == "poweroff":

        if request.get("confirm") is not True:

            return {
                "status": "error",
                "message": "Poweroff confirmation required"
            }

        return {
            "status": "success",
            "message": "Poweroff request accepted",
            "simulated": True
        }

    else:

        return {
            "status": "error",
            "message": "Unknown command"
        }


def start_server():

    settings = load_admin_settings()

    host = settings["host"]
    port = settings["port"]
    allowed_services = settings["allowed_services"]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen(1)

    print("Admin server is running...")
    print("Listening on:", host, port)
    print("Allowed services:", allowed_services)

    while True:

        client, address = server.accept()

        print("GCS connected:", address)

        try:

            request = receive_message(client)

            print("Received request:", request)

            response = handle_request(
                request,
                allowed_services
            )

            message = json.dumps(response) + "\n"

            client.sendall(message.encode())

        except Exception as error:

            print("Error:", error)

        finally:

            client.close()


if __name__ == "__main__":
    start_server()
