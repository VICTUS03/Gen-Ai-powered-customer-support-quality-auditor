import whisper
import psycopg2 # Changed from mysql.connector
from pathlib import Path
import os

from db import get_pg_conn,get_pg_dict_cursor

# --- POSTGRES DATABASE CONFIG ---
# DB_CONFIG = {
#     "host": os.getenv("DB_HOST"),
#     "database": os.getenv("DB_NAME"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"), 
#     "port": os.getenv("DB_PORT")
# }

# Load model once at the top
# print("Loading Whisper Model... please wait.")
# model = whisper.load_model("medium")
# print("Model Loaded!")

_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading Whisper Model... please wait.")
        _model = whisper.load_model("medium")
        print("Model Loaded!")
    return _model


def save_to_db(filename, txt):
    conn = None
    try:
        # Establish PostgreSQL connection
        conn = get_pg_conn                                                # psycopg2.connect(**DB_CONFIG)
        cursor = get_pg_dict_cursor                                       # conn.cursor()

        cursor.execute("SELECT id FROM transcripts WHERE filename = %s", (filename,))
        if cursor.fetchone():
            print(f"Skipping {filename}: Already in Database.")
            return
        
        # Insert statement
        query = "INSERT INTO transcripts (filename, transcript_text, status) VALUES (%s, %s, %s)"
        cursor.execute(query, (filename, txt, 'pending'))

        conn.commit()
        print(f"Successfully saved {filename} in Postgres DB")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

#  Function for Automation ---
def transcribe_single_file(file_path):
    """Handles a single audio file (Used by the Watcher/Automator)"""
    try:
        file_path = Path(file_path)
        print(f"Processing Single File: {file_path.name}...")
        model=get_model()
        
        # Transcribe
        result = model.transcribe(str(file_path), fp16=False, verbose=True)
        text = result["text"].strip()
        
        # Save to Postgres
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
        transcribe_single_file(file_path)

if __name__ == "__main__":
    path = r"C:\Users\pratik p kakade\recordings"
    transcribe_folder(path)