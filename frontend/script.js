let backendStatus = 'unknown';
let statusCheckInterval;

// Cognitive Load Alert Throttling
let lastAlertTime = 0;
let alertCount = 0;

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

// Function to check backend status
async function checkBackendStatus() {
    try {
        const response = await fetch('http://localhost:8000/health', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
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
    if (backendStatus === status) return;
    
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
        console.log('Page visibility changed:', document.visibilityState);
        if (!document.hidden) {
            checkBackendStatus();
        }
    });
});

// Add timeout support for older browsers
if (!AbortSignal.timeout) {
    AbortSignal.timeout = function(ms) {
        const controller = new AbortController();
        setTimeout(() => controller.abort(), ms);
        return controller.signal;
    };
}

// ===========================================================
// SIMPLIFIED COGNITIVE LOAD MONITORING WITH HEADER ALERT
// ===========================================================
let cognitivePollingInterval = null;
let lastCognitiveStatus = null;
let headerAlertVisible = false;

function initSimpleCognitiveMonitoring() {
    if (cognitivePollingInterval) {
        clearInterval(cognitivePollingInterval);
    }
    
    // Create header alert element if it doesn't exist
    createHeaderAlertElement();
    
    // Fetch initial data
    fetchSimpleCognitiveStatus();
    
    // Set up polling every 5 seconds
    cognitivePollingInterval = setInterval(fetchSimpleCognitiveStatus, 5000);
    
    console.log('Simple cognitive monitoring started');
}

async function fetchSimpleCognitiveStatus() {
    try {
        const response = await fetch('http://localhost:8000/cognitive-load/simple-status', {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            cache: 'no-store'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                updateSimpleCognitiveDisplay(result);
                updateHeaderAlert(result);
                lastCognitiveStatus = result;
            }
        }
    } catch (error) {
        console.error('Error fetching cognitive status:', error);
        hideHeaderAlert();
    }
}

function createHeaderAlertElement() {
    if (document.getElementById('cognitive-header-alert')) {
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.id = 'cognitive-header-alert';
    alertDiv.className = 'header-alert';
    alertDiv.style.cssText = `
        position: fixed;
        top: 70px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        display: none;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideDown 0.3s ease-out;
        backdrop-filter: blur(10px);
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        @keyframes pulseAlert {
            0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
        }
        
        .header-alert.high {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.95), rgba(255, 152, 0, 0.95));
            color: #333;
            border: 2px solid #ff9800;
            animation: pulseAlert 2s infinite, slideDown 0.3s ease-out;
        }
        
        .header-alert.normal {
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.95), rgba(32, 201, 151, 0.95));
            color: white;
            border: 2px solid #20c997;
        }
    `;
    document.head.appendChild(style);
    
    alertDiv.innerHTML = `
        <i data-feather="alert-triangle" style="width: 20px; height: 20px;"></i>
        <span id="alert-message">Cognitive Load: Normal</span>
        <button onclick="hideHeaderAlert()" style="background: none; border: none; color: inherit; cursor: pointer; margin-left: auto;">
            <i data-feather="x" style="width: 18px; height: 18px;"></i>
        </button>
    `;
    
    document.body.appendChild(alertDiv);
}

function updateHeaderAlert(data) {
    const alertDiv = document.getElementById('cognitive-header-alert');
    if (!alertDiv) return;
    
    const isHigh = data.status === 'high';
    const loadValue = data.load.toFixed(1);
    
    if (isHigh) {
        alertDiv.className = 'header-alert high';
        alertDiv.querySelector('#alert-message').textContent = 
            `⚠️ High Cognitive Load: ${loadValue}% - Consider taking a break`;
        alertDiv.style.display = 'flex';
        headerAlertVisible = true;
        
        // playAlertSound();
    } else {
        if (headerAlertVisible || (lastCognitiveStatus && lastCognitiveStatus.status === 'high')) {
            alertDiv.className = 'header-alert normal';
            alertDiv.querySelector('#alert-message').textContent = 
                `✓ Cognitive Load Normal: ${loadValue}%`;
            alertDiv.style.display = 'flex';
            headerAlertVisible = true;
            
            setTimeout(hideHeaderAlert, 3000);
        } else {
            hideHeaderAlert();
        }
    }
    
    
}

function hideHeaderAlert() {
    const alertDiv = document.getElementById('cognitive-header-alert');
    if (alertDiv) {
        alertDiv.style.display = 'none';
        headerAlertVisible = false;
    }
}

// function playAlertSound() {
//     try {
//         const audioContext = new (window.AudioContext || window.webkitAudioContext)();
//         const oscillator = audioContext.createOscillator();
//         const gainNode = audioContext.createGain();
        
//         oscillator.connect(gainNode);
//         gainNode.connect(audioContext.destination);
        
//         oscillator.frequency.value = 800;
//         oscillator.type = 'sine';
        
//         gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
//         gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
//         oscillator.start(audioContext.currentTime);
//         oscillator.stop(audioContext.currentTime + 0.5);
//     } catch (e) {
//         console.log('Audio context not supported:', e);
//     }
// }

function updateSimpleCognitiveDisplay(data) {
    const card = document.getElementById('cognitive-load-card');
    if (card) {
        const statValues = card.querySelectorAll('.stat-value');
        if (statValues.length >= 1) {
            statValues[0].textContent = `${data.load.toFixed(1)}%`;
            statValues[0].style.color = data.status === 'high' ? 'var(--warning)' : 'var(--success)';
        }
        
        const statusSpan = card.querySelector('.status-indicator span');
        if (statusSpan) {
            statusSpan.textContent = data.status === 'high' ? 'High Load' : 'Normal Load';
            statusSpan.style.color = data.status === 'high' ? 'var(--warning)' : 'var(--success)';
        }
        
        const lastAlertDiv = card.querySelector('.last-alert');
        if (data.last_alert) {
            if (!lastAlertDiv) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'last-alert';
                alertDiv.innerHTML = `<i data-feather="alert-triangle"></i> Last alert: ${new Date(data.last_alert * 1000).toLocaleTimeString()}`;
                card.appendChild(alertDiv);
            } else {
                lastAlertDiv.innerHTML = `<i data-feather="alert-triangle"></i> Last alert: ${new Date(data.last_alert * 1000).toLocaleTimeString()}`;
            }
        } else if (lastAlertDiv) {
            lastAlertDiv.remove();
        }
       
    }
}

// Threshold setting (keep this)
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

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded at:', new Date().toLocaleTimeString());
    initSimpleCognitiveMonitoring();
    checkBackendStatus();
    statusCheckInterval = setInterval(checkBackendStatus, 10000);
    
    // Existing timer display
    updateTimerDisplay();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    console.log('Page unloading at:', new Date().toLocaleTimeString());
    if (cognitivePollingInterval) {
        clearInterval(cognitivePollingInterval);
        cognitivePollingInterval = null;
    }
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
});

// ===========================================================
// EXISTING DASHBOARD FUNCTIONS (KEEP THESE)
// ===========================================================

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

        const totalSeconds = 25 * 60;
        const offset = 565 - (565 * (totalSeconds - timerSeconds) / totalSeconds);
        document.querySelector('.progress-ring-fill').style.strokeDashoffset = offset;
    } else {
        resetTimer();
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