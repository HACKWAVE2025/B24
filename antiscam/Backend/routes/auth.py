from flask import Blueprint, request, jsonify, redirect
from datetime import datetime
from database.db import get_db
from utils.auth import (
    generate_token, 
    hash_password, 
    check_password,
    token_required
)
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint('auth', __name__)

# Google OAuth credentials
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
# Get redirect URI from env or use default
# Note: This should match what you set in Google Cloud Console
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Google OAuth URLs
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        db = get_db()
        users = db.users
        
        # Check if user already exists
        existing_user = users.find_one({"email": email})
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create new user
        user_doc = {
            "email": email,
            "password": hash_password(password),
            "name": name,
            "auth_method": "email",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Generate token
        token = generate_token(user_id, email)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user_id,
                'email': email,
                'name': name
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login user with email and password"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        db = get_db()
        users = db.users
        
        # Find user
        user = users.find_one({"email": email})
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user has password (not OAuth-only user)
        if not user.get('password'):
            return jsonify({'error': 'Please login with Google'}), 401
        
        # Verify password
        if not check_password(user['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        user_id = str(user['_id'])
        token = generate_token(user_id, email)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user_id,
                'email': user.get('email'),
                'name': user.get('name', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/api/auth/google/redirect', methods=['GET'])
def google_redirect():
    """Initiate Google OAuth flow - redirects to Google login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    # Build Google OAuth URL
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)


@auth_bp.route('/api/auth/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Get frontend URL from environment or use default
        FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        # Get authorization code from query params
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return redirect(f'{FRONTEND_URL}/auth?error={error}')
        
        if not code:
            return redirect(f'{FRONTEND_URL}/auth?error=no_code')
        
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
            return redirect(f'{FRONTEND_URL}/auth?error=oauth_not_configured')
        
        # Exchange authorization code for access token
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        
        if token_response.status_code != 200:
            error_detail = token_response.text
            print(f"Token exchange failed: {error_detail}")
            return redirect(f'{FRONTEND_URL}/auth?error=token_exchange_failed')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            return redirect(f'{FRONTEND_URL}/auth?error=no_access_token')
        
        # Get user info from Google
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if userinfo_response.status_code != 200:
            return redirect(f'{FRONTEND_URL}/auth?error=userinfo_failed')
        
        google_user_data = userinfo_response.json()
        google_id = google_user_data.get('id')
        email = google_user_data.get('email', '').strip().lower()
        name = google_user_data.get('name', '').strip()
        picture = google_user_data.get('picture', '')
        
        if not email:
            return redirect(f'{FRONTEND_URL}/auth?error=no_email')
        
        db = get_db()
        users = db.users
        
        # Check if user exists
        user = users.find_one({
            "$or": [
                {"email": email},
                {"google_id": google_id}
            ]
        })
        
        if user:
            # Update user if needed
            update_data = {
                "google_id": google_id,
                "updated_at": datetime.utcnow()
            }
            if picture and not user.get('picture'):
                update_data['picture'] = picture
            if name and not user.get('name'):
                update_data['name'] = name
            
            users.update_one(
                {"_id": user['_id']},
                {"$set": update_data}
            )
            user_id = str(user['_id'])
        else:
            # Create new user
            user_doc = {
                "email": email,
                "google_id": google_id,
                "name": name,
                "picture": picture,
                "auth_method": "google",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = users.insert_one(user_doc)
            user_id = str(result.inserted_id)
        
        # Generate JWT token
        token = generate_token(user_id, email)
        
        # Redirect to frontend with token
        frontend_url = f'{FRONTEND_URL}/auth?token={token}&success=true'
        return redirect(frontend_url)
        
    except Exception as e:
        print(f"Google OAuth callback error: {str(e)}")
        FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f'{FRONTEND_URL}/auth?error={str(e)}')


@auth_bp.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = request.current_user['user_id']
        
        db = get_db()
        users = db.users
        
        from bson import ObjectId
        user = users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'email': user.get('email'),
                'name': user.get('name', ''),
                'picture': user.get('picture', ''),
                'auth_method': user.get('auth_method', 'email')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token validity"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        from utils.auth import verify_token as verify
        payload = verify(token)
        
        if payload is None:
            return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': payload['user_id'],
            'email': payload['email']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

