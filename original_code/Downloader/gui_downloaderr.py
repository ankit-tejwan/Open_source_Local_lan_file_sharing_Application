import socket
import os
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import sys
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_local_ip():
    """Automatically detects the local IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class FileReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local LAN File Receiver by Coder")
        self.root.geometry("400x400")
        
        # --- Set the Icon ---
        try:
            self.root.iconbitmap(resource_path(r"image.ico"))
        except Exception as e:
            print(f"Icon not found: {e}")
        
        # --- UI Elements ---
        tk.Label(root, text="Local IPv4 Address:", font=('Arial', 10, 'bold')).pack(pady=5)
        self.ip_label = tk.Label(root, text=get_local_ip(), fg="blue", font=('Arial', 10))
        self.ip_label.pack()

        tk.Label(root, text="Port Number:", font=('Arial', 10, 'bold')).pack(pady=5)
        self.port_entry = tk.Entry(root, justify='center')
        self.port_entry.insert(0, "5001")
        self.port_entry.pack()

        self.status_label = tk.Label(root, text="Status: Idle", fg="gray", font=('Arial', 9, 'italic'))
        self.status_label.pack(pady=10)

        self.percentage_label = tk.Label(root, text="0%", font=('Arial', 12, 'bold'))
        self.percentage_label.pack()
        
        self.download_text_label = tk.Label(root, text="", fg="#555", wraplength=350)
        self.download_text_label.pack()

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5)
        
        # FIXED: Changed Label to tk.Label
        self.speed_label = tk.Label(root, text="Download Speed: 0 MB/s")
        self.speed_label.pack()

        self.start_btn = tk.Button(root, text="Start Listening", command=self.start_thread, bg="green", fg="white", width=20)
        self.start_btn.pack(pady=15)

        self.BUFFER_SIZE = 1024 * 1024  # 1MB

    def update_ui(self, current, total, filename, speed):
        """Updates labels and progress bar safely."""
        percent = int((current / total) * 100)
        self.percentage_label.config(text=f"{percent}%")
        self.download_text_label.config(text=f"Receiving: {filename}")
        self.progress["value"] = current
        self.speed_label.config(text=f"Download Speed: {speed:.2f} MB/s")
        self.root.update_idletasks()

    def start_thread(self):
        thread = threading.Thread(target=self.receive_file, daemon=True)
        thread.start()
        self.start_btn.config(state="disabled")

    def receive_file(self):
        HOST = "0.0.0.0" 
        try:
            PORT = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Port Number")
            self.root.after(0, self.reset_ui)
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, PORT))
                s.listen(1)
                self.status_label.config(text=f"Status: Waiting for sender...", fg="blue")
                
                conn, addr = s.accept()
                with conn:
                    self.status_label.config(text=f"Status: Connected to {addr[0]}", fg="green")

                    # Receive metadata (Filename)
                    filename = conn.recv(1024).decode().strip()
                    conn.send(b"OK")
                    
                    # Receive metadata (Filesize)
                    filesize_str = conn.recv(1024).decode().strip()
                    filesize = int(filesize_str)
                    conn.send(b"OK")

                    # Resume Logic
                    existing_size = os.path.getsize(filename) if os.path.exists(filename) else 0
                    conn.send(str(existing_size).encode())

                    mode = "ab" if existing_size > 0 else "wb"
                    received_so_far = existing_size
                    
                    self.progress["maximum"] = filesize
                    
                    start_time = time.time()
                    bytes_since_last_check = 0
                    
                    with open(filename, mode) as f:
                        while received_so_far < filesize:
                            data = conn.recv(self.BUFFER_SIZE)
                            if not data:
                                break
                            f.write(data)
                            
                            chunk_len = len(data)
                            received_so_far += chunk_len
                            bytes_since_last_check += chunk_len
                            
                            # Calculate speed every second
                            elapsed = time.time() - start_time
                            if elapsed >= 1.0:
                                speed = (bytes_since_last_check / (1024 * 1024)) / elapsed
                                self.update_ui(received_so_far, filesize, filename, speed)
                                # Reset for next second
                                start_time = time.time()
                                bytes_since_last_check = 0
                            elif received_so_far == filesize:
                                self.update_ui(received_so_far, filesize, filename, 0)

                    messagebox.showinfo("Success", f"File '{filename}' received successfully!")
                    self.root.after(0, self.reset_ui)

        except Exception as e:
            messagebox.showerror("Socket Error", str(e))
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.status_label.config(text="Status: Idle", fg="gray")
        self.percentage_label.config(text="0%")
        self.download_text_label.config(text="")
        self.speed_label.config(text="Download Speed: 0 MB/s")
        self.progress["value"] = 0
        self.start_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileReceiverApp(root)
    root.mainloop()