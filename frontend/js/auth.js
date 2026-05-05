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

// FIXED: Use same keys as api.js and login.html
const AUTH_TOKEN_KEY = 'token';
const USER_DATA_KEY = 'user';
const TOKEN_EXPIRY_BUFFER = 5 * 60 * 1000; // 5 minutes buffer before expiry

// ==================== TOKEN MANAGEMENT ====================

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function removeToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_DATA_KEY);
}

function hasToken() {
    return !!getToken();
}

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

function isTokenExpired(token) {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return true;
    const expiryTime = decoded.exp * 1000;
    const currentTime = Date.now();
    return currentTime >= (expiryTime - TOKEN_EXPIRY_BUFFER);
}

function isTokenValid() {
    const token = getToken();
    if (!token) return false;
    // FIXED: Reject clearly fake/demo tokens
    if (token === 'demo-token' || token.split('.').length !== 3) return false;
    return !isTokenExpired(token);
}

// ==================== USER MANAGEMENT ====================

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

function setUser(user) {
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
}

function getUsername() {
    const user = getUser();
    return user ? user.username : null;
}

function getUserAvatarInitial() {
    const username = getUsername();
    if (username && username.length > 0) {
        return username.charAt(0).toUpperCase();
    }
    return 'U';
}

function updateLocalStreak(streak, longestStreak, totalCheckins) {
    const user = getUser();
    if (user) {
        user.streak = streak;
        user.longest_streak = longestStreak;
        user.total_checkins = totalCheckins;
        setUser(user);
    }
}

function updateLocalBadges(badges) {
    const user = getUser();
    if (user) {
        user.badges = badges;
        setUser(user);
    }
}

// ==================== LOGIN / REGISTRATION ====================

async function login(username, password) {
    try {
        const response = await AuthAPI.login(username, password);
        if (response.success && response.data) {
            return { success: true, user: response.data.user };
        } else {
            return { success: false, error: response.error || 'Login failed' };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: error.message || 'Network error' };
    }
}

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

async function logout() {
    await AuthAPI.logout();
}

function localLogout() {
    removeToken();
    window.location.href = 'index.html';
}

// ==================== SESSION MANAGEMENT ====================

function checkAuth(redirectToLogin = true) {
    const isValid = isTokenValid();

    if (!isValid && redirectToLogin) {
        removeToken(); // Clear any invalid/demo token
        const currentPage = window.location.pathname;
        if (!currentPage.includes('login.html') &&
            !currentPage.includes('index.html')) {
            window.location.href = 'login.html';
        }
        return false;
    }

    return isValid;
}

function protectPage() {
    if (!checkAuth(true)) {
        return false;
    }
    refreshUserData();
    return true;
}

function redirectIfLoggedIn() {
    if (isTokenValid()) {
        window.location.href = 'dashboard.html';
        return true;
    }
    return false;
}

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

function initGoogleSignIn(clientId) {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    window.handleGoogleCredentialResponse = async (response) => {
        const credential = response.credential;
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
                    alert('Google login failed. Please try again.');
                }
            } catch (error) {
                alert('Google login failed. Please try again.');
            }
        }
    };
}

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

async function changePassword(currentPassword, newPassword, confirmPassword) {
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

async function forgotPassword(email) {
    console.log('Password reset requested for:', email);
    return { success: true, message: 'If an account exists with this email, you will receive reset instructions.' };
}

// ==================== EXPORTS ====================

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