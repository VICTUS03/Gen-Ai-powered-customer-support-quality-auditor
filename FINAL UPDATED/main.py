import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import plotly.express as px
from fpdf import FPDF
import os
from db import get_pg_conn
from transcribe import transcribe_single_file,get_model
from pathlib import Path
from automator import NewCallHandler,shared_watch_logs
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



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

# def get_db_engine():
#     # Format: postgresql://user:password@host:port/database
#     user =  os.getenv("DB_USER")
#     password = os.getenv("DB_PASSWORD")
#     host = os.getenv("DB_HOST")
#     port =  os.getenv("DB_PORT")
#     db =  os.getenv("DB_NAME")

#     return create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

st.set_page_config(page_title="QA Auditor Dashboard", layout="wide")

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=60)
def fetch_data():
    engine = get_pg_conn()
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
view_mode = st.sidebar.radio("Select View Mode", ["Global Overview", "Process Files/Folder", "Detailed Audit Review"])

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
st.sidebar.warning(" Roadmap & Known Limits")
st.sidebar.markdown("""
* **Data Management:** Manual deletion of transcripts and audit history is currently disabled to maintain data integrity.
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
# MODE 2: PROCESS FOLDER
# ---------------------------------------------------------


elif view_mode == "Process Files/Folder":
    st.title("🎙️ Whisper Real-time Automator")

    # 1. Directory Selection
    watch_dir = st.text_input("Enter Directory to Watch:", r"C:\Users\pratik p kakade\recordings")

    # 2. Initialize Session State for the Observer
    if "observer" not in st.session_state:
        st.session_state.observer = None
        st.session_state.is_watching = False

    # 3. Toggle Button
    col1, col2 = st.columns(2)

    if col1.button("🚀 Start Watching"):
        if not os.path.exists(watch_dir):
            st.error("Directory does not exist!")
        # Check if we already have an observer running
        elif st.session_state.observer is None: 
            event_handler = NewCallHandler()
            st.session_state.observer = Observer()
            st.session_state.observer.schedule(event_handler, watch_dir, recursive=False)
            st.session_state.observer.start()
            st.session_state.is_watching = True
            st.success(f"Started monitoring: {watch_dir}")
        else:
            st.warning("Watcher is already running!")

    if col2.button("🛑 Stop Watching"):
        if st.session_state.is_watching:
            st.session_state.observer.stop()
            st.session_state.observer.join()
            st.session_state.is_watching = False
            st.session_state.observer = None
            st.info("Watcher stopped.")
        else:
            st.write("Watcher is not active.")

    # 4. UI Status Indicator
    if st.session_state.is_watching:
        st.markdown("---")
        st.status(f"Currently watching for new files in `{watch_dir}`...", state="running")

    st.warning("⚠️ *Note: Real-time file logging is currently in development. Transcriptions are running in the background—check your terminal for live updates!")

    st.markdown("LIVE ACTIVITY: ")

    st.header("🎙️ Bulk Folder Transcription")
    st.markdown("Select a folder containing audio files to process new recordings.")

    if shared_watch_logs:
        if st.button("🗑️ Clear Activity Log"):
            shared_watch_logs.clear()
            st.rerun()

    folder_path = st.text_input(
        "Enter the full directory path:", 
        placeholder="e.g., C:/Users/Audio/Project_Alpha"
    )


    col1, col2 = st.columns([1, 4])
    with col1:
        start_btn = st.button("Start Batch", type="primary")

    if start_btn:
        if not folder_path:
            st.warning("Please provide a folder path.")
        elif not os.path.isdir(folder_path):
            st.error("❌ The directory was not found.")
        else:

            with st.status("Auditing Folder...", expanded=True) as status:
                # 1. Get Local Files
                recordings_dir = Path(folder_path)
                audio_extensions = ["*.wav", "*.mp3", "*.m4a", "*.flac"]
                local_files = []
                for ext in audio_extensions:
                    local_files.extend(list(recordings_dir.glob(ext)))

                if not local_files:
                    status.update(label="No files found", state="error")
                    st.warning("No supported audio files found.")
                else:
                    # 2. Check Database for existing files
                    st.write("🔍 Checking database for duplicates...")
                    try:
                        conn = get_pg_conn()
                        cursor = conn.cursor()
                        cursor.execute("SELECT filename FROM transcripts")
                        # Create a set of filenames for O(1) lookups
                        existing_files = {row[0] for row in cursor.fetchall()}
                        cursor.close()
                        conn.close()

                        # 3. Filter only NEW files
                        files_to_process = [f for f in local_files if f.name not in existing_files]
                        skipped_files = [f for f in local_files if f.name in existing_files]
                        skipped_count = len(local_files) - len(files_to_process)

                        if skipped_files:
                            st.info(f"⏭️ Skipping {len(skipped_files)} files already in database:")
                            for i, f in enumerate(skipped_files):
                                st.write(f"{i+1}: {f.name}")

                        if not files_to_process:
                            status.update(label="All files up to date!", state="complete")

                            st.success("Everything in this folder has already been transcribed.")
                        else:
                            st.write(f"🚀 Processing {len(files_to_process)} new files...")
                            
                            # 4. Process only the new ones
                            for file_path in files_to_process:
                                st.write(f"Transcribing: `{file_path.name}`")
                                # Using your existing single file function
                                transcribe_single_file(str(file_path)) 
                            
                            status.update(label="Transcription Complete!", state="complete", expanded=False)
                            st.success(f"Successfully processed {len(files_to_process)} new files.")
                            st.balloons()

                    except Exception as e:
                        status.update(label="Database Error", state="error")
                        st.error(f"Error connecting to database: {e}")



# ---------------------------------------------------------
# MODE 3: DETAILED AUDIT REVIEW
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

            st.warning(" **Security Update:** We are currently refining our PII masking algorithms to improve redaction accuracy for names, addresses, and financial data.")

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