/**
 * auth.js - Authentication Module for Sage
 * 
 * Handles:
 * - User login and registration
 * - Session management
 * - Token validation
 * - Route protection
 * - Auto-logout on token expiry
 */

// ==================== CONSTANTS ====================

const AUTH_TOKEN_KEY = 'sage_auth_token';
const USER_DATA_KEY = 'sage_user_data';
const TOKEN_EXPIRY_BUFFER = 5 * 60 * 1000; // 5 minutes buffer before expiry

// ==================== TOKEN MANAGEMENT ====================

/**
 * Get stored auth token
 */
function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Set auth token
 */
function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove auth token (logout)
 */
function removeToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_DATA_KEY);
}

/**
 * Check if token exists (not validated)
 */
function hasToken() {
    return !!getToken();
}

/**
 * Decode JWT token payload (without verification)
 */
function decodeToken(token) {
    try {
        const payload = token.split('.')[1];
        const decoded = atob(payload);
        return JSON.parse(decoded);
    } catch (e) {
        console.error('Failed to decode token:', e);
        return null;
    }
}

/**
 * Check if token is expired
 */
function isTokenExpired(token) {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return true;
    
    const expiryTime = decoded.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();
    
    return currentTime >= (expiryTime - TOKEN_EXPIRY_BUFFER);
}

/**
 * Validate current token
 */
function isTokenValid() {
    const token = getToken();
    if (!token) return false;
    return !isTokenExpired(token);
}

// ==================== USER MANAGEMENT ====================

/**
 * Get stored user data
 */
function getUser() {
    const userStr = localStorage.getItem(USER_DATA_KEY);
    if (userStr) {
        try {
            return JSON.parse(userStr);
        } catch (e) {
            return null;
        }
    }
    return null;
}

/**
 * Set user data
 */
function setUser(user) {
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
}

/**
 * Get current username
 */
function getUsername() {
    const user = getUser();
    return user ? user.username : null;
}

/**
 * Get user avatar initial
 */
function getUserAvatarInitial() {
    const username = getUsername();
    if (username && username.length > 0) {
        return username.charAt(0).toUpperCase();
    }
    return 'U';
}

/**
 * Update user streak locally
 */
function updateLocalStreak(streak, longestStreak, totalCheckins) {
    const user = getUser();
    if (user) {
        user.streak = streak;
        user.longest_streak = longestStreak;
        user.total_checkins = totalCheckins;
        setUser(user);
    }
}

/**
 * Update user badges locally
 */
function updateLocalBadges(badges) {
    const user = getUser();
    if (user) {
        user.badges = badges;
        setUser(user);
    }
}

// ==================== LOGIN / REGISTRATION ====================

/**
 * Login with username/email and password
 */
async function login(username, password) {
    try {
        const response = await AuthAPI.login(username, password);
        
        if (response.success && response.data) {
            // Store token and user data (handled by API)
            return { success: true, user: response.data.user };
        } else {
            return { success: false, error: response.error || 'Login failed' };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: error.message || 'Network error' };
    }
}

/**
 * Register new user
 */
async function register(username, password, email = '') {
    try {
        const response = await AuthAPI.register(username, password, email);
        
        if (response.success && response.data) {
            return { success: true, user: response.data.user };
        } else {
            return { success: false, error: response.error || 'Registration failed' };
        }
    } catch (error) {
        console.error('Registration error:', error);
        return { success: false, error: error.message || 'Network error' };
    }
}

/**
 * Logout user
 */
async function logout() {
    await AuthAPI.logout();
    // AuthAPI.logout already redirects to index.html
}

/**
 * Local logout (without API call)
 */
function localLogout() {
    removeToken();
    window.location.href = 'index.html';
}

// ==================== SESSION MANAGEMENT ====================

/**
 * Check authentication status and redirect if needed
 * @param {boolean} redirectToLogin - Whether to redirect to login if unauthenticated
 * @returns {boolean} - Whether user is authenticated
 */
function checkAuth(redirectToLogin = true) {
    const isValid = isTokenValid();
    
    if (!isValid && redirectToLogin) {
        // Clear invalid token
        removeToken();
        
        // Don't redirect if already on login or index page
        const currentPage = window.location.pathname;
        if (!currentPage.includes('login.html') && 
            !currentPage.includes('index.html')) {
            window.location.href = 'login.html';
        }
        return false;
    }
    
    return isValid;
}

/**
 * Protect page - redirect to login if not authenticated
 * Call this on page load for protected pages
 */
function protectPage() {
    if (!checkAuth(true)) {
        return false;
    }
    
    // Optionally refresh user data
    refreshUserData();
    return true;
}

/**
 * Redirect to dashboard if already logged in
 * Call this on login/landing pages
 */
function redirectIfLoggedIn() {
    if (isTokenValid()) {
        window.location.href = 'dashboard.html';
        return true;
    }
    return false;
}

/**
 * Refresh user data from server
 */
async function refreshUserData() {
    if (!isTokenValid()) return null;
    
    try {
        const response = await UserAPI.getProfile();
        if (response.success && response.data) {
            setUser(response.data.profile);
            return response.data.profile;
        }
    } catch (error) {
        console.error('Failed to refresh user data:', error);
    }
    return null;
}

/**
 * Get dashboard data (prefetched for dashboard page)
 */
async function getDashboardData() {
    if (!isTokenValid()) return null;
    
    try {
        const response = await UserAPI.getDashboard();
        if (response.success) {
            return response.data;
        }
    } catch (error) {
        console.error('Failed to get dashboard data:', error);
    }
    return null;
}

// ==================== GOOGLE OAUTH ====================

/**
 * Initialize Google Sign-In
 * @param {string} clientId - Google OAuth Client ID
 */
function initGoogleSignIn(clientId) {
    // Load Google Identity Services script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    
    window.handleGoogleCredentialResponse = async (response) => {
        const credential = response.credential;
        
        // Decode JWT to get user info
        const decoded = decodeToken(credential);
        if (decoded) {
            const googleData = {
                google_id: decoded.sub,
                email: decoded.email,
                name: decoded.name,
                avatar: decoded.picture
            };
            
            try {
                const result = await AuthAPI.googleLogin(googleData);
                if (result.success) {
                    window.location.href = 'dashboard.html';
                } else {
                    console.error('Google login failed:', result.error);
                    alert('Google login failed. Please try again.');
                }
            } catch (error) {
                console.error('Google login error:', error);
                alert('Google login failed. Please try again.');
            }
        }
    };
}

/**
 * Render Google Sign-In button
 * @param {string} elementId - Container element ID
 * @param {string} clientId - Google OAuth Client ID
 */
function renderGoogleButton(elementId, clientId) {
    if (!window.google) {
        console.warn('Google Identity Services not loaded yet');
        return;
    }
    
    window.google.accounts.id.initialize({
        client_id: clientId,
        callback: window.handleGoogleCredentialResponse
    });
    
    window.google.accounts.id.renderButton(
        document.getElementById(elementId),
        { theme: 'outline', size: 'large', width: '100%' }
    );
}

// ==================== PASSWORD MANAGEMENT ====================

/**
 * Change user password
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 */
async function changePassword(currentPassword, newPassword, confirmPassword) {
    // Validate
    if (newPassword.length < 6) {
        return { success: false, error: 'Password must be at least 6 characters' };
    }
    
    if (newPassword !== confirmPassword) {
        return { success: false, error: 'New passwords do not match' };
    }
    
    try {
        const response = await AuthAPI.changePassword(currentPassword, newPassword);
        if (response.success) {
            return { success: true, message: 'Password changed successfully' };
        } else {
            return { success: false, error: response.error || 'Password change failed' };
        }
    } catch (error) {
        return { success: false, error: error.message || 'Network error' };
    }
}

/**
 * Forgot password - send reset email
 * @param {string} email - User's email address
 */
async function forgotPassword(email) {
    // This would call a password reset endpoint
    // For now, show demo message
    console.log('Password reset requested for:', email);
    return { success: true, message: 'If an account exists with this email, you will receive reset instructions.' };
}

// ==================== EXPORTS ====================

// Global exports for use in HTML
window.auth = {
    getToken,
    setToken,
    removeToken,
    hasToken,
    isTokenValid,
    getUser,
    setUser,
    getUsername,
    getUserAvatarInitial,
    updateLocalStreak,
    updateLocalBadges,
    login,
    register,
    logout,
    localLogout,
    checkAuth,
    protectPage,
    redirectIfLoggedIn,
    refreshUserData,
    getDashboardData,
    changePassword,
    forgotPassword,
    initGoogleSignIn,
    renderGoogleButton
};

console.log('✅ Auth Module Loaded');