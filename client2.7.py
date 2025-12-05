import socket

HOST = "127.0.0.1"
PORT = 678


def receive_file(sock):
    """
    Receive a file sent by the server and save it locally.

    The server first sends the file size as text.
    After receiving the size, the client reads the binary data
    in chunks until all bytes have been received.
    """
    filename = "received_screenshot.jpg"

    size_data = sock.recv(1024).decode().strip()
    if size_data.startswith("ERROR"):
        print("Server response:", size_data)
        return

    filesize = int(size_data)
    print(f"[CLIENT] Receiving screenshot ({filesize} bytes)...")

    received = 0
    with open(filename, "wb") as file:
        while received < filesize:
            chunk = sock.recv(4096)
            if not chunk:
                break
            file.write(chunk)
            received += len(chunk)

    print(f"[CLIENT] Screenshot saved to {filename}")


def main():
    """
    Connect to the server, send user commands,
    and process responses including file transfers.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    print(
        "Available commands: "
        " DIR <path> "
        " DELETE <file> "
        " COPY <src> <dst> "
        " EXECUTE <path> "
        " TAKE_SCREENSHOT "
        " SEND_PHOTO "
        " EXIT"
    )

    while True:
        cmd = input("Enter command: ").strip()
        if not cmd:
            continue

        client_socket.sendall(cmd.encode())

        # The SEND_PHOTO command transfers a binary file.
        if cmd.upper() == "SEND_PHOTO":
            receive_file(client_socket)
            continue

        # Other commands return a text response.
        data = client_socket.recv(100000).decode()
        print("Server response:", data)

        if cmd.upper() == "EXIT":
            break

    client_socket.close()
    print("Disconnected from server.")


if __name__ == "__main__":
    main()
