from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import warnings
# Suppress eventlet warnings
warnings.filterwarnings('ignore', category=UserWarning)
import os
import atexit
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from apscheduler.schedulers.background import BackgroundScheduler

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
from routes.threat_intel import create_threat_intel_blueprint
from utils.auth import token_required
from typing import Dict, Any, Optional
from services.alert_service import AlertService
from services.gemini_service import gemini_service
from services.transaction_service import init_transaction_service, get_transaction_service
from services.threat_intel_service import ThreatIntelService

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

# Initialize transaction service & CTIH
transaction_service = init_transaction_service(socketio)
threat_intel_service = ThreatIntelService()
alert_service.set_threat_intel_service(threat_intel_service)

# Schedule nightly dynamic clustering refresh
scheduler = BackgroundScheduler(timezone=timezone.utc)


def _scheduled_cluster_refresh():
    try:
        threat_intel_service.refresh_dynamic_clusters(force=True)
    except Exception as exc:
        print(f"⚠️ Scheduled cluster refresh failed: {exc}")


def _start_scheduler():
    if scheduler.get_jobs():
        return
    scheduler.add_job(
        _scheduled_cluster_refresh,
        trigger="cron",
        hour=0,
        minute=0,
        id="dynamic_cluster_refresh",
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))


if os.environ.get("DISABLE_CLUSTER_SCHEDULER") != "1":
    _start_scheduler()

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(create_threat_intel_blueprint(threat_intel_service))
app.config["THREAT_INTEL_SERVICE"] = threat_intel_service

# Configure logging to suppress expected 401 errors for unauthenticated requests
class Filter401(logging.Filter):
    """Filter to suppress 401 logs for authentication endpoints"""
    def filter(self, record):
        # Suppress 401 logs for user-analytics and other protected endpoints
        # These are expected when users aren't logged in
        if '401' in str(record.getMessage()) and any(endpoint in str(record.getMessage()) for endpoint in ['/api/user-analytics', '/api/transaction-history', '/api/analyze']):
            return False
        return True

# Apply filter to werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(Filter401())

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
        network_agent = NetworkAgent(threat_intel_service=threat_intel_service)
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

        # Central Threat Intelligence Hub integration
        # Only read existing threat intel data for alerts, don't record new data
        # New data will only be recorded when user explicitly reports a scam
        threat_intel_snapshot = {}
        receiver_threat_score = 0.0
        # Initialize variables for threat intel checks
        trending_match = None
        cluster_member = None
        cluster_match = None
        
        if threat_intel_service:
            
            try:
                # Only read existing threat score, don't record new data
                receiver_threat_score = threat_intel_service.get_receiver_threat_score(
                    transaction.get('receiver')
                )
                
                # Get existing snapshot if available (for alerts and response)
                if receiver_threat_score > 0:
                    threat_intel_snapshot = threat_intel_service.get_receiver_snapshot(
                        transaction.get('receiver')
                    )
                
                receiver = transaction.get('receiver', '')
                
                # Check if receiver is in trending threats
                trending_match = threat_intel_service.check_receiver_in_trending(receiver)
                if trending_match and alert_service:
                    print(f"🔥 Trending threat detected for user {user_id}: {trending_match.get('receiver')} ({trending_match.get('totalReports', 0)} reports)")
                    alert_service.send_trending_threat_alert(
                        user_id,
                        transaction,
                        trending_match
                    )
                
                # Check if receiver is a member of any cluster
                cluster_member = threat_intel_service.check_receiver_in_clusters(receiver)
                if cluster_member and alert_service:
                    print(f"🎯 Cluster member detected for user {user_id}: {cluster_member.get('name')} for receiver {receiver}")
                    alert_service.send_cluster_member_alert(
                        user_id,
                        transaction,
                        cluster_member
                    )
                
                # Check if transaction matches an existing cluster pattern (message similarity)
                cluster_match = threat_intel_service.check_cluster_match(
                    transaction,
                    agents,
                    similarity_threshold=0.70  # 70% similarity threshold (lowered for better detection)
                )
                
                # Send cluster match alert if found (only if not already sent as cluster member)
                if cluster_match and alert_service and not cluster_member:
                    print(f"🎯 Cluster pattern match detected for user {user_id}: {cluster_match.get('name')} (similarity: {cluster_match.get('similarity', 0):.1%})")
                    alert_service.send_cluster_match_alert(
                        user_id,
                        transaction,
                        cluster_match
                    )
                elif cluster_match and not cluster_member:
                    print(f"⚠️ Cluster match found but alert_service not available")
            except Exception as intel_error:
                print(f"⚠️ Threat Intel update failed: {intel_error}")

        if receiver_threat_score:
            overall_risk = round((overall_risk * 0.7) + (receiver_threat_score * 0.3), 1)

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

        threat_intel_payload = {}
        if threat_intel_snapshot:
            last_seen = threat_intel_snapshot.get('last_seen')
            if hasattr(last_seen, 'isoformat'):
                last_seen = last_seen.isoformat()
            threat_intel_payload = {
                'receiver': threat_intel_snapshot.get('receiver', transaction.get('receiver')),
                'threatScore': receiver_threat_score,
                'avgAgentRisk': threat_intel_snapshot.get('avg_agent_risk', 0),
                'behaviorAnomalies': threat_intel_snapshot.get('behavior_anomalies', 0),
                'patternFlags': threat_intel_snapshot.get('pattern_flags', []),
                'velocityScore': threat_intel_snapshot.get('velocity_score', 0),
                'geoAnomalies': threat_intel_snapshot.get('geo_anomalies', 0),
                'totalReports': threat_intel_snapshot.get('total_reports', 0),
                'lastSeen': last_seen,
                'clusterMatch': cluster_match,  # Include cluster match info in response
                'trendingThreat': trending_match,  # Include trending threat info if receiver is trending
                'clusterMember': cluster_member  # Include cluster member info if receiver is in a cluster
            }

        # Generate AI explanation using Gemini (include threat intel data)
        ai_explanation = ""
        if gemini_service.is_enabled():
            # Pass threat intel information to Gemini for context-aware explanations
            threat_intel_for_gemini = threat_intel_payload if threat_intel_payload else {}
            ai_explanation = gemini_service.generate_fraud_explanation(
                transaction, 
                agent_results, 
                overall_risk,
                threat_intel=threat_intel_for_gemini
            )
            print(f"AI Explanation generated: {ai_explanation[:100]}...")  # Log first 100 chars

        response = {
            'overallRisk': overall_risk,
            'aiExplanation': ai_explanation,
            'agents': agent_results,
            'threatIntel': threat_intel_payload,
            # Include raw agent outputs for reporting (will be used when user reports scam)
            '_agentOutputs': agents,
            '_transaction': transaction
        }

        if receiver_threat_score >= 85:
            alert_service.push_threat_alerts()

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
        print(f"ValueError in analyze_transaction: {e}")
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in analyze_transaction: {e}")
        print(f"Traceback: {error_trace}")
        # Return more detailed error in development, generic in production
        error_message = str(e) if app.debug else 'Internal server error'
        return jsonify({'error': error_message, 'type': type(e).__name__}), 500

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
        transaction_id = data.get('transaction_id')  # Optional: to track if already reported
        agent_outputs = data.get('agent_outputs')  # Agent analysis results
        transaction_data = data.get('transaction')  # Full transaction data

        if not receiver:
            return jsonify({'error': 'Missing receiver ID'}), 400

        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        # Check if this specific transaction was already reported to threat intel
        already_reported_to_threat_intel = False
        if transaction_id and threat_intel_service:
            history_collection = threat_intel_service._get_collection(threat_intel_service.history_collection_name)
            if history_collection:
                # Check if this transaction was already recorded
                existing_record = history_collection.find_one({
                    "transaction.user_id": user_id,
                    "receiver": receiver,
                    "transaction.amount": transaction_data.get('amount') if transaction_data else None,
                    "transaction.reason": transaction_data.get('reason') if transaction_data else None
                })
                if existing_record:
                    already_reported_to_threat_intel = True

        # Update scam_reports collection (legacy collection, still used by Network Agent)
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

        # Record to threat intel for clustering (only if not already reported)
        if threat_intel_service and agent_outputs and transaction_data and not already_reported_to_threat_intel:
            try:
                # Prepare transaction dict for threat intel
                transaction_for_intel = {
                    'receiver': receiver,
                    'amount': transaction_data.get('amount', 0),
                    'reason': transaction_data.get('reason', reason),
                    'user_id': user_id,
                    'time': transaction_data.get('time', ''),
                    'typing_speed': transaction_data.get('typing_speed'),
                    'hesitation_count': transaction_data.get('hesitation_count')
                }
                
                # Record agent outputs to threat intel (triggers clustering)
                threat_intel_service.record_agent_outputs(transaction_for_intel, agent_outputs)
                
                # Update threat score
                threat_intel_service.update_and_get_score(
                    receiver,
                    agent_outputs,
                    transaction_for_intel
                )
                
                print(f"✅ Recorded scam report to threat intel for receiver: {receiver}")
            except Exception as intel_error:
                print(f"⚠️ Failed to record to threat intel: {intel_error}")

        return jsonify({
            'success': True,
            'message': f'Scam reported successfully. Total reports: {count}',
            'recorded_to_threat_intel': not already_reported_to_threat_intel
        }), 200

    except Exception as e:
        print(f"Error in report_scam: {e}")
        import traceback
        print(traceback.format_exc())
        # Return more detailed error in development, generic in production
        error_message = str(e) if app.debug else 'Internal server error'
        return jsonify({'error': error_message, 'type': type(e).__name__}), 500

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

        # If user reports it was a scam, record to threat intel for clustering
        # (only if not already reported via the Report Scam button)
        if was_scam and threat_intel_service:
            print(f"🔍 Processing scam feedback for receiver: {receiver}, transaction_id: {transaction_id}")
            
            # Check if this transaction was already reported to threat intel
            already_reported = False
            history_collection = threat_intel_service._get_collection(threat_intel_service.history_collection_name)
            
            # Get agent outputs and transaction data from request (preferred)
            agent_outputs = data.get('agent_outputs')
            transaction_data = data.get('transaction')
            
            print(f"📦 Received data - agent_outputs: {bool(agent_outputs)}, transaction_data: {bool(transaction_data)}")
            
            # If not provided in request, try to get from transaction document
            if (not agent_outputs or not transaction_data) and transaction_id:
                transactions = db.transactions
                from bson import ObjectId
                from bson.errors import InvalidId
                try:
                    # Validate ObjectId format
                    if transaction_id and len(transaction_id) == 24:
                        tx_doc = transactions.find_one({"_id": ObjectId(transaction_id)})
                        if tx_doc:
                            # Check if already recorded
                            if history_collection:
                                existing_record = history_collection.find_one({
                                    "transaction.user_id": user_id,
                                    "receiver": receiver,
                                    "transaction.amount": tx_doc.get('amount'),
                                    "transaction.reason": tx_doc.get('reason')
                                })
                                if existing_record:
                                    already_reported = True
                            
                            # If not already reported, try to reconstruct data
                            if not already_reported:
                                if not agent_outputs or len(agent_outputs) == 0:
                                    # Try to reconstruct agent outputs from stored risk_score
                                    # This is a fallback - ideally frontend should pass agent_outputs
                                    risk_score = tx_doc.get('risk_score', 0)
                                    if risk_score > 0:
                                        agent_outputs = [
                                            {'risk_score': risk_score * 0.25, 'message': 'Pattern analysis'},
                                            {'risk_score': risk_score * 0.25, 'message': 'Network analysis'},
                                            {'risk_score': risk_score * 0.25, 'message': 'Behavior analysis'},
                                            {'risk_score': risk_score * 0.25, 'message': 'Biometric analysis'}
                                        ]
                                        print(f"📊 Reconstructed agent outputs from risk_score: {risk_score}")
                                    else:
                                        # If no risk_score, use a default based on the fact user reported it as scam
                                        agent_outputs = [
                                            {'risk_score': 50, 'message': 'User reported scam'},
                                            {'risk_score': 50, 'message': 'User reported scam'},
                                            {'risk_score': 50, 'message': 'User reported scam'},
                                            {'risk_score': 50, 'message': 'User reported scam'}
                                        ]
                                        print(f"📊 Created default agent outputs for user-reported scam")
                                
                                if not transaction_data and tx_doc:
                                    transaction_data = {
                                        'receiver': receiver,
                                        'amount': tx_doc.get('amount', 0),
                                        'reason': tx_doc.get('reason', ''),
                                        'user_id': user_id,
                                        'time': tx_doc.get('time', ''),
                                        'typing_speed': tx_doc.get('typing_speed'),
                                        'hesitation_count': tx_doc.get('hesitation_count')
                                    }
                                    print(f"📊 Reconstructed transaction_data from transaction document")
                except (InvalidId, ValueError, TypeError) as id_error:
                    print(f"⚠️ Invalid transaction_id format: {id_error}")
                except Exception as tx_error:
                    print(f"⚠️ Error checking transaction for threat intel: {tx_error}")
            
            # Record to threat intel if we have the data and not already reported
            print(f"🔍 Final check - already_reported: {already_reported}, agent_outputs: {bool(agent_outputs) and len(agent_outputs) > 0}, transaction_data: {bool(transaction_data)}")
            
            if already_reported:
                print(f"⏭️ Skipping recording - transaction already reported to threat intel")
            elif not agent_outputs or len(agent_outputs) == 0:
                print(f"⚠️ Cannot record - missing or empty agent_outputs. Attempting to create minimal agent outputs...")
                # Create minimal agent outputs as last resort
                agent_outputs = [
                    {'risk_score': 50, 'message': 'User reported as scam'},
                    {'risk_score': 50, 'message': 'User reported as scam'},
                    {'risk_score': 50, 'message': 'User reported as scam'},
                    {'risk_score': 50, 'message': 'User reported as scam'}
                ]
                print(f"📊 Created minimal agent outputs for recording")
            
            if not transaction_data:
                print(f"⚠️ Cannot record - missing transaction_data. Creating from available data...")
                # Create transaction_data from available info
                transaction_data = {
                    'receiver': receiver,
                    'amount': 0,  # Will be updated if available
                    'reason': data.get('comment', 'User reported scam'),
                    'user_id': user_id,
                    'time': '',
                    'typing_speed': None,
                    'hesitation_count': None
                }
                print(f"📊 Created minimal transaction_data for recording")
            
            # Now try to record if we have both
            if agent_outputs and len(agent_outputs) > 0 and transaction_data:
                try:
                    print(f"📝 Recording to threat intel - receiver: {receiver}, agent_outputs count: {len(agent_outputs) if agent_outputs else 0}")
                    threat_intel_service.record_agent_outputs(transaction_data, agent_outputs)
                    threat_intel_service.update_and_get_score(
                        receiver,
                        agent_outputs,
                        transaction_data
                    )
                    print(f"✅ Successfully recorded scam feedback to threat intel for receiver: {receiver}")
                except Exception as intel_error:
                    print(f"❌ Failed to record feedback to threat intel: {intel_error}")
                    import traceback
                    print(traceback.format_exc())

        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        }), 200

    except Exception as e:
        print(f"Error in submit_feedback: {e}")
        import traceback
        print(traceback.format_exc())
        # Return more detailed error in development
        error_message = str(e) if app.debug else 'Internal server error'
        return jsonify({'error': error_message, 'type': type(e).__name__}), 500

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
