from fastapi import FastAPI, Request, Form
import mysql.connector
import json

app = FastAPI()

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MYSQL",
    "database": "quality_auditor"
}

@app.get("/")
async def root():
    return {"status": "online", "endpoint": "/slack/interactive"}

@app.post("/slack/interactive")
async def handle_interactive(request: Request):
    try:
        form_data = await request.form()
        payload = json.loads(form_data["payload"])
        print(f"Received interaction from: {payload['user']['name']}") # Debug print

        action = payload["actions"][0]
        job_id = action["value"]
        user_name = payload["user"]["name"]

        if action["action_id"] == "override_score":
            update_audit_override(job_id, user_name)
            return {"text": f"✅ Score overridden by {user_name}!"}
            
    except Exception as e:
        print(f"Error: {e}")
        return {"text": "Internal error handling interaction."}
    
    return {"status": "ok"}

def update_audit_override(job_id, manager_name):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Mark as verified and boost compliance (as an example override)
        query = """
            UPDATE audit_results 
            SET compliance_score = 100, 
                suggestions = CONCAT(suggestions, ' [OVERRIDDEN BY ', %s, ']')
            WHERE transcript_id = %s
        """
        cursor.execute(query, (manager_name, job_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)