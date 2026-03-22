import os
import time
import json
import mysql.connector
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from redactor import mask_pii

# --- INITIALIZATION ---
load_dotenv()

os.getenv("HF_TOKEN")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("springboard") 
embed_model = SentenceTransformer('BAAI/bge-large-en-v1.5')

db_config = {
    "host": "localhost",
    "user": "root",        
    "password": "MYSQL", 
    "database": "quality_auditor"
}

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- DATABASE FUNCTIONS ---

def transcripts_from_db():
    """Fetches a single pending transcript, including filename for UI context."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    # Added filename to the query for better logging
    cursor.execute("SELECT id, filename, transcript_text FROM transcripts WHERE status = 'pending' LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def update_status(transcript_id, status):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE transcripts SET status = %s WHERE id = %s", (status, transcript_id))
    conn.commit()
    cursor.close()
    conn.close()

def save_audit_with_jury(transcript_id, scores, officer_notes, advocate_notes):
    """Saves final decision and individual agent thoughts."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """
            INSERT INTO audit_results (
                transcript_id, empathy_score, professionalism_score, 
                compliance_score, suggestions, officer_notes, advocate_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            transcript_id, 
            scores.get('empathy_score', 0), 
            scores.get('professionalism_score', 0), 
            scores.get('compliance_score', 0), 
            scores.get('suggestions', "N/A"),
            officer_notes,
            advocate_notes
        )
        cursor.execute(query, values)
        conn.commit()
        print(f"✅ Audit results saved for {transcript_id}")
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
    finally:
        conn.close()

# --- RAG LOGIC ---

def get_policy(transcript):
    try:
        query_vector = embed_model.encode(transcript).tolist()
        results = index.query(vector=query_vector, top_k=2, include_metadata=True)
        return "\n".join([match['metadata']['text'] for match in results['matches']])
    except Exception as e:
        print(f"Pinecone Retrieval Error: {e}")
        return "No specific policy found."

# --- MAIN SCORING ENGINE ---

def scoring():
    print("🚀 Scoring Engine Started. Waiting for transcripts...")
    while True:
        job = transcripts_from_db()

        if not job:
            time.sleep(5) # Check every 5 seconds
            continue
        
        # 1. PII Masking
        # Inside your scoring() function:
        safe_transcript = mask_pii(job['transcript_text'])

        # Update the database to store the redacted version for the UI
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transcripts SET redacted_text = %s WHERE id = %s", 
            (safe_transcript, job['id'])
        )
        conn.commit()
        conn.close()


        print(f"🔍 Auditing: {job['filename']} (ID: {job['id']})")

        # 2. RAG Context
        relevant_policy = get_policy(safe_transcript)

        system_prompt = f"""
        You are a Multi-Agent Audit Jury. Analyze this call based on these policies:
        {relevant_policy}

        STAGE 1: [COMPLIANCE OFFICER] - Check legal protocols and disclosures.
        STAGE 2: [EMPATHY ADVOCATE] - Check emotional validation and tone.
        STAGE 3: [PRESIDING JUDGE] - Synthesize final scores.

        Return ONLY a JSON object:
        {{
            "officer_notes": "...",
            "advocate_notes": "...",
            "final_decision": {{
                "empathy_score": 0-100,
                "compliance_score": 0-100,
                "professionalism_score": 0-100,
                "suggestions": "..."
            }}
        }}
        """

        try:
            # Note: Changed to a standard Groq Llama model for better JSON reliability
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": safe_transcript}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            
            # Parse Jury Output
            jury_output = json.loads(completion.choices[0].message.content)
            final_scores = jury_output['final_decision']

            # Save to Database
            save_audit_with_jury(
                job['id'], 
                final_scores, 
                jury_output.get('officer_notes', ""), 
                jury_output.get('advocate_notes', "")
            )
            
            # Update status to completed
            update_status(job['id'], 'completed')
            print(f"✨ Successfully audited {job['filename']}")
            
        except Exception as e:
            print(f"❌ Error processing {job['id']}: {e}")
            update_status(job['id'], 'failed')

        time.sleep(1)

if __name__ == "__main__":
    scoring()