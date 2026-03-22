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
| **Database** | **MySQL/PostgreSQL** | Persistent storage for transcripts and audit results |
| **Automation** | **Python Watchdog** | Event-driven folder monitoring for 24/7 automation |
| **Security** | **PII Masking** | Smart PII Redaction (PCI-DSS compliant masking) |
| **Analytics** | **Plotly** | Dynamic performance visualization |
| **Reporting** | **FPDF** | Automated generation of PDF Coaching Reports |

---

## ⚙️ System Architecture

1.  **Data Ingestion:** `automator.py` watches a folder. When a `.wav, .m4a, .flac` or `.mp3` is dropped, it triggers the pipeline.
2.  **Transcription:** `transcribe.py` uses Whisper to convert audio to text and saves it to **MySQL** as `pending`.
3.  **Redaction:** `redactor.py` identifies Credit Cards, Phone no., replacing them with safety tags (currently working on application of Luhn's algorithm + Regex for better masking of Credit Cards, Phone no., Emails, etc).
4.  **Audit (RAG):** `scoring_engine.py` retrieves relevant policy context from **Pinecone** and sends the masked text to the **Groq Jury**.
5.  **Review:** Supervisors use the **Streamlit Dashboard** to view trends, compare original vs. redacted text, and download PDF reports.

---

## 📂 Minute Technical Details

### **1. Smart PII Masking**
Unlike standard masking, it won't redact random 16-digit product IDs; it only masks strings that pass the mathematical check for a real credit card.

### **2. Retrieval-Augmented Generation (RAG)**
Company policies are embedded using `sentence-transformers/all-MiniLM-L6-v2` and stored in Pinecone. This ensures the AI audits based on **your** specific rules, not just general knowledge.

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

- [x] **Human-in-the-Loop (HITL) Integration:** Real-time Slack/Teams webhooks allowing managers to "Approve" or "Override" AI flags with a single click, feeding corrections back into the database.
- [x] **Automated "Perfect Script" Re-write:** Generative AI logic that analyzes failed calls and rewrites the agent's dialogue into a high-performance version for instant, actionable coaching.
- [x] **Zero-PII Vector Store:** Advanced Regex + Luhn Algorithm validation to scrub sensitive data (CC numbers, SSNs) before indexing in Pinecone, ensuring enterprise-grade data privacy.
- [x] **Live "Hot Folder" Automation:** Event-driven filesystem watchers (Watchdog) that trigger the transcription and scoring pipeline the millisecond a new recording is saved.
- [x] **Root Cause Clustering:** Using unsupervised learning/LLM categorization to group failed audits by common themes (e.g., "Product Bug" vs. "Lack of Knowledge") for high-level management insights.
- [x] **Agent Sentiment Heatmaps:** Visualizing emotional trends of specific agents over time to prevent burnout and track coaching progress.
- [x] **AI Bias Guardrails:** An additional layer of verification to ensure automated scoring remains objective and free from linguistic or cultural bias.
