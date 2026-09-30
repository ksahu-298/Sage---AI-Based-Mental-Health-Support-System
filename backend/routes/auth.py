"""
auth.py - Authentication routes for login, register, and Google OAuth

Endpoints:
- POST /api/auth/register - Create new user account
- POST /api/auth/login - Login existing user
- POST /api/auth/logout - Logout and invalidate token
- POST /api/auth/refresh - Refresh expired JWT token
- POST /api/auth/google - Google OAuth login
- GET /api/auth/me - Get current user info
"""

from flask import request, jsonify
from datetime import datetime, timedelta
import secrets
from .. import auth_bp
from ..models import db, User, UserSession
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ..utils.helpers import (
    validate_email, validate_username, sanitize_input,
    create_success_response, create_error_response
)

# ==================== Helper Functions ====================

def generate_jti():
    """Generate unique JWT ID for token tracking"""
    return secrets.token_urlsafe(32)

def hash_password(password):
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ==================== Authentication Routes ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON: { username, password, email (optional) }
    """
    data = request.get_json()
    
    # Validate required fields
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    
    if not username or not password:
        return create_error_response("Username and password are required", 400)
    
    # Validate username format
    if not validate_username(username):
        return create_error_response("Username must be 3-20 characters (letters, numbers, underscore)", 400)
    
    # Validate password strength
    if len(password) < 6:
        return create_error_response("Password must be at least 6 characters", 400)
    
    # Validate email if provided
    if email and not validate_email(email):
        return create_error_response("Invalid email format", 400)
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return create_error_response("Username already taken", 409)
    
    if email and User.query.filter_by(email=email).first():
        return create_error_response("Email already registered", 409)
    
    # Create new user
    new_user = User(
        username=username,
        email=email if email else None,
        password_hash=hash_password(password),
        created_at=datetime.utcnow(),
        streak=0,
        longest_streak=0,
        total_checkins=0,
        badges='[]',
        preferences='{}',
        is_active=True
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(
        identity=username,
        additional_claims={'user_id': new_user.id, 'jti': generate_jti()}
    )
    refresh_token = create_refresh_token(identity=username)
    
    # Create session record
    session = UserSession.create_session(
        user_id=new_user.id,
        token_jti=generate_jti(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(session)
    db.session.commit()
    
    return create_success_response({
        'token': access_token,
        'refresh_token': refresh_token,
        'user': new_user.to_dict()
    }, "Registration successful", 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login existing user
    Expected JSON: { username, password }
    """
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return create_error_response("Username and password required", 400)
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return create_error_response("Invalid credentials", 401)
    
    # Verify password
    if not verify_password(password, user.password_hash):
        return create_error_response("Invalid credentials", 401)
    
    # Check if account is active
    if not user.is_active:
        return create_error_response("Account deactivated. Contact support.", 403)
    
    # Generate tokens
    access_token = create_access_token(
        identity=user.username,
        additional_claims={'user_id': user.id, 'jti': generate_jti()}
    )
    refresh_token = create_refresh_token(identity=user.username)
    
    # Create session record
    session = UserSession.create_session(
        user_id=user.id,
        token_jti=generate_jti(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(session)
    db.session.commit()
    
    # Update last login (if we had such field)
    # user.last_login = datetime.utcnow()
    db.session.commit()
    
    return create_success_response({
        'token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }, "Login successful")


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user - invalidate current token
    """
    current_user = get_jwt_identity()
    jwt_data = get_jwt()
    token_jti = jwt_data.get('jti')
    
    # Find and revoke session
    session = UserSession.query.filter_by(token_jti=token_jti).first()
    if session:
        session.revoke()
        db.session.commit()
    
    return create_success_response(None, "Logged out successfully")


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Refresh expired access token using refresh token
    """
    current_user = get_jwt_identity()
    
    # Find user
    user = User.query.filter_by(username=current_user).first()
    if not user:
        return create_error_response("User not found", 404)
    
    # Create new access token
    new_access_token = create_access_token(identity=current_user)
    
    return create_success_response({
        'token': new_access_token
    }, "Token refreshed")


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    return create_success_response(user.to_dict())


@auth_bp.route('/google', methods=['POST'])
def google_login():
    """
    Google OAuth login (simplified version)
    In production, you would verify the Google ID token
    For now, this is a placeholder endpoint
    
    Expected: { google_id, email, name, avatar }
    """
    data = request.get_json()
    
    google_id = data.get('google_id')
    email = data.get('email')
    name = data.get('name', '')
    avatar = data.get('avatar', '')
    
    if not google_id or not email:
        return create_error_response("Google ID and email required", 400)
    
    # Check if user exists with this google_id
    user = User.query.filter_by(google_id=google_id).first()
    
    if not user:
        # Check if user exists with this email
        user = User.query.filter_by(email=email).first()
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            user.avatar = avatar
        else:
            # Create new user
            username = name.lower().replace(' ', '_') + str(secrets.randbelow(1000))
            # Ensure username is unique
            while User.query.filter_by(username=username).first():
                username = name.lower().replace(' ', '_') + str(secrets.randbelow(10000))
            
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                avatar=avatar,
                created_at=datetime.utcnow(),
                is_active=True,
                badges='[]',
                preferences='{}'
            )
            db.session.add(user)
    
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.username)
    refresh_token = create_refresh_token(identity=user.username)
    
    return create_success_response({
        'token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }, "Google login successful")


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    Expected: { current_password, new_password }
    """
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return create_error_response("User not found", 404)
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return create_error_response("Current and new password required", 400)
    
    if len(new_password) < 6:
        return create_error_response("New password must be at least 6 characters", 400)
    
    # Verify current password
    if not verify_password(current_password, user.password_hash):
        return create_error_response("Current password is incorrect", 401)
    
    # Update password
    user.password_hash = hash_password(new_password)
    db.session.commit()
    
    # Revoke all other sessions (optional security)
    # from ..models import UserSession
    # UserSession.query.filter_by(user_id=user.id).update({'is_revoked': True})
    # db.session.commit()
    
    return create_success_response(None, "Password changed successfully")