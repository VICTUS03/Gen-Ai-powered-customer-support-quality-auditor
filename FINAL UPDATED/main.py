import streamlit as st

import streamlit as st
st.write("Current file: main.py")

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
    pdf.cell(200, 10, f"File Name: {data.get('filename', 'N/A')}", ln=True)
    # Using .get() prevents the KeyError
    pdf.cell(200, 10, f"Status: {data.get('status', 'N/A')}", ln=True) 
    pdf.ln(5)
    
    # Scores
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Audit Scores:", ln=True)
    
    pdf.set_font("Arial", size=12)
    comp_score = data.get('compliance_score', 0)
    if comp_score < 50:
        pdf.set_text_color(255, 0, 0)
    else:
        pdf.set_text_color(0, 128, 0)
        
    pdf.cell(200, 10, f"- Compliance: {comp_score}/100", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, f"- Empathy: {data.get('empathy_score', 0)}/100", ln=True)
    pdf.cell(200, 10, f"- Professionalism: {data.get('professionalism_score', 0)}/100", ln=True)
    pdf.ln(5)
    
    # Suggestions
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Coaching Suggestions:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, str(data.get('suggestions', 'No suggestions provided.')))
    
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
@st.cache_data(ttl=60)
def fetch_data():
    conn = get_db_connection()
    query = """
    SELECT 
        t.id, 
        t.filename, 
        t.transcript_text, 
        t.redacted_text, 
        t.status, 
        a.empathy_score, 
        a.professionalism_score, 
        a.compliance_score, 
        a.officer_notes, 
        a.advocate_notes, 
        a.suggestions
    FROM transcripts t 
    LEFT JOIN audit_results a ON t.id = a.transcript_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

import streamlit as st
import pandas as pd
import plotly.express as px

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ QA Control Center")
# This is the only thing in your sidebar per your request
view_mode = st.sidebar.radio("Select View Mode", ["Global Overview", "Detailed Audit Review"])

# --- DATA FETCHING ---
# Assuming df_master is already fetched from your MySQL logic
df_master = fetch_data() 
completed_audits = df_master.dropna(subset=['empathy_score'])


# MODE 1: GLOBAL OVERVIEW

if view_mode == "Global Overview":
    st.title("📊 Global Performance Overview")
    st.markdown("Aggregated metrics across all processed transcripts.")

    if not completed_audits.empty:
        # KPI Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Empathy", f"{completed_audits['empathy_score'].mean():.1f}")
        m2.metric("Compliance Rate", f"{completed_audits['compliance_score'].mean():.1f}%")
        m3.metric("Total Audits", len(completed_audits))

        # Big Table
        st.header("📋 All Audit Results")
        st.dataframe(df_master, use_container_width=True)

        # Global Graph
        st.header("📈 Score Trends")
        fig = px.bar(completed_audits, x="filename", y=["empathy_score", "compliance_score","professionalism_score"], barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No audit data found. Please run the scoring engine.")


# MODE 2: DETAILED AUDIT REVIEW

else:
    st.title("🔍 Individual Call Inspection")

    if not df_master.empty:
        # 1. Selection & Download Row
        col_select, col_dl = st.columns([3, 1])
        
        with col_select:
            selected_file = st.selectbox("Select Audio File", df_master['filename'].unique())
        
        # Get specific row data
        call_data = df_master[df_master['filename'] == selected_file].iloc[0]

        with col_dl:
            if pd.notnull(call_data['empathy_score']):
                # Trigger your PDF function
                pdf_bytes = create_pdf_report(call_data)
                st.download_button(
                    label="📥 Download Report",
                    data=pdf_bytes,
                    file_name=f"Report_{selected_file}.pdf",
                    mime="application/pdf"
                )
            else:
                st.button("📥 Download Report", disabled=True, help="Audit pending")

        # 2. Specific Metrics for this file
        if pd.notnull(call_data['empathy_score']):
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Empathy", f"{call_data['empathy_score']}/100")
            c2.metric("Compliance", f"{call_data['compliance_score']}/100")
            c3.metric("Professionalism", f"{call_data['professionalism_score']}/100")

            # 3. Individual Graph
            # We melt the data to make a nice comparison chart for just this one call
            chart_data = pd.DataFrame({
            'Metric': ['Empathy', 'Compliance', 'Professionalism'],
            'Score': [
                call_data.get('empathy_score', 0), 
                call_data.get('compliance_score', 0), 
                call_data.get('professionalism_score', 0)
                ]
            })
            # Fill NaNs with 0 just for the chart display
            chart_data['Score'] = chart_data['Score'].fillna(0)
            fig_individual = px.bar(chart_data, x='Metric', y='Score', color='Metric', range_y=[0, 100])
            st.plotly_chart(fig_individual, use_container_width=True)

            # 4. Transcription Comparison
            st.subheader("📄 Transcription Analysis")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**Original**")
                st.text_area("Full Text", call_data['transcript_text'], height=250, disabled=True)
            with t_col2:
                st.markdown("**Scrubbed / Masked**")
                st.text_area("PII Redacted", call_data.get('redacted_text', 'Not Redacted'), height=250, disabled=True)

            # 5. Jury Reasoning
            st.subheader("👨‍⚖️ Multi-Agent Jury Notes")
            tab1, tab2, tab3 = st.tabs(["Compliance Officer", "Empathy Advocate", "Coaching Tips"])
            with tab1:
                st.info(call_data['officer_notes'])
            with tab2:
                st.info(call_data['advocate_notes'])
            with tab3:
                st.success(call_data['suggestions'])
        else:
            st.warning("⚠️ This file is currently in the queue or failed processing.")
    else:
        st.error("No data available in the database.")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()