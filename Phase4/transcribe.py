import whisper
import mysql.connector
from pathlib import Path
import os

# --- DATABASE CONFIG ---
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MYSQL",
    "database": "quality_auditor"
}

# Load model once at the top
print("Loading Whisper Model... please wait.")
model = whisper.load_model("medium")
print("Model Loaded!")


def save_to_db(filename, txt):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM transcripts WHERE filename = %s", (filename,))
        if cursor.fetchone():
            print(f"Skipping {filename}: Already in Database.")
            return
        
        query = "INSERT INTO transcripts (filename, transcript_text, status) VALUES (%s, %s, %s)"
        cursor.execute(query, (filename, txt, 'pending'))

        conn.commit()
        print(f"Successfully saved {filename} in DB")

    except mysql.connector.Error as e:
        print(f"Database err: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- NEW: Function for Automation ---
def transcribe_single_file(file_path):
    """Handles a single audio file (Used by the Watcher/Automator)"""
    try:
        file_path = Path(file_path)
        print(f"Processing Single File: {file_path.name}...")
        
        # Transcribe
        result = model.transcribe(str(file_path), fp16=False, verbose=True)
        text = result["text"].strip()
        
        # Save to MySQL
        save_to_db(file_path.name, text)
        return text
    except Exception as e:
        print(f"Failed to transcribe {file_path}: {e}")
        return None

def transcribe_folder(folder_path):
    """Handles bulk processing of an existing folder"""
    recordings_dir = Path(folder_path)
    audio_extensions = ["*.wav", "*.mp3", "*.m4a", "*.flac"]
    
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(recordings_dir.glob(ext))

    if not audio_files:
        print("No audio files found.")
        return

    print(f"Found {len(audio_files)} files. Starting bulk transcription...")
    for file_path in audio_files:
        transcribe_single_file(file_path) # Call the single-file logic

if __name__ == "__main__":
    path = r"C:\Users\pratik p kakade\recordings"
    transcribe_folder(path)