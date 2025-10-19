// Initialize Feather Icons
feather.replace();

// Presentation state
let currentSlide = 0;
let slides = [];
let isPresentationMode = false;
let isEditMode = false;
let currentFilename = '';
let driveViewUrl = '';

// API base URL
const API_BASE = 'http://localhost:8000';

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const uploadSection = document.getElementById('uploadSection');
const presentationView = document.getElementById('presentationView');
const currentSlideElement = document.getElementById('currentSlide');
const slideCounter = document.getElementById('slideCounter');
const slidePreviews = document.getElementById('slidePreviews');
const editModal = document.getElementById('editModal');
const driveIframe = document.getElementById('driveIframe');
const presentBtn = document.getElementById('presentBtn');

// Assistant tabs
const guideTab = document.getElementById('guideTab');
const quizTab = document.getElementById('quizTab');
const chatTab = document.getElementById('chatTab');
const guideContent = document.getElementById('guideContent');
const quizContent = document.getElementById('quizContent');
const chatContent = document.getElementById('chatContent');

// View mode toggle
let currentViewMode = 'drive'; // Default to drive view

// Event Listeners
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dropzone-active');
});
dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dropzone-active');
});
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dropzone-active');
    if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
    }
});
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFiles(fileInput.files);
    }
});

// Tab switching
guideTab.addEventListener('click', () => switchTab('guide'));
quizTab.addEventListener('click', () => switchTab('quiz'));
chatTab.addEventListener('click', () => switchTab('chat'));

// Chat functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    
    if (chatInput && chatSendBtn) {
        chatSendBtn.addEventListener('click', sendChatMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});

// Functions
async function handleFiles(files) {
    const file = files[0];
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pptx') && !file.name.toLowerCase().endsWith('.ppt')) {
        alert('Please upload a PPT or PPTX file');
        return;
    }

    // Show loading state
    dropzone.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12">
            <i data-feather="loader" class="w-16 h-16 text-indigo-400 mb-4 animate-spin"></i>
            <h3 class="text-xl font-medium text-gray-200 mb-2">Uploading Presentation...</h3>
            <p class="text-gray-400">Please wait while we process your file</p>
        </div>
    `;
    feather.replace();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload-ppt`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            slides = data.slides || [];
            currentFilename = data.filename;
            
            // Enable presentation button
            presentBtn.disabled = false;
            presentBtn.classList.remove('opacity-50');
            presentBtn.onclick = startFullPresentationMode;
            
            // Show success and open presentation view immediately
            showNotification('Presentation uploaded successfully!', 'success');
            openPresentationView();
            
        } else {
            throw new Error('Failed to upload presentation');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showNotification('Error uploading presentation. Showing demo mode.', 'error');
        
        // Even on error, open presentation view with demo content
        slides = generateDemoSlides();
        currentFilename = 'demo-presentation.pptx';
        presentBtn.disabled = false;
        presentBtn.classList.remove('opacity-50');
        presentBtn.onclick = startFullPresentationMode;
        
        openPresentationView();
    }
}

function generateDemoSlides() {
    return [
        {
            title: "Welcome to SlideSense",
            content: "# Welcome to SlideSense\n\n## AI-Powered Presentation Assistant\n\n• Upload your PPT files\n• Get real-time AI assistance\n• Generate interactive quizzes\n• Present with confidence",
            notes: "Welcome your audience and introduce the SlideSense platform."
        },
        {
            title: "Features Overview",
            content: "## Key Features\n\n• AI Presentation Assistant\n• Real-time Quiz Generation\n• Content Analysis\n• Speaker Notes\n• Interactive Chat",
            notes: "Highlight the main features of the platform."
        },
        {
            title: "Get Started",
            content: "## How to Use\n\n1. Upload your presentation\n2. View in Drive or Content mode\n3. Use AI assistant for guidance\n4. Generate quizzes for engagement\n5. Present with confidence",
            notes: "Explain the simple workflow to users."
        }
    ];
}

function openPresentationView() {
    // Hide upload section and show presentation view
    uploadSection.classList.add('hidden');
    presentationView.classList.remove('hidden');
    
    // Start with drive view by default
    switchToDriveView();
    
    // Set up basic keyboard navigation
    document.addEventListener('keydown', handleKeyPress);
}

function startFullPresentationMode() {
    isPresentationMode = true;
    
    // Update UI for full presentation mode
    document.getElementById('viewModeToggle').classList.add('hidden');
    document.querySelector('.absolute.bottom-8').classList.add('hidden');
    
    // Enter fullscreen if supported
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    }
    
    // Set up enhanced keyboard navigation for presentation
    document.removeEventListener('keydown', handleKeyPress);
    document.addEventListener('keydown', handlePresentationKeyPress);
    
    showNotification('Presentation mode started. Press ESC to exit.', 'success');
}

function exitFullPresentationMode() {
    isPresentationMode = false;
    
    // Restore UI elements
    document.getElementById('viewModeToggle').classList.remove('hidden');
    document.querySelector('.absolute.bottom-8').classList.remove('hidden');
    
    // Exit fullscreen if supported
    if (document.exitFullscreen) {
        document.exitFullscreen();
    }
    
    // Restore normal keyboard navigation
    document.removeEventListener('keydown', handlePresentationKeyPress);
    document.addEventListener('keydown', handleKeyPress);
    
    showNotification('Presentation mode exited.', 'info');
}

// View mode switching
function switchToDriveView() {
    currentViewMode = 'drive';
    
    // Hide content view, show drive view
    currentSlideElement.classList.add('hidden');
    driveIframe.classList.remove('hidden');
    
    // Load the presentation file in the iframe
    if (currentFilename && currentFilename !== 'demo-presentation.pptx') {
        const fileUrl = `${API_BASE}/static/uploads/${currentFilename}`;
        driveIframe.src = `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(fileUrl)}`;
    } else {
        // Fallback to demo or error message
        driveIframe.srcdoc = `
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        height: 100vh; 
                        margin: 0; 
                        background: #1f2937; 
                        color: white; 
                        font-family: Arial, sans-serif;
                    }
                    .content { text-align: center; padding: 2rem; }
                </style>
            </head>
            <body>
                <div class="content">
                    <h2>Presentation Ready</h2>
                    <p>Your presentation will be displayed here.</p>
                    <p>Switch to Content View to see slide details.</p>
                </div>
            </body>
            </html>
        `;
    }
    
    // Update view mode buttons
    updateViewModeButtons();
    
    slideCounter.textContent = `Drive View - ${currentFilename || 'Demo Presentation'}`;
}

function switchToContentView() {
    currentViewMode = 'content';
    
    // Hide drive view, show content view
    driveIframe.classList.add('hidden');
    currentSlideElement.classList.remove('hidden');
    
    // Show the current slide content
    if (slides.length > 0) {
        showSlide(currentSlide);
    } else {
        showDriveFallbackContent();
    }
    
    // Update view mode buttons
    updateViewModeButtons();
}

function updateViewModeButtons() {
    const contentBtn = document.getElementById('contentViewBtn');
    const driveBtn = document.getElementById('driveViewBtn');
    
    if (contentBtn && driveBtn) {
        if (currentViewMode === 'content') {
            contentBtn.classList.add('bg-indigo-600', 'text-white');
            contentBtn.classList.remove('bg-gray-600', 'text-gray-300');
            driveBtn.classList.add('bg-gray-600', 'text-gray-300');
            driveBtn.classList.remove('bg-indigo-600', 'text-white');
        } else {
            driveBtn.classList.add('bg-indigo-600', 'text-white');
            driveBtn.classList.remove('bg-gray-600', 'text-gray-300');
            contentBtn.classList.add('bg-gray-600', 'text-gray-300');
            contentBtn.classList.remove('bg-indigo-600', 'text-white');
        }
    }
}

function showDriveFallbackContent() {
    currentSlideElement.innerHTML = `
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 text-white p-8 rounded-lg max-w-4xl mx-auto shadow-2xl text-center h-full flex items-center justify-center">
            <div>
                <i data-feather="file" class="w-16 h-16 text-indigo-400 mx-auto mb-4"></i>
                <h2 class="text-3xl font-bold mb-4">Presentation Loaded</h2>
                <p class="text-gray-300 mb-6">Switch to Drive View to see your presentation.</p>
                <div class="space-y-4">
                    <button onclick="switchToDriveView()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium transition">
                        Switch to Drive View
                    </button>
                </div>
            </div>
        </div>
    `;
    feather.replace();
}

async function showSlide(index) {
    if (index < 0 || index >= slides.length) return;
    
    currentSlide = index;
    const slide = slides[currentSlide];
    
    // Create clean slide display with extracted content
    currentSlideElement.innerHTML = `
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 text-white p-8 rounded-lg max-w-4xl mx-auto shadow-2xl h-full overflow-auto">
            <div class="text-center mb-8">
                <div class="inline-block bg-indigo-600 text-white px-4 py-1 rounded-full text-sm mb-4">
                    Slide ${currentSlide + 1} of ${slides.length}
                </div>
                <h1 class="text-4xl font-bold mb-6 text-white">${slide.title || `Slide ${currentSlide + 1}`}</h1>
            </div>
            
            <div class="prose prose-lg max-w-none prose-invert">
                ${formatSlideContent(slide.content)}
            </div>
            
            ${slide.notes ? `
                <div class="mt-8 p-6 bg-yellow-500 bg-opacity-10 border-l-4 border-yellow-400 rounded-r-lg">
                    <h4 class="font-bold text-yellow-300 mb-3 text-lg">💡 Speaker Notes</h4>
                    <p class="text-gray-200 leading-relaxed">${slide.notes}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    slideCounter.textContent = `Slide ${currentSlide + 1} of ${slides.length} (Content View)`;
    
    // Update AI assistant content based on current slide
    await updateAssistantContent();
}

function formatSlideContent(content) {
    if (!content) return '<p class="text-gray-400 text-center">No content available for this slide</p>';
    
    const lines = content.split('\n').filter(line => line.trim());
    let html = '';
    
    lines.forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('# ')) {
            html += `<h2 class="text-3xl font-bold mb-4 text-white">${trimmedLine.substring(2)}</h2>`;
        } else if (trimmedLine.startsWith('## ')) {
            html += `<h3 class="text-2xl font-semibold mb-3 text-white">${trimmedLine.substring(3)}</h3>`;
        } else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
            if (!html.includes('<ul class="my-4">')) {
                html += '<ul class="my-4 space-y-2">';
            }
            html += `<li class="flex items-start">
                <span class="text-indigo-400 mr-3 mt-1">•</span>
                <span>${trimmedLine.substring(2)}</span>
            </li>`;
        } else {
            // Close ul if it was open
            if (html.includes('<ul class="my-4">') && !html.includes('</ul>')) {
                html += '</ul>';
            }
            html += `<p class="mb-4 text-gray-200 leading-relaxed">${trimmedLine}</p>`;
        }
    });
    
    // Close ul if still open
    if (html.includes('<ul class="my-4">') && !html.includes('</ul>')) {
        html += '</ul>';
    }
    
    return html;
}

function nextSlide() {
    if (currentViewMode === 'content' && slides.length > 0) {
        if (currentSlide < slides.length - 1) {
            showSlide(currentSlide + 1);
        }
    } else if (currentViewMode === 'drive') {
        // In drive view, we can't control slide navigation directly
        showNotification('Use presentation mode for slide navigation', 'info');
    }
}

function prevSlide() {
    if (currentViewMode === 'content' && slides.length > 0) {
        if (currentSlide > 0) {
            showSlide(currentSlide - 1);
        }
    } else if (currentViewMode === 'drive') {
        // In drive view, we can't control slide navigation directly
        showNotification('Use presentation mode for slide navigation', 'info');
    }
}

function handleKeyPress(e) {
    switch(e.key) {
        case 'ArrowRight':
        case ' ':
            e.preventDefault();
            nextSlide();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            prevSlide();
            break;
        case '1':
            e.preventDefault();
            switchToContentView();
            break;
        case '2':
            e.preventDefault();
            switchToDriveView();
            break;
    }
}

function handlePresentationKeyPress(e) {
    switch(e.key) {
        case 'ArrowRight':
        case ' ':
            e.preventDefault();
            nextSlide();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            prevSlide();
            break;
        case 'Escape':
            exitFullPresentationMode();
            break;
        case '1':
            e.preventDefault();
            switchToContentView();
            break;
        case '2':
            e.preventDefault();
            switchToDriveView();
            break;
    }
}

function switchTab(tab) {
    // Reset all tabs
    guideTab.classList.remove('text-gray-400', 'border-indigo-500', 'border-b-2');
    quizTab.classList.remove('text-gray-400', 'border-indigo-500', 'border-b-2');
    chatTab.classList.remove('text-gray-400', 'border-indigo-500', 'border-b-2');
    
    // Hide all contents
    guideContent.classList.add('hidden');
    quizContent.classList.add('hidden');
    chatContent.classList.add('hidden');
    
    // Activate selected tab
    switch(tab) {
        case 'guide':
            guideTab.classList.add('border-indigo-500', 'border-b-2');
            guideContent.classList.remove('hidden');
            break;
        case 'quiz':
            quizTab.classList.add('border-indigo-500', 'border-b-2');
            quizContent.classList.remove('hidden');
            loadQuizContent();
            break;
        case 'chat':
            chatTab.classList.add('border-indigo-500', 'border-b-2');
            chatContent.classList.remove('hidden');
            break;
    }
}

async function updateAssistantContent() {
    const slide = slides[currentSlide];
    const guideTips = guideContent.querySelector('.ai-response');
    
    if (guideTips) {
        const wordCount = slide.content ? slide.content.split(/\s+/).length : 0;
        const mainPoints = slide.content ? slide.content.split('\n').filter(line => line.trim()).slice(0, 3) : [];
        
        guideTips.innerHTML = `
            <div class="space-y-3">
                <div class="bg-gray-800 rounded-lg p-4">
                    <h4 class="font-semibold text-indigo-400 mb-2">📊 Slide Overview</h4>
                    <p class="text-sm">This slide contains approximately <strong>${wordCount} words</strong>.</p>
                </div>
                
                ${mainPoints.length > 0 ? `
                <div class="bg-gray-800 rounded-lg p-4">
                    <h4 class="font-semibold text-indigo-400 mb-2">🎯 Key Points</h4>
                    <ul class="text-sm space-y-1">
                        ${mainPoints.map(point => `<li class="flex items-start">
                            <span class="text-green-400 mr-2 mt-1">•</span>
                            <span>${point.substring(0, 80)}${point.length > 80 ? '...' : ''}</span>
                        </li>`).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${slide.notes ? `
                <div class="bg-gray-800 rounded-lg p-4">
                    <h4 class="font-semibold text-indigo-400 mb-2">💡 Speaker Notes</h4>
                    <p class="text-sm">${slide.notes}</p>
                </div>
                ` : ''}
            </div>
        `;
    }
}

// Main quiz loading function - called when user clicks quiz tab
async function loadQuizContent() {
    const quizContainer = quizContent.querySelector('.ai-response');
    if (!quizContainer) return;
    
    // Show loading state
    quizContainer.innerHTML = `
        <div class="text-center py-8">
            <i data-feather="loader" class="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-spin"></i>
            <h3 class="text-lg font-medium text-gray-200 mb-2">Generating Quiz Questions...</h3>
            <p class="text-gray-400">Analyzing your presentation content</p>
        </div>
    `;
    feather.replace();
    
    try {
        let quizData;
        
        if (currentFilename && currentFilename !== 'demo-presentation.pptx') {
            // Try POST request first with the actual uploaded presentation
            quizData = await generateQuizFromPresentation();
        } else {
            // Use demo content with text-based generation
            quizData = await generateQuizFromDemoContent();
        }
        
        if (quizData && quizData.questions) {
            renderQuizQuestions(quizData.questions);
        } else {
            throw new Error('No quiz questions generated');
        }
        
    } catch (error) {
        console.error('Error loading quiz:', error);
        // Show demo questions as fallback
        showDemoQuizQuestions();
    }
}

// Generate quiz from actual uploaded presentation - SIMPLIFIED
async function generateQuizFromPresentation() {
    console.log('Generating quiz for:', currentFilename);
    
    // Try POST request first
    try {
        const response = await fetch(`${API_BASE}/generate-quiz/${currentFilename}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                num_questions: 5,
                question_types: ["mcq"]
            })
        });
        
        if (response.ok) {
            return await response.json();
        }
    } catch (postError) {
        console.log('POST request failed, trying GET:', postError);
    }
    
    // If POST fails, try GET request
    try {
        const response = await fetch(`${API_BASE}/generate-quiz/${currentFilename}?num_questions=5`);
        if (response.ok) {
            return await response.json();
        }
    } catch (getError) {
        console.log('GET request also failed:', getError);
    }
    
    // If both fail, try text-based generation
    try {
        const allContent = slides.map(slide => slide.content).join('\n\n');
        const response = await fetch(`${API_BASE}/generate-quiz-from-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: allContent,
                num_questions: 5,
                question_types: ["mcq"]
            })
        });
        
        if (response.ok) {
            return await response.json();
        }
    } catch (textError) {
        console.log('Text-based generation failed:', textError);
    }
    
    throw new Error('All quiz generation methods failed');
}

// Generate quiz from demo content
async function generateQuizFromDemoContent() {
    const demoContent = slides.map(slide => slide.content).join('\n\n');
    const response = await fetch(`${API_BASE}/generate-quiz-from-text`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: demoContent,
            num_questions: 5,
            question_types: ["mcq"]
        })
    });
    
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
}

// Fallback to demo questions
function showDemoQuizQuestions() {
    const quizContainer = quizContent.querySelector('.ai-response');
    if (!quizContainer) return;
    
    const demoQuestions = [
        {
            question: "What is the main purpose of SlideSense?",
            options: [
                "To create presentations from scratch",
                "To provide AI-powered presentation assistance", 
                "To replace PowerPoint completely",
                "To generate images for slides"
            ],
            explanation: "SlideSense provides AI-powered assistance for your existing presentations, including quiz generation and real-time help."
        },
        {
            question: "Which feature helps test audience understanding?",
            options: [
                "AI Chat Assistant",
                "Interactive Quiz Generation",
                "Slide Thumbnails", 
                "Presentation Mode"
            ],
            explanation: "The interactive quiz generation feature creates questions based on your presentation content to test audience comprehension."
        },
        {
            question: "What file formats does SlideSense support?",
            options: [
                "Only PDF files",
                "Only Google Slides", 
                "PPT and PPTX files",
                "All image formats"
            ],
            explanation: "SlideSense currently supports PowerPoint files in PPT and PPTX formats for processing and analysis."
        }
    ];
    
    renderQuizQuestions(demoQuestions);
}

function renderQuizQuestions(questions) {
    const quizContainer = quizContent.querySelector('.ai-response');
    if (!quizContainer) return;
    
    quizContainer.innerHTML = '';
    
    if (!questions || questions.length === 0) {
        quizContainer.innerHTML = `
            <div class="text-center py-8">
                <i data-feather="help-circle" class="w-12 h-12 text-gray-400 mx-auto mb-4"></i>
                <p class="text-gray-400">No quiz questions available at the moment.</p>
                <button onclick="loadQuizContent()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm transition mt-4">
                    Try Again
                </button>
            </div>
        `;
        feather.replace();
        return;
    }
    
    questions.forEach((q, index) => {
        const questionElement = document.createElement('div');
        questionElement.className = 'bg-gray-800 rounded-lg p-4 mb-4';
        questionElement.innerHTML = `
            <h5 class="font-medium mb-3 text-white">Question ${index + 1}: ${q.question}</h5>
            <div class="space-y-2">
                ${(q.options || []).map((option, optIndex) => `
                    <div class="flex items-center p-2 hover:bg-gray-700 rounded cursor-pointer">
                        <input type="radio" id="q${index}_${optIndex}" name="q${index}" class="mr-3" value="${optIndex}">
                        <label for="q${index}_${optIndex}" class="text-sm text-gray-200 flex-1 cursor-pointer">${option}</label>
                    </div>
                `).join('')}
            </div>
            ${q.explanation ? `
                <div class="mt-3 p-3 bg-gray-700 rounded-lg text-sm text-gray-300">
                    <strong>Explanation:</strong> ${q.explanation}
                </div>
            ` : ''}
        `;
        quizContainer.appendChild(questionElement);
    });
    
    // Add generate more button
    const generateButton = document.createElement('button');
    generateButton.className = 'bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm transition mt-4 w-full';
    generateButton.textContent = 'Generate More Questions';
    generateButton.onclick = loadQuizContent;
    quizContainer.appendChild(generateButton);
    
    feather.replace();
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput?.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage('user', message);
    chatInput.value = '';
    
    try {
        // Send message to backend for AI response
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                slide_index: currentSlide,
                filename: currentFilename
            })
        });
        
        const data = await response.json();
        addChatMessage('ai', data.response || 'I cannot answer that right now.');
    } catch (error) {
        console.error('Error sending chat message:', error);
        addChatMessage('ai', 'I\'m here to help with your presentation! Ask me about slide content, presentation tips, or generate quiz questions.');
    }
}

function addChatMessage(sender, message) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageElement = document.createElement('div');
    
    messageElement.className = sender === 'user' 
        ? 'bg-indigo-600 rounded-lg p-4 mb-3 ml-8'
        : 'bg-gray-700 rounded-lg p-4 mb-3';
    
    messageElement.innerHTML = `
        <div class="flex items-start mb-2">
            <div class="flex-shrink-0 mr-3">
                <div class="${sender === 'user' ? 'bg-white' : 'bg-indigo-500'} rounded-full w-8 h-8 flex items-center justify-center">
                    <i data-feather="${sender === 'user' ? 'user' : 'zap'}" class="w-4 h-4 ${sender === 'user' ? 'text-indigo-600' : 'text-white'}"></i>
                </div>
            </div>
            <div>
                <h4 class="font-medium text-white">${sender === 'user' ? 'You' : 'AI Assistant'}</h4>
            </div>
        </div>
        <div class="pl-11">
            <p class="text-gray-200">${message}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    feather.replace();
}

// Utility function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-600' : 
        type === 'error' ? 'bg-red-600' : 'bg-indigo-600'
    } text-white`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i data-feather="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}" class="w-5 h-5 mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    feather.replace();
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Exit presentation mode when clicking the exit button
function exitPresentationMode() {
    if (isPresentationMode) {
        exitFullPresentationMode();
    } else {
        presentationView.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        document.removeEventListener('keydown', handleKeyPress);
    }
}