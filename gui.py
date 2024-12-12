from tkinter import Tk, filedialog, Button, Label, Text, ttk, Frame, Toplevel, Spinbox
import threading
from downloader import FileDownloader


class DownloaderGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("Multi-Threaded Downloader")
        self.root.geometry("700x700")
        self.urls = []
        self.dest_folder = ""
        self.threads = []
        self.thread_count = 1
        self.download_windows = []
        self.retry_limit = 3  # Default retry limit
        self.downloaders = {}  # Map Toplevel windows to downloader instances
        self.setup_ui()

    def setup_ui(self):
        self.root.configure(bg="white")

        Label(self.root, text="Multi-Threaded Downloader", font=("Arial", 16), bg="white", fg="black").pack(pady=10)

        Label(self.root, text="Enter URLs (one per line):", bg="white", fg="black").pack()
        self.text_box = Text(self.root, height=10, width=50, bg="#FFE4E1", fg="black")  # Light pink background
        self.text_box.pack(pady=10)

        Label(self.root, text="Select Destination Folder:", bg="white", fg="black").pack()
        self.folder_label = Label(self.root, text="Not Selected", bg="#D3D3D3", width=40, fg="black")
        self.folder_label.pack(pady=5)
        Button(self.root, text="Browse", command=self.browse_folder, bg="#008080", fg="white").pack(pady=5)  # Teal button

        Label(self.root, text="Number of Threads:", bg="white", fg="black").pack(pady=5)
        self.thread_selector = Spinbox(self.root, from_=1, to=10, width=5, command=self.update_thread_count, bg="white", fg="black")
        self.thread_selector.pack()

        Label(self.root, text="Retry Limit:", bg="white", fg="black").pack(pady=5)
        self.retry_limit_selector = Spinbox(self.root, from_=1, to=10, width=5, command=self.update_retry_limit, bg="white", fg="black")
        self.retry_limit_selector.pack()

        Button(self.root, text="Start Download", command=self.start_download, bg="#008080", fg="white").pack(pady=10)  # Teal button

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder = folder
            self.folder_label.config(text=folder)

    def update_thread_count(self):
        self.thread_count = int(self.thread_selector.get())

    def update_retry_limit(self):
        self.retry_limit = int(self.retry_limit_selector.get())

    def start_download(self):
        urls = self.text_box.get("1.0", "end-1c").splitlines()
        if not urls:
            self.show_error("No URLs provided.")
            return
        if not self.dest_folder:
            self.show_error("Destination folder not selected.")
            return

        self.urls = urls

        for i in range(self.thread_count):
            download_window = Toplevel(self.root)
            download_window.title(f"Thread {i+1} Progress")
            download_window.configure(bg="white")

            progress_bar = ttk.Progressbar(download_window, length=400, mode="determinate")
            progress_bar.pack(pady=20)

            log_box = Text(download_window, state="disabled", height=10, width=50, bg="#FFE4E1", fg="black")  # Light pink background
            log_box.pack(pady=10)

            button_frame = Frame(download_window, bg="white")
            button_frame.pack(pady=10)

            pause_button = Button(button_frame, text="Pause", command=lambda d=download_window: self.pause_download(d), bg="#008080", fg="white")
            pause_button.pack(side="left", padx=5)

            resume_button = Button(button_frame, text="Resume", command=lambda d=download_window: self.resume_download(d), bg="#008080", fg="white")
            resume_button.pack(side="left", padx=5)

            cancel_button = Button(button_frame, text="Cancel", command=lambda d=download_window: self.cancel_download(d), bg="#008080", fg="white")
            cancel_button.pack(side="left", padx=5)

            downloader = FileDownloader(
                urls[i::self.thread_count],  # Distribute URLs among threads
                self.dest_folder,
                lambda idx, prog, bar=progress_bar: self.update_progress(bar, prog),
                lambda idx, err, log=log_box: self.log_error(log, err),
                self.retry_limit
            )

            thread = threading.Thread(target=downloader.start_download)
            self.threads.append(thread)
            self.download_windows.append(download_window)
            self.downloaders[download_window] = downloader  # Link window to downloader instance

            thread.start()

    def pause_download(self, download_window):
        if download_window in self.downloaders:
            self.downloaders[download_window].pause()

    def resume_download(self, download_window):
        if download_window in self.downloaders:
            self.downloaders[download_window].resume()

    def cancel_download(self, download_window):
        if download_window in self.downloaders:
            self.downloaders[download_window].stop()
            self.download_windows.remove(download_window)
            download_window.destroy()

    def update_progress(self, progress_bar, progress):
        progress_bar["value"] = progress

    def log_error(self, log_box, error):
        log_box.config(state="normal")
        log_box.insert("end", error + "\n")
        log_box.config(state="disabled")

    def show_error(self, message):
        error_window = Toplevel(self.root)
        error_window.title("Error")
        error_window.configure(bg="white")
        Label(error_window, text=message, fg="red", bg="white").pack(pady=10)
        Button(error_window, text="OK", command=error_window.destroy, bg="#008080", fg="white").pack(pady=5)

    def run(self):
        self.root.mainloop()

