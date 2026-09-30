"""
gamification.py - Gamification Service for streaks, badges, and rewards

Features:
- Daily streak tracking for mood check-ins
- Badge system for achievements
- Motivational messages based on progress
- Milestone celebrations
- User progress statistics
"""

from datetime import datetime, timedelta
from ..utils.helpers import get_today_date, get_yesterday_date

class GamificationService:
    """Main service for managing streaks, badges, and rewards"""
    
    # All available badges in the system
    AVAILABLE_BADGES = {
        'first_step': {
            'name': 'First Step',
            'description': 'Completed your first mood check-in',
            'icon': '👣',  # footstep emoji
            'requirement_type': 'checkin',
            'requirement_value': 1,
            'reward_message': "🎉 You've taken your first step! Every journey begins with a single step. Keep going!"
        },
        'resilience_star': {
            'name': 'Resilience Star',
            'description': '7-day check-in streak',
            'icon': '⭐',
            'requirement_type': 'streak',
            'requirement_value': 7,
            'reward_message': "🌟 Amazing! 7 days in a row! You've earned the Resilience Star badge. Your consistency is inspiring!"
        },
        'mindful_warrior': {
            'name': 'Mindful Warrior',
            'description': '14-day check-in streak',
            'icon': '🧘',
            'requirement_type': 'streak',
            'requirement_value': 14,
            'reward_message': "🧘‍♂️ Wow! 14 consecutive days! You're building incredible mindfulness habits. Mindful Warrior badge unlocked!"
        },
        'wellness_champion': {
            'name': 'Wellness Champion',
            'description': '30-day check-in streak',
            'icon': '🏆',
            'requirement_type': 'streak',
            'requirement_value': 30,
            'reward_message': "🏆 EXCEPTIONAL! 30 days of consistent self-care! You are a Wellness Champion! This is a huge achievement!"
        },
        'journal_keeper': {
            'name': 'Journal Keeper',
            'description': 'Wrote 10 journal entries',
            'icon': '📔',
            'requirement_type': 'journal_entries',
            'requirement_value': 10,
            'reward_message': "📔 You've written 10 journal entries! The Journal Keeper badge is yours. Writing helps heal."
        },
        'dedicated_journaler': {
            'name': 'Dedicated Journaler',
            'description': 'Wrote 50 journal entries',
            'icon': '📚',
            'requirement_type': 'journal_entries',
            'requirement_value': 50,
            'reward_message': "📚 50 journal entries! Your dedication to self-reflection is remarkable. Dedicated Journaler badge unlocked!"
        },
        'emotion_explorer': {
            'name': 'Emotion Explorer',
            'description': 'Logged 5 different mood types',
            'icon': '🎭',
            'requirement_type': 'mood_variety',
            'requirement_value': 5,
            'reward_message': "🎭 You've experienced and logged 5 different emotions! The Emotion Explorer badge celebrates your emotional awareness."
        },
        'chat_companion': {
            'name': 'Chat Companion',
            'description': 'Sent 50 messages to Sage',
            'icon': '💬',
            'requirement_type': 'chat_messages',
            'requirement_value': 50,
            'reward_message': "💬 50 conversations with Sage! You're building a beautiful practice of reaching out. Chat Companion badge earned!"
        },
        'gratitude_guru': {
            'name': 'Gratitude Guru',
            'description': 'Completed 5 gratitude journal entries',
            'icon': '🙏',
            'requirement_type': 'gratitude_entries',
            'requirement_value': 5,
            'reward_message': "🙏 Practicing gratitude regularly! The Gratitude Guru badge celebrates your positive focus."
        },
        'early_riser': {
            'name': 'Early Riser',
            'description': 'Logged mood before 9 AM, 5 times',
            'icon': '🌅',
            'requirement_type': 'morning_checkins',
            'requirement_value': 5,
            'reward_message': "🌅 Morning check-ins build a positive start to your day! Early Riser badge unlocked!"
        },
        'night_owl': {
            'name': 'Night Owl',
            'description': 'Logged mood after 10 PM, 5 times',
            'icon': '🦉',
            'requirement_type': 'evening_checkins',
            'requirement_value': 5,
            'reward_message': "🦉 Reflecting on your day before sleep is powerful. Night Owl badge is yours!"
        },
        'streak_saver': {
            'name': 'Streak Saver',
            'description': 'Recovered a streak after breaking it',
            'icon': '🔄',
            'requirement_type': 'streak_recovery',
            'requirement_value': 1,
            'reward_message': "🔄 You came back after a break! That takes real courage. Streak Saver badge celebrates your resilience!"
        }
    }
    
    def __init__(self):
        self.badges = self.AVAILABLE_BADGES
    
    def update_streak(self, user, checkin_date=None):
        """
        Update user's streak based on check-in
        Returns: (new_streak, is_new_record, newly_earned_badges)
        """
        if checkin_date is None:
            checkin_date = get_today_date()
        
        today = checkin_date
        yesterday = get_yesterday_date()
        
        old_streak = user.streak
        last_checkin = user.last_checkin if hasattr(user, 'last_checkin') else None
        
        # Calculate new streak
        if last_checkin == today:
            # Already checked in today
            new_streak = old_streak
            is_new_record = False
        elif last_checkin == yesterday:
            # Consecutive day
            new_streak = old_streak + 1
            is_new_record = new_streak > user.longest_streak
        else:
            # Streak broken or first check-in
            new_streak = 1
            is_new_record = False
            
            # Check if this is a streak recovery (was broken)
            if old_streak > 0 and last_checkin and last_checkin != yesterday:
                # User came back after break - award streak saver badge if eligible
                self.award_badge_if_not_earned(user, 'streak_saver')
        
        # Update user streak
        user.streak = new_streak
        user.last_checkin = today
        
        if is_new_record:
            user.longest_streak = new_streak
        
        # Check for streak-based badges
        newly_earned = self.check_streak_badges(user, new_streak)
        
        return {
            'new_streak': new_streak,
            'is_new_record': is_new_record,
            'old_streak': old_streak,
            'newly_earned_badges': newly_earned
        }
    
    def check_streak_badges(self, user, current_streak):
        """
        Check and award streak-based badges
        Returns list of newly awarded badge names
        """
        newly_earned = []
        
        streak_badges = [
            ('resilience_star', 7),
            ('mindful_warrior', 14),
            ('wellness_champion', 30)
        ]
        
        for badge_key, required_streak in streak_badges:
            if current_streak >= required_streak:
                if self.award_badge_if_not_earned(user, badge_key):
                    newly_earned.append(self.badges[badge_key]['name'])
        
        return newly_earned
    
    def check_mood_based_badges(self, user, mood_history):
        """
        Check and award mood-related badges
        """
        newly_earned = []
        
        # Check for Emotion Explorer (5 different moods logged)
        unique_moods = set()
        for mood_entry in mood_history:
            score = mood_entry.get('mood_score', mood_entry if isinstance(mood_entry, int) else 0)
            # Categorize mood score into mood type
            if score >= 9:
                unique_moods.add('amazing')
            elif score >= 7:
                unique_moods.add('good')
            elif score >= 5:
                unique_moods.add('okay')
            elif score >= 3:
                unique_moods.add('low')
            else:
                unique_moods.add('very_low')
        
        if len(unique_moods) >= 5:
            if self.award_badge_if_not_earned(user, 'emotion_explorer'):
                newly_earned.append(self.badges['emotion_explorer']['name'])
        
        return newly_earned
    
    def check_journal_based_badges(self, user, journal_count):
        """
        Check and award journal-related badges
        """
        newly_earned = []
        
        if journal_count >= 10:
            if self.award_badge_if_not_earned(user, 'journal_keeper'):
                newly_earned.append(self.badges['journal_keeper']['name'])
        
        if journal_count >= 50:
            if self.award_badge_if_not_earned(user, 'dedicated_journaler'):
                newly_earned.append(self.badges['dedicated_journaler']['name'])
        
        return newly_earned
    
    def check_chat_based_badges(self, user, chat_count):
        """
        Check and award chat-related badges
        """
        newly_earned = []
        
        if chat_count >= 50:
            if self.award_badge_if_not_earned(user, 'chat_companion'):
                newly_earned.append(self.badges['chat_companion']['name'])
        
        return newly_earned
    
    def award_badge_if_not_earned(self, user, badge_key):
        """
        Award a badge to user if they don't already have it
        Returns True if badge was awarded
        """
        if badge_key not in self.badges:
            return False
        
        badge_name = self.badges[badge_key]['name']
        
        if not user.has_badge(badge_name):
            user.add_badge(badge_name)
            return True
        
        return False
    
    def get_motivational_message(self, streak, total_checkins, newly_earned_badges=None):
        """
        Generate motivational message based on user progress
        """
        if newly_earned_badges:
            badges_text = ', '.join(newly_earned_badges)
            return f"🎉 Congratulations! You've earned: {badges_text}! Keep up the amazing work! 🌟"
        
        if streak == 1:
            return "🌟 Great start! Every journey begins with a single step. Come back tomorrow to build your streak! 💪"
        elif streak == 3:
            return "🔥 3 days in a row! You're building a beautiful habit. Small steps, big changes! 🌱"
        elif streak == 5:
            return "⭐ 5 days! You're halfway to your first major badge. Consistency looks good on you! ✨"
        elif streak == 7:
            return "🎉 AMAZING! 7 days! You've unlocked the Resilience Star badge! You're unstoppable! 🌟"
        elif streak == 10:
            return "💪 10 days! Double digits! Your commitment to yourself is inspiring! 🧘‍♀️"
        elif streak == 14:
            return "🏆 WOW! 14 days! You're a Mindful Warrior! This is incredible dedication! 🙌"
        elif streak == 21:
            return "🔥 21 days! They say it takes 21 days to form a habit. You've done it! 🌟"
        elif streak == 30:
            return "🎊 30 DAYS! You are a Wellness Champion! This is extraordinary. Celebrate yourself! 🎉"
        elif streak % 10 == 0 and streak > 0:
            return f"✨ {streak} days in a row! You're building incredible resilience. Keep going! 💚"
        elif total_checkins == 1:
            return "👋 Welcome to Sage! Check in daily to build your streak and earn badges. You've got this! 💪"
        elif total_checkins % 10 == 0:
            return f"📊 {total_checkins} total check-ins! That's {total_checkins} days you've shown up for yourself. Beautiful! 💚"
        
        return None
    
    def get_streak_warning(self, last_checkin_date):
        """
        Generate warning message if user hasn't checked in today
        """
        if not last_checkin_date:
            return "🌱 You haven't logged your mood today. A 10-second check-in keeps your streak alive!"
        
        today = get_today_date()
        if last_checkin_date == get_yesterday_date():
            return "⚠️ You haven't logged your mood today. Your streak is at risk! Log now to keep it going. 🔥"
        elif last_checkin_date != today:
            return "🌱 You're back! Log your mood today to start a new streak. Every day is a fresh start. 💚"
        
        return None
    
    def get_user_progress_stats(self, user, mood_entries_count, journal_entries_count, chat_messages_count):
        """
        Generate comprehensive progress statistics for dashboard
        """
        # Calculate next badge progress
        next_badges = []
        
        if not user.has_badge('resilience_star') and user.streak < 7:
            next_badges.append({
                'name': 'Resilience Star',
                'progress': user.streak,
                'target': 7,
                'percentage': int((user.streak / 7) * 100)
            })
        
        if not user.has_badge('journal_keeper') and journal_entries_count < 10:
            next_badges.append({
                'name': 'Journal Keeper',
                'progress': journal_entries_count,
                'target': 10,
                'percentage': int((journal_entries_count / 10) * 100)
            })
        
        if not user.has_badge('chat_companion') and chat_messages_count < 50:
            next_badges.append({
                'name': 'Chat Companion',
                'progress': chat_messages_count,
                'target': 50,
                'percentage': int((chat_messages_count / 50) * 100)
            })
        
        return {
            'current_streak': user.streak,
            'longest_streak': user.longest_streak,
            'total_checkins': user.total_checkins,
            'badges_earned': user.badges,
            'badges_count': len(user.badges),
            'total_badges_available': len(self.badges),
            'next_badges': next_badges,
            'streak_percentage': int((user.streak / 30) * 100) if user.streak < 30 else 100,
            'checkin_percentage': int((user.total_checkins / 30) * 100) if user.total_checkins < 30 else 100
        }


class StreakManager:
    """Simplified streak management interface"""
    
    @staticmethod
    def update_streak(user, checkin_date=None):
        """Update user's streak"""
        service = GamificationService()
        return service.update_streak(user, checkin_date)
    
    @staticmethod
    def get_streak_info(user):
        """Get streak information for display"""
        return {
            'current_streak': user.streak,
            'longest_streak': user.longest_streak,
            'last_checkin': user.last_checkin,
            'total_checkins': user.total_checkins
        }


class BadgeManager:
    """Simplified badge management interface"""
    
    @staticmethod
    def get_all_badges():
        """Get all available badges"""
        return GamificationService.AVAILABLE_BADGES
    
    @staticmethod
    def get_user_badges(user):
        """Get user's earned badges with full details"""
        service = GamificationService()
        user_badges = []
        
        for badge_key, badge_info in service.badges.items():
            badge_name = badge_info['name']
            user_badges.append({
                'key': badge_key,
                'name': badge_info['name'],
                'description': badge_info['description'],
                'icon': badge_info['icon'],
                'earned': user.has_badge(badge_name),
                'requirement': badge_info['requirement_value'],
                'requirement_type': badge_info['requirement_type']
            })
        
        return user_badges
    
    @staticmethod
    def award_badge(user, badge_key):
        """Award a specific badge to user"""
        service = GamificationService()
        return service.award_badge_if_not_earned(user, badge_key)