let backendStatus = 'unknown';
let statusCheckInterval;

// Cognitive Load Alert Throttling
let lastAlertTime = 0;
let alertCount = 0;
let alertResetTimer = null;

function canShowAlert() {
    const now = Date.now();
    const oneMinute = 60000; // 1 minute in milliseconds
    
    // Reset counter if more than 1 minute has passed since first alert
    if (now - lastAlertTime > oneMinute) {
        alertCount = 0;
        lastAlertTime = now;
    }
    
    // Check if we haven't exceeded 2 alerts per minute
    if (alertCount < 2) {
        alertCount++;
        return true;
    }
    
    return false;
}

function resetAlertCounter() {
    alertCount = 0;
    lastAlertTime = Date.now();
}

// Function to check backend status
async function checkBackendStatus() {
    try {
        const response = await fetch('http://localhost:8000/health', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            // Add timeout for the request
            signal: AbortSignal.timeout(7000)
        });
        
        if (response.ok) {
            const data = await response.json();
            updateBackendStatus('active');
        } else {
            updateBackendStatus('inactive');
        }
    } catch (error) {
        console.log('Backend connection failed:', error);
        updateBackendStatus('inactive');
    }
}

// Function to update the status indicator
function updateBackendStatus(status) {
    if (backendStatus === status) return; // No change needed
    
    backendStatus = status;
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    
    if (status === 'active') {
        statusDot.style.background = 'var(--success)';
        statusText.textContent = 'Active';
        statusDot.style.animation = 'pulse 2s infinite';
    } else {
        statusDot.style.background = 'var(--danger)';
        statusText.textContent = 'Inactive';
        statusDot.style.animation = 'none';
    }
}

// Start checking backend status when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initial check
    checkBackendStatus();
    
    // Set up periodic checking (every 10 seconds)
    statusCheckInterval = setInterval(checkBackendStatus, 10000);
    
    // Also check when user focuses on the page
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkBackendStatus();
        }
    });
});

// Function to manually check status (can be called from console or buttons)
function refreshBackendStatus() {
    checkBackendStatus();
}

// Add timeout support for older browsers
if (!AbortSignal.timeout) {
    AbortSignal.timeout = function(ms) {
        const controller = new AbortController();
        setTimeout(() => controller.abort(), ms);
        return controller.signal;
    };
}









// Cognitive Load Monitoring
let cognitiveLoadSocket = null;
let isCognitiveMonitoring = false;

// Initialize cognitive load monitoring
function initCognitiveLoadMonitoring() {
    try {
        cognitiveLoadSocket = new WebSocket('ws://localhost:8000/cognitive-load/ws');
        
        cognitiveLoadSocket.onopen = function(event) {
            console.log('Cognitive load WebSocket connected');
            updateCognitiveStatus('Connected');
        };
        
        cognitiveLoadSocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'status_update') {
                    updateCognitiveDisplay(data.data);
                } else if (data.type === 'cognitive_load_alert') {
                    // Apply throttling to alerts
                    showCognitiveLoadAlert(data);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };
        
        cognitiveLoadSocket.onclose = function(event) {
            console.log('Cognitive load WebSocket disconnected');
            updateCognitiveStatus('Disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(initCognitiveLoadMonitoring, 5000);
        };
        
        cognitiveLoadSocket.onerror = function(error) {
            console.error('Cognitive load WebSocket error:', error);
            updateCognitiveStatus('Error');
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateCognitiveStatus('Failed');
    }
}

// Update cognitive load display
// Update cognitive load display for external monitoring
function updateCognitiveDisplay(data) {
    const cognitiveCard = document.getElementById('cognitive-load-card') || createCognitiveLoadCard();
    
    cognitiveCard.innerHTML = `
        <div class="card-header">
            <div class="card-icon">
                <i class="fas fa-brain"></i>
            </div>
            <h3>Cognitive Load Monitor</h3>
            <div class="status-indicator" style="margin-left: auto;">
                <div class="status-dot" style="background: var(--success)"></div>
                <span>External Monitoring</span>
            </div>
        </div>
        
        <div class="cognitive-stats">
            <div class="cognitive-stat">
                <div class="stat-value" style="color: ${data.current_load > 50 ? 'var(--warning)' : 'var(--success)'}">
                    ${data.current_load.toFixed(1)}%
                </div>
                <div class="stat-label">Overall Load</div>
            </div>
            <div class="cognitive-stat">
                <div class="stat-value">${data.emotion_load.toFixed(1)}%</div>
                <div class="stat-label">Emotion</div>
            </div>
            <div class="cognitive-stat">
                <div class="stat-value">${data.body_load.toFixed(1)}%</div>
                <div class="stat-label">Body Posture</div>
            </div>
        </div>
        
        <div class="cognitive-info">
            <p><i class="fas fa-info-circle"></i> Data from external cognitive_load_fusion.py</p>
            <p><i class="fas fa-sync-alt"></i> Updates every 5 seconds</p>
        </div>
        
        ${data.last_alert ? `
            <div class="last-alert">
                <i class="fas fa-exclamation-triangle" style="color: var(--warning);"></i>
                Last alert: ${new Date(data.last_alert * 1000).toLocaleTimeString()}
            </div>
        ` : ''}
    `;
}

// Create cognitive load card in dashboard
function createCognitiveLoadCard() {
    const card = document.createElement('div');
    card.className = 'dashboard-card';
    card.id = 'cognitive-load-card';
    
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) {
        dashboardGrid.appendChild(card);
    }
    
    return card;
}

// Show cognitive load alert
function showCognitiveLoadAlert(alertData) {
    // Check if we can show this alert (max 2 per minute)
    if (!canShowAlert()) {
        console.log('Alert throttled: Too many alerts in the last minute');
        return;
    }
    
    // Create yellow popup alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'cognitive-alert-popup';
    alertDiv.innerHTML = `
        <div class="alert-content">
            <div class="alert-header">
                <i data-feather="alert-triangle"></i>
                <h4>High Cognitive Load Detected</h4>
                <div class="alert-counter" style="font-size: 0.8rem; color: #666; margin-left: auto;">
                    Alert ${alertCount}/2 (per minute)
                </div>
                <button class="close-alert" onclick="this.parentElement.parentElement.remove()">
                    <i data-feather="x"></i>
                </button>
            </div>
            <div class="alert-body">
                <p>Current cognitive load: <strong>${alertData.load_value.toFixed(1)}%</strong></p>
                <p>Consider taking a break or changing activities.</p>
            </div>
            <div class="alert-footer">
                <button class="btn btn-primary" onclick="this.parentElement.parentElement.parentElement.remove()">
                    Acknowledge
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    feather.replace();
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 10000);
    
    console.log(`Alert shown: ${alertCount}/2 alerts in current minute`);
}



async function setCognitiveThreshold(threshold) {
    try {
        const response = await fetch('http://localhost:8000/cognitive-load/set-threshold', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ threshold: parseFloat(threshold) })
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Threshold set to:', threshold + '%');
        } else {
            console.error('Failed to set threshold:', data.message);
        }
    } catch (error) {
        console.error('Error setting threshold:', error);
    }
}

function updateCognitiveStatus(status) {
    const statusElement = document.getElementById('cognitive-status');
    if (statusElement) {
        statusElement.textContent = status;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initCognitiveLoadMonitoring();
});








// Section navigation
function showSection(sectionId) {
    document.querySelectorAll('.dashboard-section, .hero').forEach(section => {
        section.style.display = 'none';
    });

    if (sectionId === 'hero') {
        document.getElementById('heroSection').style.display = 'flex';
    } else if (sectionId === 'dashboard') {
        document.getElementById('dashboardSection').style.display = 'block';
        document.getElementById('dashboardSection').classList.add('active');
        initCharts();
    }
}

// Timer functionality
let timerInterval;
let timerRunning = false;
let timerSeconds = 25 * 60;

function toggleTimer() {
    const playBtn = document.getElementById('playBtn');

    if (!timerRunning) {
        timerInterval = setInterval(updateTimer, 1000);
        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
        timerRunning = true;
    } else {
        clearInterval(timerInterval);
        playBtn.innerHTML = '<i class="fas fa-play"></i>';
        timerRunning = false;
    }
}

function resetTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    timerSeconds = 25 * 60;
    updateTimerDisplay();
    document.getElementById('playBtn').innerHTML = '<i class="fas fa-play"></i>';
}

function updateTimer() {
    if (timerSeconds > 0) {
        timerSeconds--;
        updateTimerDisplay();

        // Update progress ring
        const totalSeconds = 25 * 60;
        const offset = 565 - (565 * (totalSeconds - timerSeconds) / totalSeconds);
        document.querySelector('.progress-ring-fill').style.strokeDashoffset = offset;
    } else {
        resetTimer();
        // Notification would go here
    }
}

function updateTimerDisplay() {
    const minutes = Math.floor(timerSeconds / 60);
    const seconds = timerSeconds % 60;
    document.getElementById('timerDisplay').textContent =
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Chat functionality
function toggleChat() {
    document.getElementById('chatWindow').classList.toggle('active');
}

// Hardware connection
function connectHardware() {
    alert('Hardware connection dialog would appear here');
}

// Initialize charts
function initCharts() {
    const ctx = document.getElementById('chartCanvas').getContext('2d');

    // Simple chart data
    const data = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Focus Level (%)',
            data: [75, 85, 70, 90, 95, 65, 80],
            borderColor: '#4361ee',
            backgroundColor: 'rgba(67, 97, 238, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f8fafc'
                    }
                }
            }
        }
    };

    new Chart(ctx, config);
}

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    updateTimerDisplay();
});