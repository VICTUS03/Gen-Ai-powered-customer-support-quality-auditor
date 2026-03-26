import os
import time
import json
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from redactor import mask_pii
# from main import get_db_connection
from db import get_pg_conn

# --- INITIALIZATION ---
load_dotenv()

os.getenv("HF_TOKEN")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("springboard") 
embed_model = SentenceTransformer('BAAI/bge-large-en-v1.5')

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- DATABASE FUNCTIONS (POSTGRESQL) ---

def transcripts_from_db():
    """Fetches a pending transcript using Postgres RealDictCursor."""
    from psycopg2.extras import RealDictCursor
    conn = get_pg_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT id, transcript_text, filename 
            FROM transcripts 
            WHERE status IN ('pending', 'failed') 
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row
    except Exception as e:
        print(f"❌ DB Fetch Error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_status(transcript_id, status, redacted_text=None):
    """Updates status and saves redacted text in one go (Postgres)."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    try:
        if redacted_text:
            cursor.execute(
                "UPDATE transcripts SET status = %s, redacted_text = %s WHERE id = %s",
                (status, redacted_text, transcript_id)
            )
        else:
            cursor.execute(
                "UPDATE transcripts SET status = %s WHERE id = %s",
                (status, transcript_id)
            )
        conn.commit()
    except Exception as e:
        print(f"❌ DB Update Error: {e}")
    finally:
        cursor.close()
        conn.close()

def save_audit_with_jury(transcript_id, scores, officer_notes, advocate_notes):
    """Saves multi-agent jury results to Postgres."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO audit_results (
                transcript_id, empathy_score, professionalism_score, 
                compliance_score, suggestions, officer_notes, advocate_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            transcript_id, 
            scores.get('empathy_score', 0), 
            scores.get('professionalism_score', 0), 
            scores.get('compliance_score', 0), 
            scores.get('suggestions', "N/A"),
            officer_notes,
            advocate_notes
        ))
        conn.commit()
    except Exception as e:
        print(f"❌ DB Save Audit Error: {e}")
    finally:
        cursor.close()
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
    print("🚀 PostgreSQL Scoring Engine Active. Watching for transcripts...")
    while True:
        job = transcripts_from_db()

        if not job:
            time.sleep(5) 
            continue
        
        # 1. PII Masking
        safe_transcript = mask_pii(job['transcript_text'])

        # Update redacted text immediately so UI shows it
        update_status(job['id'], 'processing', safe_transcript)

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
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": safe_transcript}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            
            jury_output = json.loads(completion.choices[0].message.content)
            final_scores = jury_output['final_decision']

            save_audit_with_jury(
                job['id'], 
                final_scores, 
                jury_output.get('officer_notes', ""), 
                jury_output.get('advocate_notes', "")
            )
            
            update_status(job['id'], 'completed')
            print(f"✨ Successfully audited {job['filename']}")
            
        except Exception as e:
            print(f"❌ Error processing {job['id']}: {e}")
            update_status(job['id'], 'failed')

        time.sleep(1)

if __name__ == "__main__":
    scoring()