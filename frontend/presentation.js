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

// Event Listeners
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
            
            // Enable quiz generation
            generateQuizBtn.disabled = false;
            
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

// Functions
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
            await loadAvailablePresentations();
            await selectPresentation(data.filename);
        } else {
            showError(data.detail || 'Failed to upload presentation');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideUploadLoading();
    }
}

async function loadAvailablePresentations() {
    try {
        const response = await fetch(`${API_BASE_URL}/available-presentations`);
        const data = await response.json();
        
        if (response.ok) {
            availablePresentations = data.presentations || [];
            renderPresentationList();
            
            if (availablePresentations.length > 0) {
                presentationSelector.style.display = 'block';
            } else {
                presentationSelector.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Failed to load presentations:', error);
    }
}

function renderPresentationList() {
    presentationList.innerHTML = '';
    
    if (availablePresentations.length === 0) {
        presentationList.innerHTML = '<div class="presentation-item">No presentations available</div>';
        return;
    }
    
    availablePresentations.forEach(presentation => {
        const item = document.createElement('div');
        item.className = 'presentation-item';
        if (currentPresentation && currentPresentation.filename === presentation.filename) {
            item.classList.add('active');
        }
        item.textContent = presentation.original_name;
        item.addEventListener('click', () => selectPresentation(presentation.filename));
        presentationList.appendChild(item);
    });
}

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
            
            // Show presentation view
            presentationView.style.display = 'block';
            
            // Enable quiz generation
            generateQuizBtn.disabled = false;
            
            // Update presentation list
            renderPresentationList();
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
    
    // Determine which slides to use for quiz generation
    let slideNumbers = [];
    
    if (slideRangeValue === 'current') {
        // Only use the current slide
        slideNumbers = [currentSlideIndex + 1]; // +1 because slides are 1-indexed
    } else if (slideRangeValue === 'previous') {
        // Use all slides up to the current one
        for (let i = 1; i <= currentSlideIndex + 1; i++) {
            slideNumbers.push(i);
        }
    } else {
        // Use all slides
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
    
    // Update modal display
    totalQuestions.textContent = currentQuiz.questions.length;
    updateQuestionDisplay();
    
    // Show modal
    quizModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Start timer
    startQuizTimer();
    
    // Refresh icons
    feather.replace();
}

function closeQuizModal() {
    quizModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Stop timer
    stopQuizTimer();
}

function startQuizTimer() {
    stopQuizTimer(); // Clear any existing timer
    
    quizTimer = setInterval(() => {
        timeElapsed++;
        updateTimerDisplay();
    }, 1000);
}

function stopQuizTimer() {
    if (quizTimer) {
        clearInterval(quizTimer);
        quizTimer = null;
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
    
    let questionHTML = `
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
    if (userAnswer) {
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
    
    // Refresh icons
    feather.replace();
}

function handleFullscreenOptionClick(event) {
    const option = event.currentTarget;
    const questionIndex = parseInt(option.getAttribute('data-question'));
    const optionKey = option.getAttribute('data-option');
    
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
    // Calculate score
    let score = 0;
    currentQuiz.questions.forEach((question, index) => {
        if (userAnswers[index] === question.correct_answer) {
            score++;
        }
    });
    
    // Stop timer
    stopQuizTimer();
    
    // Show results
    const timeSpent = `${Math.floor(timeElapsed / 60)}:${(timeElapsed % 60).toString().padStart(2, '0')}`;
    quizModalBody.innerHTML = `
        <div class="single-question-view" style="text-align: center;">
            <h2>Quiz Completed!</h2>
            <div style="font-size: 1.5rem; margin: 20px 0;">
                Your Score: <strong>${score}/${currentQuiz.questions.length}</strong>
            </div>
            <div style="font-size: 1.1rem; margin: 10px 0;">
                Time Spent: ${timeSpent}
            </div>
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
}

function hideQuizLoading() {
    quizLoading.style.display = 'none';
    generateQuizBtn.disabled = false;
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

// Refresh icons when needed
feather.replace();