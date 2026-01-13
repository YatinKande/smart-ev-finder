# 📂 Application Core

This directory contains the source code for the EV Status Bot. It is structured as a standard modular FastAPI application.

## Structure

*   **`main.py`**: The entry point of the application. It initializes the `FastAPI` app, configures dependency injection for services, defines the API endpoints (routes), and mounts the static frontend files.
*   **`models/`**: Contains Pydantic data schemas. These ensure that data flowing between the frontend, backend, and external APIs is strictly typed and validated.
*   **`services/`**: The "brain" of the application. It houses the business logic for talking to the LLM (Groq) and the External Data Provider (Open Charge Map).
*   **`static/`**: Holds the raw frontend assets (HTML, CSS, JS) that are served directly to the browser.

## Key Design Patterns

*   **Dependency Injection**: Services are instantiated in `main.py` and reused, allowing for efficient resource management.
*   **Separation of Concerns**: Routes (in `main.py`) handled HTTP logic, while Services handle business logic.
