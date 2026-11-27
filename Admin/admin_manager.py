import socket
import json


class AdminManager:

    def __init__(self, host, port):

        self.host = host
        self.port = port

    def send_request(self, command, service=None, confirm=False):

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            client.connect((self.host, self.port))

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

            return response

        except Exception as error:

            print("Admin connection error:", error)
            return None

        finally:

            client.close()
if __name__ == "__main__":

    manager = AdminManager("127.0.0.1", 5001)

    response = manager.send_request("status")

    print("Server response:", response)