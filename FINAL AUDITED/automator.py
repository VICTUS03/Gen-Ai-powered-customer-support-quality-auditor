import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from transcribe import transcribe_single_file 
from datetime import datetime
import streamlit as st
import threading


SUPPORTED_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac"]
WATCH_DIRECTORY = r"C:\Users\pratik p kakade\recordings"


shared_watch_logs = []


class NewCallHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Only log and process supported files
            if file_ext in SUPPORTED_EXTENSIONS:
                file_name = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                new_entry = {
                    "time": timestamp,
                    "file": file_name,
                    "status": "⏳ Processing..." 
                }
                shared_watch_logs.append(new_entry)
                print(f"[STEP 1] File detected: {file_name}")
                return self.process(event)
                



    def process(self, event):
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in SUPPORTED_EXTENSIONS:
            print(f" [STEP 2] Waiting for file to be ready: {os.path.basename(file_path)}")
            
            time.sleep(2) 
            
            print(f" [STEP 3] Calling Whisper for: {os.path.basename(file_path)}")
            try:
                transcribe_single_file(file_path)
                print(f" [STEP 4] Finished processing: {os.path.basename(file_path)}")
            except Exception as e:
                print(f" [ERROR] Transcription failed: {e}")

            if "watch_logs" in st.session_state:
                shared_watch_logs[-1]["status"] = " Processed"  

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIRECTORY):
        print(f" Error: Path {WATCH_DIRECTORY} does not exist!")
    else:
        event_handler = NewCallHandler()
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
        
        print(f"🚀 Watcher Active. Monitoring: {WATCH_DIRECTORY}")
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()