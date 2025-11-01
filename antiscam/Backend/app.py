from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from agents.pattern_agent import PatternAgent
from agents.network_agent import NetworkAgent
from agents.behavior_agent import BehaviorAgent
from agents.biometric_agent import BiometricAgent
from database.db import get_db, connect
from utils.score_aggregator import aggregate_scores
from routes.auth import auth_bp
from utils.auth import token_required

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Register blueprints
app.register_blueprint(auth_bp)

# Initialize MongoDB connection
connect()

# Initialize agents
pattern_agent = PatternAgent()
network_agent = NetworkAgent()
behavior_agent = BehaviorAgent()
biometric_agent = BiometricAgent()


@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze_transaction():
    """
    Main endpoint: Analyzes transaction through all 4 agents
    
    Request body:
    {
        "receiver": "loanhelp@upi",
        "amount": 8000,
        "reason": "urgent help",
        "time": "2:05 AM",
        "user_id": "U123",
        "typing_speed": 150,  // optional for biometric agent
        "hesitation_count": 2  // optional
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['receiver', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get user_id from token (from token_required decorator)
        user_id = request.current_user['user_id']
        
        # Extract transaction details
        transaction = {
            'receiver': data.get('receiver', ''),
            'amount': float(data.get('amount', 0)),
            'reason': data.get('reason', data.get('message', '')),  # Accept 'message' or 'reason'
            'time': data.get('time', ''),
            'user_id': user_id,
            'typing_speed': data.get('typing_speed', None),
            'hesitation_count': data.get('hesitation_count', None)
        }
        
        # Run all agents
        pattern_result = pattern_agent.analyze(transaction)
        network_result = network_agent.analyze(transaction)
        behavior_result = behavior_agent.analyze(transaction)
        biometric_result = biometric_agent.analyze(transaction)
        
        # Aggregate scores
        agents = [
            pattern_result,
            network_result,
            behavior_result,
            biometric_result
        ]
        
        overall_risk = aggregate_scores(agents)
        
        # Format response
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
    """
    Report a scam ID to improve network agent
    
    Request body:
    {
        "receiver": "scammer@upi",
        "reason": "Fake loan scam"
    }
    """
    try:
        data = request.get_json()
        
        receiver = data.get('receiver')
        user_id = request.current_user['user_id']
        reason = data.get('reason', 'Reported scam')
        
        if not receiver:
            return jsonify({'error': 'Missing receiver ID'}), 400
        
        # Save to MongoDB
        db = get_db()
        scam_reports = db.scam_reports
        
        # Find existing report or create new
        existing = scam_reports.find_one({"receiver_id": receiver})
        
        if existing:
            # Update existing - increment count, add reason, add user_id if not present
            new_count = existing.get('count', 0) + 1
            reasons = existing.get('reasons', [])
            user_ids = existing.get('user_ids', [])
            
            if reason and reason not in reasons:
                reasons.append(reason)
            if user_id and user_id not in user_ids:
                user_ids.append(user_id)
            
            scam_reports.update_one(
                {"receiver_id": receiver},
                {
                    "$set": {
                        "count": new_count,
                        "reasons": reasons,
                        "user_ids": user_ids,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            count = new_count
        else:
            # Create new report
            scam_reports.insert_one({
                "receiver_id": receiver,
                "count": 1,
                "reasons": [reason] if reason else [],
                "user_ids": [user_id] if user_id else [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            count = 1
        
        return jsonify({
            'success': True,
            'message': f'Scam reported successfully. Total reports for this ID: {count}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    """
    Get transaction history for the authenticated user
    """
    try:
        user_id = request.current_user['user_id']
        
        db = get_db()
        transactions = db.transactions
        
        # Get user transactions
        tx_list = list(transactions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(20))
        
        # Convert to list of dicts
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
    """
    Complete a transaction (save to history after PIN confirmation)
    
    Request body:
    {
        "receiver": "example@upi",
        "amount": 1000,
        "reason": "Payment",
        "time": "2:05 AM",
        "risk_score": 85.5
    }
    """
    try:
        data = request.get_json()
        
        receiver = data.get('receiver')
        amount = data.get('amount')
        user_id = request.current_user['user_id']
        
        if not receiver or not amount:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Save to MongoDB
        db = get_db()
        transactions = db.transactions
        
        transaction_doc = {
            "receiver_id": receiver,
            "amount": float(amount),
            "reason": data.get('reason', ''),
            "user_id": user_id,
            "time": data.get('time', ''),
            "risk_score": data.get('risk_score', 0),
            "created_at": datetime.utcnow()
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
    """
    Submit feedback after transaction completion
    
    Request body:
    {
        "transaction_id": "tx123",
        "receiver": "example@upi",
        "was_scam": true,  // true if it was actually a scam, false otherwise
        "comment": "Optional comment"
    }
    """
    try:
        data = request.get_json()
        
        receiver = data.get('receiver')
        user_id = request.current_user['user_id']
        was_scam = data.get('was_scam')
        transaction_id = data.get('transaction_id')
        
        if receiver is None or was_scam is None:
            return jsonify({'error': 'Missing required fields: receiver, was_scam'}), 400
        
        db = get_db()
        feedback_collection = db.feedback
        
        # Save feedback
        feedback_doc = {
            "transaction_id": transaction_id,
            "receiver_id": receiver,
            "user_id": user_id,
            "was_scam": was_scam,
            "comment": data.get('comment', ''),
            "created_at": datetime.utcnow()
        }
        
        feedback_collection.insert_one(feedback_doc)
        
        # If user confirms it was a scam, increment scam count
        if was_scam:
            scam_reports = db.scam_reports
            existing = scam_reports.find_one({"receiver_id": receiver})
            
            if existing:
                # Increment count
                new_count = existing.get('count', 0) + 1
                reasons = existing.get('reasons', [])
                user_ids = existing.get('user_ids', [])
                
                if user_id and user_id not in user_ids:
                    user_ids.append(user_id)
                
                scam_reports.update_one(
                    {"receiver_id": receiver},
                    {
                        "$set": {
                            "count": new_count,
                            "user_ids": user_ids,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            else:
                # Create new scam report
                scam_reports.insert_one({
                    "receiver_id": receiver,
                    "count": 1,
                    "reasons": [data.get('comment', 'Confirmed scam by user')],
                    "user_ids": [user_id] if user_id else [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)

