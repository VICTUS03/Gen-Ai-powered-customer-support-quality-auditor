from groq import Groq
from pinecone import Pinecone
import json
from sentence_transformers import SentenceTransformer
import mysql.connector
import os
import time

from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("infosys-sprinboard") 

# Embedding Model 
embed_model = SentenceTransformer('BAAI/bge-large-en-v1.5')


db_config={
    "host": "localhost",
    "user": "root",        
    "password": "(db_pass)", 
    "database": "quality_auditor"
}

client=Groq(
    api_key=os.getenv("GROQ_API_KEY")
)



def get_policy(transcript):
    try:
        query_vector=embed_model.encode(transcript).to_list()

        results=index.query(vector=query_vector,top_k=2,include_metadata=True)
        return "\n".join([match['metadata']['text'] for match in results['matches']])

    except Exception as e:
        print(f"Pinecone Retrieval Error: {e}")
        return "No specific policy found."



def transcripts_from_db():
    conn=mysql.connector.connect(**db_config)
    cursor=conn.cursor(dictionary=True)

    cursor.execute("SELECT id, transcript_text FROM transcripts WHERE status = 'pending' OR status = 'failed' LIMIT 1")
    row = cursor.fetchone()

    cursor.close()
    return row

def update_status(transcript_id,status):
    conn=mysql.connector.connect(**db_config)
    cursor=conn.cursor()
    cursor.execute("UPDATE transcripts SET status = %s WHERE id = %s", (status, transcript_id))
    conn.commit()
    conn.close()

def save_audit(transcript_id,scores):
    conn=mysql.connector.connect(**db_config)
    cursor=conn.cursor()
    query = """
        INSERT INTO audit_results (transcript_id, empathy_score, professionalism_score, compliance_score, suggestions)
        VALUES (%s, %s, %s, %s, %s)
    """
    values=(
        transcript_id, 
        scores.get('empathy_score', 0), 
        scores.get('professionalism_score', 0), 
        scores.get('compliance_score', 0), 
        scores.get('suggestions', "N/A")
    )
    cursor.execute(query,values)
    conn.commit()
    conn.close()

def scoring():
    while True:
        job=transcripts_from_db()

        if not job:
            print("No pending transcripts.")
            time.sleep(10)
            return

        print(f"Auditing Transcript ID: {job['id']}...")

        relevant_policy=get_policy(job['transcript_text'])

        system_prompt = (
            "You are a QA Auditor. Evaluate the transcript based on the provided COMPANY POLICY.\n"
            f"### COMPANY POLICY:\n{relevant_policy}\n\n"
            "Score (1-100): Empathy, Professionalism, Compliance. "
            "If the agent violated the policy above, Compliance MUST be below 40. "
            "Return ONLY JSON: {empathy_score, professionalism_score, compliance_score, suggestions}"
        )

        try:
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": job['transcript_text']}],
                model="openai/gpt-oss-120b",
                response_format={"type": "json_object"}
            )
            
            scores = json.loads(completion.choices[0].message.content)
            save_audit(job['id'], scores)
            update_status(job['id'], 'completed')
            print(f"Success! Record {job['id']} audited.")
            
        except Exception as e:
            print(f"Error processing {job['id']}: {e}")
            update_status(job['id'], 'failed')

        time.sleep(2)

if __name__ == "__main__":
    scoring()





    
