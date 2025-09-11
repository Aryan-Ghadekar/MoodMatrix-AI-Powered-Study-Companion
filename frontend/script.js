
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