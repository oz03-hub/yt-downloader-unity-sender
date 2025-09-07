import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

# Remember to change these
WATCH_DIRECTORY = "/tmp/PATH_TO_YOUR_DIR"
RSYNC_DEST = "unity:/PATH_TO_YOUR_SCRATCH_SPACE" # do not erase unity: part

class NewWavHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".wav"):
            print(f"Detected new .wav file: {event.src_path}")
            self.rsync_file(event.src_path)

    def rsync_file(self, filepath):
        try:
            command = [
                "rsync",
                "-avP", "--partial", "--info=progress2", "--bwlimit=20000",
                "-e", "ssh -i ~/.ssh/ytb_rsync_key -T -o Compression=no -o StrictHostKeyChecking=no",
                filepath,
                RSYNC_DEST
            ]
            print(f"Running rsync for: {filepath}")
            subprocess.run(command, check=True)
            print(f"File successfully synced: {filepath}")

            os.remove(filepath)
            print(f"Deleted local file: {filepath}")
        except subprocess.CalledProcessError as e:
            print(f"Rsync failed for {filepath} with error: {e}")

if __name__ == "__main__":
    event_handler = NewWavHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)
    observer.start()
    print(f"Watching recursively: {WATCH_DIRECTORY} for .wav files")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
