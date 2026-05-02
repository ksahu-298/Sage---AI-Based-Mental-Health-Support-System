/**
 * sentiment.js - Sentiment Analysis Module for Sage
 * Handles sentiment analysis display and API calls
 */

const API_URL = 'http://localhost:5000/api';

// Emotion to emoji mapping
const EMOTION_EMOJIS = {
    'joy': '😊',
    'gratitude': '🙏',
    'sadness': '😔',
    'anxiety': '🌬️',
    'anger': '⚡',
    'loneliness': '💔',
    'calm': '🧘',
    'hope': '🌈',
    'nostalgia': '🕰️',
    'neutral': '😐'
};

// Get sentiment for a message
async function fetchSentiment(messageId) {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch(`${API_URL}/chat/sentiment/${messageId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.success ? data.data : null;
        }
    } catch (error) {
        console.error('Error fetching sentiment:', error);
    }
    return null;
}

// Show sentiment popup modal
function showSentimentPopup(sentimentData) {
    // Remove existing modal if any
    const existingModal = document.querySelector('.sentiment-modal');
    if (existingModal) existingModal.remove();
    
    const emoji = EMOTION_EMOJIS[sentimentData.emotion] || '📊';
    const sentimentColor = sentimentData.sentiment === 'positive' ? '#2D6A4F' : 
                          (sentimentData.sentiment === 'negative' ? '#DC2626' : '#8A9A8A');
    
    const modal = document.createElement('div');
    modal.className = 'sentiment-modal';
    modal.innerHTML = `
        <div class="sentiment-modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;">
            <div class="sentiment-modal-content" style="background: white; border-radius: 1.5rem; padding: 1.5rem; max-width: 380px; width: 90%; margin: 1rem; box-shadow: 0 20px 40px rgba(0,0,0,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="color: #1B3A2B; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-chart-line"></i> Sentiment Analysis
                    </h3>
                    <button onclick="this.closest('.sentiment-modal').remove()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #8A9A8A;">&times;</button>
                </div>
                
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div style="font-size: 3.5rem;">${emoji}</div>
                    <div style="font-size: 1.3rem; font-weight: 600; color: ${sentimentColor}; margin-top: 0.5rem;">
                        ${sentimentData.emotion ? sentimentData.emotion.charAt(0).toUpperCase() + sentimentData.emotion.slice(1) : 'Neutral'}
                    </div>
                    <div style="font-size: 0.85rem; color: #6B7E6B; margin-top: 0.25rem;">
                        Score: ${sentimentData.score} (${sentimentData.sentiment})
                    </div>
                </div>
                
                <div style="background: #F5F7F2; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem;">
                    <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; white-space: pre-line;">${sentimentData.explanation || 'Analysis complete.'}</p>
                </div>
                
                <div style="display: flex; gap: 0.75rem;">
                    <button onclick="this.closest('.sentiment-modal').remove()" style="flex: 1; padding: 0.6rem; background: #2D6A4F; color: white; border: none; border-radius: 2rem; cursor: pointer; font-size: 0.85rem;">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('sentiment-modal-overlay')) {
            modal.remove();
        }
    });
}

// Main function to show sentiment for a message
async function showSentiment(messageId, messageText) {
    try {
        const sentimentData = await fetchSentiment(messageId);
        
        if (sentimentData) {
            showSentimentPopup(sentimentData);
        } else {
            // Fallback local analysis
            const localAnalysis = analyzeLocalSentiment(messageText);
            showSentimentPopup(localAnalysis);
        }
    } catch (error) {
        console.error('Error:', error);
        const localAnalysis = analyzeLocalSentiment(messageText);
        showSentimentPopup(localAnalysis);
    }
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
    
    // Detect specific emotions
    if (lowerText.includes('nostalgic') || lowerText.includes('nostalgia') || lowerText.includes('remember when')) {
        emotion = 'nostalgia';
    } else if (lowerText.includes('hope') || lowerText.includes('hopeful') || lowerText.includes('optimistic')) {
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
    } else if (lowerText.includes('anxious') || lowerText.includes('anxiety') || lowerText.includes('worried')) {
        emotion = 'anxiety';
        sentiment = 'negative';
    } else if (lowerText.includes('sad') || lowerText.includes('depressed')) {
        emotion = 'sadness';
        sentiment = 'negative';
    } else if (score > 0.3) {
        emotion = 'joy';
    }
    
    let explanation = '';
    if (sentiment === 'positive') {
        explanation = '😊 This message has a positive emotional tone. ';
    } else if (sentiment === 'negative') {
        explanation = '💙 This message has a negative emotional tone. Remember that it\'s okay to feel this way. ';
    } else {
        explanation = '😐 This message has a neutral emotional tone. ';
    }
    
    if (emotion !== 'neutral') {
        explanation += `Detected emotion: ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}.`;
    }
    
    return {
        sentiment: sentiment,
        score: score,
        emotion: emotion,
        explanation: explanation
    };
}