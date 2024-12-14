import os
import threading
import time
from queue import PriorityQueue
import requests

class FileDownloader:
    #  Initializes the FileDownloader with URLs to download, destination folder, 
    #  progress callback, error callback, and retry limit.
    def __init__(self, urls, dest_folder, progress_callback, error_callback, retry_limit=3):
        self.urls = PriorityQueue()    # Queue to manage URLs with priority
        for priority, url in enumerate(urls):
            self.urls.put((priority, url))  # Assign priority to each URL
        self.dest_folder = dest_folder
        self.progress_callback = progress_callback  # Callback to update progress
        self.error_callback = error_callback  # Callback to log errors
        self.retry_limit = retry_limit # Maximum retry attempts for failed downloads
        self.lock = threading.Lock() # Lock to ensure thread safety while updating progress
        self.stop_event = threading.Event() # Event to stop download
        self.pause_event = threading.Event() # Event to pause download
        self.pause_event.set()   # Initially set to "resumed" (can pause when cleared)

    def download_file(self, url, index):
        # Downloads a  file with retries and updates progress.
        file_name = os.path.basename(url) # Extracts the file name from the URL
        dest_path = os.path.join(self.dest_folder, file_name) # Path where file will be saved
        attempt = 0
        # Retry logic in case of failure
        while attempt < self.retry_limit:
            try:
                headers = {}
                # Resumes download if part of the file exists
                current_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
                headers['Range'] = f"bytes={current_size}-" # Download from where it was left off
                response = requests.get(url, headers=headers, stream=True, timeout=10)  # Send request to download
                total_size = int(response.headers.get('content-length', 0)) + current_size  # Total file size
                progress = current_size # Current download progress

                with open(dest_path, "ab" if current_size > 0 else "wb") as file:  # Writing file data
                    for data in response.iter_content(chunk_size=1024): # Download data in chunks 1024byte=1kb
                        self.pause_event.wait() # Wait if paused
                        if self.stop_event.is_set():  # Check if download should be stopped
                            return
                        file.write(data)  # Write chunk to file
                        progress += len(data)  # add size of chunk data to progress
                        with self.lock:
                            self.progress_callback(index, progress / total_size * 100) # Update progress

                with self.lock:
                    self.progress_callback(index, 100) # Complete download
                return
            except Exception as e:
                attempt += 1 # Increment retry attempt
                time.sleep(2 ** attempt)  # Exponential backoff before retrying
                error_message = f"Attempt {attempt}/{self.retry_limit} failed: {str(e)}"
                with self.lock:
                    self.error_callback(index, error_message) # Log error message
                if attempt == self.retry_limit:
                    return # Stop after max retries

    def start_download(self):
        # Starts the download process for all URLs in the queue.
        while not self.urls.empty():  # While there are URLs to download
            priority, url = self.urls.get()  # Get the next URL with its priority
            index = priority # Set the download index (priority)
            self.download_file(url, index) # Start downloading the file

    def pause(self):
        #  Pauses the download by clearing the pause event. pause event set to false
        self.pause_event.clear()

    def resume(self):
        #  Resumes the download by setting the pause event.pause event set to true
        self.pause_event.set()

    def stop(self):
        #  Stops the download process.
        self.stop_event.set()


