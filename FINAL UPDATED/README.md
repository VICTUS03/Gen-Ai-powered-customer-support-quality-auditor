# 🛡️ GenAI Quality Auditor: Multi-Agent Compliance Engine

A high-performance, automated quality assurance (QA) pipeline that uses Generative AI to audit customer-agent call transcripts. This system replaces manual auditing with a **Multi-Agent "Audit Jury"** that evaluates empathy, professionalism, and legal compliance in real-time.

---

## 🚀 Project Overview
The **GenAI Quality Auditor** monitors a local recording directory, transcribes audio instantly using Whisper, scrubs sensitive PII (Credit Cards/SSNs) using a math-validated redaction layer, and performs a deep audit using RAG (Retrieval-Augmented Generation) against company policies.

### **Core Innovation: The "Audit Jury"**
Instead of a single AI score, the system employs three specialized AI personas:
1.  **Compliance Officer:** Focuses on legal disclosures and security.
2.  **Empathy Advocate:** Focuses on emotional intelligence and customer satisfaction.
3.  **Presiding Judge:** Consolidates findings into a final score and actionable coaching tips.

---

## 🛠️ Technical Stack & Tools

| Layer | Technology / Tool | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | **Streamlit** | Interactive Supervisor Dashboard & PDF Reporting |
| **Transcription** | **OpenAI Whisper (Medium)** | Local SOTA Speech-to-Text conversion |
| **LLM Inference** | **Groq (Llama-3.3-70b)** | Ultra-fast reasoning for the Multi-Agent Jury |
| **Vector DB** | **Pinecone** | RAG storage for company policy documents |
| **Database** | **MySQL** | Persistent storage for transcripts and audit results |
| **Automation** | **Python Watchdog** | Event-driven folder monitoring for 24/7 automation |
| **Security** | **Regex + Luhn Algorithm** | Smart PII Redaction (PCI-DSS compliant masking) |
| **Analytics** | **Plotly** | Dynamic performance visualization |
| **Reporting** | **FPDF** | Automated generation of PDF Coaching Reports |
| **Operations** | **Slack Webhooks** | Real-time "Human-in-the-Loop" compliance alerts |

---

## ⚙️ System Architecture

1.  **Data Ingestion:** `automator.py` watches a folder. When a `.wav` or `.mp3` is dropped, it triggers the pipeline.
2.  **Transcription:** `transcribe.py` uses Whisper to convert audio to text and saves it to **MySQL** as `pending`.
3.  **Redaction:** `redactor.py` identifies Credit Cards (using Luhn's algorithm), Emails, and SSNs, replacing them with safety tags.
4.  **Audit (RAG):** `scoring_engine.py` retrieves relevant policy context from **Pinecone** and sends the masked text to the **Groq Jury**.
5.  **Action:** High-risk violations (<40% score) trigger a **Slack Alert** with an "Override" button for managers.
6.  **Review:** Supervisors use the **Streamlit Dashboard** to view trends, compare original vs. redacted text, and download PDF reports.

---

## 📂 Minute Technical Details

### **1. Smart PII Masking**
Unlike standard masking, this project uses a **Luhn Algorithm validator**. It won't redact random 16-digit product IDs; it only masks strings that pass the mathematical check for a real credit card.

### **2. Retrieval-Augmented Generation (RAG)**
Company policies are embedded using `sentence-transformers/all-MiniLM-L6-v2` and stored in Pinecone. This ensures the AI audits based on **your** specific rules, not just general knowledge.

### **3. Human-in-the-Loop (HITL)**
The system includes a Webhook listener. If a manager disagrees with the AI, they can click "Override" in Slack, which updates the MySQL database and reflects the human score in the dashboard.

---

## 🚦 Getting Started

1.  **Set Environment Variables:**
    * `GROQ_API_KEY`
    * `PINECONE_API_KEY`
2.  **Start the Automation Engine:**
    ```bash
    python automator.py
    ```
3.  **Start the Scoring Worker:**
    ```bash
    python scoring_engine.py
    ```
4.  **Launch the Dashboard:**
    ```bash
    streamlit run main.py
    ```

---

## 📈 Future Roadmap
- [ ] **Batch Export:** One-click ZIP generation for monthly audits.
- [ ] **Agent Sandbox:** A separate UI for agents to view their own "Coaching Tips" without seeing others' data.
- [ ] **Sentiment Vibe-Check:** Comparing agent tone vs. customer frustration levels.
