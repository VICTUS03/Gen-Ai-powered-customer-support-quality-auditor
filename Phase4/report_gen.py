from fpdf import FPDF
import mysql.connector

def generate_audit_pdf(audit_id):
    # 1. Fetch data from MySQL
    conn = mysql.connector.connect(host="localhost", user="root", password="MYSQL", database="quality_auditor")
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT t.filename, a.* FROM audit_results a 
        JOIN transcripts t ON a.transcript_id = t.id WHERE a.id = %s
    """
    cursor.execute(query, (audit_id,))
    data = cursor.fetchone()

    # 2. Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "OFFICIAL QUALITY AUDIT REPORT", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"File Name: {data['filename']}", ln=True)
    pdf.cell(200, 10, f"Audit Date: {data['audited_at']}", ln=True)
    
    # 3. Add Scores
    pdf.set_text_color(255, 0, 0) if data['compliance_score'] < 50 else pdf.set_text_color(0, 128, 0)
    pdf.cell(200, 10, f"Compliance Score: {data['compliance_score']}/100", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, f"Empathy Score: {data['empathy_score']}/100", ln=True)
    
    # 4. Suggestions
    pdf.multi_cell(0, 10, f"Coaching Suggestions: {data['suggestions']}")
    
    pdf.output(f"Audit_Report_{audit_id}.pdf")
    print(f"PDF Generated: Audit_Report_{audit_id}.pdf")

if __name__ == "__main__":
    generate_audit_pdf(1) # Test with your first ID