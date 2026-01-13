# 🎨 Frontend (Static Assets)

This directory contains the client-side code that runs in the user's browser. It is built with vanilla technologies for maximum performance and zero build-step complexity.

## Files

### `index.html`
The semantic skeleton of the application. It features a responsive grid layout that adapts between mobile and desktop views.

### `style.css`
Implements the **"Cyber-Glass"** aesthetic.
*   **Glassmorphism**: Uses `backdrop-filter: blur()` and semi-transparent backgrounds to create depth.
*   **Animations**: Messages slide in (`fadeInUp`) for a smooth chat experience.
*   **Responsive Variables**: Uses CSS variables (`--primary`, `--bg-dark`) for effortless theming.

### `script.js`
The engine of the frontend.
*   **Geolocation API**: Hooks into `navigator.geolocation` to get high-accuracy GPS coordinates (with user permission).
*   **State Management**: Uses `localStorage` to persist the simpler `userProfile` (name and preferences), enabling the "Memory" feature of the bot.
*   **DOM Manipulation**: Dynamically constructs station cards and injects trust badges based on data quality.
