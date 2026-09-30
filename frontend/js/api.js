/**
 * api.js - API Service for Sage Mental Health Companion
 * Handles all backend communication with automatic token management
 * 
 * Base URL: http://localhost:5000/api
 * All functions return Promises with standardized response format
 */

const API_BASE_URL = 'https://sage-ai-based-mental-health-support-system-production.up.railway.app/api'; // Update with your backend URL

/**
 * Get authentication token from localStorage
 */
function getAuthToken() {
    return localStorage.getItem('token');
}

/**
 * Save authentication token to localStorage
 */
function setAuthToken(token) {
    localStorage.setItem('token', token);
}

/**
 * Remove authentication token (logout)
 */
function removeAuthToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

/**
 * Get current user from localStorage
 */
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        return JSON.parse(userStr);
    }
    return null;
}

/**
 * Save current user to localStorage
 */
function setCurrentUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

/**
 * Generic fetch wrapper with error handling and token
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getAuthToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            // Handle token expiration
            if (response.status === 401) {
                removeAuthToken();
                window.location.href = 'login.html';
            }
            throw new Error(data.error || data.message || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// ==================== AUTHENTICATION APIS ====================

const AuthAPI = {
    /**
     * Login user with username/email and password
     * @param {string} username - Username or email
     * @param {string} password - Password
     */
    async login(username, password) {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (response.success && response.data) {
            setAuthToken(response.data.token);
            setCurrentUser(response.data.user);
        }
        
        return response;
    },
    
    /**
     * Register new user
     * @param {string} username - Desired username
     * @param {string} password - Password
     * @param {string} email - Email address (optional)
     */
    async register(username, password, email = '') {
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, email })
        });
        
        if (response.success && response.data) {
            setAuthToken(response.data.token);
            setCurrentUser(response.data.user);
        }
        
        return response;
    },
    
    /**
     * Logout user
     */
    async logout() {
        try {
            await apiRequest('/auth/logout', { method: 'POST' });
        } catch (error) {
            // Ignore errors on logout
        } finally {
            removeAuthToken();
            window.location.href = 'index.html';
        }
    },
    
    /**
     * Get current user info
     */
    async getCurrentUserInfo() {
        return await apiRequest('/auth/me');
    },
    
    /**
     * Change password
     * @param {string} currentPassword - Current password
     * @param {string} newPassword - New password
     */
    async changePassword(currentPassword, newPassword) {
        return await apiRequest('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
        });
    },
    
    /**
     * Google OAuth login
     * @param {object} googleData - Google OAuth response data
     */
    async googleLogin(googleData) {
        const response = await apiRequest('/auth/google', {
            method: 'POST',
            body: JSON.stringify(googleData)
        });
        
        if (response.success && response.data) {
            setAuthToken(response.data.token);
            setCurrentUser(response.data.user);
        }
        
        return response;
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!getAuthToken();
    }
};

// ==================== CHAT APIS ====================

const ChatAPI = {
    /**
     * Send a message to Sage
     * @param {string} message - User's message
     */
    async sendMessage(message) {
        return await apiRequest('/chat/send', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    },
    
    /**
     * Get chat history
     * @param {number} limit - Number of messages (default 50)
     * @param {number} offset - Pagination offset
     */
    async getHistory(limit = 50, offset = 0) {
        return await apiRequest(`/chat/history?limit=${limit}&offset=${offset}`);
    },
    
    /**
     * Get single message by ID
     * @param {number} messageId - Message ID
     */
    async getMessage(messageId) {
        return await apiRequest(`/chat/history/${messageId}`);
    },
    
    /**
     * Submit feedback for a response
     * @param {number} messageId - Message ID (Sage response)
     * @param {number} rating - Rating 1-5
     * @param {boolean} wasHelpful - Whether response was helpful
     */
    async submitFeedback(messageId, rating, wasHelpful) {
        return await apiRequest(`/chat/feedback/${messageId}`, {
            method: 'POST',
            body: JSON.stringify({ rating, was_helpful: wasHelpful })
        });
    },
    
    /**
     * Clear all chat history
     */
    async clearHistory() {
        return await apiRequest('/chat/history', { method: 'DELETE' });
    },
    
    /**
     * Get conversation context (last 10 messages)
     */
    async getContext() {
        return await apiRequest('/chat/context');
    }
};

// ==================== MOOD APIS ====================

const MoodAPI = {
    /**
     * Record today's mood
     * @param {number} score - Mood score 1-10
     * @param {string} note - Optional note
     * @param {string} timeOfDay - Optional time of day
     */
    async recordMood(score, note = '', timeOfDay = null) {
        return await apiRequest('/mood/record', {
            method: 'POST',
            body: JSON.stringify({ score, note, time_of_day: timeOfDay })
        });
    },
    
    /**
     * Get mood history
     * @param {number} days - Number of days to fetch
     */
    async getHistory(days = 30) {
        return await apiRequest(`/mood/history?days=${days}`);
    },
    
    /**
     * Get weekly mood data for graph
     */
    async getWeekly() {
        return await apiRequest('/mood/weekly');
    },
    
    /**
     * Get mood statistics
     */
    async getStats() {
        return await apiRequest('/mood/stats');
    },
    
    /**
     * Export mood data as CSV
     */
    async exportData() {
        window.open(`${API_BASE_URL}/mood/export?token=${getAuthToken()}`);
    },
    
    /**
     * Check if user logged mood today
     */
    async checkToday() {
        return await apiRequest('/mood/check-today');
    },
    
    /**
     * Get calendar data for a specific month
     * @param {number} year - Year
     * @param {number} month - Month (1-12)
     */
    async getCalendar(year, month) {
        return await apiRequest(`/mood/calendar?year=${year}&month=${month}`);
    }
};

// ==================== JOURNAL APIS ====================

const JournalAPI = {
    /**
     * Create a new journal entry
     * @param {string} content - Journal content
     * @param {string} title - Optional title
     * @param {string} promptUsed - Optional prompt used
     */
    async create(content, title = '', promptUsed = '') {
        return await apiRequest('/journal/create', {
            method: 'POST',
            body: JSON.stringify({ content, title, prompt_used: promptUsed })
        });
    },
    
    /**
     * Get journal entries list
     * @param {number} limit - Number of entries
     * @param {number} offset - Pagination offset
     * @param {boolean} favoriteOnly - Show only favorites
     */
    async list(limit = 20, offset = 0, favoriteOnly = false) {
        let url = `/journal/list?limit=${limit}&offset=${offset}`;
        if (favoriteOnly) url += '&favorite=true';
        return await apiRequest(url);
    },
    
    /**
     * Get single journal entry
     * @param {number} entryId - Entry ID
     */
    async get(entryId) {
        return await apiRequest(`/journal/${entryId}`);
    },
    
    /**
     * Update journal entry
     * @param {number} entryId - Entry ID
     * @param {object} data - Updated data
     */
    async update(entryId, data) {
        return await apiRequest(`/journal/${entryId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * Delete journal entry
     * @param {number} entryId - Entry ID
     */
    async delete(entryId) {
        return await apiRequest(`/journal/${entryId}`, { method: 'DELETE' });
    },
    
    /**
     * Toggle favorite status
     * @param {number} entryId - Entry ID
     */
    async toggleFavorite(entryId) {
        return await apiRequest(`/journal/${entryId}/favorite`, { method: 'POST' });
    },
    
    /**
     * Get journal prompts
     * @param {string} emotion - Optional emotion filter
     */
    async getPrompts(emotion = null) {
        let url = '/journal/prompts';
        if (emotion) url += `?emotion=${emotion}`;
        return await apiRequest(url);
    },
    
    /**
     * Get random journal prompt
     * @param {string} category - Optional category
     */
    async getRandomPrompt(category = null) {
        let url = '/journal/prompts/random';
        if (category) url += `?category=${category}`;
        return await apiRequest(url);
    },
    
    /**
     * Export all journal entries as CSV
     */
    async exportData() {
        window.open(`${API_BASE_URL}/journal/export?token=${getAuthToken()}`);
    },
    
    /**
     * Get journal statistics
     */
    async getStats() {
        return await apiRequest('/journal/stats');
    }
};

// ==================== USER APIS ====================

const UserAPI = {
    /**
     * Get user profile
     */
    async getProfile() {
        return await apiRequest('/user/profile');
    },
    
    /**
     * Update user profile
     * @param {object} data - Profile data to update
     */
    async updateProfile(data) {
        return await apiRequest('/user/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * Get streak information
     */
    async getStreak() {
        return await apiRequest('/user/streak');
    },
    
    /**
     * Get user badges
     */
    async getBadges() {
        return await apiRequest('/user/badges');
    },
    
    /**
     * Get all available badges
     */
    async getAllBadges() {
        return await apiRequest('/user/badges/all');
    },
    
    /**
     * Get user preferences
     */
    async getPreferences() {
        return await apiRequest('/user/preferences');
    },
    
    /**
     * Update user preferences
     * @param {object} preferences - Preferences object
     */
    async updatePreferences(preferences) {
        return await apiRequest('/user/preferences', {
            method: 'PUT',
            body: JSON.stringify(preferences)
        });
    },
    
    /**
     * Get dashboard data (all in one call)
     */
    async getDashboard() {
        return await apiRequest('/user/dashboard');
    },
    
    /**
     * Delete user account (permanent)
     * @param {boolean} confirm - Confirmation flag
     */
    async deleteAccount(confirm = true) {
        return await apiRequest('/user/account', {
            method: 'DELETE',
            body: JSON.stringify({ confirm })
        });
    }
};

// ==================== HELPLINES APIS ====================

const HelplinesAPI = {
    /**
     * Get all Indian helplines
     */
    async getAll() {
        return await apiRequest('/helplines/all');
    },
    
    /**
     * Get emergency numbers only
     */
    async getEmergency() {
        return await apiRequest('/helplines/emergency');
    },
    
    /**
     * Get formatted crisis response
     */
    async getCrisis() {
        return await apiRequest('/helplines/crisis');
    },
    
    /**
     * Get KIRAN helpline details
     */
    async getKiran() {
        return await apiRequest('/helplines/kiran');
    },
    
    /**
     * Get iCall helpline details
     */
    async getICall() {
        return await apiRequest('/helplines/icall');
    },
    
    /**
     * Get Vandrevala helpline details
     */
    async getVandrevala() {
        return await apiRequest('/helplines/vandrevala');
    },
    
    /**
     * Get AASRA helpline details
     */
    async getAasra() {
        return await apiRequest('/helplines/aasra');
    },
    
    /**
     * Get NIMHANS helpline details
     */
    async getNimhans() {
        return await apiRequest('/helplines/nimhans');
    },
    
    /**
     * Get Snehi helpline details
     */
    async getSnehi() {
        return await apiRequest('/helplines/snehi');
    },
    
    /**
     * Get state-specific helplines
     * @param {string} state - State name
     */
    async getStateHelplines(state) {
        return await apiRequest(`/helplines/state?state=${encodeURIComponent(state)}`);
    }
};

// ==================== EXPORT ====================

// Make APIs available globally
window.AuthAPI = AuthAPI;
window.ChatAPI = ChatAPI;
window.MoodAPI = MoodAPI;
window.JournalAPI = JournalAPI;
window.UserAPI = UserAPI;
window.HelplinesAPI = HelplinesAPI;
window.getCurrentUser = getCurrentUser;
window.isAuthenticated = () => !!getAuthToken();

console.log('✅ Sage API Service Loaded');