from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import warnings
# Suppress eventlet warnings
warnings.filterwarnings('ignore', category=UserWarning)
import os
import pandas as pd
from datetime import datetime, timezone

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
from services.alert_service import AlertService

# -------------------------------------------------------------
# Flask setup
# -------------------------------------------------------------
app = Flask(__name__)
<<<<<<< HEAD
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
=======
CORS(app)
>>>>>>> 8b231281e303f9616859ac75b7ed2821ac187f70

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

# Initialize MongoDB connection
connect()

# Initialize agents
pattern_agent = PatternAgent()
network_agent = NetworkAgent()
behavior_agent = BehaviorAgent()
biometric_agent = BiometricAgent()

# -------------------------------------------------------------
# Helper: Save feedback locally + trigger retraining
# -------------------------------------------------------------
def save_feedback_and_check_retrain(feedback):
    feedback_path = os.path.join(os.path.dirname(__file__), 'data', 'behavior_feedback.csv')
    os.makedirs(os.path.dirname(feedback_path), exist_ok=True)

    df = pd.DataFrame([feedback])

    if os.path.exists(feedback_path) and os.path.getsize(feedback_path) > 0:
        df.to_csv(feedback_path, mode='a', header=False, index=False)
    else:
        df.to_csv(feedback_path, index=False)

    feedback_count = len(pd.read_csv(feedback_path))
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

    df = pd.DataFrame([feedback])

    if os.path.exists(feedback_path) and os.path.getsize(feedback_path) > 0:
        df.to_csv(feedback_path, mode='a', header=False, index=False)
    else:
        df.to_csv(feedback_path, index=False)

    feedback_count = len(pd.read_csv(feedback_path))
    print(f"📥 Pattern feedback count: {feedback_count}")

    if feedback_count >= 10:
        print("🚀 Threshold reached — retraining pattern model...")
        retrain_pattern_model()

# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze_transaction():
    try:
        data = request.get_json()

        required_fields = ['receiver', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        user_id = request.current_user['user_id']

        transaction = {
            'receiver': data.get('receiver', ''),
            'amount': float(data.get('amount', 0)),
            'reason': data.get('reason', data.get('message', '')),
            'time': data.get('time', ''),
            'user_id': user_id,
            'typing_speed': data.get('typing_speed', None),
            'hesitation_count': data.get('hesitation_count', None)
        }

        pattern_result = pattern_agent.analyze(transaction)
        network_result = network_agent.analyze(transaction)
        behavior_result = behavior_agent.analyze(transaction)
        biometric_result = biometric_agent.analyze(transaction)

        agents = [pattern_result, network_result, behavior_result, biometric_result]
        overall_risk = aggregate_scores(agents)

        response = {
            'overallRisk': overall_risk,
            'agents': [
                {
                    'name': 'Pattern Agent',
                    'icon': '🕵️',
                    'color': '#00C896',
                    'riskScore': pattern_result['risk_score'],
                    'message': pattern_result['message'],
                    'details': pattern_result['details'],
                    'evidence': pattern_result.get('evidence', [])
                },
                {
                    'name': 'Network Agent',
                    'icon': '🕸️',
                    'color': '#0091FF',
                    'riskScore': network_result['risk_score'],
                    'message': network_result['message'],
                    'details': network_result['details'],
                    'evidence': network_result.get('evidence', [])
                },
                {
                    'name': 'Behavior Agent',
                    'icon': '🔍',
                    'color': '#A78BFA',
                    'riskScore': behavior_result['risk_score'],
                    'message': behavior_result['message'],
                    'details': behavior_result['details'],
                    'evidence': behavior_result.get('evidence', [])
                },
                {
                    'name': 'Biometric Agent',
                    'icon': '🎭',
                    'color': '#F472B6',
                    'riskScore': biometric_result['risk_score'],
                    'message': biometric_result['message'],
                    'details': biometric_result['details'],
                    'evidence': biometric_result.get('evidence', [])
                }
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report', methods=['POST'])
@token_required
def report_scam():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        user_id = request.current_user['user_id']
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
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    try:
        user_id = request.current_user['user_id']

        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        transactions = db.transactions
        tx_list = list(transactions.find({"user_id": user_id}).sort("created_at", -1).limit(20))

        history = []
        for tx in tx_list:
            history.append({
                'id': str(tx.get('_id', '')),
                'receiver': tx.get('receiver_id', ''),
                'amount': tx.get('amount', 0),
                'reason': tx.get('reason', ''),
                'created_at': tx.get('created_at', '').isoformat() if tx.get('created_at') else ''
            })

        return jsonify({'transactions': history}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/complete-transaction', methods=['POST'])
@token_required
def complete_transaction():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        amount = data.get('amount')
        user_id = request.current_user['user_id']

        if not receiver or not amount:
            return jsonify({'error': 'Missing required fields'}), 400

        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500

        transactions = db.transactions
        transaction_doc = {
            "receiver_id": receiver,
            "amount": float(amount),
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
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
@token_required
def submit_feedback():
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        user_id = request.current_user['user_id']
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
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == '__main__':
<<<<<<< HEAD
    # Start alert service
    alert_service.start()
    
    # Run SocketIO server (threading mode works with standard Flask dev server)
    print("🚀 Starting Flask-SocketIO server on http://localhost:5000")
    print("📡 WebSocket alerts enabled")
    socketio.run(app, debug=True, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)
=======
    app.run(debug=True, port=5000)
>>>>>>> 8b231281e303f9616859ac75b7ed2821ac187f70
