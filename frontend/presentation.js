// Initialize Feather Icons
feather.replace();

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentPresentation = null;
let currentSlideIndex = 0;
let availablePresentations = [];
let currentQuiz = null;
let userAnswers = {};
let quizTimer = null;
let timeElapsed = 0;
let currentQuestionIndex = 0;
let isPresenting = false;

// TTS and Explanation state
let currentExplanation = null;
let currentAudio = null;
let isPlaying = false;
let currentExplanationPart = 0;
let totalExplanationParts = 0;


// Add to global state
let questionTimer = null;
let timePerQuestion = 60; // Default time
let timeRemaining = 60;
let autoProgressEnabled = false;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadLoading = document.getElementById('uploadLoading');
const presentationView = document.getElementById('presentationView');
const presentationFrame = document.getElementById('presentationFrame'); 
const presentationTitle = document.getElementById('presentationTitle');
const slideCount = document.getElementById('slideCount');
const currentSlide = document.getElementById('currentSlide');
const prevSlideBtn = document.getElementById('prevSlide');
const nextSlideBtn = document.getElementById('nextSlide');
const viewInNewTabBtn = document.getElementById('viewInNewTab');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const generateQuizBtn = document.getElementById('generateQuizBtn');
const quizLoading = document.getElementById('quizLoading');
const quizResults = document.getElementById('quizResults');
const presentationSelector = document.getElementById('presentationSelector');
const presentationList = document.getElementById('presentationList');
const slideRange = document.getElementById('slideRange');

// Quiz Modal Elements
const quizModal = document.getElementById('quizModal');
const quizTimerDisplay = document.getElementById('quizTimer');
const currentQuestionNumber = document.getElementById('currentQuestionNumber');
const totalQuestions = document.getElementById('totalQuestions');
const quizModalBody = document.getElementById('quizModalBody');
const exitFullscreenQuizBtn = document.getElementById('exitFullscreenQuiz');
const prevQuestionBtn = document.getElementById('prevQuestionBtn');
const nextQuestionBtn = document.getElementById('nextQuestionBtn');
const submitQuizBtn = document.getElementById('submitQuizBtn');


const generateExplanationBtn = document.getElementById('generateExplanationBtn');
const explanationLoading = document.getElementById('explanationLoading');
const explanationResults = document.getElementById('explanationResults');
const explanationType = document.getElementById('explanationType');
const explanationRange = document.getElementById('explanationRange');
const slideBySlide = document.getElementById('slideBySlide');

// Explanation Modal Elements
const explanationModal = document.getElementById('explanationModal');
const explanationModalBody = document.getElementById('explanationModalBody');
const explanationModalTitle = document.getElementById('explanationModalTitle');
const exitFullscreenExplanationBtn = document.getElementById('exitFullscreenExplanation');
const listenExplanationBtn = document.getElementById('listenExplanationBtn');
const pauseExplanationBtn = document.getElementById('pauseExplanationBtn');
const currentExplanationPartEl = document.getElementById('currentExplanationPart');
const totalExplanationPartsEl = document.getElementById('totalExplanationParts');
const explanationProgressFill = document.getElementById('explanationProgressFill');

// Event Listeners for explanation modal
exitFullscreenExplanationBtn.addEventListener('click', closeExplanationModal);
listenExplanationBtn.addEventListener('click', listenToExplanation);
pauseExplanationBtn.addEventListener('click', pauseExplanation);

// Event Listeners
generateExplanationBtn.addEventListener('click', generateExplanation);
uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileUpload);
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.backgroundColor = 'rgba(67, 97, 238, 0.1)';
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.backgroundColor = 'rgba(30, 41, 59, 0.5)';
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.backgroundColor = 'rgba(30, 41, 59, 0.5)';
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileUpload();
    }
});
prevSlideBtn.addEventListener('click', showPreviousSlide);
nextSlideBtn.addEventListener('click', showNextSlide);
viewInNewTabBtn.addEventListener('click', openPresentationInNewTab);
generateQuizBtn.addEventListener('click', generateQuiz);

// Quiz Modal Event Listeners
exitFullscreenQuizBtn.addEventListener('click', closeQuizModal);
prevQuestionBtn.addEventListener('click', showPreviousQuestion);
nextQuestionBtn.addEventListener('click', showNextQuestion);
submitQuizBtn.addEventListener('click', submitQuiz);

// Initialize
document.addEventListener('DOMContentLoaded', loadAvailablePresentations);

// Presentation mode event listeners
document.getElementById('presentModeBtn').addEventListener('click', startPresentationMode);
document.getElementById('exitPresentMode').addEventListener('click', exitPresentationMode);
document.getElementById('prevSlideModal').addEventListener('click', showPreviousSlideModal);
document.getElementById('nextSlideModal').addEventListener('click', showNextSlideModal);


// Keyboard shortcuts for presentation mode
document.addEventListener('keydown', handlePresentationKeyboard);


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


// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadAvailablePresentations();
    initTabs();
    
    // Start backend status monitoring
    checkBackendStatus();
    statusCheckInterval = setInterval(checkBackendStatus, 10000);
    
    // Start cognitive load monitoring
    initCognitiveLoadMonitoring();
    
    // Check status when page becomes visible
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkBackendStatus();
        }
    });
});





// Backend Status Monitoring
async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });
        
        if (response.ok) {
            updateBackendStatus('active');
        } else {
            updateBackendStatus('inactive');
        }
    } catch (error) {
        console.log('Backend connection failed:', error);
        updateBackendStatus('inactive');
    }
}

function updateBackendStatus(status) {
    if (backendStatus === status) return;
    
    backendStatus = status;
    const statusIndicator = document.getElementById('backendStatusIndicator');
    
    if (statusIndicator) {
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('span');
        
        if (status === 'active') {
            statusDot.style.background = 'var(--success)';
            statusText.textContent = 'Backend Active';
            statusDot.classList.add('active');
        } else {
            statusDot.style.background = 'var(--danger)';
            statusText.textContent = 'Backend Inactive';
            statusDot.classList.remove('active');
        }
    }
}

// Cognitive Load Monitoring
function initCognitiveLoadMonitoring() {
    try {
        cognitiveLoadSocket = new WebSocket(`ws://localhost:8000/cognitive-load/ws`);
        
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

function updateCognitiveDisplay(data) {
    let cognitiveCard = document.getElementById('cognitive-load-card');
    
    if (!cognitiveCard) {
        cognitiveCard = createCognitiveLoadCard();
    }
    
    cognitiveCard.innerHTML = `
        <div class="card-header">
            <div class="card-icon">
                <i data-feather="brain"></i>
            </div>
            <h3>Cognitive Load Monitor</h3>
            <div class="status-indicator" style="margin-left: auto;">
                <div class="status-dot active"></div>
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
            <p><i data-feather="info"></i> Data from external cognitive_load_fusion.py</p>
            <p><i data-feather="refresh-cw"></i> Updates every 5 seconds</p>
        </div>
        
        ${data.last_alert ? `
            <div class="last-alert">
                <i data-feather="alert-triangle"></i>
                Last alert: ${new Date(data.last_alert * 1000).toLocaleTimeString()}
            </div>
        ` : ''}
    `;
    
    feather.replace();
}

function createCognitiveLoadCard() {
    const card = document.createElement('div');
    card.className = 'dashboard-card';
    card.id = 'cognitive-load-card';
    
    // Add to the dashboard section or create a new section
    const dashboardSection = document.getElementById('dashboardSection');
    if (dashboardSection) {
        dashboardSection.appendChild(card);
    }
    
    return card;
}

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

function updateCognitiveStatus(status) {
    console.log('Cognitive monitoring status:', status);
}

async function setCognitiveThreshold(threshold) {
    try {
        const response = await fetch(`${API_BASE_URL}/cognitive-load/set-threshold`, {
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








// Explanation Functions
async function generateExplanation() {
    if (!currentPresentation) return;
    
    const explanationTypeValue = explanationType.value;
    const explanationRangeValue = explanationRange.value;
    const slideBySlideValue = slideBySlide.checked;
    
    // Determine which slides to use for explanation
    let slideNumbers = [];
    
    if (explanationRangeValue === 'current') {
        slideNumbers = [currentSlideIndex + 1];
    } else if (explanationRangeValue === 'previous') {
        for (let i = 1; i <= currentSlideIndex + 1; i++) {
            slideNumbers.push(i);
        }
    } else {
        for (let i = 1; i <= currentPresentation.total_slides; i++) {
            slideNumbers.push(i);
        }
    }
    
    showExplanationLoading();
    explanationResults.style.display = 'none';
    hideError();
    
    try {
        let url = `${API_BASE_URL}/generate-explanation/${currentPresentation.filename}?explanation_type=${explanationTypeValue}&slide_by_slide=${slideBySlideValue}`;
        
        // Add slide numbers
        slideNumbers.forEach(num => {
            url += `&slide_numbers=${num}`;
        });
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayExplanation(data);
        } else {
            showError(data.detail || 'Failed to generate explanation');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideExplanationLoading();
    }
}

function displayExplanation(explanationData) {
    explanationResults.innerHTML = '';
    explanationResults.style.display = 'block';
    currentExplanation = explanationData;

    // Only show the fullscreen button, no explanation content
    let html = `
        <div class="explanation-ready">
            
            <div class="explanation-ready-text" >
                <h3>Explanation Generated Successfully!</h3>
                <p>Your AI explanation is ready to view in fullscreen mode.</p>
            </div>
            <div class="fullscreen-explanation-btn" >
                <button class="btn btn-fullscreen" id="openFullscreenExplanation">
                    <i data-feather="maximize-2"></i> View Explanation in Fullscreen
                </button>
            </div>
        </div>
    `;
    
    explanationResults.innerHTML = html;
    
    // Add event listener to fullscreen button
    document.getElementById('openFullscreenExplanation').addEventListener('click', openFullscreenExplanation);
    
    // Refresh icons
    feather.replace();
}

function closeExplanationModal() {
    explanationModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Stop any playing audio
    stopAudio();
}

function openFullscreenExplanation() {
    if (!currentExplanation) return;
    
    currentExplanationPart = 0;
    
    // Update modal display
    explanationModalTitle.textContent = currentExplanation.explanation_title || 'AI Explanation';
    updateExplanationDisplay();
    
    // Show modal
    explanationModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Refresh icons
    feather.replace();
}

function updateExplanationDisplay() {
    if (!currentExplanation) return;
    
    let html = '';
    
    if (currentExplanation.type === 'slide_by_slide') {
        html = displayFullscreenSlideBySlideExplanation(currentExplanation);
        totalExplanationParts = currentExplanation.slide_explanations.length;
    } else {
        html = displayFullscreenCombinedExplanation(currentExplanation);
        totalExplanationParts = 1;
    }
    
    explanationModalBody.innerHTML = html;
    
    // Update progress
    currentExplanationPartEl.textContent = currentExplanationPart + 1;
    totalExplanationPartsEl.textContent = totalExplanationParts;
    
    const progress = ((currentExplanationPart + 1) / totalExplanationParts) * 100;
    explanationProgressFill.style.width = `${progress}%`;
    
    // Refresh icons
    feather.replace();
}

function displayFullscreenSlideBySlideExplanation(explanationData) {
    let html = '';
    
    if (explanationData.slide_explanations && explanationData.slide_explanations.length > 0) {
        const currentSlide = explanationData.slide_explanations[currentExplanationPart];
        
        html = `
            <div class="slide-explanation-fullscreen">
                <div class="slide-explanation-header-fullscreen">
                    <div class="slide-number-badge-fullscreen">Slide ${currentSlide.slide_number}</div>
                    <div class="slide-explanation-title-fullscreen">${currentSlide.slide_title}</div>
                </div>
                
                ${currentSlide.main_topic ? `<div class="slide-main-topic-fullscreen">Main Topic: ${currentSlide.main_topic}</div>` : ''}
                
                <div class="slide-explanation-content-fullscreen">${currentSlide.explanation}</div>
        `;
        
        // Add real-life examples for this slide
        if (currentSlide.real_life_examples && currentSlide.real_life_examples.length > 0) {
            html += `
                <div class="slide-real-life-examples">
                    <h5>Real-Life Examples:</h5>
                    <div class="examples-list">
            `;
            
            currentSlide.real_life_examples.forEach(example => {
                html += `
                    <div class="example-item">
                        <div class="example-icon">💡</div>
                        <div class="example-content">
                            <strong>${example.example}</strong>
                            <div class="example-explanation">${example.explanation}</div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        // Add practical applications
        if (currentSlide.practical_applications && currentSlide.practical_applications.length > 0) {
            html += `
                <div class="slide-practical-applications">
                    <h5>Practical Applications:</h5>
                    <ul>
            `;
            
            currentSlide.practical_applications.forEach(application => {
                html += `<li>${application}</li>`;
            });
            
            html += `
                    </ul>
                </div>
            `;
        }
        
        if (currentSlide.key_points && currentSlide.key_points.length > 0) {
            html += `
                <div class="slide-key-points-fullscreen">
                    <h5>Key Points:</h5>
                    <ul>
            `;
            
            currentSlide.key_points.forEach(point => {
                html += `<li>${point}</li>`;
            });
            
            html += `
                    </ul>
                </div>
            `;
        }
        
        // Add TTS controls for this slide
        const slideText = getSlideExplanationText(currentSlide);
        html += `
            <div class="tts-controls">
                <button class="btn btn-control" onclick="speakText('${btoa(encodeURIComponent(slideText))}')">
                    <i data-feather="volume-2"></i> Listen to This Slide
                </button>
            </div>
        `;
        
        html += `</div>`;
        
        // Add navigation buttons for slide-by-slide
        html += `
            <div class="explanation-navigation">
                <button class="btn" onclick="previousExplanationPart()" ${currentExplanationPart === 0 ? 'disabled' : ''}>
                    <i data-feather="arrow-left"></i> Previous Slide
                </button>
                <button class="btn btn-secondary" onclick="nextExplanationPart()" ${currentExplanationPart === explanationData.slide_explanations.length - 1 ? 'disabled' : ''}>
                    Next Slide <i data-feather="arrow-right"></i>
                </button>
            </div>
        `;
    }
    
    return html;
}

function previousExplanationPart() {
    if (currentExplanationPart > 0) {
        currentExplanationPart--;
        updateExplanationDisplay();
    }
}

function nextExplanationPart() {
    if (currentExplanation && currentExplanationPart < totalExplanationParts - 1) {
        currentExplanationPart++;
        updateExplanationDisplay();
    }
}

function getSlideExplanationText(slideData) {
    let text = `Slide ${slideData.slide_number}: ${slideData.slide_title}. `;
    
    if (slideData.main_topic) {
        text += `Main Topic: ${slideData.main_topic}. `;
    }
    
    text += `Explanation: ${slideData.explanation}. `;
    
    if (slideData.real_life_examples && slideData.real_life_examples.length > 0) {
        text += 'Real-life examples: ';
        slideData.real_life_examples.forEach(example => {
            text += `${example.example}: ${example.explanation}. `;
        });
    }
    
    if (slideData.practical_applications && slideData.practical_applications.length > 0) {
        text += 'Practical applications: ';
        slideData.practical_applications.forEach(application => {
            text += `${application}. `;
        });
    }
    
    if (slideData.key_points && slideData.key_points.length > 0) {
        text += 'Key Points: ';
        slideData.key_points.forEach(point => {
            text += `${point}. `;
        });
    }
    
    return text;
}


function getExplanationFullText(explanationData) {
    let text = '';
    
    if (explanationData.summary) {
        text += `Summary: ${explanationData.summary}. `;
    }
    
    if (explanationData.key_concepts && explanationData.key_concepts.length > 0) {
        text += 'Key Concepts: ';
        explanationData.key_concepts.forEach(concept => {
            text += `${concept.concept}: ${concept.explanation}. `;
            if (concept.importance) {
                text += `Why it matters: ${concept.importance}. `;
            }
            if (concept.real_life_examples && concept.real_life_examples.length > 0) {
                text += 'Real-life examples: ';
                concept.real_life_examples.forEach(example => {
                    text += `${example.example}: ${example.explanation}. `;
                });
            }
        });
    }
    
    if (explanationData.real_world_applications && explanationData.real_world_applications.length > 0) {
        text += 'Real-world applications: ';
        explanationData.real_world_applications.forEach(application => {
            text += `${application}. `;
        });
    }
    
    if (explanationData.practical_tips && explanationData.practical_tips.length > 0) {
        text += 'Practical tips: ';
        explanationData.practical_tips.forEach(tip => {
            text += `${tip}. `;
        });
    }
    
    if (explanationData.detailed_explanation) {
        text += `Detailed Explanation: ${explanationData.detailed_explanation}. `;
    }
    
    if (explanationData.takeaways && explanationData.takeaways.length > 0) {
        text += 'Key Takeaways: ';
        explanationData.takeaways.forEach(takeaway => {
            text += `${takeaway}. `;
        });
    }
    
    return text;
}



function displayRealLifeExamples(examplesData) {
    explanationResults.innerHTML = '';
    explanationResults.style.display = 'block';
    
    let html = `
        <div class="explanation-content">
            <div class="explanation-title">Real-Life Examples & Applications</div>
    `;
    
    if (examplesData.real_life_examples) {
        const examples = examplesData.real_life_examples;
        
        // Show key concepts with examples
        if (examples.key_concepts && examples.key_concepts.length > 0) {
            html += `
                <div class="key-concepts">
                    <h4>Key Concepts with Real-Life Examples</h4>
            `;
            
            examples.key_concepts.forEach(concept => {
                html += `
                    <div class="concept-item">
                        <div class="concept-name">${concept.concept}</div>
                        <div class="concept-explanation">${concept.explanation}</div>
                `;
                
                if (concept.real_life_examples && concept.real_life_examples.length > 0) {
                    html += `
                        <div class="real-life-examples">
                            <h5>Real-Life Examples:</h5>
                            <div class="examples-list">
                    `;
                    
                    concept.real_life_examples.forEach(example => {
                        html += `
                            <div class="example-item">
                                <div class="example-icon">💡</div>
                                <div class="example-content">
                                    <strong>${example.example}</strong>
                                    <div class="example-explanation">${example.explanation}</div>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                }
                
                html += `</div>`;
            });
            
            html += `</div>`;
        }
        
        // Show real-world applications
        if (examples.real_world_applications && examples.real_world_applications.length > 0) {
            html += `
                <div class="applications-section">
                    <h4>Real-World Applications</h4>
                    <div class="applications-list">
            `;
            
            examples.real_world_applications.forEach(application => {
                html += `
                    <div class="application-item">
                        <div class="application-icon">🚀</div>
                        <div class="application-text">${application}</div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        // Show practical tips
        if (examples.practical_tips && examples.practical_tips.length > 0) {
            html += `
                <div class="practical-tips-section">
                    <h4>Practical Tips</h4>
                    <div class="tips-list">
            `;
            
            examples.practical_tips.forEach(tip => {
                html += `
                    <div class="tip-item">
                        <div class="tip-icon">💡</div>
                        <div class="tip-text">${tip}</div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
    }
    
    html += `</div>`;
    explanationResults.innerHTML = html;
}

function displayFullscreenCombinedExplanation(explanationData) {
    let html = `
        <div class="explanation-content-large">
            <div class="explanation-title-fullscreen">${explanationData.explanation_title || 'Detailed Explanation'}</div>
    `;
    
    if (explanationData.summary) {
        html += `
            <div class="explanation-summary-fullscreen">
                <strong>Summary:</strong> ${explanationData.summary}
            </div>
        `;
    }
    
    if (explanationData.key_concepts && explanationData.key_concepts.length > 0) {
        html += `
            <div class="key-concepts-fullscreen">
                <h4>Key Concepts</h4>
        `;
        
        explanationData.key_concepts.forEach(concept => {
            html += `
                <div class="concept-item-fullscreen">
                    <div class="concept-name-fullscreen">${concept.concept}</div>
                    <div class="concept-explanation-fullscreen">${concept.explanation}</div>
                    ${concept.importance ? `<div class="concept-importance-fullscreen">Why it matters: ${concept.importance}</div>` : ''}
            `;
            
            // Add real-life examples if available
            if (concept.real_life_examples && concept.real_life_examples.length > 0) {
                html += `
                    <div class="real-life-examples">
                        <h5>Real-Life Examples:</h5>
                        <div class="examples-list">
                `;
                
                concept.real_life_examples.forEach(example => {
                    html += `
                        <div class="example-item">
                            <div class="example-icon">💡</div>
                            <div class="example-content">
                                <strong>${example.example}</strong>
                                <div class="example-explanation">${example.explanation}</div>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            html += `</div>`;
        });
        
        html += `</div>`;
    }
    
    // Add real-world applications section
    if (explanationData.real_world_applications && explanationData.real_world_applications.length > 0) {
        html += `
            <div class="applications-section">
                <h4>Real-World Applications</h4>
                <div class="applications-list">
        `;
        
        explanationData.real_world_applications.forEach(application => {
            html += `
                <div class="application-item">
                    <div class="application-icon">🚀</div>
                    <div class="application-text">${application}</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Add practical tips section
    if (explanationData.practical_tips && explanationData.practical_tips.length > 0) {
        html += `
            <div class="practical-tips-section">
                <h4>Practical Tips</h4>
                <div class="tips-list">
        `;
        
        explanationData.practical_tips.forEach(tip => {
            html += `
                <div class="tip-item">
                    <div class="tip-icon">💡</div>
                    <div class="tip-text">${tip}</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    if (explanationData.detailed_explanation) {
        html += `
            <div class="detailed-explanation-fullscreen">
                <h4>Comprehensive Explanation</h4>
                <div>${explanationData.detailed_explanation}</div>
            </div>
        `;
    }
    
    if (explanationData.takeaways && explanationData.takeaways.length > 0) {
        html += `
            <div class="takeaways-list-fullscreen">
                <h4>Key Takeaways</h4>
                <ul>
        `;
        
        explanationData.takeaways.forEach(takeaway => {
            html += `<li>${takeaway}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    // Add TTS controls
    const fullText = getExplanationFullText(explanationData);
    html += `
        <div class="tts-controls">
            <button class="btn btn-control" onclick="speakText('${btoa(encodeURIComponent(fullText))}')">
                <i data-feather="volume-2"></i> Listen to Full Explanation
            </button>
        </div>
    `;
    
    html += `</div>`;
    return html;
}

async function speakText(encodedText) {
    try {
        const text = decodeURIComponent(atob(encodedText));
        
        // Show loading state
        listenExplanationBtn.disabled = true;
        listenExplanationBtn.innerHTML = '<div class="spinner-small"></div> Generating...';
        
        const response = await fetch(`${API_BASE_URL}/generate-tts?text=${encodeURIComponent(text)}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            if (data.use_browser_tts) {
                // Use browser's built-in speech synthesis
                useBrowserTTS(text);
            } else if (data.audio_base64) {
                // Use server-generated audio
                playAudioFromBase64(data.audio_base64);
            } else {
                throw new Error('No audio data received');
            }
        } else {
            // Fallback to browser TTS
            useBrowserTTS(text);
        }
    } catch (error) {
        console.error('TTS error, using browser fallback:', error);
        const text = decodeURIComponent(atob(encodedText));
        useBrowserTTS(text);
    } finally {
        // Reset button state
        listenExplanationBtn.disabled = false;
        listenExplanationBtn.innerHTML = '<i data-feather="volume-2"></i> Listen';
        feather.replace();
    }
}

function playAudioFromBase64(audioBase64) {
    // Create audio element
    const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
    
    // Stop any currently playing audio
    stopAudio();
    
    // Set current audio
    currentAudio = audio;
    isPlaying = true;
    
    // Update UI
    listenExplanationBtn.style.display = 'none';
    pauseExplanationBtn.style.display = 'flex';
    listenExplanationBtn.classList.add('listening');
    
    // Play audio
    audio.play();
    
    // Handle audio end
    audio.onended = () => {
        stopAudio();
    };
    
    // Handle audio error
    audio.onerror = () => {
        stopAudio();
        showError('Failed to play audio');
    };
}


function useBrowserTTS(text) {
    // Check if browser supports speech synthesis
    if ('speechSynthesis' in window) {
        // Stop any current speech
        window.speechSynthesis.cancel();
        
        // Create speech utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure voice
        utterance.rate = 0.8; // Slower speed for better comprehension
        utterance.pitch = 1;
        utterance.volume = 1;
        
        // Set a pleasant voice if available
        const voices = window.speechSynthesis.getVoices();
        const englishVoice = voices.find(voice => 
            voice.lang.includes('en') && voice.name.includes('Female')
        ) || voices.find(voice => voice.lang.includes('en'));
        
        if (englishVoice) {
            utterance.voice = englishVoice;
        }
        
        // Update UI
        listenExplanationBtn.style.display = 'none';
        pauseExplanationBtn.style.display = 'flex';
        listenExplanationBtn.classList.add('listening');
        
        // Set current audio
        currentAudio = utterance;
        isPlaying = true;
        
        // Play speech
        window.speechSynthesis.speak(utterance);
        
        // Handle events
        utterance.onend = () => {
            stopAudio();
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            stopAudio();
            showError('Speech synthesis failed');
        };
        
    } else {
        showError('Text-to-Speech not supported in your browser');
    }
}



function listenToExplanation() {
    if (!currentExplanation) return;
    
    let text = '';
    if (currentExplanation.type === 'slide_by_slide') {
        const currentSlide = currentExplanation.slide_explanations[currentExplanationPart];
        text = getSlideExplanationText(currentSlide);
    } else {
        text = getExplanationFullText(currentExplanation);
    }
    
    speakText(btoa(encodeURIComponent(text)));
}

function pauseExplanation() {
    if (isPlaying) {
        // Pause server-generated audio
        if (currentAudio && currentAudio.pause) {
            currentAudio.pause();
        }
        
        // Pause browser TTS
        if ('speechSynthesis' in window) {
            window.speechSynthesis.pause();
        }
        
        isPlaying = false;
        pauseExplanationBtn.innerHTML = '<i data-feather="play"></i> Resume';
        feather.replace();
    } else {
        // Resume server-generated audio
        if (currentAudio && currentAudio.play) {
            currentAudio.play();
        }
        
        // Resume browser TTS
        if ('speechSynthesis' in window) {
            window.speechSynthesis.resume();
        }
        
        isPlaying = true;
        pauseExplanationBtn.innerHTML = '<i data-feather="pause"></i> Pause';
        feather.replace();
    }
}

function stopAudio() {
    // Stop server-generated audio
    if (currentAudio && currentAudio.pause) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
    
    // Stop browser TTS
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    
    // Reset state
    currentAudio = null;
    isPlaying = false;
    pauseExplanationBtn.style.display = 'none';
    listenExplanationBtn.style.display = 'flex';
    listenExplanationBtn.classList.remove('listening');
}

function displayCombinedExplanation(explanationData) {
    let html = `
        <div class="explanation-content">
            <div class="explanation-title">${explanationData.explanation_title || 'Explanation'}</div>
    `;
    
    if (explanationData.summary) {
        html += `
            <div class="explanation-summary">
                <strong>Summary:</strong> ${explanationData.summary}
            </div>
        `;
    }
    
    if (explanationData.key_concepts && explanationData.key_concepts.length > 0) {
        html += `
            <div class="key-concepts">
                <h4>Key Concepts</h4>
        `;
        
        explanationData.key_concepts.forEach(concept => {
            html += `
                <div class="concept-item">
                    <div class="concept-name">${concept.concept}</div>
                    <div class="concept-explanation">${concept.explanation}</div>
                    ${concept.importance ? `<div class="concept-importance">Why it matters: ${concept.importance}</div>` : ''}
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    if (explanationData.detailed_explanation) {
        html += `
            <div class="detailed-explanation">
                <h4>Detailed Explanation</h4>
                <div>${explanationData.detailed_explanation}</div>
            </div>
        `;
    }
    
    if (explanationData.takeaways && explanationData.takeaways.length > 0) {
        html += `
            <div class="takeaways-list">
                <h4>Key Takeaways</h4>
                <ul>
        `;
        
        explanationData.takeaways.forEach(takeaway => {
            html += `<li>${takeaway}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    if (explanationData.difficulty_level) {
        const difficultyClass = `difficulty-${explanationData.difficulty_level}`;
        html += `
            <div class="difficulty-badge ${difficultyClass}">
                ${explanationData.difficulty_level.toUpperCase()}
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}


function displaySlideBySlideExplanation(explanationData) {
    let html = `
        <div class="explanation-content">
            <div class="explanation-title">
                Slide-by-Slide Explanation
                <span style="font-size: 0.9rem; color: var(--text-secondary);">
                    (${explanationData.total_slides} slides)
                </span>
            </div>
    `;
    
    if (explanationData.slide_explanations && explanationData.slide_explanations.length > 0) {
        explanationData.slide_explanations.forEach(slide => {
            html += `
                <div class="slide-explanation-item">
                    <div class="slide-explanation-header">
                        <div class="slide-number-badge">Slide ${slide.slide_number}</div>
                        <div class="slide-explanation-title">${slide.slide_title}</div>
                    </div>
                    ${slide.main_topic ? `<div class="slide-main-topic">Main Topic: ${slide.main_topic}</div>` : ''}
                    <div class="slide-explanation-content">${slide.explanation}</div>
            `;
            
            if (slide.key_points && slide.key_points.length > 0) {
                html += `
                    <div class="slide-key-points">
                        <h5>Key Points:</h5>
                        <ul>
                `;
                
                slide.key_points.forEach(point => {
                    html += `<li>${point}</li>`;
                });
                
                html += `
                        </ul>
                    </div>
                `;
            }
            
            html += `</div>`;
        });
    }
    
    html += `</div>`;
    return html;
}

function showExplanationLoading() {
    explanationLoading.style.display = 'block';
    generateExplanationBtn.disabled = true;
}

function hideExplanationLoading() {
    explanationLoading.style.display = 'none';
    generateExplanationBtn.disabled = false;
}

// Update the selectPresentation function to enable explanation button
async function selectPresentation(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/presentation-info/${filename}`);
        const data = await response.json();
        
        if (response.ok) {
            currentPresentation = data;
            currentSlideIndex = 0;
            
            // Update UI
            presentationTitle.textContent = data.original_name;
            slideCount.textContent = `Total Slides: ${data.total_slides}`;
            updateSlideDisplay();
            
            // Show presentation view and present button
            presentationView.style.display = 'block';
            document.getElementById('presentModeBtn').style.display = 'flex';
            
            // Enable quiz and explanation generation
            generateQuizBtn.disabled = false;
            generateExplanationBtn.disabled = false;
            
            // Update presentation list
            renderPresentationList();
        } else {
            showError('Failed to load presentation data');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}


// Tab functionality
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            btn.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            // Refresh icons when switching tabs
            setTimeout(() => {
                feather.replace();
            }, 100);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadAvailablePresentations();
    initTabs(); // Initialize tabs
});

function startPresentationMode() {
    if (!currentPresentation) return;
    
    isPresenting = true;
    const presentationModal = document.getElementById('presentationModal');
    presentationModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Update modal with current presentation info
    document.getElementById('presentationTitleModal').textContent = currentPresentation.original_name;
    updatePresentationSlide();
    
    // Refresh icons after a short delay to ensure DOM is updated
    setTimeout(() => {
        feather.replace();
    }, 100);
}

function exitPresentationMode() {
    isPresenting = false;
    const presentationModal = document.getElementById('presentationModal');
    presentationModal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function updatePresentationSlide() {
    if (!currentPresentation || !isPresenting) return;
    
    const slideData = currentPresentation.slides[currentSlideIndex];
    const contentContainer = document.getElementById('presentationContentModal');
    const slideCounter = document.getElementById('slideCounterModal');
    const progressFill = document.getElementById('progressFill');
    
    // Update slide counter
    slideCounter.textContent = `Slide ${currentSlideIndex + 1} of ${currentPresentation.total_slides}`;
    
    // Update progress bar
    const progress = ((currentSlideIndex + 1) / currentPresentation.total_slides) * 100;
    progressFill.style.width = `${progress}%`;
    
    // Display slide content
    if (slideData && slideData.image_url) {
        contentContainer.innerHTML = `
            <div class="presentation-slide">
                <img src="${API_BASE_URL}${slideData.image_url}?t=${new Date().getTime()}" 
                     alt="Slide ${currentSlideIndex + 1}"
                     onerror="handlePresentationImageError(this)"
                     style="max-width: 95%; max-height: 95vh;">
            </div>
        `;
    } else {
        // Fallback to text content
        contentContainer.innerHTML = `
            <div class="slide-text-presentation">
                <h3>Slide ${currentSlideIndex + 1}</h3>
                <div class="slide-text">
                    ${slideData?.content || 'No content available'}
                </div>
            </div>
        `;
    }
    
    // Update navigation buttons state
    const prevBtn = document.getElementById('prevSlideModal');
    const nextBtn = document.getElementById('nextSlideModal');
    
    if (prevBtn) prevBtn.disabled = currentSlideIndex === 0;
    if (nextBtn) nextBtn.disabled = currentSlideIndex === currentPresentation.total_slides - 1;
    
    // Refresh icons
    feather.replace();
}

function handlePresentationImageError(imgElement) {
    const slideData = currentPresentation.slides[currentSlideIndex];
    const contentContainer = document.getElementById('presentationContentModal');
    
    contentContainer.innerHTML = `
        <div class="slide-text-presentation">
            <h3>Slide ${currentSlideIndex + 1}</h3>
            <div class="slide-text">
                ${slideData?.content || 'No content available'}
            </div>
        </div>
    `;
}

function showPreviousSlideModal() {
    if (currentSlideIndex > 0) {
        currentSlideIndex--;
        updatePresentationSlide();
        updateSlideDisplay(); // Also update regular view
    }
}

function showNextSlideModal() {
    if (currentPresentation && currentSlideIndex < currentPresentation.total_slides - 1) {
        currentSlideIndex++;
        updatePresentationSlide();
        updateSlideDisplay(); // Also update regular view
    }
}

function handlePresentationKeyboard(event) {
    if (!isPresenting) return;
    
    switch(event.key) {
        case 'ArrowLeft':
        case 'PageUp':
            event.preventDefault();
            showPreviousSlideModal();
            break;
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
            event.preventDefault();
            showNextSlideModal();
            break;
        case 'Escape':
            event.preventDefault();
            exitPresentationMode();
            break;
        case 'F5':
            event.preventDefault();
            break;
    }
}

// Update the selectPresentation function to show/hide present button
async function selectPresentation(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/presentation-info/${filename}`);
        const data = await response.json();
        
        if (response.ok) {
            currentPresentation = data;
            currentSlideIndex = 0;
            
            // Update UI
            presentationTitle.textContent = data.original_name;
            slideCount.textContent = `Total Slides: ${data.total_slides}`;
            updateSlideDisplay();
            
            // Show presentation view and present button
            presentationView.style.display = 'block';
            document.getElementById('presentModeBtn').style.display = 'flex';
            
            // Enable both quiz and explanation generation
            generateQuizBtn.disabled = false;
            generateExplanationBtn.disabled = false;
            
            // Update presentation list
            renderPresentationList();
        } else {
            showError('Failed to load presentation data');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Update the updateSlideDisplay function to sync with presentation mode
function updateSlideDisplay() {
    if (!currentPresentation) return;
    
    currentSlide.textContent = `Slide ${currentSlideIndex + 1} of ${currentPresentation.total_slides}`;
    
    // Get the current slide data
    const slideData = currentPresentation.slides[currentSlideIndex];
    
    // Check if we have an image URL for this slide
    if (slideData && slideData.image_url) {
        presentationFrame.innerHTML = `
            <div class="slide-image-container">
                <div class="image-loading">Loading slide image...</div>
                <img src="${API_BASE_URL}${slideData.image_url}?t=${new Date().getTime()}" 
                     alt="Slide ${currentSlideIndex + 1}" 
                     class="slide-image"
                     onload="this.parentElement.querySelector('.image-loading').style.display = 'none'"
                     onerror="handleImageError(this)">
                <div class="slide-content-overlay">
                    <h3>Slide ${currentSlideIndex + 1}</h3>
                    ${slideData.content ? `<p class="slide-preview-text">${slideData.content.substring(0, 150)}${slideData.content.length > 150 ? '...' : ''}</p>` : ''}
                </div>
            </div>
        `;
    } else {
        presentationFrame.innerHTML = `
            <div class="slide-text-content">
                <h3>Slide ${currentSlideIndex + 1}</h3>
                <div class="slide-text">
                    ${slideData?.content || 'No content available'}
                </div>
                <div class="image-unavailable">
                    <i>🖼️</i>
                    <p>Slide preview image not available</p>
                    <button class="btn btn-secondary" onclick="tryLoadImage()">Try Load Image</button>
                </div>
            </div>
        `;
    }
    
    // Update navigation buttons
    prevSlideBtn.disabled = currentSlideIndex === 0;
    nextSlideBtn.disabled = currentSlideIndex === currentPresentation.total_slides - 1;
    
    // If in presentation mode, update the presentation view as well
    if (isPresenting) {
        updatePresentationSlide();
    }
}

// Update the handleFileUpload function
async function handleFileUpload() {
    if (!fileInput.files.length) return;
    
    const file = fileInput.files[0];
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.ppt') && !file.name.toLowerCase().endsWith('.pptx')) {
        showError('Please select a PowerPoint file (.ppt or .pptx)');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showUploadLoading();
    hideError();
    hideSuccess();
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload-ppt`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('Presentation uploaded successfully!');
            
            // Clear the file input
            fileInput.value = '';
            
            // Reload and display the presentations
            await loadAvailablePresentations();
            
            // Automatically select the newly uploaded presentation
            if (data.filename) {
                await selectPresentation(data.filename);
            }
            
            // Show the presentation selector
            presentationSelector.style.display = 'block';
            
        } else {
            showError(data.detail || 'Failed to upload presentation');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideUploadLoading();
    }
}

// Update the loadAvailablePresentations function to ensure it shows the selector
async function loadAvailablePresentations() {
    try {
        const response = await fetch(`${API_BASE_URL}/available-presentations`);
        const data = await response.json();
        
        if (response.ok) {
            availablePresentations = data.presentations || [];
            renderPresentationList();
            
            // Always show the selector if there are presentations
            if (availablePresentations.length > 0) {
                presentationSelector.style.display = 'block';
                
                // If no presentation is currently selected, select the first one
                if (!currentPresentation && availablePresentations.length > 0) {
                    await selectPresentation(availablePresentations[0].filename);
                }
            } else {
                presentationSelector.style.display = 'none';
                presentationView.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Failed to load presentations:', error);
    }
}

// Update the renderPresentationList function to better handle the list
function renderPresentationList() {
    presentationList.innerHTML = '';
    
    if (availablePresentations.length === 0) {
        presentationList.innerHTML = '<div class="presentation-item" style="color: var(--text-secondary); font-style: italic;">No presentations available. Upload a PPT file to get started.</div>';
        return;
    }
    
    // Sort presentations by upload date (newest first)
    const sortedPresentations = [...availablePresentations].sort((a, b) => {
        return new Date(b.upload_date || 0) - new Date(a.upload_date || 0);
    });
    
    sortedPresentations.forEach(presentation => {
        const item = document.createElement('div');
        item.className = 'presentation-item';
        
        // Highlight the currently selected presentation
        if (currentPresentation && currentPresentation.filename === presentation.filename) {
            item.classList.add('active');
        }
        
        // Create a more informative presentation item
        const uploadDate = presentation.upload_date ? new Date(presentation.upload_date).toLocaleDateString() : 'Recently uploaded';
        item.innerHTML = `
            <div style="font-weight: 600;">${presentation.original_name}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">
                ${presentation.total_slides || 0} slides • ${uploadDate}
            </div>
        `;
        
        item.addEventListener('click', () => selectPresentation(presentation.filename));
        presentationList.appendChild(item);
    });
}

// Update the selectPresentation function to handle edge cases
async function selectPresentation(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/presentation-info/${filename}`);
        const data = await response.json();
        
        if (response.ok) {
            currentPresentation = data;
            currentSlideIndex = 0;
            
            // Update UI
            presentationTitle.textContent = data.original_name;
            slideCount.textContent = `Total Slides: ${data.total_slides}`;
            updateSlideDisplay();
            
            // Show presentation view and present button
            presentationView.style.display = 'block';
            document.getElementById('presentModeBtn').style.display = 'flex';
            
            // Enable quiz and explanation generation
            generateQuizBtn.disabled = false;
            generateExplanationBtn.disabled = false;
            
            // Update presentation list to reflect current selection
            renderPresentationList();
            
            // Show success message when switching presentations
            showSuccess(`Now viewing: ${data.original_name}`);
            setTimeout(hideSuccess, 3000);
            
        } else {
            showError('Failed to load presentation data');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function updateSlideDisplay() {
    if (!currentPresentation) return;
    
    currentSlide.textContent = `Slide ${currentSlideIndex + 1} of ${currentPresentation.total_slides}`;
    
    // Get the current slide data
    const slideData = currentPresentation.slides[currentSlideIndex];
    
    console.log('Slide data:', slideData); // Debug log
    
    // Check if we have an image URL for this slide
    if (slideData && slideData.image_url) {
        console.log('Using image URL:', slideData.image_url); // Debug log
        
        // Display slide image with loading state
        presentationFrame.innerHTML = `
            <div class="slide-image-container">
                <div class="image-loading">Loading slide image...</div>
                <img src="${API_BASE_URL}${slideData.image_url}?t=${new Date().getTime()}" 
                     alt="Slide ${currentSlideIndex + 1}" 
                     class="slide-image"
                     onload="this.parentElement.querySelector('.image-loading').style.display = 'none'"
                     onerror="handleImageError(this)">
                <div class="slide-content-overlay">
                    <h3>Slide ${currentSlideIndex + 1}</h3>
                    ${slideData.content ? `<p class="slide-preview-text">${slideData.content.substring(0, 150)}${slideData.content.length > 150 ? '...' : ''}</p>` : ''}
                </div>
            </div>
        `;
    } else {
        console.log('No image URL, using fallback'); // Debug log
        // Fallback to text content
        presentationFrame.innerHTML = `
            <div class="slide-text-content">
                <h3>Slide ${currentSlideIndex + 1}</h3>
                <div class="slide-text">
                    ${slideData?.content || 'No content available'}
                </div>
                <div class="image-unavailable">
                    <i>🖼️</i>
                    <p>Slide preview image not available</p>
                    <button class="btn btn-secondary" onclick="tryLoadImage()">Try Load Image</button>
                </div>
            </div>
        `;
    }
    
    // Update navigation buttons
    prevSlideBtn.disabled = currentSlideIndex === 0;
    nextSlideBtn.disabled = currentSlideIndex === currentPresentation.total_slides - 1;
}

// Initialize the auto-refresh when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadAvailablePresentations();
    initTabs();
    startPresentationListRefresh();
});

function startPresentationListRefresh() {
    // Optional: Add automatic refresh logic here if needed
    // For now, we'll just load presentations periodically
    setInterval(loadAvailablePresentations, 30000); // Refresh every 30 seconds
}

// Also add an event listener for page visibility to refresh when user returns to the page
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        loadAvailablePresentations();
    }
});

function handleImageError(imgElement) {
    console.log('Image load error'); // Debug log
    const container = imgElement.parentElement;
    const loadingElement = container.querySelector('.image-loading');
    if (loadingElement) {
        loadingElement.textContent = 'Image not available, using API fallback...';
        loadingElement.style.color = '#ff9e00';
    }
    
    // Try to load the image via the API endpoint as fallback
    const slideData = currentPresentation.slides[currentSlideIndex];
    if (slideData && currentPresentation) {
        fetch(`${API_BASE_URL}/slide-image/${currentPresentation.filename}/${currentSlideIndex}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('API call failed');
                }
                return response.json();
            })
            .then(data => {
                if (data.base64_image) {
                    imgElement.src = `data:image/png;base64,${data.base64_image}`;
                    if (loadingElement) {
                        loadingElement.style.display = 'none';
                    }
                } else {
                    throw new Error('No base64 image in response');
                }
            })
            .catch(error => {
                console.error('Failed to load fallback image:', error);
                if (loadingElement) {
                    loadingElement.textContent = 'Image not available';
                    loadingElement.style.color = '#ef476f';
                }
                // Show text content as final fallback
                showTextFallback();
            });
    } else {
        showTextFallback();
    }
}

function showTextFallback() {
    const slideData = currentPresentation.slides[currentSlideIndex];
    presentationFrame.innerHTML = `
        <div class="slide-text-content">
            <h3>Slide ${currentSlideIndex + 1}</h3>
            <div class="slide-text">
                ${slideData?.content || 'No content available'}
            </div>
            <div class="image-unavailable">
                <i>🖼️</i>
                <p>Unable to load slide image</p>
            </div>
        </div>
    `;
}

function tryLoadImage() {
    updateSlideDisplay();
}

function showPreviousSlide() {
    if (currentSlideIndex > 0) {
        currentSlideIndex--;
        updateSlideDisplay();
    }
}

function showNextSlide() {
    if (currentPresentation && currentSlideIndex < currentPresentation.total_slides - 1) {
        currentSlideIndex++;
        updateSlideDisplay();
    }
}

function openPresentationInNewTab() {
    if (!currentPresentation) return;
    
    const url = `${API_BASE_URL}/presentation-file/${currentPresentation.filename}`;
    window.open(url, '_blank');
}

async function generateQuiz() {
    if (!currentPresentation) return;
    
    const numQuestions = document.getElementById('numQuestions').value;
    const slideRangeValue = document.getElementById('slideRange').value;
    timePerQuestion = parseInt(document.getElementById('timePerQuestion').value) || 0;
    
    // Determine which slides to use for quiz generation
    let slideNumbers = [];
    
    if (slideRangeValue === 'current') {
        slideNumbers = [currentSlideIndex + 1];
    } else if (slideRangeValue === 'previous') {
        for (let i = 1; i <= currentSlideIndex + 1; i++) {
            slideNumbers.push(i);
        }
    } else {
        for (let i = 1; i <= currentPresentation.total_slides; i++) {
            slideNumbers.push(i);
        }
    }
    
    showQuizLoading();
    quizResults.style.display = 'none';
    hideError();
    
    try {
        let url = `${API_BASE_URL}/generate-quiz/${currentPresentation.filename}?num_questions=${numQuestions}&question_types=mcq`;
        
        // Add slide numbers
        slideNumbers.forEach(num => {
            url += `&slide_numbers=${num}`;
        });
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentQuiz = data;
            userAnswers = {};
            displayQuizTest(data);
        } else {
            showError(data.detail || 'Failed to generate quiz');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideQuizLoading();
    }
}

function displayQuizTest(quizData) {
    quizResults.innerHTML = '';
    quizResults.style.display = 'block';
    
    // Add quiz header
    const quizHeader = document.createElement('div');
    quizHeader.className = 'quiz-header';
    quizHeader.innerHTML = `
        <div class="quiz-title">${quizData.quiz_title || 'Generated Quiz'}</div>
        <div class="quiz-stats">Score: <span id="quizScore">0</span>/${quizData.questions ? quizData.questions.length : 0}</div>
    `;
    quizResults.appendChild(quizHeader);
    
    // Add fullscreen button
    const fullscreenBtn = document.createElement('div');
    fullscreenBtn.className = 'fullscreen-quiz-btn';
    fullscreenBtn.innerHTML = `
        <button class="btn btn-fullscreen" id="openFullscreenQuiz">
            <i data-feather="maximize-2"></i> Take Quiz in Fullscreen
        </button>
    `;
    quizResults.appendChild(fullscreenBtn);
    
    // Add questions (hidden in regular view when fullscreen is available)
    const questionsContainer = document.createElement('div');
    questionsContainer.id = 'questionsContainer';
    questionsContainer.style.display = 'none'; // Hide in regular view
    quizResults.appendChild(questionsContainer);
    
    if (quizData.questions && quizData.questions.length) {
        quizData.questions.forEach((question, index) => {
            const questionEl = document.createElement('div');
            questionEl.className = 'quiz-question';
            questionEl.id = `question-${index}`;
            
            let questionHTML = `
                <div class="question-text">${question.id}. ${question.question}</div>
                <div class="options">
            `;
            
            // MCQ options
            if (question.type === 'mcq' && question.options) {
                for (const [key, value] of Object.entries(question.options)) {
                    questionHTML += `
                        <div class="option" data-question="${index}" data-option="${key}">
                            ${key}. ${value}
                        </div>
                    `;
                }
            }
            
            questionHTML += `
                </div>
                <div class="feedback" id="feedback-${index}"></div>
            `;
            
            // Explanation
            if (question.explanation) {
                questionHTML += `<div class="explanation" id="explanation-${index}" style="display: none;">${question.explanation}</div>`;
            }
            
            // Slide reference
            if (question.slide_number) {
                questionHTML += `<div class="slide-reference">Based on Slide ${question.slide_number}</div>`;
            }
            
            questionEl.innerHTML = questionHTML;
            questionsContainer.appendChild(questionEl);
            
            // Add event listeners to options
            const options = questionEl.querySelectorAll('.option');
            options.forEach(option => {
                option.addEventListener('click', handleOptionClick);
            });
        });
        
        // Add quiz actions
        const quizActions = document.createElement('div');
        quizActions.className = 'quiz-actions';
        quizActions.innerHTML = `
            <button class="btn" id="checkAnswersBtn">Check Answers</button>
            <button class="btn btn-secondary" id="resetQuizBtn">Reset Quiz</button>
        `;
        quizResults.appendChild(quizActions);
        
        // Add event listeners to buttons
        document.getElementById('checkAnswersBtn').addEventListener('click', checkAllAnswers);
        document.getElementById('resetQuizBtn').addEventListener('click', resetQuiz);
        document.getElementById('openFullscreenQuiz').addEventListener('click', openFullscreenQuiz);
        
        // Refresh icons
        feather.replace();
    } else {
        quizResults.innerHTML = '<p>No questions were generated. Please try again with different settings.</p>';
    }
}

function openFullscreenQuiz() {
    if (!currentQuiz || !currentQuiz.questions) return;
    
    // Reset quiz state
    currentQuestionIndex = 0;
    userAnswers = {};
    timeElapsed = 0;
    timePerQuestion = parseInt(document.getElementById('timePerQuestion').value) || 0;
    
    // Update modal display
    totalQuestions.textContent = currentQuiz.questions.length;
    updateQuestionDisplay();
    
    // Show modal
    quizModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Start overall quiz timer
    startQuizTimer();
    
    // Start question timer if enabled
    if (timePerQuestion > 0) {
        startQuestionTimer();
    }
    
    // Refresh icons
    feather.replace();
}

function closeQuizModal() {
    quizModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Stop all timers
    stopQuizTimer();
    stopQuestionTimer();
}
// Add auto-progress toggle (optional feature)
function toggleAutoProgress() {
    autoProgressEnabled = !autoProgressEnabled;
    return autoProgressEnabled;
}

function startQuizTimer() {
    stopQuizTimer(); // Clear any existing timer
    
    quizTimer = setInterval(() => {
        timeElapsed++;
        updateTimerDisplay();
    }, 1000);
}

// Add question timer functions
function startQuestionTimer() {
    stopQuestionTimer(); // Clear any existing timer
    
    timeRemaining = timePerQuestion;
    updateQuestionTimerDisplay();
    
    questionTimer = setInterval(() => {
        timeRemaining--;
        updateQuestionTimerDisplay();
        
        if (timeRemaining <= 0) {
            handleTimeUp();
        }
    }, 1000);
}




function handleTimeUp() {
    stopQuestionTimer();
    
    const currentQuestion = currentQuiz.questions[currentQuestionIndex];
    
    // If no answer selected, mark as unanswered and auto-progress
    if (!userAnswers[currentQuestionIndex]) {
        userAnswers[currentQuestionIndex] = 'unanswered';
        
        // Show time up message
        const timeUpMessage = document.createElement('div');
        timeUpMessage.className = 'time-up-message';
        timeUpMessage.innerHTML = `
            <strong>Time's up!</strong> 
            ${autoProgressEnabled ? 'Moving to next question...' : 'Please select an answer to continue.'}
        `;
        
        const questionContainer = quizModalBody.querySelector('.single-question-view');
        if (questionContainer) {
            questionContainer.appendChild(timeUpMessage);
        }
        
        // Auto-progress to next question if enabled
        if (autoProgressEnabled) {
            setTimeout(() => {
                if (currentQuestionIndex < currentQuiz.questions.length - 1) {
                    showNextQuestion();
                } else {
                    submitQuiz();
                }
            }, 2000);
        }
    }
    
    // Update display to show feedback
    updateQuestionDisplay();
}

function stopQuizTimer() {
    if (quizTimer) {
        clearInterval(quizTimer);
        quizTimer = null;
    }
}

function updateQuestionTimerDisplay() {
    const timerDisplay = document.getElementById('questionTimerDisplay');
    if (!timerDisplay) return;
    
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    // Update styling based on time remaining
    timerDisplay.className = 'timer-display';
    if (timeRemaining <= 10) {
        timerDisplay.classList.add('danger');
    } else if (timeRemaining <= 30) {
        timerDisplay.classList.add('warning');
    }
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeElapsed / 60);
    const seconds = timeElapsed % 60;
    quizTimerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    // Add warning styles based on time
    quizTimerDisplay.className = 'quiz-timer';
    if (timeElapsed > 300) { // 5 minutes
        quizTimerDisplay.classList.add('warning');
    }
    if (timeElapsed > 600) { // 10 minutes
        quizTimerDisplay.classList.add('danger');
    }
}

function updateQuestionDisplay() {
    if (!currentQuiz || !currentQuiz.questions) return;
    
    const question = currentQuiz.questions[currentQuestionIndex];
    currentQuestionNumber.textContent = currentQuestionIndex + 1;
    
    // Stop previous question timer
    stopQuestionTimer();
    
    let questionHTML = '';
    
    // Add timer display if time per question is set
    if (timePerQuestion > 0) {
        questionHTML += `
            <div class="question-timer">
                <div class="timer-label">Time remaining:</div>
                <div class="timer-display" id="questionTimerDisplay">
                    ${Math.floor(timePerQuestion / 60).toString().padStart(2, '0')}:${(timePerQuestion % 60).toString().padStart(2, '0')}
                </div>
            </div>
            ${autoProgressEnabled ? '<div class="auto-progress-notice">⚠️ Will auto-progress to next question when time is up</div>' : ''}
        `;
    }
    
    questionHTML += `
        <div class="single-question-view">
            <div class="question-header">
                <div class="question-text-large">${question.id}. ${question.question}</div>
            </div>
            
            <div class="options-large">
    `;
    
    // MCQ options
    if (question.type === 'mcq' && question.options) {
        for (const [key, value] of Object.entries(question.options)) {
            const isSelected = userAnswers[currentQuestionIndex] === key;
            questionHTML += `
                <div class="option-large ${isSelected ? 'selected' : ''}" 
                     data-question="${currentQuestionIndex}" 
                     data-option="${key}">
                    ${key}. ${value}
                </div>
            `;
        }
    }
    
    questionHTML += `
            </div>
    `;
    
    // Feedback
    const userAnswer = userAnswers[currentQuestionIndex];
    if (userAnswer && userAnswer !== 'unanswered') {
        const isCorrect = userAnswer === question.correct_answer;
        questionHTML += `
            <div class="feedback-large ${isCorrect ? 'correct' : 'incorrect'}">
                ${isCorrect ? '✓ Correct!' : `✗ Incorrect. The correct answer is ${question.correct_answer}.`}
            </div>
        `;
        
        // Explanation
        if (question.explanation) {
            questionHTML += `<div class="explanation-large">${question.explanation}</div>`;
        }
    } else if (userAnswer === 'unanswered') {
        questionHTML += `
            <div class="feedback-large incorrect">
                ⏰ Time's up! The correct answer was ${question.correct_answer}.
            </div>
        `;
        if (question.explanation) {
            questionHTML += `<div class="explanation-large">${question.explanation}</div>`;
        }
    }
    
    // Slide reference
    if (question.slide_number) {
        questionHTML += `<div class="slide-reference-large">Based on Slide ${question.slide_number}</div>`;
    }
    
    questionHTML += `</div>`;
    
    quizModalBody.innerHTML = questionHTML;
    
    // Add event listeners to options
    const options = quizModalBody.querySelectorAll('.option-large');
    options.forEach(option => {
        option.addEventListener('click', handleFullscreenOptionClick);
    });
    
    // Update navigation buttons
    updateNavigationButtons();
    
    // Start timer for this question if time per question is set
    if (timePerQuestion > 0 && (!userAnswer || userAnswer === 'unanswered')) {
        startQuestionTimer();
    }
    
    // Refresh icons
    feather.replace();
}

function stopQuestionTimer() {
    if (questionTimer) {
        clearInterval(questionTimer);
        questionTimer = null;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadAvailablePresentations();
    initTabs();
    
    // Add auto-progress checkbox event listener
    const autoProgressCheckbox = document.getElementById('autoProgress');
    if (autoProgressCheckbox) {
        autoProgressCheckbox.addEventListener('change', function() {
            autoProgressEnabled = this.checked;
        });
    }
});

function handleFullscreenOptionClick(event) {
    const option = event.currentTarget;
    const questionIndex = parseInt(option.getAttribute('data-question'));
    const optionKey = option.getAttribute('data-option');
    
    // Stop the timer when an answer is selected
    stopQuestionTimer();
    
    // Clear previous selection for this question
    const options = quizModalBody.querySelectorAll('.option-large');
    options.forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Select this option
    option.classList.add('selected');
    
    // Store user's answer
    userAnswers[questionIndex] = optionKey;
    
    // Update display to show feedback
    updateQuestionDisplay();
}

function updateNavigationButtons() {
    prevQuestionBtn.disabled = currentQuestionIndex === 0;
    
    if (currentQuestionIndex === currentQuiz.questions.length - 1) {
        nextQuestionBtn.style.display = 'none';
        submitQuizBtn.style.display = 'block';
    } else {
        nextQuestionBtn.style.display = 'block';
        submitQuizBtn.style.display = 'none';
    }
}

function showPreviousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        updateQuestionDisplay();
    }
}

function showNextQuestion() {
    if (currentQuiz && currentQuestionIndex < currentQuiz.questions.length - 1) {
        currentQuestionIndex++;
        updateQuestionDisplay();
    }
}

function submitQuiz() {
    // Stop all timers
    stopQuizTimer();
    stopQuestionTimer();
    
    // Calculate score
    let score = 0;
    let totalAnswered = 0;
    
    currentQuiz.questions.forEach((question, index) => {
        const userAnswer = userAnswers[index];
        if (userAnswer && userAnswer !== 'unanswered') {
            totalAnswered++;
            if (userAnswer === question.correct_answer) {
                score++;
            }
        }
    });
    
    // Show results
    const timeSpent = `${Math.floor(timeElapsed / 60)}:${(timeElapsed % 60).toString().padStart(2, '0')}`;
    const completionRate = Math.round((totalAnswered / currentQuiz.questions.length) * 100);
    
    quizModalBody.innerHTML = `
        <div class="single-question-view" style="text-align: center;">
            <h2>Quiz Completed!</h2>
            <div style="font-size: 1.5rem; margin: 20px 0;">
                Your Score: <strong>${score}/${currentQuiz.questions.length}</strong>
            </div>
            <div style="font-size: 1.1rem; margin: 10px 0;">
                Questions Answered: ${totalAnswered}/${currentQuiz.questions.length} (${completionRate}%)
            </div>
            <div style="font-size: 1.1rem; margin: 10px 0;">
                Time Spent: ${timeSpent}
            </div>
            ${timePerQuestion > 0 ? `<div style="font-size: 1rem; margin: 10px 0; color: var(--text-secondary);">
                Time per question: ${timePerQuestion} seconds
            </div>` : ''}
            <div style="margin: 20px 0;">
                <button class="btn btn-secondary" id="reviewQuizBtn">Review Answers</button>
                <button class="btn" id="closeQuizBtn">Close Quiz</button>
            </div>
        </div>
    `;
    
    document.getElementById('reviewQuizBtn').addEventListener('click', () => {
        currentQuestionIndex = 0;
        updateQuestionDisplay();
    });
    
    document.getElementById('closeQuizBtn').addEventListener('click', closeQuizModal);
    
    // Hide navigation buttons
    prevQuestionBtn.style.display = 'none';
    nextQuestionBtn.style.display = 'none';
    submitQuizBtn.style.display = 'none';
}

function handleOptionClick(event) {
    const option = event.currentTarget;
    const questionIndex = option.getAttribute('data-question');
    const optionKey = option.getAttribute('data-option');
    
    // Clear previous selection for this question
    const questionEl = document.getElementById(`question-${questionIndex}`);
    const options = questionEl.querySelectorAll('.option');
    options.forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Select this option
    option.classList.add('selected');
    
    // Store user's answer
    userAnswers[questionIndex] = optionKey;
    
    // Hide any previous feedback
    const feedbackEl = document.getElementById(`feedback-${questionIndex}`);
    feedbackEl.style.display = 'none';
    feedbackEl.className = 'feedback';
    
    // Hide explanation
    const explanationEl = document.getElementById(`explanation-${questionIndex}`);
    if (explanationEl) {
        explanationEl.style.display = 'none';
    }
}

function checkAllAnswers() {
    if (!currentQuiz || !currentQuiz.questions) return;
    
    let score = 0;
    
    currentQuiz.questions.forEach((question, index) => {
        const userAnswer = userAnswers[index];
        const correctAnswer = question.correct_answer;
        const feedbackEl = document.getElementById(`feedback-${index}`);
        const explanationEl = document.getElementById(`explanation-${index}`);
        
        // Clear previous styling
        const questionEl = document.getElementById(`question-${index}`);
        const options = questionEl.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('correct', 'incorrect');
        });
        
        if (userAnswer) {
            // Mark correct answer
            const correctOption = questionEl.querySelector(`.option[data-option="${correctAnswer}"]`);
            if (correctOption) {
                correctOption.classList.add('correct');
            }
            
            // Check if user's answer is correct
            if (userAnswer === correctAnswer) {
                score++;
                feedbackEl.textContent = 'Correct!';
                feedbackEl.className = 'feedback correct';
            } else {
                // Mark incorrect answer
                const userOption = questionEl.querySelector(`.option[data-option="${userAnswer}"]`);
                if (userOption) {
                    userOption.classList.add('incorrect');
                }
                
                feedbackEl.textContent = `Incorrect. The correct answer is ${correctAnswer}.`;
                feedbackEl.className = 'feedback incorrect';
            }
            
            // Show explanation if available
            if (explanationEl) {
                explanationEl.style.display = 'block';
            }
            
            feedbackEl.style.display = 'block';
        } else {
            feedbackEl.textContent = 'Please select an answer.';
            feedbackEl.className = 'feedback incorrect';
            feedbackEl.style.display = 'block';
        }
    });
    
    // Update score
    document.getElementById('quizScore').textContent = score;
}

function resetQuiz() {
    if (!currentQuiz || !currentQuiz.questions) return;
    
    userAnswers = {};
    
    currentQuiz.questions.forEach((question, index) => {
        const questionEl = document.getElementById(`question-${index}`);
        const options = questionEl.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected', 'correct', 'incorrect');
        });
        
        const feedbackEl = document.getElementById(`feedback-${index}`);
        feedbackEl.style.display = 'none';
        
        const explanationEl = document.getElementById(`explanation-${index}`);
        if (explanationEl) {
            explanationEl.style.display = 'none';
        }
    });
    
    // Reset score
    document.getElementById('quizScore').textContent = '0';
}

function showUploadLoading() {
    uploadLoading.style.display = 'block';
    uploadBtn.disabled = true;
}

function hideUploadLoading() {
    uploadLoading.style.display = 'none';
    uploadBtn.disabled = false;
}

function showQuizLoading() {
    quizLoading.style.display = 'block';
    generateQuizBtn.disabled = true;
    generateQuizBtn.innerHTML = '<div class="spinner-small"></div> Generating...';
}   

function hideQuizLoading() {
    quizLoading.style.display = 'none';
    generateQuizBtn.disabled = false;
    generateQuizBtn.innerHTML = '<i data-feather="help-circle"></i> Generate Quiz';
    feather.replace();
}


function showExplanationLoading() {
    explanationLoading.style.display = 'block';
    generateExplanationBtn.disabled = true;
    generateExplanationBtn.innerHTML = '<div class="spinner-small"></div> Generating...';
}
function hideExplanationLoading() {
    explanationLoading.style.display = 'none';
    generateExplanationBtn.disabled = false;
    generateExplanationBtn.innerHTML = '<i data-feather="book-open"></i> Generate Explanation';
    feather.replace();
}
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
}


function hideSuccess() {
    successMessage.style.display = 'none';
}

function refreshBackendStatus() {
    checkBackendStatus();
    if (cognitiveLoadSocket && cognitiveLoadSocket.readyState === WebSocket.OPEN) {
        cognitiveLoadSocket.send(JSON.stringify({ type: 'status_request' }));
    }
}

// Refresh icons when needed
feather.replace();