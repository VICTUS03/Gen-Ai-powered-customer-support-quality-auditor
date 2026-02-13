from pathlib import Path
import pandas as pd
import whisper
import mysql.connector

db_config={
    "host": "localhost",
    "user": "root",        
    "password": "MYSQL", 
    "database": "quality_auditor"
}


model = whisper.load_model("medium")


def save_to_db(filename,txt):

    try:
        conn=mysql.connector.connect(**db_config)
        cursor=conn.cursor()

        cursor.execute("SELECT id FROM transcripts WHERE filename = %s", (filename,))
        if cursor.fetchone():
            print(f"Skipping {filename}: Already in Database.")
            return
        
        query="INSERT INTO transcripts (filename, transcript_text, status) VALUES (%s, %s, %s)"
        cursor.execute(query,(filename,txt,'pending'))

        conn.commit()
        print(f"sucessfully saved {filename} in db ")

    except mysql.connector.Error as e:
        print(f"Database err: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def transcribe_folder(folder_path):
    recordings_dir = Path(folder_path)
    results = []

    audio_extensions = ["*.wav", "*.mp3", "*.m4a", "*.flac"]
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(recordings_dir.glob(ext))

    if not audio_files:
        print("No audio files found in the directory.")
        return pd.DataFrame()

    print(f"Found {len(audio_files)} files. Starting transcription...")

    # 2. Loop through and transcribe
    for file_path in audio_files:
        try:
            print(f"Processing: {file_path.name}...")
            
            # Transcribe the file
 
            result = model.transcribe(str(file_path),fp16=False)

            save_to_db(file_path.name,result["text"].strip())
            
            # Store data in a dictionary
            results.append({
                "filename": file_path.name,
                "transcription": result["text"].strip(),
                "language": result.get("language", "unknown")
            })
            break
            
        except Exception as e:
            print(f"Failed to transcribe {file_path.name}: {e}")
            results.append({
                "filename": file_path.name,
                "transcription": f"ERROR: {str(e)}",
                "language": "N/A"
            })

    # df = pd.DataFrame(results)
    # return df 

if __name__=="__main__":
    path = r"C:\Users\pratik p kakade\recordings"
    transcribe_folder(path)