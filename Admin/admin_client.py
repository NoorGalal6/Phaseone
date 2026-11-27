
import socket
import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "settings.json"


def load_admin_settings():

    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)

    return config["admin"]


def send_request(command, service=None, confirm=False):

    settings = load_admin_settings()

    host = settings["host"]
    port = settings["port"]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:

        client.connect((host, port))

        print("Connected to admin server!")

        request = {
            "command": command
        }

        if service is not None:
            request["service"] = service

        if confirm:
            request["confirm"] = True

        message = (json.dumps(request) + "\n").encode()

        client.sendall(message)

        data = b""

        while True:

            chunk = client.recv(1024)

            if not chunk:
                break

            data += chunk

            if b"\n" in data:
                break

        response = json.loads(data.decode().strip())

        print("Server response:", response)

    except Exception as error:

        print("Connection error:", error)

    finally:

        client.close()
        print("Connection closed.")


if __name__ == "__main__":

    send_request("status")
