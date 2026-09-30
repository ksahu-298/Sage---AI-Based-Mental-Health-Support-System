/**
 * chat.js - Chat Module for Sage
 * 
 * Handles:
 * - Sending and receiving messages
 * - Displaying chat history
 * - XAI explanations ("Why Sage said this")
 * - Typing indicators
 * - Message formatting and timestamps
 */

// ==================== DOM ELEMENTS ====================

let messagesContainer = null;
let messageInput = null;
let sendButton = null;
let isTyping = false;
let currentConversationId = null;

// ==================== INITIALIZATION ====================

/**
 * Initialize chat module
 * @param {string} containerId - ID of messages container element
 * @param {string} inputId - ID of message input element
 * @param {string} buttonId - ID of send button element
 */
function initChat(containerId, inputId, buttonId) {
    messagesContainer = document.getElementById(containerId);
    messageInput = document.getElementById(inputId);
    sendButton = document.getElementById(buttonId);
    
    if (!messagesContainer || !messageInput || !sendButton) {
        console.error('Chat elements not found');
        return;
    }
    
    // Add event listeners
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    // Load chat history
    loadChatHistory();
}

// ==================== MESSAGE DISPLAY ====================

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp
 * @returns {string} - Formatted time (e.g., "2:30 PM")
 */
function formatMessageTime(timestamp) {
    if (!timestamp) {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format date for message grouping
 * @param {string} timestamp - ISO timestamp
 * @returns {string} - Formatted date (e.g., "Today", "Yesterday", "Jan 15")
 */
function formatMessageDate(timestamp) {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Add a message to the chat container
 * @param {string} text - Message content
 * @param {string} role - 'user' or 'sage'
 * @param {string} explanation - XAI explanation (for bot messages)
 * @param {string} timestamp - ISO timestamp
 */
function addMessage(text, role, explanation = null, timestamp = null) {
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
    messageDiv.setAttribute('data-role', role);
    
    const time = formatMessageTime(timestamp);
    const formattedText = escapeHtml(text).replace(/\n/g, '<br>');
    
    let actionsHtml = '';
    if (role === 'sage' && explanation) {
        const escapedExplanation = escapeHtml(explanation).replace(/'/g, '&#39;');
        actionsHtml = `
            <div class="message-actions">
                <button class="xai-btn" onclick="toggleExplanation(this, '${escapedExplanation}')">
                    <i class="fas fa-info-circle"></i> Why Sage said this
                </button>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-bubble">${formattedText}</div>
        ${actionsHtml}
        <div class="message-time">${time}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Add date separator to chat
 * @param {string} dateText - Date text (e.g., "Today")
 */
function addDateSeparator(dateText) {
    if (!messagesContainer) return;
    
    const separator = document.createElement('div');
    separator.className = 'date-separator';
    separator.innerHTML = `<span>${dateText}</span>`;
    messagesContainer.appendChild(separator);
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    if (!messagesContainer || isTyping) return;
    isTyping = true;
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message bot-message';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    if (!messagesContainer) return;
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) typingDiv.remove();
    isTyping = false;
}

/**
 * Toggle XAI explanation display
 * @param {HTMLElement} btn - The button that was clicked
 * @param {string} explanation - Explanation text
 */
function toggleExplanation(btn, explanation) {
    const messageDiv = btn.closest('.message');
    if (!messageDiv) return;
    
    const existingBox = messageDiv.querySelector('.explanation-box');
    if (existingBox) {
        existingBox.remove();
        return;
    }
    
    const explanationBox = document.createElement('div');
    explanationBox.className = 'explanation-box';
    explanationBox.innerHTML = `
        <i class="fas fa-brain"></i> 
        <strong>Why Sage said this:</strong><br>
        ${escapeHtml(explanation)}
    `;
    messageDiv.appendChild(explanationBox);
    explanationBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ==================== MESSAGE SENDING ====================

/**
 * Send a message to Sage
 * @param {string} message - Optional message (uses input value if not provided)
 */
async function sendMessage(message = null) {
    const text = message || messageInput.value.trim();
    
    if (!text) return;
    
    // Clear input
    if (!message) {
        messageInput.value = '';
    }
    
    // Add user message to UI
    addMessage(text, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await ChatAPI.sendMessage(text);
        
        hideTypingIndicator();
        
        if (response.success && response.data) {
            addMessage(
                response.data.response,
                'sage',
                response.data.explanation
            );
            
            // Store conversation ID if returned
            if (response.data.conversation_id) {
                currentConversationId = response.data.conversation_id;
            }
        } else {
            addMessage(
                "I'm having trouble responding right now. Please try again.",
                'sage'
            );
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Send message error:', error);
        addMessage(
            "Sorry, I'm having technical difficulties. Please check your connection and try again.",
            'sage'
        );
    }
}

/**
 * Send a suggested message (from prompt chips)
 * @param {string} message - The suggested message text
 */
function sendSuggestedMessage(message) {
    sendMessage(message);
}

// ==================== CHAT HISTORY ====================

/**
 * Load chat history from backend
 * @param {number} limit - Number of messages to load
 */
async function loadChatHistory(limit = 50) {
    if (!messagesContainer) return;
    
    try {
        const response = await ChatAPI.getHistory(limit);
        
        if (response.success && response.data) {
            const heading = response.data.day_heading || '';
            const messages = response.data.messages || [];

            messagesContainer.innerHTML = '';

            if (heading) {
                const banner = document.createElement('div');
                banner.className = 'chat-day-banner';
                banner.textContent = `Today's conversation · ${heading}`;
                messagesContainer.appendChild(banner);
            }

            if (messages.length === 0) {
                addMessage(
                    "🌿 Hello! I'm Sage, your mental wellness companion. I'm here to listen without judgment. How are you feeling today?",
                    'sage'
                );
                return;
            }

            messages.forEach(msg => {
                addMessage(msg.message, msg.role, msg.explanation, msg.timestamp);
            });
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
        // Keep default welcome message
    }
}

/**
 * Clear all chat history
 */
async function clearChatHistory() {
    if (confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
        try {
            const response = await ChatAPI.clearHistory();
            if (response.success) {
                // Reload page to show empty chat
                window.location.reload();
            }
        } catch (error) {
            console.error('Failed to clear chat history:', error);
            alert('Could not clear history. Please try again.');
        }
    }
}

/**
 * Submit feedback for a response
 * @param {number} messageId - Message ID
 * @param {number} rating - Rating 1-5
 * @param {boolean} wasHelpful - Whether response was helpful
 */
async function submitFeedback(messageId, rating, wasHelpful) {
    try {
        await ChatAPI.submitFeedback(messageId, rating, wasHelpful);
        console.log('Feedback submitted');
    } catch (error) {
        console.error('Failed to submit feedback:', error);
    }
}

// ==================== UTILITIES ====================

/**
 * Get message input value
 * @returns {string} - Current input value
 */
function getMessageInput() {
    return messageInput ? messageInput.value : '';
}

/**
 * Set message input value
 * @param {string} value - Value to set
 */
function setMessageInput(value) {
    if (messageInput) {
        messageInput.value = value;
        messageInput.focus();
    }
}

/**
 * Focus message input
 */
function focusMessageInput() {
    if (messageInput) {
        messageInput.focus();
    }
}

/**
 * Check if user is typing (for future features)
 */
function isUserTyping() {
    return messageInput && messageInput.value.length > 0;
}

// ==================== CRISIS HANDLING ====================

/**
 * Handle crisis response (show helplines)
 * @param {object} crisisData - Crisis response data from backend
 */
function showCrisisHelplines(crisisData) {
    if (!messagesContainer) return;
    
    let helplineText = '';
    if (crisisData.helplines) {
        crisisData.helplines.forEach(h => {
            helplineText += `📞 **${h.name}**: ${h.number}\n`;
        });
    }
    
    addMessage(helplineText, 'sage');
}

// ==================== EXPORTS ====================

// Global exports for use in HTML
window.chat = {
    init: initChat,
    sendMessage,
    sendSuggestedMessage,
    loadChatHistory,
    clearChatHistory,
    addMessage,
    showTypingIndicator,
    hideTypingIndicator,
    toggleExplanation,
    getMessageInput,
    setMessageInput,
    focusMessageInput,
    submitFeedback
};
// Add this function to show sentiment for a message
async function showSentiment(messageId, messageText) {
    // First check if sentiment data is already in the message object
    if (window.sentimentData && window.sentimentData[messageId]) {
        showSentimentPopup(window.sentimentData[messageId]);
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/chat/sentiment/${messageId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.data) {
                // Cache the sentiment data
                if (!window.sentimentData) window.sentimentData = {};
                window.sentimentData[messageId] = data.data;
                showSentimentPopup(data.data);
            }
        } else {
            // Fallback to local analysis
            const localAnalysis = analyzeLocalSentiment(messageText);
            showSentimentPopup(localAnalysis);
        }
    } catch (error) {
        console.error('Error fetching sentiment:', error);
        const localAnalysis = analyzeLocalSentiment(messageText);
        showSentimentPopup(localAnalysis);
    }
}

// Emotion to emoji mapping
const EMOTION_EMOJIS = {
    'joy': '😊', 'gratitude': '🙏', 'sadness': '😔', 'anxiety': '🌬️',
    'anger': '⚡', 'loneliness': '💔', 'calm': '🧘', 'hope': '🌈',
    'nostalgia': '🕰️', 'neutral': '😐'
};

// Show sentiment popup
function showSentimentPopup(sentimentData) {
    const existingModal = document.querySelector('.sentiment-modal');
    if (existingModal) existingModal.remove();
    
    const emoji = EMOTION_EMOJIS[sentimentData.emotion] || '📊';
    const sentimentColor = sentimentData.sentiment === 'positive' ? '#2D6A4F' : 
                          (sentimentData.sentiment === 'negative' ? '#DC2626' : '#8A9A8A');
    
    const modal = document.createElement('div');
    modal.className = 'sentiment-modal';
    modal.innerHTML = `
        <div class="sentiment-modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;">
            <div style="background: white; border-radius: 1.5rem; padding: 1.5rem; max-width: 350px; width: 90%; margin: 1rem; box-shadow: 0 20px 40px rgba(0,0,0,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="color: #1B3A2B; margin: 0;"><i class="fas fa-chart-line"></i> Sentiment Analysis</h3>
                    <button onclick="this.closest('.sentiment-modal').remove()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">&times;</button>
                </div>
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div style="font-size: 3rem;">${emoji}</div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: ${sentimentColor}; margin-top: 0.5rem;">
                        ${sentimentData.emotion ? sentimentData.emotion.charAt(0).toUpperCase() + sentimentData.emotion.slice(1) : 'Neutral'}
                    </div>
                    <div style="font-size: 0.8rem; color: #6B7E6B;">Score: ${sentimentData.score} (${sentimentData.sentiment})</div>
                </div>
                <div style="background: #F5F7F2; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem;">
                    <p style="margin: 0; font-size: 0.85rem; line-height: 1.5;">${sentimentData.explanation || 'Analysis complete.'}</p>
                </div>
                <button onclick="this.closest('.sentiment-modal').remove()" style="width: 100%; padding: 0.6rem; background: #2D6A4F; color: white; border: none; border-radius: 2rem; cursor: pointer;">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('sentiment-modal-overlay')) {
            modal.remove();
        }
    });
}

// Local fallback sentiment analysis
function analyzeLocalSentiment(text) {
    const positiveWords = ['happy', 'joy', 'grateful', 'good', 'great', 'excited', 'wonderful', 'amazing', 'love', 'peaceful', 'calm'];
    const negativeWords = ['sad', 'anxious', 'scared', 'fear', 'angry', 'lonely', 'depressed', 'hopeless', 'stressed', 'overwhelmed', 'hurt'];
    
    const lowerText = text.toLowerCase();
    let score = 0;
    
    positiveWords.forEach(word => {
        if (lowerText.includes(word)) score += 0.15;
    });
    negativeWords.forEach(word => {
        if (lowerText.includes(word)) score -= 0.15;
    });
    
    score = Math.min(0.9, Math.max(-0.9, score));
    
    let sentiment = score > 0.2 ? 'positive' : (score < -0.2 ? 'negative' : 'neutral');
    let emotion = 'neutral';
    
    if (lowerText.includes('nostalgic') || lowerText.includes('nostalgia')) {
        emotion = 'nostalgia';
    } else if (lowerText.includes('hope') || lowerText.includes('hopeful')) {
        emotion = 'hope';
        sentiment = 'positive';
    } else if (lowerText.includes('grateful') || lowerText.includes('thankful')) {
        emotion = 'gratitude';
        sentiment = 'positive';
    } else if (lowerText.includes('calm') || lowerText.includes('peaceful')) {
        emotion = 'calm';
        sentiment = 'positive';
    } else if (lowerText.includes('lonely') || lowerText.includes('alone')) {
        emotion = 'loneliness';
        sentiment = 'negative';
    } else if (lowerText.includes('angry') || lowerText.includes('frustrated')) {
        emotion = 'anger';
        sentiment = 'negative';
    } else if (lowerText.includes('anxious') || lowerText.includes('anxiety')) {
        emotion = 'anxiety';
        sentiment = 'negative';
    } else if (lowerText.includes('sad') || lowerText.includes('depressed')) {
        emotion = 'sadness';
        sentiment = 'negative';
    } else if (score > 0.3) {
        emotion = 'joy';
    }
    
    return {
        sentiment: sentiment,
        score: score,
        emotion: emotion,
        explanation: `Detected ${sentiment} sentiment (score: ${score}). Emotion: ${emotion}.`
    };
}

// Make toggleExplanation globally available for onclick
window.toggleExplanation = toggleExplanation;

console.log('✅ Chat Module Loaded');