// Initialize Feather Icons
feather.replace();

// Presentation state
let currentSlide = 0;
let slides = [];
let isPresentationMode = false;
let isEditMode = false;

// Mock data for demonstration
const mockSlides = [
    {
        title: "Welcome to SlideSense",
        content: "AI-Powered Presentation Assistant\n\n• Real-time AI guidance\n• Interactive quizzes\n• Smart speaker notes\n• Live chat assistance",
        thumbnail: "https://via.placeholder.com/300x200/4f46e5/ffffff?text=Slide+1",
        notes: "Welcome the audience and introduce the key features of SlideSense",
        slide_number: 1
    },
    {
        title: "Key Features",
        content: "Advanced Presentation Features\n\n• AI-powered real-time assistance\n• Automatic slide processing\n• Interactive audience engagement\n• Smart content suggestions\n• Cross-platform compatibility",
        thumbnail: "https://via.placeholder.com/300x200/059669/ffffff?text=Slide+2",
        notes: "Highlight the main features and benefits for presenters",
        slide_number: 2
    },
    {
        title: "AI Assistant",
        content: "Smart Presentation Support\n\n• Real-time speaking tips\n• Audience engagement suggestions\n• Content explanations\n• Time management alerts\n• Q&A preparation",
        thumbnail: "https://via.placeholder.com/300x200/dc2626/ffffff?text=Slide+3",
        notes: "Explain how the AI assistant helps during presentations",
        slide_number: 3
    },
    {
        title: "Get Started",
        content: "Start Creating Amazing Presentations\n\n1. Upload your slides\n2. Get AI-powered insights\n3. Engage your audience\n4. Present with confidence\n\nReady to begin?",
        thumbnail: "https://via.placeholder.com/300x200/7c3aed/ffffff?text=Slide+4",
        notes: "Encourage users to start using the platform with their own content",
        slide_number: 4
    }
];

// Mock quiz questions
const mockQuiz = [
    {
        id: 1,
        question: "What is the main benefit of using AI in presentations?",
        options: [
            "Real-time assistance and guidance",
            "Automatic slide creation",
            "Voice recognition",
            "Background music"
        ],
        correct: 0
    },
    {
        id: 2,
        question: "Which feature helps engage the audience?",
        options: [
            "Interactive quizzes",
            "Color schemes",
            "Font selection",
            "Slide transitions"
        ],
        correct: 0
    },
    {
        id: 3,
        question: "What does SlideSense provide for speakers?",
        options: [
            "Smart speaker notes",
            "Video editing",
            "Image filters",
            "Audio recording"
        ],
        correct: 0
    }
];

// DOM Elements
let dropzone, fileInput, uploadSection, presentationView, currentSlideElement;
let slideCounter, slidePreviews, editModal;
let guideTab, quizTab, chatTab, guideContent, quizContent, chatContent;

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDOMElements();
    setupEventListeners();
    console.log('SlideSense initialized - Ready to use!');
});

function initializeDOMElements() {
    dropzone = document.getElementById('dropzone');
    fileInput = document.getElementById('fileInput');
    uploadSection = document.getElementById('uploadSection');
    presentationView = document.getElementById('presentationView');
    currentSlideElement = document.getElementById('currentSlide');
    slideCounter = document.getElementById('slideCounter');
    slidePreviews = document.getElementById('slidePreviews');
    editModal = document.getElementById('editModal');
    
    // Assistant tabs
    guideTab = document.getElementById('guideTab');
    quizTab = document.getElementById('quizTab');
    chatTab = document.getElementById('chatTab');
    guideContent = document.getElementById('guideContent');
    quizContent = document.getElementById('quizContent');
    chatContent = document.getElementById('chatContent');
}

function setupEventListeners() {
    // File input event
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                handleFiles(fileInput.files);
            }
        });
    }

    // Dropzone events
    if (dropzone) {
        // Click event
        dropzone.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                fileInput.click();
            }
        });

        // Drag and drop events
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
    }

    // Tab switching
    if (guideTab) guideTab.addEventListener('click', () => switchTab('guide'));
    if (quizTab) quizTab.addEventListener('click', () => switchTab('quiz'));
    if (chatTab) chatTab.addEventListener('click', () => switchTab('chat'));

    // Chat functionality
    setupChatListeners();
}

function setupChatListeners() {
    // These will be set up when chat tab is activated
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('chat-send')) {
            sendChatMessage();
        }
    });
    
    const chatInput = document.querySelector('.chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
}

// File handling function - Uses mock data
async function handleFiles(files) {
    const file = files[0];
    console.log('Processing file:', file.name);
    
    // Show loading state
    dropzone.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12">
            <i data-feather="loader" class="w-16 h-16 text-indigo-400 mb-4 animate-spin"></i>
            <h3 class="text-xl font-medium text-gray-200 mb-2">Processing Presentation...</h3>
            <p class="text-gray-400">Please wait while we load your slides</p>
        </div>
    `;
    feather.replace();

    // Simulate processing delay
    setTimeout(() => {
        // Use mock data for demonstration
        slides = [...mockSlides];
        
        renderSlidePreviews();
        enablePresentationButton();
        
        // Show success state
        dropzone.innerHTML = `
            <div class="flex flex-col items-center justify-center py-8">
                <i data-feather="check-circle" class="w-12 h-12 text-green-400 mb-3"></i>
                <h3 class="text-lg font-medium text-gray-200 mb-1">Presentation Loaded!</h3>
                <p class="text-gray-400 text-sm">${slides.length} slides processed</p>
                <button class="upload-another-btn mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm transition">
                    Upload Another
                </button>
            </div>
        `;
        
        // Add event listener to the new "Upload Another" button
        const uploadAnotherBtn = dropzone.querySelector('.upload-another-btn');
        if (uploadAnotherBtn) {
            uploadAnotherBtn.addEventListener('click', resetToUploadState);
        }
        
        feather.replace();
        
    }, 2000); // 2 second delay to simulate processing
}

function loadSamplePresentation() {
    // Use mock data directly
    slides = [...mockSlides];
    renderSlidePreviews();
    enablePresentationButton();
    
    // Show success state
    dropzone.innerHTML = `
        <div class="flex flex-col items-center justify-center py-8">
            <i data-feather="check-circle" class="w-12 h-12 text-green-400 mb-3"></i>
            <h3 class="text-lg font-medium text-gray-200 mb-1">Sample Presentation Loaded!</h3>
            <p class="text-gray-400 text-sm">${slides.length} demo slides loaded</p>
            <button class="upload-another-btn mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm transition">
                Upload Your Own
            </button>
        </div>
    `;
    
    // Add event listener to the new button
    const uploadAnotherBtn = dropzone.querySelector('.upload-another-btn');
    if (uploadAnotherBtn) {
        uploadAnotherBtn.addEventListener('click', resetToUploadState);
    }
    
    feather.replace();
}

function enablePresentationButton() {
    const presentButton = document.querySelector('.presentation-btn');
    if (presentButton) {
        presentButton.disabled = false;
        presentButton.classList.remove('opacity-50');
    }
}

function resetToUploadState() {
    dropzone.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12">
            <i data-feather="upload-cloud" class="w-16 h-16 text-indigo-400 mb-4"></i>
            <h3 class="text-xl font-medium text-gray-200 mb-2">Drag & Drop your presentation file</h3>
            <p class="text-gray-400 mb-4">or click to browse files (PPTX, DOCX, PDF, TXT)</p>
            <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md transition">
                Select File
            </button>
        </div>
        <input type="file" id="fileInput" class="hidden" accept=".pptx,.docx,.pdf,.txt,.md">
    `;
    
    // Re-initialize the file input
    fileInput = document.getElementById('fileInput');
    
    // Re-attach file input listener
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                handleFiles(fileInput.files);
            }
        });
    }
    
    // Reset presentation state
    slides = [];
    currentSlide = 0;
    
    // Disable presentation button
    const presentButton = document.querySelector('.presentation-btn');
    if (presentButton) {
        presentButton.disabled = true;
        presentButton.classList.add('opacity-50');
    }
    
    // Clear slide previews
    if (slidePreviews) {
        slidePreviews.innerHTML = '';
    }
    
    feather.replace();
}

function renderSlidePreviews() {
    if (!slidePreviews) return;
    
    slidePreviews.innerHTML = '';
    
    slides.forEach((slide, index) => {
        const slideElement = document.createElement('div');
        slideElement.className = 'bg-gray-800 rounded-lg overflow-hidden slide-container cursor-pointer';
        slideElement.innerHTML = `
            <div class="relative" onclick="previewSlide(${index})">
                <img src="${slide.thumbnail}" alt="${slide.title}" class="w-full h-40 object-cover">
                <div class="slide-toolbar absolute top-2 right-2 flex space-x-1">
                    <button class="bg-gray-900 bg-opacity-70 text-white p-1 rounded hover:bg-opacity-100 transition"
                            onclick="event.stopPropagation(); editSlide(${index})">
                        <i data-feather="edit-2" class="w-4 h-4"></i>
                    </button>
                    <button class="bg-gray-900 bg-opacity-70 text-white p-1 rounded hover:bg-opacity-100 transition"
                            onclick="event.stopPropagation(); deleteSlide(${index})">
                        <i data-feather="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
                <div class="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                    Slide ${slide.slide_number}
                </div>
            </div>
            <div class="p-3">
                <h4 class="font-medium truncate">${slide.title}</h4>
                <p class="text-xs text-gray-400 truncate">${slide.content.substring(0, 50)}...</p>
            </div>
        `;
        slidePreviews.appendChild(slideElement);
    });
    feather.replace();
}

function previewSlide(index) {
    currentSlide = index;
    showSlide(currentSlide);
    startPresentationMode();
}

function startPresentationMode() {
    if (slides.length === 0) {
        alert('Please upload a presentation first');
        return;
    }
    
    uploadSection.classList.add('hidden');
    presentationView.classList.remove('hidden');
    isPresentationMode = true;
    currentSlide = 0;
    showSlide(currentSlide);
    
    document.addEventListener('keydown', handleKeyPress);
}

function exitPresentationMode() {
    presentationView.classList.add('hidden');
    uploadSection.classList.remove('hidden');
    isPresentationMode = false;
    document.removeEventListener('keydown', handleKeyPress);
}

function showSlide(index) {
    if (index < 0 || index >= slides.length) return;
    
    currentSlide = index;
    const slide = slides[currentSlide];
    
    currentSlideElement.innerHTML = `
        <div class="bg-white text-black p-8 rounded-lg max-w-4xl max-h-full overflow-auto">
            <h2 class="text-3xl font-bold mb-4">${slide.title}</h2>
            <div class="prose prose-lg">
                ${formatSlideContent(slide.content)}
            </div>
            ${slide.notes ? `
                <div class="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400">
                    <h4 class="font-bold mb-2">Speaker Notes:</h4>
                    <p class="text-gray-700">${slide.notes}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    slideCounter.textContent = `Slide ${currentSlide + 1}/${slides.length}`;
    updateAssistantContent();
}

function formatSlideContent(content) {
    if (!content) return '<p>No content available</p>';
    
    const lines = content.split('\n');
    let html = '';
    let inList = false;
    
    lines.forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine) {
            if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•') || /^\d+\./.test(trimmedLine)) {
                if (!inList) {
                    html += '<ul class="list-disc list-inside my-4 space-y-2">';
                    inList = true;
                }
                const listItem = trimmedLine.replace(/^[-•\d\.\s]+/, '');
                html += `<li class="text-lg">${listItem}</li>`;
            } else {
                if (inList) {
                    html += '</ul>';
                    inList = false;
                }
                if (line.trim() === line) { // It's a heading
                    html += `<h3 class="text-2xl font-semibold my-4">${line}</h3>`;
                } else {
                    html += `<p class="my-3 text-lg">${line}</p>`;
                }
            }
        }
    });
    
    if (inList) html += '</ul>';
    return html;
}

function nextSlide() {
    if (currentSlide < slides.length - 1) {
        showSlide(currentSlide + 1);
    }
}

function prevSlide() {
    if (currentSlide > 0) {
        showSlide(currentSlide - 1);
    }
}

function toggleEditMode() {
    if (isEditMode) {
        closeEditModal();
    } else {
        openEditModal();
    }
    isEditMode = !isEditMode;
}

function openEditModal() {
    const slide = slides[currentSlide];
    const modalContent = editModal.querySelector('.p-6');
    
    modalContent.innerHTML = `
        <div class="mb-6">
            <label class="block text-sm font-medium mb-2">Slide Title</label>
            <input type="text" id="editSlideTitle" class="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:border-indigo-500" value="${slide.title}">
        </div>
        
        <div class="mb-6">
            <label class="block text-sm font-medium mb-2">Content</label>
            <textarea id="editSlideContent" class="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:border-indigo-500 min-h-40">${slide.content}</textarea>
        </div>
        
        <div class="mb-6">
            <label class="block text-sm font-medium mb-2">Speaker Notes</label>
            <textarea id="editSlideNotes" class="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:border-indigo-500 min-h-20">${slide.notes || ''}</textarea>
        </div>
        <div class="flex justify-end space-x-3">
            <button onclick="closeEditModal()" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition">Cancel</button>
            <button onclick="saveSlideChanges()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md transition">Save Changes</button>
        </div>
    `;
    
    editModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeEditModal() {
    editModal.classList.add('hidden');
    document.body.style.overflow = '';
}

function saveSlideChanges() {
    const title = document.getElementById('editSlideTitle').value;
    const content = document.getElementById('editSlideContent').value;
    const notes = document.getElementById('editSlideNotes').value;
    
    slides[currentSlide].title = title;
    slides[currentSlide].content = content;
    slides[currentSlide].notes = notes;
    
    showSlide(currentSlide);
    renderSlidePreviews();
    closeEditModal();
}

function editSlide(index) {
    currentSlide = index;
    toggleEditMode();
}

function deleteSlide(index) {
    if (confirm('Are you sure you want to delete this slide?')) {
        slides.splice(index, 1);
        renderSlidePreviews();
        
        if (isPresentationMode && currentSlide >= slides.length) {
            currentSlide = Math.max(0, slides.length - 1);
            showSlide(currentSlide);
        }
    }
}

function handleKeyPress(e) {
    if (!isPresentationMode) return;
    
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
            exitPresentationMode();
            break;
        case 'e':
            toggleEditMode();
            break;
    }
}

function switchTab(tab) {
    // Reset tabs
    [guideTab, quizTab, chatTab].forEach(tab => {
        if (tab) {
            tab.classList.remove('border-b-2', 'border-indigo-500');
            tab.classList.add('text-gray-400');
        }
    });
    
    // Hide contents
    [guideContent, quizContent, chatContent].forEach(content => {
        if (content) content.classList.add('hidden');
    });
    
    // Activate selected tab
    switch(tab) {
        case 'guide':
            if (guideTab) {
                guideTab.classList.add('border-b-2', 'border-indigo-500');
                guideTab.classList.remove('text-gray-400');
            }
            if (guideContent) guideContent.classList.remove('hidden');
            break;
        case 'quiz':
            if (quizTab) {
                quizTab.classList.add('border-b-2', 'border-indigo-500');
                quizTab.classList.remove('text-gray-400');
            }
            if (quizContent) {
                quizContent.classList.remove('hidden');
                loadQuizContent();
            }
            break;
        case 'chat':
            if (chatTab) {
                chatTab.classList.add('border-b-2', 'border-indigo-500');
                chatTab.classList.remove('text-gray-400');
            }
            if (chatContent) {
                chatContent.classList.remove('hidden');
                setupChatListeners();
            }
            break;
    }
}

function updateAssistantContent() {
    const slide = slides[currentSlide];
    const guideTips = guideContent?.querySelector('.ai-response');
    
    if (guideTips) {
        const keyPoints = slide.content.split('\n').filter(line => 
            line.trim().startsWith('-') || line.trim().startsWith('•') || /^\d+\./.test(line.trim())
        );
        
        guideTips.innerHTML = `
            <p class="font-semibold text-indigo-300 mb-2">Speaking Tips:</p>
            <p><strong>Focus on:</strong> ${slide.title}</p>
            <p><strong>Key points:</strong> ${keyPoints.length} main elements</p>
            <p class="mt-2"><strong>Timing:</strong> Spend 1-2 minutes on this slide</p>
            <p><strong>Engagement:</strong> Ask questions about ${slide.title.toLowerCase()}</p>
        `;
    }
}

function loadQuizContent() {
    const quizContainer = quizContent?.querySelector('.quiz-questions');
    if (!quizContainer) return;
    
    quizContainer.innerHTML = '';
    
    mockQuiz.forEach((q, index) => {
        const questionElement = document.createElement('div');
        questionElement.className = 'mb-6 p-3 bg-gray-700 rounded-lg';
        questionElement.innerHTML = `
            <h5 class="font-medium mb-2">Question ${index + 1}:</h5>
            <p class="text-gray-300 text-sm mb-3">${q.question}</p>
            <div class="space-y-2">
                ${q.options.map((option, optIndex) => `
                    <div class="flex items-center">
                        <input type="radio" id="q${q.id}_${optIndex}" name="q${q.id}" class="mr-2 quiz-option" data-correct="${optIndex === q.correct}">
                        <label for="q${q.id}_${optIndex}" class="text-sm cursor-pointer">${option}</label>
                    </div>
                `).join('')}
            </div>
            <div class="quiz-feedback mt-2 text-xs hidden"></div>
        `;
        quizContainer.appendChild(questionElement);
    });
    
    // Add event listeners for quiz options
    setTimeout(() => {
        document.querySelectorAll('.quiz-option').forEach(option => {
            option.addEventListener('change', function() {
                const feedback = this.closest('.mb-6').querySelector('.quiz-feedback');
                if (this.dataset.correct === 'true') {
                    feedback.innerHTML = '<span class="text-green-400">✓ Correct! Well done.</span>';
                } else {
                    feedback.innerHTML = '<span class="text-red-400">✗ Try again. Consider the main features discussed.</span>';
                }
                feedback.classList.remove('hidden');
            });
        });
    }, 100);
    
    const generateButton = document.createElement('button');
    generateButton.className = 'bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm transition mt-4';
    generateButton.textContent = 'Generate More Questions';
    generateButton.onclick = loadQuizContent;
    quizContainer.appendChild(generateButton);
}

function sendChatMessage() {
    const chatInput = document.querySelector('.chat-input');
    const chatMessages = document.querySelector('.chat-messages');
    
    if (!chatInput || !chatMessages) return;
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    addChatMessage('user', message);
    chatInput.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        const slide = slides[currentSlide];
        const aiResponses = [
            `Based on slide "${slide.title}", I suggest emphasizing the key points and engaging the audience with questions.`,
            `For this slide about ${slide.title.toLowerCase()}, consider sharing a relevant story or example to make it more memorable.`,
            `This content looks great! Remember to maintain eye contact and speak clearly when presenting these concepts.`,
            `You might want to add a quick activity or poll related to ${slide.title.toLowerCase()} to increase engagement.`,
            `Consider using analogies or real-world applications to help the audience understand ${slide.title.toLowerCase()} better.`
        ];
        
        const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
        addChatMessage('ai', randomResponse);
    }, 1000);
}

function addChatMessage(sender, message) {
    const chatMessages = document.querySelector('.chat-messages');
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
                <h4 class="font-medium">${sender === 'user' ? 'You' : 'AI Assistant'}</h4>
            </div>
        </div>
        <div class="pl-11">
            <p>${message}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    feather.replace();
}

// Make all functions globally available
window.startPresentationMode = startPresentationMode;
window.exitPresentationMode = exitPresentationMode;
window.nextSlide = nextSlide;
window.prevSlide = prevSlide;
window.toggleEditMode = toggleEditMode;
window.closeEditModal = closeEditModal;
window.saveSlideChanges = saveSlideChanges;
window.editSlide = editSlide;
window.deleteSlide = deleteSlide;
window.previewSlide = previewSlide;
window.resetToUploadState = resetToUploadState;
window.sendChatMessage = sendChatMessage;
window.switchTab = switchTab;
window.loadQuizContent = loadQuizContent;
window.loadSamplePresentation = loadSamplePresentation;