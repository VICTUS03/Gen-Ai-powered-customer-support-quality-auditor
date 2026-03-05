import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from fpdf import FPDF
from io import BytesIO

# --- 1. PDF GENERATION UTILITY ---
def create_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "OFFICIAL QUALITY AUDIT REPORT", ln=True, align='C')
    pdf.ln(10)
    
    # Metadata
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, f"File Name: {data['filename']}", ln=True)
    pdf.cell(200, 10, f"Status: {data['status']}", ln=True)
    pdf.ln(5)
    
    # Scores with Conditional Coloring
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Audit Scores:", ln=True)
    
    pdf.set_font("Arial", size=12)
    # Compliance color logic
    if data['compliance_score'] < 50:
        pdf.set_text_color(255, 0, 0) # Red
    else:
        pdf.set_text_color(0, 128, 0) # Green
        
    pdf.cell(200, 10, f"- Compliance: {data['compliance_score']}/100", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, f"- Empathy: {data['empathy_score']}/100", ln=True)
    pdf.cell(200, 10, f"- Professionalism: {data['professionalism_score']}/100", ln=True)
    pdf.ln(5)
    
    # Suggestions
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Coaching Suggestions:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, data['suggestions'])
    
    # Return as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- 2. DATABASE CONNECTION ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MYSQL",
        database="quality_auditor"
    )

st.set_page_config(page_title="QA Auditor Dashboard", layout="wide")

# --- 3. DATA FETCHING ---
conn = get_db_connection()
query = """
    SELECT t.id, t.filename, t.status, a.empathy_score, a.professionalism_score, a.compliance_score, a.officer_notes, a.advocate_notes, a.suggestions 
    FROM transcripts t 
    LEFT JOIN audit_results a ON t.id = a.transcript_id
"""
df_master = pd.read_sql(query, conn)
conn.close()

# --- HEADER & STATS ---
st.title("🛡️ GenAI Quality Auditor: Supervisor Control Tower")

# Main Metrics
completed_audits = df_master.dropna(subset=['empathy_score'])
if not completed_audits.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Avg Empathy", f"{completed_audits['empathy_score'].mean():.1f}")
    m2.metric("Compliance Rate", f"{completed_audits['compliance_score'].mean():.1f}%")
    m3.metric("Audits Done", len(completed_audits))

# --- PDF REPORT SECTION ---
st.sidebar.divider()
st.sidebar.header("📥 Export Audit PDF")
if not completed_audits.empty:
    selected_file = st.sidebar.selectbox("Select File to Export", completed_audits['filename'].unique())
    
    # Get data for the selected file
    report_data = completed_audits[completed_audits['filename'] == selected_file].iloc[0]
    
    # Generate PDF trigger
    pdf_bytes = create_pdf_report(report_data)
    
    st.sidebar.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"Audit_{selected_file}.pdf",
        mime="application/pdf"
    )
else:
    st.sidebar.info("No completed audits available for export.")

# --- DATA TABLES & VISUALS ---
st.header("📋 Audit Explorer")
st.dataframe(df_master, use_container_width=True)

if not completed_audits.empty:
    st.header("📈 Score Distribution")
    fig = px.bar(completed_audits, x="filename", y=["empathy_score", "compliance_score"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh Dashboard"):
    st.rerun()