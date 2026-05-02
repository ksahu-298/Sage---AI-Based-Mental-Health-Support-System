/**
 * mood.js - Mood Tracking Module for Sage
 * 
 * Handles:
 * - Recording daily mood scores
 * - Rendering 7-day mood graph with Chart.js
 * - Displaying streak information
 * - Showing badges and progress
 * - Mood statistics and averages
 */

// ==================== GLOBAL VARIABLES ====================

let moodChart = null;
let currentMoodData = [];
let currentStreak = 0;
let currentBadges = [];

// ==================== INITIALIZATION ====================

/**
 * Initialize mood module
 * @param {string} chartCanvasId - ID of canvas element for chart
 */
async function initMood(chartCanvasId = 'moodChart') {
    await loadWeeklyMood();
    await loadStreakInfo();
    await loadBadges();
    setupMoodButtons();
}

/**
 * Setup mood button event listeners
 */
function setupMoodButtons() {
    const moodButtons = document.querySelectorAll('.mood-btn');
    moodButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const score = parseInt(btn.dataset.score);
            await recordMood(score);
        });
    });
}

// ==================== MOOD RECORDING ====================

/**
 * Record today's mood
 * @param {number} score - Mood score (1-10)
 * @param {string} note - Optional note
 */
async function recordMood(score, note = '') {
    try {
        const response = await MoodAPI.recordMood(score, note);
        
        if (response.success) {
            // Show success message
            showMoodFeedback(`✅ Mood recorded: ${score}/10! ${response.data.message || ''}`);
            
            // Refresh data
            await loadWeeklyMood();
            await loadStreakInfo();
            await loadBadges();
            
            // Update streak display
            updateStreakDisplay(response.data);
            
            return { success: true, data: response.data };
        } else {
            showMoodFeedback('❌ Could not save mood. Please try again.', 'error');
            return { success: false, error: response.error };
        }
    } catch (error) {
        console.error('Failed to record mood:', error);
        showMoodFeedback('❌ Network error. Please try again.', 'error');
        return { success: false, error: error.message };
    }
}

/**
 * Show mood recording feedback
 * @param {string} message - Message to display
 * @param {string} type - 'success' or 'error'
 */
function showMoodFeedback(message, type = 'success') {
    const feedbackDiv = document.getElementById('moodFeedback');
    if (!feedbackDiv) return;
    
    feedbackDiv.innerHTML = message;
    feedbackDiv.className = `alert alert-${type === 'success' ? 'success' : 'error'}`;
    feedbackDiv.style.display = 'block';
    
    setTimeout(() => {
        feedbackDiv.style.display = 'none';
    }, 3000);
}

// ==================== MOOD GRAPH ====================

/**
 * Load weekly mood data and render graph
 */
async function loadWeeklyMood() {
    try {
        const response = await MoodAPI.getWeekly();
        
        if (response.success && response.data) {
            currentMoodData = response.data.weekly_data;
            renderMoodGraph(currentMoodData);
            
            // Update average display
            if (response.data.average) {
                updateAverageDisplay(response.data.average);
            }
        } else {
            // Show empty state
            renderEmptyGraph();
        }
    } catch (error) {
        console.error('Failed to load weekly mood:', error);
        renderEmptyGraph();
    }
}

/**
 * Render mood graph using Chart.js
 * @param {Array} data - Weekly mood data array
 */
function renderMoodGraph(data) {
    const canvas = document.getElementById('moodChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data for chart
    const labels = data.map(d => d.day);
    const scores = data.map(d => d.score || null);
    const hasData = scores.some(s => s !== null);
    
    // Destroy existing chart
    if (moodChart) {
        moodChart.destroy();
    }
    
    if (!hasData) {
        renderEmptyGraph();
        return;
    }
    
    moodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mood Score (1-10)',
                data: scores,
                borderColor: '#2D6A4F',
                backgroundColor: 'rgba(45, 106, 79, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointBackgroundColor: scores.map(s => s ? '#2D6A4F' : '#ccc'),
                pointBorderColor: '#fff',
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 1,
                    max: 10,
                    title: {
                        display: true,
                        text: 'Mood Score',
                        color: '#4A5B4A'
                    },
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            const emojis = {1: '😔', 2: '😔', 3: '😐', 4: '😐', 5: '🙂', 6: '🙂', 7: '😊', 8: '😊', 9: '😍', 10: '😍'};
                            return `${value} ${emojis[value] || ''}`;
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Day',
                        color: '#4A5B4A'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            if (value === null) return 'No data';
                            const emojis = {1: '😔 Very Low', 2: '😔 Low', 3: '😐 Low', 4: '😐 Okay', 5: '🙂 Okay', 6: '🙂 Good', 7: '😊 Good', 8: '😊 Great', 9: '😍 Amazing', 10: '😍 Amazing'};
                            return `${emojis[value] || `Mood: ${value}/10`}`;
                        }
                    }
                },
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10
                    }
                }
            }
        }
    });
}

/**
 * Render empty graph state
 */
function renderEmptyGraph() {
    const canvas = document.getElementById('moodChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (moodChart) {
        moodChart.destroy();
    }
    
    // Display empty message on canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px Inter, sans-serif';
    ctx.fillStyle = '#8A9A8A';
    ctx.textAlign = 'center';
    ctx.fillText('No mood entries yet. Tap an emoji to start tracking!', canvas.width / 2, canvas.height / 2);
}

/**
 * Update average display
 * @param {number} average - Average mood score
 */
function updateAverageDisplay(average) {
    const avgElement = document.getElementById('moodAvgText');
    if (avgElement) {
        const emoji = getMoodEmoji(average);
        avgElement.innerHTML = `${emoji} 7-day average: ${average.toFixed(1)}/10`;
    }
}

/**
 * Get emoji for mood score
 * @param {number} score - Mood score (1-10)
 * @returns {string} - Emoji character
 */
function getMoodEmoji(score) {
    if (score >= 9) return '😍';
    if (score >= 7) return '😊';
    if (score >= 5) return '🙂';
    if (score >= 3) return '😐';
    return '😔';
}

// ==================== STREAK MANAGEMENT ====================

/**
 * Load streak information
 */
async function loadStreakInfo() {
    try {
        const response = await UserAPI.getStreak();
        
        if (response.success && response.data) {
            currentStreak = response.data.current_streak;
            updateStreakDisplay(response.data);
        }
    } catch (error) {
        console.error('Failed to load streak:', error);
    }
}

/**
 * Update streak display in UI
 * @param {object} streakData - Streak data from API
 */
function updateStreakDisplay(streakData) {
    const streakElement = document.getElementById('currentStreak');
    const longestElement = document.getElementById('longestStreak');
    const totalElement = document.getElementById('totalCheckins');
    const messageElement = document.getElementById('streakMessage');
    const warningElement = document.getElementById('streakWarning');
    
    if (streakElement) {
        streakElement.innerHTML = `🔥 ${streakData.current_streak || 0}`;
    }
    if (longestElement) {
        longestElement.innerText = streakData.longest_streak || 0;
    }
    if (totalElement) {
        totalElement.innerText = streakData.total_checkins || 0;
    }
    
    // Update streak message
    if (streakData.current_streak === 0) {
        if (messageElement) {
            messageElement.innerHTML = 'Start your streak by logging your mood today! 🌱';
        }
    } else if (streakData.current_streak === 1) {
        if (messageElement) {
            messageElement.innerHTML = `Great start! ${streakData.current_streak} day streak! Come back tomorrow! ⭐`;
        }
    } else {
        if (messageElement) {
            messageElement.innerHTML = `You're on a ${streakData.current_streak} day streak! Keep going! 🌟`;
        }
    }
    
    // Show warning if streak at risk
    if (warningElement && streakData.streak_warning) {
        warningElement.style.display = 'block';
        warningElement.innerHTML = streakData.streak_warning;
    } else if (warningElement) {
        warningElement.style.display = 'none';
    }
}

// ==================== BADGES ====================

/**
 * Load and display badges
 */
async function loadBadges() {
    try {
        const response = await UserAPI.getBadges();
        
        if (response.success && response.data) {
            currentBadges = response.data.earned_badges;
            displayBadges(currentBadges);
            
            // Update total badges count
            const totalElement = document.getElementById('totalBadges');
            if (totalElement) {
                totalElement.innerText = `${currentBadges.length}/${response.data.total_available}`;
            }
        }
    } catch (error) {
        console.error('Failed to load badges:', error);
    }
}

/**
 * Display badges in UI
 * @param {Array} badges - List of earned badges
 */
function displayBadges(badges) {
    const badgesContainer = document.getElementById('badgesList');
    if (!badgesContainer) return;
    
    if (badges.length === 0) {
        badgesContainer.innerHTML = `
            <div class="empty-badges">
                <i class="fas fa-medal"></i>
                <p>Your first badge unlocks when you check in today!</p>
            </div>
        `;
        return;
    }
    
    badgesContainer.innerHTML = badges.map(badge => `
        <div class="badge-item">
            <i class="fas fa-medal"></i>
            <span class="badge-name">${escapeHtml(badge.name)}</span>
            <span class="badge-description">${escapeHtml(badge.description || '')}</span>
        </div>
    `).join('');
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

// ==================== STATISTICS ====================

/**
 * Load mood statistics
 */
async function loadMoodStats() {
    try {
        const response = await MoodAPI.getStats();
        
        if (response.success && response.data && response.data.has_data) {
            updateStatsDisplay(response.data);
        }
    } catch (error) {
        console.error('Failed to load mood stats:', error);
    }
}

/**
 * Update statistics display
 * @param {object} stats - Statistics data
 */
function updateStatsDisplay(stats) {
    const avgElement = document.getElementById('statsAverage');
    const trendElement = document.getElementById('statsTrend');
    const bestElement = document.getElementById('statsBest');
    const worstElement = document.getElementById('statsWorst');
    
    if (avgElement) {
        avgElement.innerHTML = `${stats.average}/10`;
    }
    if (trendElement) {
        const trendIcon = stats.trend === 'improving' ? '📈' : (stats.trend === 'declining' ? '📉' : '📊');
        trendElement.innerHTML = `${trendIcon} ${stats.trend_message}`;
    }
    if (bestElement) {
        bestElement.innerHTML = `${getMoodEmoji(stats.highest_score)} ${stats.highest_score}/10 on ${stats.highest_date}`;
    }
    if (worstElement) {
        worstElement.innerHTML = `${getMoodEmoji(stats.lowest_score)} ${stats.lowest_score}/10 on ${stats.lowest_date}`;
    }
}

// ==================== EXPORT ====================

// Make functions globally available
window.mood = {
    init: initMood,
    recordMood,
    loadWeeklyMood,
    loadStreakInfo,
    loadBadges,
    loadMoodStats,
    getMoodEmoji,
    showMoodFeedback
};

console.log('✅ Mood Module Loaded');