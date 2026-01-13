# 📦 Data Models

This directory defines the **Pydantic** schemas used for data validation and serialization.

## Key Models

### `schemas.py`

*   **`ChatRequest`**: Defines the structure of messages coming from the user. It uniquely includes fields for `user_latitude`, `user_longitude`, and `user_profile` to support the geospatial and personalization features.
*   **`ChargerResponse`**: A standardized format for a single charging station. It normalizes distinct data points (like status ID or usage cost) into a consistent Python object that the frontend can easily render. It now includes "Trust Fields" like `last_verified` and `confidence_score`.
*   **`BotResponse`**: The final payload sent back to the frontend, combining the LLM's natural language insight (`llm_response`) with the structured list of stations (`stations`).
