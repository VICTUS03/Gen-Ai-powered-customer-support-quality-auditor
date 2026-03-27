# 🚧 Project Limitations & Technical Constraints

This document outlines the current boundaries of the system. These constraints are either intentional for data safety or represent pending features in the development roadmap.

---

### 1. Data & Security 🔐
* **Data Integrity Protection:** Manual deletion of transcripts and audit history is currently disabled. This ensures a permanent audit trail during the initial beta phase.
* **User Authentication:** The system currently supports **Single-user access only**. Multi-tenant Role-Based Access Control (RBAC) is scheduled for a future security patch.
* **Session Management:** State persistence is limited to the current browser session; refreshing the application may reset unsaved filtered views.

### 2. Integration & Automation ⚙️
* **Human-in-the-Loop (HITL):** "Manager Override" buttons are currently **simulated**. Webhook integrations are built but pending a verified Production URL for live execution.
* **Real-time Monitoring:** The 'Automator' watcher is optimized for **local environments**. Migrating to cloud-based S3 bucket event-driven triggers (AWS Lambda/SNS) is the next major infrastructure milestone.
* **API Rate Limiting:** External scoring calls are currently synchronous; high-volume batch processing may experience latency without an asynchronous task queue (e.g., Celery/Redis).

### 3. UI/UX & Optimization 🎨
* **UI Fluidity:** The current interface is functional but lacks advanced **Micro-interactions**. Transition animations and Skeleton Loaders are not yet implemented, which may result in a "stutter" during heavy data fetches.
* **Mobile Responsiveness:** The dashboard is optimized for Desktop (1920x1080). Mobile and tablet layouts are currently in a "best-effort" state and may require horizontal scrolling.
* **Data Visualization:** Large dataset rendering (1,000+ rows) is not yet virtualized. Users may experience UI lag when scrolling through extremely large transcript histories.
* **Search & Discovery:** Current filtering relies on exact string matching. **Fuzzy Search** and advanced NLP-based querying are currently missing.

---

