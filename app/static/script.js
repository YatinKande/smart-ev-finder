const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const locationBtn = document.getElementById('location-btn');
const stationList = document.getElementById('station-list');

// State to store user location if shared
let userCoordinates = null;

// Initialize User Profile from LocalStorage
let userProfile = JSON.parse(localStorage.getItem('ev_user_profile')) || {
    name: null,
    preferences: {}
};

async function sendMessage(textOverride = null) {
    const text = textOverride || userInput.value.trim();
    if (!text) return;

    // Add user message
    addMessage(text, 'user');
    if (!textOverride) userInput.value = '';

    // Show loading
    const loadingId = addMessage('Finding chargers...', 'bot');

    try {
        const payload = {
            message: text,
            user_profile: userProfile
        };
        // Attach coordinates if we have them
        if (userCoordinates) {
            payload.user_latitude = userCoordinates.latitude;
            payload.user_longitude = userCoordinates.longitude;
        }

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // Update user profile if backend suggests changes
        if (data.new_user_profile_data) {
            updateUserProfile(data.new_user_profile_data);
        }

        // Update bot message with LLM response
        updateMessage(loadingId, data.llm_response);

        // Update sidebar with stations
        updateStationList(data.stations);

    } catch (error) {
        updateMessage(loadingId, "Sorry, connection error. Please try again.");
        console.error(error);
    }
}

function updateUserProfile(newData) {
    let changed = false;
    if (newData.name && newData.name !== userProfile.name) {
        userProfile.name = newData.name;
        changed = true;
    }
    if (newData.preferences) {
        userProfile.preferences = { ...userProfile.preferences, ...newData.preferences };
        changed = true;
    }

    if (changed) {
        localStorage.setItem('ev_user_profile', JSON.stringify(userProfile));
        console.log("User Profile Updated:", userProfile);
    }
}

// Geolocation Handler
if (locationBtn) {
    locationBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            locationBtn.style.opacity = '0.5';
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    userCoordinates = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    locationBtn.style.opacity = '1';
                    locationBtn.innerHTML = '✅';
                    setTimeout(() => locationBtn.innerHTML = '📍', 3000);

                    const name = userProfile.name ? `, ${userProfile.name}` : '';
                    addMessage(`📍 Location found${name}! What sort of charger are you looking for today?`, 'bot');
                    userInput.focus();
                },
                (error) => {
                    locationBtn.style.opacity = '1';
                    addMessage("Unable to retrieve your location. Check browser permissions.", 'bot');
                }
            );
        } else {
            addMessage("Geolocation is not supported by this browser.", 'bot');
        }
    });
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;
    div.innerHTML = text.replace(/\n/g, '<br>');
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    div.id = 'msg-' + Date.now();
    return div.id;
}

function updateMessage(id, newText) {
    const el = document.getElementById(id);
    if (el) {
        el.innerHTML = newText.replace(/\n/g, '<br>');
    }
}

function updateStationList(stations) {
    stationList.innerHTML = '';

    if (stations && stations.length > 0) {
        stations.forEach(station => {
            const isOperational = station.status && station.status.toLowerCase().includes('operational');
            const statusClass = isOperational ? 'status-operational' : 'status-unknown';

            // Trust Logic
            let trustBadge = '';
            const conf = station.confidence_score || 0.5;
            const lastVer = station.last_verified || 'Unknown';

            if (conf >= 0.8) {
                trustBadge = `<span class="badge-verified" title="Verified recently: ${lastVer}">✓ Verified</span>`;
            } else if (conf <= 0.2) {
                trustBadge = `<span class="badge-stale" title="Data may be old: ${lastVer}">⚠ Stale Data</span>`;
            }

            const card = document.createElement('div');
            card.className = 'station-card';
            card.innerHTML = `
                <div class="station-name">${station.station_name}</div>
                <div class="station-details">
                    <div>📍 ${station.address || 'Address n/a'}</div>
                    <div>
                        📏 ${station.distance_miles ? station.distance_miles.toFixed(1) + ' mi' : '--'} • 
                        ⚡ ${station.power_kw ? station.power_kw + 'kW' : 'Unknown Power'}
                    </div>
                    <div>🔌 ${station.connection_type || 'Unknown Connector'}</div>
                    <div class="data-provider">Source: ${station.data_provider || 'Open Charge Map'}</div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
                    <div>
                        <span class="status-badge ${statusClass}">${station.status}</span>
                        ${trustBadge}
                    </div>
                    ${station.maps_link ? `<a href="${station.maps_link}" target="_blank" style="color: var(--primary); text-decoration: none; font-size: 0.9rem; font-weight: 500;">Navigate ➔</a>` : ''}
                </div>
            `;
            stationList.appendChild(card);
        });
    } else {
        stationList.innerHTML = '<div style="text-align:center; color: var(--text-muted); margin-top: 2rem;">No stations found matching criteria.</div>';
    }
}

sendBtn.addEventListener('click', () => sendMessage());
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
