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
PORT = 6777
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
    try:
        file_path = r"C:\Users\Bari\OneDrive\Desktop\bari\screenshot.jpg"

        if not os.path.exists(file_path):
            client_socket.sendall(b"ERROR: screenshot file not found")
            return
        file_size = os.path.getsize(file_path)

        # שולחים קודם את הגודל (כטקסט)
        client_socket.sendall(f"{file_size}".encode() + b"\n")

        # שולחים את התוכן עצמו
        with open(file_path, "rb") as f:
            client_socket.sendall(f.read())

        logging.info("Screenshot sent successfully.")

    except Exception as e:
        client_socket.sendall(f"ERROR sending screenshot: {e}".encode())


def cmd_screenshot():
    try:
        filename = "screenshot.jpg"
        save_path = r"C:\Users\Bari\OneDrive\Desktop\bari"  # תיקייה
        full_path = os.path.join(save_path, filename)       # מחברים תיקייה + שם קובץ

        image = pyautogui.screenshot()
        image.save(full_path)

        return f"Screenshot saved: {full_path}"
    except Exception as e:
        return f"Screenshot failed: {e}"




def cmd_copy(src, dst):
    """

    :param src:
    :param dst:
    :return:
    """
    """Copy a file from src to dst."""
    try:
        if not src or not dst:
            return "Error: COPY requires source and destination paths.\nExample: COPY C:\\a.txt C:\\b.txt"

        # הסרת גרשיים
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

    except Exception as e:
        return f"Error copying file: {e}"


def cmd_delete(file_path):
    """Delete a file from the given path."""
    try:
        if not file_path:
            return "Error: You must provide a file path. Example: DELETE C:\\Cyber\\file.txt"

        file_path = file_path.strip('"')

        if not os.path.exists(file_path):
            logging.warning(f"DELETE: file not found: {file_path}")
            return f"Error: File not found -> {file_path}"

        if os.path.isdir(file_path):
            return f"Error: {file_path} is a directory, not a file."

        os.remove(file_path)
        logging.info(f"File deleted successfully: {file_path}")
        return f"File deleted successfully: {file_path}"

    except Exception as e:
        logging.error(f"DELETE command failed for {file_path}: {e}")
        return f"Error deleting file: {e}"

def cmd_execute(program_path):
    """Execute a program on the server."""
    try:
        if not program_path:
            return "Error: You must provide a program path. Example: EXECUTE C:\\Windows\\notepad.exe"

        program_path = program_path.strip('"')

        # בדיקה שהתוכנה קיימת
        if not os.path.exists(program_path):
            return f"Error: Program not found -> {program_path}"

        # ניסיון להריץ את התוכנה
        result = subprocess.call(program_path)

        # אם ההרצה הצליחה
        if result == 0:
            return f"Program executed successfully: {program_path}"
        else:
            return f"Error: Program returned exit code {result}"

    except Exception as e:
        return f"Execution failed: {e}"


def cmd_exit():
    """Return exit message."""
    return "Goodbye!"

def cmd_dir(path):
    """Return list of files and folders in a given directory."""
    try:
        if not path:
            return "Error: You must provide a folder path. Example: DIR C:\\Cyber"

        if not os.path.exists(path):
            logging.warning(f"DIR: path not found: {path}")
            return f"Error: Path not found -> {path}"

        items = os.listdir(path)
        if not items:
            return f"The directory {path} is empty."

        result = f"Contents of {path}:\n" + "\n".join(items)
        logging.info(f"DIR command executed successfully for {path}")
        return result

    except Exception as e:
        logging.error(f"DIR command failed for {path}: {e}")
        return f"Error reading directory: {e}"

def cmd_unknown(command):
    """Handle unknown command."""
    logging.warning(f"Unknown command received: {command}")
    return f"Unknown command: {command}"


# ========== CLIENT HANDLER ==========
def handle_client(client_socket, client_address):
    """
    Handle a single client connection: read commands, process them, and send responses.
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

            # 🟢 עדכון: נפרק את הפקודה עם shlex כדי לתמוך בגרשיים
            try:
                parts = shlex.split(command_line)  # מפרק לפי רווחים ומתחשב בגרשיים
            except ValueError:
                client_socket.sendall(b"Error: Invalid command format.")
                continue

            command = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            # טיפול בפקודות
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
                    src = parts[1]
                    dst = parts[2]
                    response = cmd_copy(src, dst)

                client_socket.sendall(response.encode())
                logging.info(f"Client {client_address} disconnected by EXIT command.")
                break
            else:
                response = cmd_unknown(command)

            # שליחת תשובה ללקוח
            client_socket.sendall(response.encode())
            logging.info(f"Response sent to {client_address}: {response[:100]}...")

    except Exception as e:
        logging.error(f"Error handling client {client_address}: {e}")
        print(f"Error handling client {client_address}: {e}")

    finally:
        client_socket.close()
        logging.info(f"Client disconnected: {client_address}")
        print(f"[-] Client disconnected: {client_address}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # יצירת socket TCP
    server.bind((HOST, PORT))                                     # חיבור לכתובת ופורט
    server.listen(5)                                              # מאזין עד 5 חיבורים בו זמנית
    print(f"[+] {SERVER_NAME} listening on {HOST}:{PORT}")
    logging.info(f"{SERVER_NAME} started on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()           # מחכה ללקוח חדש
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()                                            # מתחיל thread חדש לטיפול בלקוח
        logging.info(f"Thread started for {client_address}")

if __name__ == "__main__":
    print(cmd_copy("./test.txt", "./test1.txt"))
    main()

