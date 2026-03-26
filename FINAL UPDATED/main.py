import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import plotly.express as px
from fpdf import FPDF
import os


def style_dataframe(df):
    styled_df = df.copy()

    display_cols = ['filename', 'status', 'compliance_score', 'empathy_score', 'professionalism_score', 'created_at']
    
    # Ensure columns exist before filtering to prevent KeyError
    available_cols = [c for c in display_cols if c in styled_df.columns]
    
    
    return styled_df[available_cols]


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
    pdf.cell(200, 10, f"Status: {data.get('status', 'N/A')}", ln=True) 
    pdf.ln(5)
    
    # Scores
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Audit Scores:", ln=True)
    
    pdf.set_font("Arial", size=12)
    comp_score = data.get('compliance_score', 0)
    if comp_score < 50:
        pdf.set_text_color(255, 0, 0) # Red
    else:
        pdf.set_text_color(0, 128, 0) # Green
        
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

# --- 2. POSTGRES DATABASE CONNECTION ---
def get_db_engine():
    # Format: postgresql://user:password@host:port/database
    user =  os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port =  os.getenv("DB_PORT")
    db =  os.getenv("DB_NAME")

    return create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

st.set_page_config(page_title="QA Auditor Dashboard", layout="wide")

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=60)
def fetch_data():
    engine = get_db_engine()
    query = """
    SELECT 
        t.id, 
        t.filename, 
        t.transcript_text, 
        t.redacted_text, 
        t.status, 
        t.created_at,
        a.empathy_score, 
        a.professionalism_score, 
        a.compliance_score, 
        a.officer_notes, 
        a.advocate_notes, 
        a.suggestions,
        a.audited_at
    FROM transcripts t 
    LEFT JOIN audit_results a ON t.id = a.transcript_id
    ORDER BY t.created_at DESC
    """
    # read_sql works perfectly with SQLAlchemy engine
    df = pd.read_sql(query, engine)
    return df

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ QA Control Center")
view_mode = st.sidebar.radio("Select View Mode", ["Global Overview", "Detailed Audit Review"])

# Fetch the data
df_master = fetch_data() 
# Safely handle empty DataFrames
if not df_master.empty:
    completed_audits = df_master.dropna(subset=['empathy_score'])
else:
    completed_audits = pd.DataFrame()

# ---------------------------------------------------------
# MODE 1: GLOBAL OVERVIEW
# ---------------------------------------------------------

st.sidebar.divider()
st.sidebar.subheader("🚀 Roadmap & Known Limits")
st.sidebar.markdown("""
* **Data Management:** Manual deletion of transcripts and audit history is currently disabled to maintain data integrity.
* **Batch Processing:** The system processes one file at a time; bulk upload queueing is under development.
* **Human-in-the-Loop:** "Manager Override" buttons are currently simulated (Webhook integration pending production URL).
* **Real-time Monitoring:** The 'Automator' watcher is optimized for local environments; Cloud-based S3 bucket watching is the next milestone.
* **User Auth:** Single-user access only; Multi-tenant Role-Based Access Control (RBAC) is not yet implemented.
""")

if view_mode == "Global Overview":
    st.title("📊 Global Performance Overview")
    
    if not completed_audits.empty:
        # KPI Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Empathy", f"{completed_audits['empathy_score'].mean():.1f}")
        m2.metric("Avg Compliance Rate", f"{completed_audits['compliance_score'].mean():.1f}%")
        m3.metric("Total Audits", len(completed_audits))

        st.header("📋 Operational Audit Log")
    
        # Add Filters above the table
        f1, f2 = st.columns(2)
        with f1:
            status_filter = st.multiselect("Filter by Status", df_master['status'].unique(), default=df_master['status'].unique())
        with f2:
            score_threshold = st.slider("Compliance Threshold (Below)", 0, 100, 100)

        # Apply Filters
        filtered_df = df_master[
            (df_master['status'].isin(status_filter)) & 
            (df_master['compliance_score'].fillna(0) <= score_threshold)
        ]

        # Use Data Editor for a professional look
        st.data_editor(
            style_dataframe(filtered_df),
            column_config={
                "compliance_score": st.column_config.ProgressColumn(
                    "Compliance", help="Compliance Score out of 100", min_value=0, max_value=100, format="%d"
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status", options=["pending", "completed", "failed"], required=True
                ),
            },
            disabled=True,
            use_container_width=True,
            hide_index=True
        )
        
        # --- GLOBAL DOWNLOAD ---
        st.divider()
        csv = df_master.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Global CSV", csv, "audit_summary.csv", "text/csv")
        
    else:
        st.info("No audit data found. Please run the scoring engine.")

# ---------------------------------------------------------
# MODE 2: DETAILED AUDIT REVIEW
# ---------------------------------------------------------
else:
    st.title("🔍 Individual Call Inspection")

    if not df_master.empty:
        col_select, col_dl = st.columns([3, 1])
        with col_select:
            selected_file = st.selectbox("Select Audio File", df_master['filename'].unique())
        
        call_data = df_master[df_master['filename'] == selected_file].iloc[0]

        with col_dl:
            if pd.notnull(call_data['empathy_score']):
                pdf_bytes = create_pdf_report(call_data)
                st.download_button(
                    label="📥 Download Report",
                    data=pdf_bytes,
                    file_name=f"Report_{selected_file}.pdf",
                    mime="application/pdf"
                )
            else:
                st.button("📥 Download Report", disabled=True, help="Audit pending")

        if pd.notnull(call_data['empathy_score']):
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Empathy", f"{call_data['empathy_score']}/100")
            c2.metric("Compliance", f"{call_data['compliance_score']}/100")
            c3.metric("Professionalism", f"{call_data['professionalism_score']}/100")

            # Chart
            chart_data = pd.DataFrame({
                'Metric': ['Empathy', 'Compliance', 'Professionalism'],
                'Score': [call_data['empathy_score'], call_data['compliance_score'], call_data['professionalism_score']]
            }).fillna(0)
            
            fig_individual = px.bar(chart_data, x='Metric', y='Score', color='Metric', range_y=[0, 100])
            st.plotly_chart(fig_individual, use_container_width=True)

            # Transcripts
            st.subheader("📄 Transcription Analysis")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**Original**")
                st.text_area("Full Text", call_data['transcript_text'], height=250, disabled=True)
            with t_col2:
                st.markdown("**Scrubbed / Masked**")
                st.text_area("PII Redacted", call_data.get('redacted_text', 'Not Redacted'), height=250, disabled=True)

            # Jury
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
    st.cache_data.clear() # Clear cache to fetch fresh Postgres data
    st.rerun()