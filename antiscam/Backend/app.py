from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import warnings
# Suppress eventlet warnings
warnings.filterwarnings('ignore', category=UserWarning)
import os
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import agents
from agents.pattern_agent import PatternAgent
from agents.network_agent import NetworkAgent
from agents.behavior_agent import BehaviorAgent
from agents.biometric_agent import BiometricAgent
from agents.retrain_behavior_manual import retrain_behavior_model

# 🆕 Import pattern retraining function
from agents.retrain_pattern_manual import retrain_pattern_model  

# Database and utils
from database.db import get_db, connect
from utils.score_aggregator import aggregate_scores
from routes.auth import auth_bp
from utils.auth import token_required
from typing import Dict, Any, Optional
from services.alert_service import AlertService
from services.gemini_service import gemini_service
from services.transaction_service import init_transaction_service, get_transaction_service

# -------------------------------------------------------------
# Flask setup
# -------------------------------------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for frontend

# Initialize SocketIO - Updated versions (5.5.1+) have better Python 3.12 support
# Configure to allow both polling and websocket transports
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
    async_mode='threading'
)

# Initialize alert service
alert_service = AlertService(socketio)

# Initialize transaction service
transaction_service = init_transaction_service(socketio)

# Register blueprints
app.register_blueprint(auth_bp)

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'status': 'connected'})
    # Send first alert immediately when client connects (if not sent yet)
    alert_service.send_first_alert_if_needed()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_alerts')
def handle_request_alerts():
    """Handle client request for alerts (resend first alert if needed)"""
    print('Client requested alerts')
    emit('alerts_enabled', {'status': 'enabled'})
    # Send first alert immediately when client requests (if not sent yet)
    alert_service.send_first_alert_if_needed()

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Handle user joining their private room for personalized updates"""
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        join_room(room)
        print(f'User {user_id} joined room {room}')
        emit('room_joined', {'room': room, 'status': 'success'})

@socketio.on('leave_user_room')
def handle_leave_user_room(data):
    """Handle user leaving their private room"""
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        leave_room(room)
        print(f'User {user_id} left room {room}')
        emit('room_left', {'room': room, 'status': 'success'})

@socketio.on('request_recent_transactions')
def handle_request_recent_transactions(data):
    """Handle client request for recent transactions"""
    user_id = data.get('user_id')
    limit = data.get('limit', 10)
    
    if user_id and transaction_service:
        transactions = transaction_service.get_recent_transactions(user_id, limit)
        emit('recent_transactions', {'transactions': transactions})

# Initialize MongoDB connection
connect()

# Initialize agents
pattern_agent: Optional[PatternAgent] = None
network_agent: Optional[NetworkAgent] = None
behavior_agent: Optional[BehaviorAgent] = None
biometric_agent: Optional[BiometricAgent] = None

def initialize_agents() -> bool:
    """Initialize all AI agents"""
    global pattern_agent, network_agent, behavior_agent, biometric_agent
    try:
        pattern_agent = PatternAgent()
        network_agent = NetworkAgent()
        behavior_agent = BehaviorAgent()
        biometric_agent = BiometricAgent()
        print("✅ All AI agents initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize AI agents: {e}")
        return False

def get_current_user_id() -> Optional[str]:
    """Extract user_id from request context set by token_required decorator"""
    try:
        # The token_required decorator sets request.current_user
        # Using getattr with default to avoid linter issues
        current_user = getattr(request, 'current_user', None)
        if current_user:
            return current_user.get('user_id')
        return None
    except Exception:
        return None

# -------------------------------------------------------------
# Helper: Save feedback locally + trigger retraining
# -------------------------------------------------------------
import platform  # To detect the operating system

# Cross-platform file locking
try:
    if platform.system() == 'Windows':
        import msvcrt
        def _lock_file(file_handle):
            while True:
                try:
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except IOError:
                    import time
                    time.sleep(0.1)
        
        def _unlock_file(file_handle):
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        def _lock_file(file_handle):
            fcntl.flock(file_handle, fcntl.LOCK_EX)
        
        def _unlock_file(file_handle):
            fcntl.flock(file_handle, fcntl.LOCK_UN)
except ImportError:
    # Fallback if locking is not available
    def _lock_file(file_handle):
        pass
    
    def _unlock_file(file_handle):
        pass

def save_feedback_and_check_retrain(feedback):
    feedback_path = os.path.join(os.path.dirname(__file__), 'data', 'behavior_feedback.csv')
    os.makedirs(os.path.dirname(feedback_path), exist_ok=True)

    # Use file locking to prevent race conditions
    df = pd.DataFrame([feedback])
    
    # Create file if it doesn't exist with header
    if not os.path.exists(feedback_path):
        df.to_csv(feedback_path, index=False)
    else:
        # Append with file locking to prevent corruption
        with open(feedback_path, 'a', newline='', encoding='utf-8') as f:
            _lock_file(f)
            try:
                df.to_csv(f, header=False, index=False)
            finally:
                _unlock_file(f)

    # Read with error handling to prevent crashes on corrupted files
    try:
        feedback_df = pd.read_csv(feedback_path)
        feedback_count = len(feedback_df)
    except pd.errors.ParserError as e:
        print(f"⚠️ CSV parsing error in behavior feedback: {e}")
        # Attempt to fix corrupted file
        feedback_count = _fix_corrupted_csv(feedback_path)
    
    print(f"📥 Behavior feedback count: {feedback_count}")

    if feedback_count >= 10:
        print("🚀 Threshold reached — retraining behavior model...")
        retrain_behavior_model()


# 🆕 Pattern retraining support
def save_pattern_feedback_and_retrain(feedback):
    """
    Save feedback for pattern agent retraining (locally) and trigger retrain if threshold met.
    """
    feedback_path = os.path.join(os.path.dirname(__file__), 'data', 'pattern_feedback.csv')
    os.makedirs(os.path.dirname(feedback_path), exist_ok=True)

    # Use file locking to prevent race conditions
    df = pd.DataFrame([feedback])
    
    # Create file if it doesn't exist with header
    if not os.path.exists(feedback_path):
        df.to_csv(feedback_path, index=False)
    else:
        # Append with file locking to prevent corruption
        with open(feedback_path, 'a', newline='', encoding='utf-8') as f:
            _lock_file(f)
            try:
                df.to_csv(f, header=False, index=False)
            finally:
                _unlock_file(f)

    # Read with error handling to prevent crashes on corrupted files
    try:
        feedback_df = pd.read_csv(feedback_path)
        feedback_count = len(feedback_df)
    except pd.errors.ParserError as e:
        print(f"⚠️ CSV parsing error in pattern feedback: {e}")
        # Attempt to fix corrupted file
        feedback_count = _fix_corrupted_csv(feedback_path)
    
    print(f"📥 Pattern feedback count: {feedback_count}")

    if feedback_count >= 10:
        print("🚀 Threshold reached — retraining pattern model...")
        retrain_pattern_model()


def _fix_corrupted_csv(file_path):
    """
    Attempt to fix corrupted CSV files by reading line by line
    and writing valid lines to a new file.
    """
    try:
        backup_path = file_path + ".backup"
        # Create backup
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, backup_path)
        
        valid_lines = []
        expected_columns = 5  # user_id,receiver,was_scam,comment,timestamp
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Count commas to check if line has expected number of fields
            comma_count = line.count(',')
            if comma_count == expected_columns - 1:  # Expected fields - 1 (since commas separate fields)
                valid_lines.append(line)
            else:
                print(f"⚠️ Skipping corrupted line {i+1}: {line[:50]}...")
        
        # Write valid lines back to file
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.writelines(valid_lines)
            
        print(f"✅ Fixed CSV file: {len(lines)} → {len(valid_lines)} valid lines")
        return len(valid_lines) - 1 if len(valid_lines) > 0 else 0  # Subtract 1 for header
    except Exception as e:
        print(f"❌ Error fixing CSV file: {e}")
        return 0

# Initialize MongoDB connection and agents on startup
with app.app_context():
    try:
        initialize_agents()
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")

# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze_transaction():
    try:
        # Check if agents are initialized
        if not all([pattern_agent, network_agent, behavior_agent, biometric_agent]):
            return jsonify({'error': 'AI agents not initialized'}), 500
        
        data = request.get_json()

        required_fields = ['receiver', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Extract transaction details
        transaction: Dict[str, Any] = {
            'receiver': data.get('receiver', ''),
            'amount': float(data.get('amount', 0)),
            'reason': data.get('reason', data.get('message', '')),
            'time': data.get('time', ''),
            'user_id': user_id,
            'typing_speed': data.get('typing_speed', None),
            'hesitation_count': data.get('hesitation_count', None)
        }
        
        # Run all agents
        pattern_result = pattern_agent.analyze(transaction) if pattern_agent else {}
        network_result = network_agent.analyze(transaction) if network_agent else {}
        behavior_result = behavior_agent.analyze(transaction) if behavior_agent else {}
        biometric_result = biometric_agent.analyze(transaction) if biometric_agent else {}
        
        # Aggregate scores
        agents = [
            pattern_result,
            network_result,
            behavior_result,
            biometric_result
        ]
        
        overall_risk = aggregate_scores(agents)

        # Prepare agent results for response and AI explanation
        agent_results = [
            {
                'name': 'Pattern Agent',
                'icon': '🕵️',
                'color': '#00C896',
                'riskScore': pattern_result.get('risk_score', 0),
                'message': pattern_result.get('message', ''),
                'details': pattern_result.get('details', ''),
                'evidence': pattern_result.get('evidence', [])
            },
            {
                'name': 'Network Agent',
                'icon': '🕸️',
                'color': '#0091FF',
                'riskScore': network_result.get('risk_score', 0),
                'message': network_result.get('message', ''),
                'details': network_result.get('details', ''),
                'evidence': network_result.get('evidence', [])
            },
            {
                'name': 'Behavior Agent',
                'icon': '🔍',
                'color': '#A78BFA',
                'riskScore': behavior_result.get('risk_score', 0),
                'message': behavior_result.get('message', ''),
                'details': behavior_result.get('details', ''),
                'evidence': behavior_result.get('evidence', [])
            },
            {
                'name': 'Biometric Agent',
                'icon': '🎭',
                'color': '#F472B6',
                'riskScore': biometric_result.get('risk_score', 0),
                'message': biometric_result.get('message', ''),
                'details': biometric_result.get('details', ''),
                'evidence': biometric_result.get('evidence', [])
            }
        ]

        # Generate AI explanation using Gemini
        ai_explanation = ""
        if gemini_service.is_enabled():
            ai_explanation = gemini_service.generate_fraud_explanation(transaction, agent_results, overall_risk)
            print(f"AI Explanation generated: {ai_explanation[:100]}...")  # Log first 100 chars

        response = {
            'overallRisk': overall_risk,
            'aiExplanation': ai_explanation,
            'agents': agent_results
        }

        print(f"Returning response with AI explanation length: {len(ai_explanation)}")
        
        # Emit real-time analysis result to the user
        if transaction_service:
            # Add transaction details to the analysis result
            analysis_result = response.copy()
            analysis_result['transaction'] = {
                'receiver': transaction.get('receiver', ''),
                'amount': transaction.get('amount', 0),
                'reason': transaction.get('reason', ''),
                'time': transaction.get('time', ''),
                'user_id': user_id
            }
            transaction_service.emit_analysis_result(analysis_result, user_id)
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in analyze_transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/report', methods=['POST'])
@token_required
def report_scam():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        reason = data.get('reason', 'Reported scam')

        if not receiver:
            return jsonify({'error': 'Missing receiver ID'}), 400

        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        scam_reports = db.scam_reports
        existing = scam_reports.find_one({"receiver_id": receiver})

        if existing:
            new_count = existing.get('count', 0) + 1
            reasons = existing.get('reasons', [])
            user_ids = existing.get('user_ids', [])

            if reason and reason not in reasons:
                reasons.append(reason)
            if user_id and user_id not in user_ids:
                user_ids.append(user_id)

            scam_reports.update_one(
                {"receiver_id": receiver},
                {"$set": {
                    "count": new_count,
                    "reasons": reasons,
                    "user_ids": user_ids,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            count = new_count
        else:
            scam_reports.insert_one({
                "receiver_id": receiver,
                "count": 1,
                "reasons": [reason] if reason else [],
                "user_ids": [user_id] if user_id else [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            count = 1

        return jsonify({
            'success': True,
            'message': f'Scam reported successfully. Total reports: {count}'
        }), 200

    except Exception as e:
        print(f"Error in report_scam: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    try:
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        transactions = db.transactions
        tx_list = list(transactions.find({"user_id": user_id}).sort("created_at", -1).limit(20))

        history = []
        for tx in tx_list:
            # Handle datetime conversion safely
            created_at = tx.get('created_at')
            if created_at and hasattr(created_at, 'isoformat'):
                formatted_date = created_at.isoformat()
            else:
                formatted_date = str(created_at) if created_at else ''
                
            history.append({
                'id': str(tx.get('_id', '')),
                'receiver': tx.get('receiver_id', ''),
                'amount': tx.get('amount', 0),
                'reason': tx.get('reason', ''),
                'risk_score': tx.get('risk_score', 0),
                'created_at': formatted_date
            })

        return jsonify({'transactions': history}), 200

    except Exception as e:
        print(f"Error in get_history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/complete-transaction', methods=['POST'])
@token_required
def complete_transaction():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        amount = data.get('amount')
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if not receiver or not amount:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate amount is numeric
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        # Save to MongoDB
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        transactions = db.transactions
        transaction_doc = {
            "receiver_id": receiver,
            "amount": amount,
            "reason": data.get('reason', ''),
            "user_id": user_id,
            "time": data.get('time', ''),
            "risk_score": data.get('risk_score', 0),
            "created_at": datetime.now(timezone.utc)
        }

        result = transactions.insert_one(transaction_doc)

        return jsonify({
            'success': True,
            'transaction_id': str(result.inserted_id),
            'message': 'Transaction completed successfully'
        }), 200

    except Exception as e:
        print(f"Error in complete_transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/feedback', methods=['POST'])
@token_required
def submit_feedback():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        was_scam = data.get('was_scam')
        transaction_id = data.get('transaction_id')

        if receiver is None or was_scam is None:
            return jsonify({'error': 'Missing required fields: receiver, was_scam'}), 400

        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        feedback_collection = db.feedback
        feedback_doc = {
            "transaction_id": transaction_id,
            "receiver_id": receiver,
            "user_id": user_id,
            "was_scam": was_scam,
            "comment": data.get('comment', ''),
            "created_at": datetime.now(timezone.utc)
        }
        feedback_collection.insert_one(feedback_doc)

        # Save feedback for both models
        feedback_entry = {
            "user_id": user_id,
            "receiver": receiver,
            "was_scam": was_scam,
            "comment": data.get('comment', ''),
            "timestamp": datetime.now().isoformat()
        }

        save_feedback_and_check_retrain(feedback_entry)
        save_pattern_feedback_and_retrain(feedback_entry)  # 🆕 added

        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        }), 200

    except Exception as e:
        print(f"Error in submit_feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transaction-history', methods=['GET'])
@token_required
def get_transaction_history():
    """Get transaction history for the current user"""
    try:
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get limit parameter (default to 20)
        limit = request.args.get('limit', 20, type=int)
        
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        transactions = db.transactions
        tx_list = list(transactions.find({"user_id": user_id})
                      .sort("created_at", -1)
                      .limit(limit))

        history = []
        for tx in tx_list:
            # Handle datetime conversion safely
            created_at = tx.get('created_at')
            if created_at and hasattr(created_at, 'isoformat'):
                formatted_date = created_at.isoformat()
            else:
                formatted_date = str(created_at) if created_at else ''
                
            history.append({
                'id': str(tx.get('_id', '')),
                'receiver': tx.get('receiver_id', ''),
                'amount': tx.get('amount', 0),
                'reason': tx.get('reason', ''),
                'risk_score': tx.get('risk_score', 0),
                'created_at': formatted_date
            })

        return jsonify({'transactions': history}), 200

    except Exception as e:
        print(f"Error in get_transaction_history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user-analytics', methods=['GET'])
@token_required
def get_user_analytics():
    """Get analytics data for the current user"""
    try:
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get transaction service
        if transaction_service is None:
            return jsonify({'error': 'Transaction service not initialized'}), 500
            
        # Get user analytics
        analytics = transaction_service.get_user_analytics(user_id)
        
        return jsonify(analytics), 200

    except Exception as e:
        print(f"Error in get_user_analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/global-analytics', methods=['GET'])
def get_global_analytics():
    """Get global analytics data"""
    try:
        # Get transaction service
        if transaction_service is None:
            return jsonify({'error': 'Transaction service not initialized'}), 500
            
        # Get global analytics
        analytics = transaction_service.get_global_analytics()
        
        return jsonify(analytics), 200

    except Exception as e:
        print(f"Error in get_global_analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == '__main__':
    # Start alert service
    alert_service.start()
    
    # Run SocketIO server (threading mode works with standard Flask dev server)
    print("🚀 Starting Flask-SocketIO server on http://localhost:5000")
    print("📡 WebSocket alerts enabled")
    socketio.run(app, debug=True, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)
