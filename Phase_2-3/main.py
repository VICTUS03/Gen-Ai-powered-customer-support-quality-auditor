import streamlit as st
import pandas as pd
from transcribe import transcribe_folder # Assuming you modify this to accept a single file
from scoring_engine import scoring
import whisper
import tempfile
import os

import pandas as pd
import mysql.connector
import plotly.express as px

# --- DATABASE CONNECTION ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MYSQL",
        database="quality_auditor"
    )

st.set_page_config(page_title="QA Auditor Dashboard", layout="wide")

# --- HEADER ---
st.title("🛡️ GenAI Quality Auditor: Supervisor Control Tower")
st.markdown("Monitoring MySQL Database Pipeline | Groq & Pinecone RAG")

# --- SIDEBAR STATS ---
st.sidebar.header("System Health")
conn = get_db_connection()
df_status = pd.read_sql("SELECT status, COUNT(*) as count FROM transcripts GROUP BY status", conn)
conn.close()

for _, row in df_status.iterrows():
    st.sidebar.metric(f"Status: {row['status'].upper()}", row['count'])

# --- MAIN DASHBOARD METRICS ---
conn = get_db_connection()
# Fetch joined results for the dashboard
query = """
    SELECT t.filename, t.status, a.empathy_score, a.professionalism_score, a.compliance_score, a.suggestions 
    FROM transcripts t 
    LEFT JOIN audit_results a ON t.id = a.transcript_id
"""
df_master = pd.read_sql(query, conn)
conn.close()

# KPI Rows
completed_audits = df_master.dropna(subset=['empathy_score'])
if not completed_audits.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Global Avg Empathy", f"{completed_audits['empathy_score'].mean():.1f}")
    col2.metric("Compliance Rate", f"{completed_audits['compliance_score'].mean():.1f}%")
    col3.metric("Critical Red Flags", len(completed_audits[completed_audits['compliance_score'] < 50]))

# --- AUDIT EXPLORER ---
st.header("📋 Recent Audit Reports")
st.dataframe(
    df_master.style.highlight_between(left=0, right=50, subset=['compliance_score'], color='lightpink'),
    use_container_width=True
)

# --- VISUALIZATION ---
if not completed_audits.empty:
    st.header("📈 Performance Trends")
    fig = px.histogram(completed_audits, x="empathy_score", nbins=10, title="Empathy Score Distribution")
    st.plotly_chart(fig)

# --- MANUAL ACTIONS ---
st.divider()
if st.button("🔄 Refresh Data from MySQL"):
    st.rerun()