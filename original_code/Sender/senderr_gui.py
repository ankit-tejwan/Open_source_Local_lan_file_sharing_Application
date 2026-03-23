import socket
import sys
import os
import threading
import time
from tkinter import *
from tkinter import filedialog, messagebox, ttk

BUFFER_SIZE = 1024 * 1024  # 1MB


# ---------------------------
# Resource Path (for EXE)
# ---------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------------
# GUI Class
# ---------------------------
class FileSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Local LAN File Sender by Coder")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        # ✅ ICON FIX
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except Exception as e:
            print("Icon load failed:", e)

        self.filepath = ""

        # --- IP ---
        Label(root, text="Receiver IP:").pack(pady=5)
        self.ip_entry = Entry(root, width=40)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.pack()

        # --- PORT ---
        Label(root, text="Port:").pack(pady=5)
        self.port_entry = Entry(root, width=20)
        self.port_entry.insert(0, "5001")
        self.port_entry.pack()

        # --- File Type ---
        Label(root, text="File Type:").pack(pady=5)
        self.file_type = ttk.Combobox(
            root,
            values=["ZIP/RAR", "Images", "Videos", "All Files"]
        )
        self.file_type.current(0)
        self.file_type.pack()

        # --- Browse ---
        Button(root, text="Browse File", command=self.browse_file).pack(pady=10)

        self.file_label = Label(root, text="No file selected", wraplength=450)
        self.file_label.pack()

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(root, length=450, mode="determinate")
        self.progress.pack(pady=15)

        # --- Labels ---
        self.progress_label = Label(root, text="Progress: 0%")
        self.progress_label.pack()

        self.speed_label = Label(root, text="Upload Speed: 0 MB/s")
        self.speed_label.pack()

        # --- Send Button ---
        self.send_btn = Button(root, text="Send File",
                               command=self.start_sending,
                               bg="green", fg="white")
        self.send_btn.pack(pady=10)

    # ---------------------------
    def browse_file(self):
        filetype = self.file_type.get()

        if filetype == "ZIP/RAR":
            types = [("Archive Files", "*.zip *.rar")]
        elif filetype == "Images":
            types = [("Image Files", "*.png *.jpg *.jpeg *.webp")]
        elif filetype == "Videos":
            types = [("Video Files", "*.mp4 *.avi *.mkv")]
        else:
            types = [("All Files", "*.*")]

        file = filedialog.askopenfilename(filetypes=types)

        if file:
            self.filepath = file
            self.file_label.config(text=file)

    # ---------------------------
    def start_sending(self):
        if not self.filepath:
            messagebox.showerror("Error", "Please select a file")
            return

        self.send_btn.config(state=DISABLED)
        self.root.config(cursor="watch")

        threading.Thread(target=self.send_file, daemon=True).start()

    # ---------------------------
    def update_ui(self, percent, speed):
        self.progress["value"] = percent
        self.progress_label.config(text=f"Progress: {percent:.2f}%")
        self.speed_label.config(text=f"Speed: {speed:.2f} MB/s")

    # ---------------------------
    def send_file(self):
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get())

            if not ip:
                raise Exception("Invalid IP")

            filesize = os.path.getsize(self.filepath)
            filename = os.path.basename(self.filepath)

            start_time = time.time()

            with socket.socket() as s:
                s.settimeout(10)
                s.connect((ip, port))

                # Send filename
                s.send(filename.encode())
                s.recv(1024)

                # Send filesize
                s.send(str(filesize).encode())
                s.recv(1024)

                # Resume offset
                offset = int(s.recv(1024).decode())
                sent = offset

                with open(self.filepath, "rb") as f:
                    f.seek(offset)

                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break

                        s.sendall(data)
                        sent += len(data)

                        percent = min((sent / filesize) * 100, 100)

                        elapsed = time.time() - start_time
                        speed = (sent / (1024 * 1024)) / elapsed if elapsed > 0 else 0

                        # Thread-safe UI update
                        self.root.after(0, self.update_ui, percent, speed)

            self.root.after(0, self.finish_success)

        except Exception as e:
            self.root.after(0, self.finish_error, str(e))

    # ---------------------------
    def finish_success(self):
        self.progress_label.config(text="Progress: 100%")
        self.speed_label.config(text="Speed: Done ✅")
        self.send_btn.config(state=NORMAL)
        self.root.config(cursor="")
        messagebox.showinfo("Success", "File sent successfully!")

    def finish_error(self, error):
        self.send_btn.config(state=NORMAL)
        self.root.config(cursor="")
        messagebox.showerror("Error", error)


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    root = Tk()
    app = FileSenderGUI(root)
    root.mainloop()