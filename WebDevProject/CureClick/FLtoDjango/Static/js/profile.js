document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const editProfileModal = document.getElementById('editProfileModal');
    const openEditProfileBtn = document.getElementById('openEditProfileBtn');
    const openEditProfileBtn2 = document.getElementById('openEditProfileBtn2');
    const closeEditProfileModal = document.getElementById('closeEditProfileModal');
    const cancelEditProfile = document.getElementById('cancelEditProfile');
    const profileEditForm = document.getElementById('profileEditForm');
    const dateOfBirthInput = document.getElementById('date_of_birth');
    const ageInput = document.getElementById('age');

    // Set initial styles for modal - ensure it's hidden by default
    if (editProfileModal) {
        editProfileModal.style.display = 'none';
        editProfileModal.setAttribute('aria-hidden', 'true');
    }

    // Open modal functionality with explicit styling
    function openModal() {
        console.log('Opening modal');
        if (editProfileModal) {
            // Make sure modal is fully visible with proper styles
            editProfileModal.style.display = 'flex';
            editProfileModal.style.visibility = 'visible';
            editProfileModal.style.opacity = '1';
            editProfileModal.style.zIndex = '1000';
            editProfileModal.setAttribute('aria-hidden', 'false');
            
            // Make sure modal container is visible
            const modalContainer = editProfileModal.querySelector('.profile-edit__modal-container');
            if (modalContainer) {
                modalContainer.style.opacity = '1';
                modalContainer.style.visibility = 'visible';
                modalContainer.style.transform = 'translateY(0)';
            }
            
            // Add overlay styling
            editProfileModal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }
    }

    // Close modal functionality
    function closeModal() {
        console.log('Closing modal');
        if (editProfileModal) {
            editProfileModal.style.display = 'none';
            editProfileModal.style.visibility = 'hidden';
            editProfileModal.style.opacity = '0';
            editProfileModal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = ''; // Re-enable scrolling
        }
    }

    // Calculate age from date of birth
    function calculateAge(birthDate) {
        const today = new Date();
        const dob = new Date(birthDate);
        let age = today.getFullYear() - dob.getFullYear();
        const monthDiff = today.getMonth() - dob.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        
        return age;
    }

    // Event listeners with specific styling fixes
    if (openEditProfileBtn) {
        openEditProfileBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openModal();
            return false; // Prevent event bubbling
        });
    }
    
    if (openEditProfileBtn2) {
        openEditProfileBtn2.addEventListener('click', function(e) {
            e.preventDefault();
            openModal();
            return false; // Prevent event bubbling
        });
    }
    
    // Adding click listeners to all elements with specific classes
    document.querySelectorAll('.edit-button, #openEditProfileBtn, #openEditProfileBtn2').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            openModal();
            return false; // Prevent event bubbling
        });
    });
    
    if (closeEditProfileModal) {
        closeEditProfileModal.addEventListener('click', function(e) {
            e.preventDefault();
            closeModal();
            return false;
        });
    }
    
    if (cancelEditProfile) {
        cancelEditProfile.addEventListener('click', function(e) {
            e.preventDefault();
            closeModal();
            return false;
        });
    }

    // Close modal if clicked outside the content
    window.addEventListener('click', function(event) {
        if (event.target === editProfileModal) {
            closeModal();
        }
    });

    // Auto-calculate age when date of birth changes
    if (dateOfBirthInput && ageInput) {
        dateOfBirthInput.addEventListener('change', function() {
            if (this.value) {
                ageInput.value = calculateAge(this.value);
            }
        });
    }

    // Form validation before submission
    if (profileEditForm) {
        profileEditForm.addEventListener('submit', function(event) {
            const fullName = document.getElementById('full_name').value.trim();
            const email = document.getElementById('email').value.trim();
            
            if (!fullName) {
                event.preventDefault();
                alert('Please enter your full name');
                return;
            }
            
            if (!email) {
                event.preventDefault();
                alert('Please enter your email address');
                return;
            }
            
            // Basic email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                event.preventDefault();
                alert('Please enter a valid email address');
                return;
            }
        });
    }

    // Add direct button click handling for testing
    console.log('Adding additional click handlers for testing');
    document.addEventListener('click', function(e) {
        if (e.target.id === 'openEditProfileBtn' || e.target.id === 'openEditProfileBtn2' || 
            e.target.classList.contains('edit-button')) {
            console.log('Clicked on edit button via document listener');
            e.preventDefault();
            openModal();
        }
    });

    console.log('Profile edit modal script loaded');
});

// Create a self-executing function to avoid polluting the global namespace
(function() {
    // Azure OpenAI configuration
    const endpoint = "https://neela-maa2tdpw-swedencentral.openai.azure.com/openai/deployments/CureBot/chat/completions?api-version=2025-01-01-preview";
    const apiKey = "256OQtOitExk9M6g7cniyb3vnSgv07R1YzwimDBwQHWbWonsS3BDJQQJ99BEACfhMk5XJ3w3AAAAACOGPHka";
    
    // Create and inject CSS
    const injectStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Base styles */
            body {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f8fafc;
                color: #334155;
            }
            
            /* Toggle Button with enhanced design */
            .chat-toggle {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 65px;
                height: 65px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                box-shadow: 0 6px 16px rgba(0, 120, 215, 0.3);
                z-index: 1000;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: none;
                outline: none;
            }
            
            .chat-toggle:hover {
                transform: translateY(-5px) scale(1.05);
                box-shadow: 0 10px 20px rgba(0, 120, 215, 0.4);
            }
            
            .chat-toggle:active {
                transform: translateY(0) scale(0.95);
            }
            
            .chat-toggle .icon {
                font-size: 28px;
                transition: all 0.3s ease;
            }
            
            .chat-toggle::before {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                transform: scale(0);
                transition: transform 0.5s ease;
            }
            
            .chat-toggle:hover::before {
                transform: scale(1.2);
                opacity: 0;
            }
            
            /* Pulse animation for the toggle button */
            .chat-toggle::after {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.4);
                z-index: -1;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    transform: scale(1);
                    opacity: 0.7;
                }
                70% {
                    transform: scale(1.3);
                    opacity: 0;
                }
                100% {
                    transform: scale(1);
                    opacity: 0;
                }
            }
            
            /* Chat Container */
            .chat-container {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 380px;
                height: 520px;
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                z-index: 999;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                opacity: 0;
                pointer-events: none;
                transform: translateY(20px) scale(0.95);
                border: 1px solid rgba(0, 120, 215, 0.1);
            }
            
            .chat-container.active {
                opacity: 1;
                pointer-events: all;
                transform: translateY(0) scale(1);
            }
  
            /* Chat Header */
            .chat-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
            
            .chat-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                font-size: 18px;
            }
            
            .chat-logo {
                width: 24px;
                height: 24px;
                background-color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #2563eb;
                font-size: 14px;
                font-weight: bold;
            }
            
            .chat-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 20px;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                transition: background 0.3s;
            }
            
            .chat-close:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Messages area */
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 16px;
                scroll-behavior: smooth;
            }
            
            .message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                line-height: 1.4;
                font-size: 15px;
                word-wrap: break-word;
                position: relative;
                animation: fadeIn 0.3s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message.user {
                align-self: flex-end;
                background: #e2f1ff;
                color: #1e40af;
                border-bottom-right-radius: 4px;
            }
            
            .message.bot {
                align-self: flex-start;
                background: #f1f5f9;
                color: #334155;
                border-bottom-left-radius: 4px;
            }
            
            .typing-indicator {
                align-self: flex-start;
                background: #f1f5f9;
                color: #64748b;
                padding: 12px 16px;
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background: #64748b;
                border-radius: 50%;
                animation: typingAnimation 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typingAnimation {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-5px); }
            }
            
            /* Input area */
            .chat-input-container {
                padding: 16px;
                background-color: #fff;
                border-top: 1px solid #e5e7eb;
            }
            
            .chat-input-form {
                display: flex;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 24px;
                outline: none;
                font-size: 15px;
                transition: border-color 0.3s, box-shadow 0.3s;
                font-family: inherit;
                resize: none;
                height: auto;
                overflow-y: hidden;
            }
            
            .chat-input:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
            }
            
            .chat-send-btn {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                border: none;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s;
                flex-shrink: 0;
            }
            
            .chat-send-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 120, 215, 0.3);
            }
            
            .chat-send-btn:active {
                transform: translateY(0);
            }
            
            .chat-send-btn:disabled {
                background: #cbd5e1;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            /* Welcome message styling */
            .welcome-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 30px 20px;
                height: 100%;
            }
            
            .welcome-icon {
                font-size: 48px;
                margin-bottom: 16px;
                color: #2563eb;
            }
            
            .welcome-title {
                font-size: 22px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 12px;
            }
            
            .welcome-message {
                font-size: 16px;
                color: #64748b;
                margin-bottom: 24px;
                line-height: 1.5;
            }
            
            .start-chat-btn {
                padding: 12px 24px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .start-chat-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0, 120, 215, 0.2);
            }
        `;
        document.head.appendChild(styleElement);
    };
    
    // Create chat toggle button
    const createChatToggle = () => {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'chat-toggle';
        toggleBtn.id = 'chatToggle';
        toggleBtn.setAttribute('aria-label', 'Open chat');
        
        const icon = document.createElement('span');
        icon.className = 'icon';
        icon.innerHTML = '💬';
        
        toggleBtn.appendChild(icon);
        document.body.appendChild(toggleBtn);
        
        return toggleBtn;
    };
    
    // Create chat container with full interface
    const createChatContainer = () => {
        const container = document.createElement('div');
        container.className = 'chat-container';
        container.id = 'chatContainer';
        
        // Chat header
        const header = document.createElement('div');
        header.className = 'chat-header';
        
        const title = document.createElement('div');
        title.className = 'chat-title';
        
        const logo = document.createElement('div');
        logo.className = 'chat-logo';
        logo.textContent = 'C';
        
        const titleText = document.createElement('span');
        titleText.textContent = 'CureBot';
        
        title.appendChild(logo);
        title.appendChild(titleText);
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'chat-close';
        closeBtn.innerHTML = '✕';
        closeBtn.setAttribute('aria-label', 'Close chat');
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        // Chat messages area
        const messagesArea = document.createElement('div');
        messagesArea.className = 'chat-messages';
        messagesArea.id = 'chatMessages';
        
        // Welcome message (initial state)
        const welcomeContainer = document.createElement('div');
        welcomeContainer.className = 'welcome-container';
        welcomeContainer.id = 'welcomeContainer';
        
        const welcomeIcon = document.createElement('div');
        welcomeIcon.className = 'welcome-icon';
        welcomeIcon.innerHTML = '👋';
        
        const welcomeTitle = document.createElement('h2');
        welcomeTitle.className = 'welcome-title';
        welcomeTitle.textContent = 'Welcome to CureBot';
        
        const welcomeMessage = document.createElement('p');
        welcomeMessage.className = 'welcome-message';
        welcomeMessage.textContent = 'I can help answer your healthcare questions. How can I assist you today?';
        
        const startChatBtn = document.createElement('button');
        startChatBtn.className = 'start-chat-btn';
        startChatBtn.textContent = 'Start Chatting';
        
        welcomeContainer.appendChild(welcomeIcon);
        welcomeContainer.appendChild(welcomeTitle);
        welcomeContainer.appendChild(welcomeMessage);
        welcomeContainer.appendChild(startChatBtn);
        
        messagesArea.appendChild(welcomeContainer);
        
        // Chat input area
        const inputContainer = document.createElement('div');
        inputContainer.className = 'chat-input-container';
        
        const inputForm = document.createElement('form');
        inputForm.className = 'chat-input-form';
        inputForm.id = 'chatInputForm';
        
        const textInput = document.createElement('textarea');
        textInput.className = 'chat-input';
        textInput.id = 'chatInput';
        textInput.placeholder = 'Type your message...';
        textInput.setAttribute('rows', '1');
        
        const sendBtn = document.createElement('button');
        sendBtn.className = 'chat-send-btn';
        sendBtn.type = 'submit';
        sendBtn.innerHTML = '➤';
        sendBtn.setAttribute('aria-label', 'Send message');
        
        inputForm.appendChild(textInput);
        inputForm.appendChild(sendBtn);
        
        inputContainer.appendChild(inputForm);
        
        // Add all elements to container
        container.appendChild(header);
        container.appendChild(messagesArea);
        container.appendChild(inputContainer);
        
        document.body.appendChild(container);
        
        return container;
    };
    
    // Handle chat message sending
    const handleMessageSend = async (inputElement) => {
        const messageText = inputElement.value.trim();
        if (!messageText) return;
        
        // Clear input
        inputElement.value = '';
        
        // Add user message to chat
        addMessage(messageText, 'user');
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send message to Azure OpenAI
            const response = await sendMessageToAzureOpenAI(messageText);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            if (response) {
                addMessage(response, 'bot');
            } else {
                addMessage("I'm sorry, I couldn't process your request. Please try again.", 'bot');
            }
        } catch (error) {
            console.error('Error processing message:', error);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add error message
            addMessage("I'm sorry, there was an error processing your request. Please try again later.", 'bot');
        }
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Add a message to the chat
    const addMessage = (text, sender) => {
        const messagesContainer = document.getElementById('chatMessages');
        const welcomeContainer = document.getElementById('welcomeContainer');
        
        // Remove welcome message if it exists
        if (welcomeContainer && welcomeContainer.parentNode === messagesContainer) {
            messagesContainer.removeChild(welcomeContainer);
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        messageElement.textContent = text;
        
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Show typing indicator
    const showTypingIndicator = () => {
        const messagesContainer = document.getElementById('chatMessages');
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typingIndicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingIndicator.appendChild(dot);
        }
        
        messagesContainer.appendChild(typingIndicator);
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Hide typing indicator
    const hideTypingIndicator = () => {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.parentNode.removeChild(typingIndicator);
        }
    };
    
    // Scroll chat to bottom
    const scrollToBottom = () => {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    // Send message to Azure OpenAI API
    const sendMessageToAzureOpenAI = async (message) => {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'api-key': apiKey
                },
                body: JSON.stringify({
                    messages: [
                        { role: "system", content: "You are a helpful healthcare assistant named CureBot. You can answer anything related to medical stuff. But you will not answer anything except it, say It is beyond my learning model! Provide accurate, helpful information on health topics, but always remind users to consult our healthcare professionals from CureClick for medical advice. Prefer to give small responses unless asked for in detail." },
                        { role: "user", content: message }
                    ],
                    max_tokens: 800
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error('Error sending message to Azure OpenAI:', error);
            throw error;
        }
    };
    
    // Auto-grow textarea
    const setupTextareaAutoGrow = (textarea) => {
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            const newHeight = Math.min(textarea.scrollHeight, 120);
            textarea.style.height = `${newHeight}px`;
        });
    };
    
    // Initialize chat functionality
    const initChat = () => {
        // Inject styles
        injectStyles();
        
        // Create UI elements
        const chatToggle = createChatToggle();
        const chatContainer = createChatContainer();
        
        // Get elements
        const closeBtn = chatContainer.querySelector('.chat-close');
        const chatForm = document.getElementById('chatInputForm');
        const chatInput = document.getElementById('chatInput');
        const startChatBtn = document.querySelector('.start-chat-btn');
        
        // Setup textarea auto-grow
        setupTextareaAutoGrow(chatInput);
        
        // Toggle chat open/close
        chatToggle.addEventListener('click', () => {
            chatContainer.classList.add('active');
        });
        
        // Close chat
        closeBtn.addEventListener('click', () => {
            chatContainer.classList.remove('active');
        });
        
        // Start chat button click
        if (startChatBtn) {
            startChatBtn.addEventListener('click', () => {
                const welcomeContainer = document.getElementById('welcomeContainer');
                if (welcomeContainer) {
                    welcomeContainer.style.display = 'none';
                }
                
                // Add initial bot message
                addMessage("Hi there! I'm CureBot. How can I help with your health questions today?", 'bot');
                
                // Focus on input
                chatInput.focus();
            });
        }
        
        // Handle form submission
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleMessageSend(chatInput);
        });
        
        // Handle Enter key (submit on Enter, new line on Shift+Enter)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleMessageSend(chatInput);
            }
        });
    };
    
    // Initialize everything when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', initChat);
  })();