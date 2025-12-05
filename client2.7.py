import socket

HOST = "127.0.0.1"
PORT = 6776

def receive_file(sock):
    """מקבל קובץ מהשרת ושומר אותו"""
    # מקבל את שם הקובץ (למטרה שלך אפשר לשמור בשם קבוע)
    filename = "received_screenshot.jpg"

    # מקבל את גודל הקובץ
    size_data = sock.recv(1024).decode().strip()
    if size_data.startswith("ERROR"):
        print("Server response:", size_data)
        return

    filesize = int(size_data)
    print(f"[CLIENT] Receiving screenshot ({filesize} bytes)...")

    # מקבל את תוכן הקובץ
    received = 0
    with open(filename, "wb") as f:
        while received < filesize:
            chunk = sock.recv(4096)
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)

    print(f"[CLIENT] Screenshot saved to {filename}")

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    print("Connected to server. Commands: DIR <path>, DELETE <file>, COPY <src> <dst>, EXECUTE <path>, TAKE_SCREENSHOT, SEND_PHOTO, EXIT")

    while True:
        cmd = input("Enter command: ").strip()
        if not cmd:
            continue

        client_socket.sendall(cmd.encode())

        # פקודה שמחזירה קובץ
        if cmd.upper() == "SEND_PHOTO":
            receive_file(client_socket)
            continue

        # שאר הפקודות מחזירות טקסט
        data = client_socket.recv(100000).decode()
        print("Server response:", data)

        if cmd.upper() == "EXIT":
            break

    client_socket.close()
    print("Disconnected.")

if __name__ == "__main__":
    main()
