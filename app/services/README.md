# 🧠 Application Services

This directory contains the business logic engines that power the application.

## Services

### 1. `ev_api_service.py` (The Navigator)
*   **Role**: Interfaces with the Open Charge Map API.
*   **Key Feature**: **Trust Scoring**. It doesn't just blindly pass data. It inspects the `DateLastStatusUpdate` field. If a station hasn't been verified in >6 months, it downgrades the `confidence_score`, which results in a warning badge on the UI.
*   **Normalization**: Converts cryptic status codes (e.g., "StatusID: 50") into human-readable strings ("Operational").

### 2. `llm_service.py` (The Brain)
*   **Role**: Manages interactions with the Groq API (Llama 3).
*   **Zero-Shot Extraction**: Uses a carefully crafted system prompt to extract structured JSON (lat/lon/filters) from unstructured user queries without needing fine-tuning.
*   **Personalization**: Dynamically injects the user's profile (name, preferences) into the prompt context, allowing the AI to give tailored advice.
