from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime, timezone
from agents.pattern_agent import PatternAgent
from agents.network_agent import NetworkAgent
from agents.behavior_agent import BehaviorAgent
from agents.biometric_agent import BiometricAgent
from database.db import get_db, connect
from utils.score_aggregator import aggregate_scores
from routes.auth import auth_bp
from utils.auth import token_required
from typing import Dict, Any, Optional

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Register blueprints
app.register_blueprint(auth_bp)

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

# Initialize MongoDB connection and agents on startup
with app.app_context():
    try:
        connect()
        initialize_agents()
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")

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
        # Check if agents are initialized
        if not all([pattern_agent, network_agent, behavior_agent, biometric_agent]):
            return jsonify({'error': 'AI agents not initialized'}), 500
        
        data = request.get_json()
        
        # Validate required fields
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
            'reason': data.get('reason', data.get('message', '')),  # Accept 'message' or 'reason'
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
        
        # Format response
        response = {
            'overallRisk': overall_risk,
            'agents': [
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
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in analyze_transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        reason = data.get('reason', 'Reported scam')
        
        if not receiver:
            return jsonify({'error': 'Missing receiver ID'}), 400
        
        # Save to MongoDB
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
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
                        "updated_at": datetime.now(timezone.utc)
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
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            count = 1
        
        return jsonify({
            'success': True,
            'message': f'Scam reported successfully. Total reports for this ID: {count}'
        }), 200
        
    except Exception as e:
        print(f"Error in report_scam: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    """
    Get transaction history for the authenticated user
    """
    try:
        # Get user_id from token (from token_required decorator)
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        transactions = db.transactions
        
        # Get user transactions
        tx_list = list(transactions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(20))
        
        # Convert to list of dicts
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
                'created_at': formatted_date
            })
        
        return jsonify({'transactions': history}), 200
        
    except Exception as e:
        print(f"Error in get_history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
        
        # Save feedback
        feedback_doc = {
            "transaction_id": transaction_id,
            "receiver_id": receiver,
            "user_id": user_id,
            "was_scam": was_scam,
            "comment": data.get('comment', ''),
            "created_at": datetime.now(timezone.utc)
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
                            "updated_at": datetime.now(timezone.utc)
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
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in submit_feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)