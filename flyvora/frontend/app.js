const API_BASE = 'http://127.0.0.1:8000/api';

// ── State ─────────────────────────────────────────────────────
let flights = [];
let prevFlights = [];
let hotels = [];
let currentSearching = false;
let authToken = localStorage.getItem('authToken') || null;
let userLocation = null;
let map = null;
let marker = null;
let platformStats = null;

// Major Nigerian Airports for locator
const AIRPORTS = [
    { name: 'Murtala Muhammed', code: 'LOS', city: 'Lagos', town: 'Ikeja', lat: 6.5774, lon: 3.3210 },
    { name: 'Nnamdi Azikiwe', code: 'ABV', city: 'Abuja', town: 'Apo', lat: 9.0068, lon: 7.2631 },
    { name: 'Port Harcourt', code: 'PHC', city: 'Port Harcourt', town: 'Omagwa', lat: 5.0150, lon: 6.9490 },
    { name: 'Mallam Aminu', code: 'KAN', city: 'Kano', town: 'Kano City', lat: 12.0475, lon: 8.5246 },
    { name: 'Akanu Ibiam', code: 'ENU', city: 'Enugu', town: 'Emene', lat: 6.4743, lon: 7.5619 }
];

// ── DOM Elements ──────────────────────────────────────────────
const searchBtn = document.getElementById('search-btn');
const resultsGrid = document.getElementById('results-grid');
const resultsTitle = document.getElementById('results-title');
const noFlights = document.getElementById('no-flights');
const liveIndicator = document.getElementById('live-indicator');
const locationStatus = document.getElementById('location-status');
const logo = document.getElementById('logo');

// Modals
const bookingModal = document.getElementById('booking-modal');
const bookingForm = document.getElementById('booking-form');
const closeModal = document.getElementById('close-modal');
const loginNavBtn = document.getElementById('login-nav-btn');
const loginModal = document.getElementById('login-modal');
const loginForm = document.getElementById('login-form');
const closeLogin = document.getElementById('close-login');
const registerModal = document.getElementById('register-modal');
const registerForm = document.getElementById('register-form');
const closeRegister = document.getElementById('close-register');

// Chat
const chatToggle = document.getElementById('chat-toggle');
const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendChat = document.getElementById('send-chat');
const chatMessages = document.getElementById('chat-messages');
const typingIndicator = document.getElementById('typing-indicator');

// ── Initialization ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('map-container')) {
        initMap();
        detectLocation();
    }
    if (document.getElementById('results-grid')) {
        if (window.location.pathname.includes('hotels.html')) {
            fetchHotels();
        } else {
            fetchFlights();
        }
    }
    setupAuth();
    fetchStats();
    
    // Live Polling
    setInterval(() => {
        if (!currentSearching && document.getElementById('results-grid')) {
            if (window.location.pathname.includes('hotels.html')) fetchHotels();
            else pollFlights();
        }
    }, 10000);

    // AI suggestion after 5 seconds
    setTimeout(aiInitiate, 5000);
});

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats/`);
        const data = await res.json();
        platformStats = data;
    } catch (e) { console.warn('Stats fetch offline'); }
}

// ── Geolocation & Leaflet Map ─────────────────────────────────

function initMap() {
    // Start map at center of Nigeria
    map = L.map('map-container').setView([9.0820, 8.6753], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
}

async function detectLocation() {
    locationStatus.textContent = 'Locating...';
    
    try {
        // Try IP Geolocation (Most compatible)
        const res = await fetch('http://ip-api.com/json');
        const data = await res.json();
        
        if (data && data.lat) {
            console.log('Detected via IP:', data.city);
            locationStatus.textContent = `Located: ${data.city}`;
            userLocation = { lat: data.lat, lon: data.lon };
            updateMapToLocation(data.lat, data.lon, data.city);
            findNearestAirport(data.lat, data.lon);
            return;
        }
    } catch (e) { console.warn('IP Geo failed, trying Browser GPS'); }

    // Fallback to Browser GPS
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                userLocation = { lat: latitude, lon: longitude };
                updateMapToLocation(latitude, longitude, 'Your Location');
                findNearestAirport(latitude, longitude);
            },
            () => { 
                locationStatus.textContent = 'Default: Lagos';
                findNearestAirport(6.5774, 3.3210); 
            }
        );
    } else {
        locationStatus.textContent = 'Default: Lagos';
        findNearestAirport(6.5774, 3.3210);
    }
}

function updateMapToLocation(lat, lon, label) {
    if (!map) return;
    map.setView([lat, lon], 12);
    if (marker) map.removeLayer(marker);
    marker = L.marker([lat, lon]).addTo(map).bindPopup(label).openPopup();
}

function findNearestAirport(lat, lon) {
    let nearest = null;
    let minDistance = Infinity;

    AIRPORTS.forEach(ap => {
        const d = calculateDistance(lat, lon, ap.lat, ap.lon);
        if (d < minDistance) { minDistance = d; nearest = ap; }
    });

    if (nearest) {
        document.getElementById('departure-input').value = nearest.name;
        if (map) {
            L.circle([nearest.lat, nearest.lon], { radius: 2000, color: '#3b82f6' }).addTo(map)
             .bindPopup(`Nearest Airport: ${nearest.name}`).openPopup();
        }
    }
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// ── Flights Logic ─────────────────────────────────────────────

async function pollFlights() {
    try {
        const res = await fetch(`${API_BASE}/flights/`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (res.ok) {
            prevFlights = [...flights];
            flights = data.flights;
            if (resultsGrid.children.length > 0) renderFlights();
        }
    } catch (e) { console.warn('Polling offline'); }
}

async function fetchFlights() {
    try {
        const res = await fetch(`${API_BASE}/flights/`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (res.ok) {
            flights = data.flights;
            renderFlights();
        }
    } catch (e) { console.warn('Fetch failed'); }
}

async function searchFlights() {
    const dpt = document.getElementById('departure-input').value.trim();
    const dst = document.getElementById('destination-input').value.trim();
    const dat = document.getElementById('date-input').value.trim();

    if (!dpt && !dst && !dat) { 
        showToast('Showing all available flights.');
        fetchFlights(); 
        return; 
    }

    currentSearching = true;
    searchBtn.disabled = true;
    searchBtn.innerText = 'Searching...';

    try {
        const payload = {};
        if (dpt) payload.departure = dpt;
        if (dst) payload.destination = dst;
        if (dat) payload.date = dat;

        const res = await fetch(`${API_BASE}/flights/search/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            if (data.flights.length === 0) {
                showToast('No exact flights found for your dates. Showing all available flights & airports.', 'error');
                fetchFlights();
            } else {
                flights = data.flights;
                renderFlights();
                liveIndicator.style.display = 'flex';
            }
        }
    } catch (e) { console.error(e); }
    finally {
        currentSearching = false;
        searchBtn.disabled = false;
        searchBtn.innerText = 'Search Flights';
    }
}

function renderFlights() {
    resultsGrid.innerHTML = '';
    if (flights.length === 0) {
        resultsTitle.style.display = 'none';
        noFlights.style.display = 'block';
        liveIndicator.style.display = 'none';
        return;
    }

    resultsTitle.style.display = 'block';
    noFlights.style.display = 'none';

    flights.forEach((f, i) => {
        const card = document.createElement('div');
        card.className = 'flight-card animate-fade';
        card.style.animationDelay = `${i * 0.1}s`;
        
        const timeStr = new Date(f.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const updateTime = new Date(f.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        let priceTag = '';
        if (f.previous_price && parseFloat(f.price) !== parseFloat(f.previous_price)) {
            const isDown = parseFloat(f.price) < parseFloat(f.previous_price);
            priceTag = `<div class="price-update-tag ${isDown ? 'price-down' : 'price-up'}">${isDown ? '↓' : '↑'} Price Update</div>`;
        }

        const dptInfo = AIRPORTS.find(a => f.departure.toLowerCase().includes(a.city.toLowerCase())) || { city: f.departure, town: 'Terminal' };
        const dstInfo = AIRPORTS.find(a => f.destination.toLowerCase().includes(a.city.toLowerCase())) || { city: f.destination, town: 'Terminal' };

        card.innerHTML = `
            ${priceTag}
            <div class="card-header"><span class="airline-name">${f.airline}</span><span class="price-tag">₦${parseFloat(f.price).toLocaleString()}</span></div>
            <div class="route-info">
                <div class="city-display">
                    <div class="city-code">${f.departure.slice(0,3).toUpperCase()}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${dptInfo.city}, ${dptInfo.town}</div>
                </div>
                <div class="route-line"></div>
                <div class="city-display">
                    <div class="city-code">${f.destination.slice(0,3).toUpperCase()}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: right;">${dstInfo.city}, ${dstInfo.town}</div>
                </div>
            </div>
            <div class="flight-footer"><div class="time-info"><div>Dep: ${timeStr}</div><span class="update-time">Verified: ${updateTime}</span></div><button class="btn-primary" onclick="openBooking(${f.id})">Book</button></div>
        `;
        resultsGrid.appendChild(card);
    });
}

// ── Hotels Logic ──────────────────────────────────────────────

async function fetchHotels() {
    try {
        // Send map coordinates if available to simulate Amadeus nearest search
        let url = `${API_BASE}/hotels/nearest/`;
        if (userLocation) {
            url += `?lat=${userLocation.lat}&lon=${userLocation.lon}`;
        }
        const res = await fetch(url, { headers: getAuthHeaders() });
        const data = await res.json();
        if (res.ok) {
            hotels = data.hotels;
            renderHotels();
        }
    } catch (e) { console.warn('Hotel fetch failed'); }
}

function renderHotels() {
    const grid = document.getElementById('results-grid');
    if (!grid) return;
    grid.innerHTML = '';
    
    if (hotels.length === 0) {
        noFlights.style.display = 'block';
        return;
    }

    noFlights.style.display = 'none';
    hotels.forEach((h, i) => {
        const card = document.createElement('div');
        card.className = 'hotel-card animate-fade';
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <img src="${h.image_url}" alt="${h.name}" class="hotel-img">
            <div class="hotel-content">
                <div class="hotel-header">
                    <span class="hotel-name">${h.name}</span>
                    <span class="hotel-price">₦${parseFloat(h.price_per_night).toLocaleString()}/night</span>
                </div>
                <div class="hotel-location">
                    <i class="fas fa-location-dot"></i> ${h.location}
                </div>
                <div class="hotel-airport-info">
                    <i class="fas fa-plane"></i> ${h.distance_from_airport}
                </div>
                <button class="btn-primary" onclick="window.openHotelBooking(${h.id})">Book Room</button>
            </div>
        `;
        grid.appendChild(card);
    });
}


// ── Auth Logic ──────────────────────────────────────────────

function setupAuth() {
    updateAuthUI();
    loginNavBtn.onclick = () => authToken ? logout() : loginModal.classList.add('active');
    document.getElementById('close-login').onclick = () => loginModal.classList.remove('active');
    document.getElementById('show-register').onclick = (e) => { e.preventDefault(); loginModal.classList.remove('active'); registerModal.classList.add('active'); };
    document.getElementById('close-register').onclick = () => registerModal.classList.remove('active');
    document.getElementById('show-login').onclick = (e) => { e.preventDefault(); registerModal.classList.remove('active'); loginModal.classList.add('active'); };
    
    loginForm.onsubmit = async (e) => { e.preventDefault(); login(); };
    registerForm.onsubmit = async (e) => { e.preventDefault(); register(); };
}

function updateAuthUI() { loginNavBtn.textContent = authToken ? 'Log Out' : 'Log In'; }

async function login() {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    try {
        const res = await fetch(`${API_BASE}/auth/login/`, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ username: u, password: p }) 
        });
        
        if (!res.ok) {
            const errText = await res.text();
            console.error("Login Server Error Response:", res.status, errText);
            showToast(`Server returned ${res.status}: Invalid credentials or server crash.`, 'error');
            return;
        }

        const data = await res.json();
        authToken = data.access || data.token; 
        localStorage.setItem('authToken', authToken); 
        loginModal.classList.remove('active'); 
        updateAuthUI(); 
        showToast(`Welcome back, ${u}! Successfully logged in.`);
    } catch (e) { 
        console.error("Login Network/JSON Error:", e);
        showToast(`Network error: ${e.message}`, 'error'); 
    }
}

function logout() { authToken = null; localStorage.removeItem('authToken'); updateAuthUI(); }

async function register() {
    const u = document.getElementById('reg-username').value;
    const e = document.getElementById('reg-email').value;
    const p = document.getElementById('reg-password').value;
    if (p !== document.getElementById('reg-confirm-password').value) {
        showToast('Passwords do not match', 'error');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/register/`, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ username: u, email: e, password: p }) 
        });
        const data = await res.json();
        if (res.ok) { 
            authToken = data.token || data.access; 
            localStorage.setItem('authToken', authToken); 
            registerModal.classList.remove('active'); 
            updateAuthUI(); 
            showToast('Account created! Welcome to Flyvora.');
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (err) { showToast('Reg error', 'error'); }
}

function getAuthHeaders() { return authToken ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` } : { 'Content-Type': 'application/json' }; }

// ── Booking Logic ─────────────────────────────────────────────

function openBooking(id) {
    const f = flights.find(f => f.id === id);
    if (!f) return;
    document.getElementById('modal-flight-id').value = id;
    document.getElementById('modal-flight-summary').innerText = `${f.airline} | ${f.departure} → ${f.destination}`;
    bookingModal.classList.add('active');
}

function openHotelBooking(id) {
    const h = hotels.find(h => h.id === id);
    if (!h) return;
    document.getElementById('modal-flight-id').value = id; // reuse id field
    document.getElementById('modal-flight-summary').innerText = `Hotel: ${h.name} | ${h.location}`;
    bookingModal.classList.add('active');
    bookingForm.dataset.type = 'hotel';
}

document.getElementById('close-modal').onclick = () => bookingModal.classList.remove('active');
bookingForm.onsubmit = async (e) => {
    e.preventDefault();
    const isHotel = bookingForm.dataset.type === 'hotel';
    const bodyParams = isHotel ? {
        hotel_id: document.getElementById('modal-flight-id').value,
        passenger_name: document.getElementById('passenger-name').value,
        passenger_email: document.getElementById('passenger-email').value,
        nights: document.getElementById('seats-booked').value
    } : {
        flight_id: document.getElementById('modal-flight-id').value,
        passenger_name: document.getElementById('passenger-name').value,
        passenger_email: document.getElementById('passenger-email').value,
        seats_booked: document.getElementById('seats-booked').value
    };

    try {
        const res = await fetch(`${API_BASE}/bookings/confirm/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(bodyParams)
        });
        if (res.ok) { 
            showToast('Booking Confirmed! Check "My Bookings" for details.');
            bookingModal.classList.remove('active'); 
            if (!isHotel) searchFlights();
            else fetchHotels();
        } else {
            const data = await res.json();
            showToast(data.error || 'Booking failed', 'error');
        }
    } catch (e) { showToast('Connection error', 'error'); }
};

// ── My Bookings ───────────────────────────────────────────────
if (document.getElementById('my-bookings-btn')) {
    document.getElementById('my-bookings-btn').onclick = () => document.getElementById('my-bookings-modal').classList.add('active');
}
if (document.getElementById('close-bookings')) {
    document.getElementById('close-bookings').onclick = () => document.getElementById('my-bookings-modal').classList.remove('active');
}
if (document.getElementById('find-bookings-btn')) {
    document.getElementById('find-bookings-btn').onclick = async () => {
        const email = document.getElementById('search-email').value;
        if (!email) return;
        const bl = document.getElementById('bookings-list');
        bl.innerHTML = '...';
        try {
            const res = await fetch(`${API_BASE}/bookings/?email=${email}`, { headers: getAuthHeaders() });
            const data = await res.json();
            bl.innerHTML = '';
            data.bookings.forEach(b => {
                const div = document.createElement('div');
                div.className = 'booking-item';
                div.style.background = 'rgba(255,255,255,0.05)';
                div.style.padding = '15px';
                div.style.borderRadius = '12px';
                div.style.marginBottom = '10px';
                div.innerHTML = `<strong>${b.flight_info.airline}</strong><br>${b.flight_info.departure} → ${b.flight_info.destination}`;
                bl.appendChild(div);
            });
        } catch (e) { bl.innerHTML = 'None found'; }
    };
}

// ── Chat Logic ────────────────────────────────────────────────

chatToggle.onclick = (e) => {
    e.stopPropagation();
    const isActive = chatWindow.classList.toggle('active');
    if (isActive) {
        setTimeout(() => {
            chatInput.disabled = false;
            chatInput.focus();
        }, 50);
    }
};

// Nuclear Interaction Guard: Prevent any clicks inside the window from closing it 
// or being intercepted by parent elements
chatWindow.onclick = (e) => e.stopPropagation();
chatInput.onclick = (e) => e.stopPropagation();

function addMessage(txt, bot = true) {
    const m = document.createElement('div');
    m.className = `message ${bot ? 'bot-msg' : 'user-msg'}`;
    m.innerText = txt;
    chatMessages.appendChild(m);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleChat() {
    const t = chatInput.value.trim();
    if (!t) return;
    addMessage(t, false); chatInput.value = '';
    typingIndicator.style.display = 'flex';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const locStatus = document.getElementById('location-status');
        const contextData = {
            detectedCity: locStatus ? locStatus.textContent.replace('Located: ', '').trim() : 'Unknown'
        };

        const res = await fetch(`${API_BASE}/ai/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: t, context: contextData })
        });
        
        const data = await res.json();
        typingIndicator.style.display = 'none';

        if (res.ok) {
            addMessage(data.reply);
        } else {
            addMessage("I'm having trouble connecting to my central servers.");
        }
    } catch (e) {
        typingIndicator.style.display = 'none';
        addMessage("Network error. Could not reach Flyvora AI core.");
    }
}

function aiInitiate() {
    const factoids = [
        "Did you know? Flyvora covers all major Nigerian airports including Lagos, Abuja, and Kano.",
        "Need a place to stay? I can show you premium hotels near your destination airport.",
        "Traveling soon? Make sure to check our live flight prices for the best deals.",
        "Looking for luxury? Check out the Legend Hotel in Ikeja - it's right at the airport!"
    ];
    if (chatMessages.children.length < 2) {
        addMessage(factoids[Math.floor(Math.random() * factoids.length)]);
    }
}

sendChat.onclick = handleChat;

// Fix: Use keydown and ensure we don't return false for non-Enter keys
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        handleChat();
    }
});

// Debug Logger: Verify typing works in real-time
chatInput.addEventListener('input', (e) => {
    console.log('Typing detected:', e.target.value);
});

// Globals
if (logo) logo.onclick = () => { 
    if (window.location.pathname.includes('hotels.html')) fetchHotels();
    else if (document.getElementById('results-grid')) fetchFlights(); 
};
if (searchBtn) searchBtn.onclick = searchFlights;
window.openBooking = openBooking;
window.openHotelBooking = openHotelBooking;
if (document.getElementById('enable-location')) {
    document.getElementById('enable-location').onclick = detectLocation;
}
