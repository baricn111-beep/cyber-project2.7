import socket
import logging
import subprocess
import threading
import os
import shlex
import shutil
import pyautogui

# ========== CONFIGURATION ==========
SERVER_NAME = "MyServer"
HOST = "127.0.0.1"
PORT = 678
LOG_FILE = "server_log.txt"

# ========== LOGGING SETUP ==========
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ========== COMMAND FUNCTIONS ==========
def cmd_photo_send(client_socket):
    """
    Send the previously saved screenshot to the client.

    The server first sends the file size (as text with newline)
    and then sends the full binary content of the file.
    """
    try:
        file_path = r"C:\Users\Bari\OneDrive\Desktop\bari\screenshot.jpg"

        if not os.path.exists(file_path):
            client_socket.sendall(b"ERROR: screenshot file not found")
            return

        file_size = os.path.getsize(file_path)
        client_socket.sendall(f"{file_size}\n".encode())

        with open(file_path, "rb") as file:
            client_socket.sendall(file.read())

        logging.info("Screenshot sent successfully.")

    except Exception as error:
        client_socket.sendall(f"ERROR sending screenshot: {error}".encode())


def cmd_screenshot():
    """
    Take a screenshot of the server's screen and save it to disk.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        filename = "screenshot.jpg"
        save_path = r"C:\Users\Bari\OneDrive\Desktop\bari"
        full_path = os.path.join(save_path, filename)

        image = pyautogui.screenshot()
        image.save(full_path)

        return f"Screenshot saved: {full_path}"

    except Exception as error:
        return f"Screenshot failed: {error}"


def cmd_copy(src, dst):
    """
    Copy a file from source path to destination path.

    Args:
        src (str): Source file path.
        dst (str): Destination file path.

    Returns:
        str: Operation result message.
    """
    try:
        if not src or not dst:
            return ("Error: COPY requires source and destination paths.\n"
                    "Example: COPY C:\\a.txt C:\\b.txt")

        src = src.strip().strip('"')
        dst = dst.strip().strip('"')

        if not os.path.exists(src):
            return f"Error: Source file not found -> {src}"

        if os.path.isdir(src):
            return f"Error: Source path is a directory -> {src}"

        shutil.copy(src, dst)

        return f"File copied successfully:\nFROM: {src}\nTO:   {dst}"

    except PermissionError:
        return f"Error: Permission denied while copying to -> {dst}"

    except Exception as error:
        return f"Error copying file: {error}"


def cmd_delete(file_path):
    """
    Delete a file at the specified path.

    Args:
        file_path (str): Path of the file to delete.

    Returns:
        str: Result of the deletion operation.
    """
    try:
        if not file_path:
            return "Error: You must provide a file path."

        file_path = file_path.strip('"')

        if not os.path.exists(file_path):
            logging.warning(f"DELETE: file not found: {file_path}")
            return f"Error: File not found -> {file_path}"

        if os.path.isdir(file_path):
            return f"Error: {file_path} is a directory, not a file."

        os.remove(file_path)
        logging.info(f"File deleted successfully: {file_path}")

        return f"File deleted successfully: {file_path}"

    except Exception as error:
        logging.error(f"DELETE command failed for {file_path}: {error}")
        return f"Error deleting file: {error}"


def cmd_execute(program_path):
    """
    Execute a program on the server machine.

    Args:
        program_path (str): Full path to the executable file.

    Returns:
        str: Execution result message.
    """
    try:
        if not program_path:
            return "Error: You must provide a program path."

        program_path = program_path.strip('"')

        if not os.path.exists(program_path):
            return f"Error: Program not found -> {program_path}"

        result = subprocess.call(program_path)

        if result == 0:
            return f"Program executed successfully: {program_path}"

        return f"Error: Program returned exit code {result}"

    except Exception as error:
        return f"Execution failed: {error}"


def cmd_exit():
    """
    Return an exit message.

    Returns:
        str: "Goodbye!"
    """
    return "Goodbye!"


def cmd_dir(path):
    """
    List all files and folders inside the specified directory.

    Args:
        path (str): Directory path.

    Returns:
        str: Directory contents or an error message.
    """
    try:
        if not path:
            return "Error: You must provide a directory path."

        if not os.path.exists(path):
            logging.warning(f"DIR: path not found: {path}")
            return f"Error: Path not found -> {path}"

        items = os.listdir(path)

        if not items:
            return f"The directory {path} is empty."

        logging.info(f"DIR command executed successfully for {path}")

        return f"Contents of {path}:\n" + "\n".join(items)

    except Exception as error:
        logging.error(f"DIR command failed for {path}: {error}")
        return f"Error reading directory: {error}"


def cmd_unknown(command):
    """
    Handle unknown commands.

    Args:
        command (str): The unrecognized command.

    Returns:
        str: Unknown command message.
    """
    logging.warning(f"Unknown command received: {command}")
    return f"Unknown command: {command}"


# ========== CLIENT HANDLER ==========
def handle_client(client_socket, client_address):
    """
    Handle a connected client, process incoming commands,
    and send appropriate responses.
    """
    logging.info(f"Client connected: {client_address}")
    print(f"[+] Client connected: {client_address}")

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            command_line = data.decode().strip()
            logging.info(f"Command received from {client_address}: {command_line}")
            print(f"[{client_address}] Command received: {command_line}")

            try:
                parts = shlex.split(command_line)
            except ValueError:
                client_socket.sendall(b"Error: Invalid command format.")
                continue

            command = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            if command == "DIR":
                response = cmd_dir(arg)

            elif command == "DELETE":
                response = cmd_delete(arg)

            elif command == "EXIT":
                response = cmd_exit()

            elif command == "EXECUTE":
                response = cmd_execute(arg)

            elif command == "SEND_PHOTO":
                cmd_photo_send(client_socket)
                continue

            elif command == "TAKE_SCREENSHOT":
                response = cmd_screenshot()

            elif command == "COPY":
                if len(parts) < 3:
                    response = "Error: COPY requires source and destination paths."
                else:
                    response = cmd_copy(parts[1], parts[2])

                client_socket.sendall(response.encode())
                continue

            else:
                response = cmd_unknown(command)

            client_socket.sendall(response.encode())

    except Exception as error:
        logging.error(f"Error handling client {client_address}: {error}")

    finally:
        client_socket.close()
        logging.info(f"Client disconnected: {client_address}")
        print(f"[-] Client disconnected: {client_address}")


# ========== MAIN SERVER LOOP ==========
def main():
    """
    Start the TCP server, accept incoming connections,
    and create a new thread to handle each client.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[+] {SERVER_NAME} listening on {HOST}:{PORT}")
    logging.info(f"{SERVER_NAME} started on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address)
        )
        thread.start()
        logging.info(f"Thread started for {client_address}")


if __name__ == "__main__":
    main()
