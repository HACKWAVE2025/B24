"""
Transaction Service - Manages real-time transaction analysis and updates
"""
from database.db import get_db
from typing import Dict, Any, List, Optional
from pymongo.database import Database
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.db = get_db()
        
    def get_recent_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent transactions for a user from MongoDB
        
        Args:
            user_id: The user ID to fetch transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction documents
        """
        try:
            if self.db is None:
                logger.warning("Database not connected")
                return []
                
            transactions = self.db.transactions
            tx_list = list(transactions.find({"user_id": user_id})
                          .sort("created_at", -1)
                          .limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for tx in tx_list:
                if '_id' in tx:
                    tx['id'] = str(tx['_id'])
                    del tx['_id']
                    
            return tx_list
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []
    
    def get_transaction_analysis(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed analysis for a specific transaction
        
        Args:
            transaction_id: The transaction ID to fetch analysis for
            
        Returns:
            Transaction analysis data or None if not found
        """
        try:
            if self.db is None:
                logger.warning("Database not connected")
                return None
                
            transactions = self.db.transactions
            transaction = transactions.find_one({"_id": transaction_id})
            
            if transaction:
                # Convert ObjectId to string for JSON serialization
                transaction['id'] = str(transaction['_id'])
                del transaction['_id']
                return transaction
                
            return None
        except Exception as e:
            logger.error(f"Error fetching transaction analysis: {e}")
            return None
    
    def emit_transaction_update(self, transaction_data: Dict[str, Any], room: Optional[str] = None):
        """
        Emit a real-time transaction update to connected clients
        
        Args:
            transaction_data: The transaction data to emit
            room: Optional room to emit to (for user-specific updates)
        """
        try:
            if room:
                self.socketio.emit('transaction_update', transaction_data, room=room)
            else:
                self.socketio.emit('transaction_update', transaction_data)
            logger.info(f"Emitted transaction update for {transaction_data.get('receiver_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error emitting transaction update: {e}")
    
    def emit_analysis_result(self, analysis_result: Dict[str, Any], user_id: Optional[str] = None):
        """
        Emit a real-time analysis result to connected clients
        
        Args:
            analysis_result: The analysis result to emit
            user_id: Optional user ID to emit to (for user-specific updates)
        """
        try:
            # Add user_id to the result for client-side filtering
            analysis_result['user_id'] = user_id
            
            if user_id:
                # Emit to specific user room
                self.socketio.emit('analysis_result', analysis_result, room=f"user_{user_id}")
            else:
                # Emit to all connected clients
                self.socketio.emit('analysis_result', analysis_result)
            logger.info("Emitted analysis result")
        except Exception as e:
            logger.error(f"Error emitting analysis result: {e}")

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a specific user
        
        Args:
            user_id: The user ID to fetch analytics for
            
        Returns:
            Dictionary containing analytics data
        """
        try:
            if self.db is None:
                logger.warning("Database not connected")
                return {
                    'total_transactions': 0,
                    'high_risk_transactions': 0,
                    'medium_risk_transactions': 0,
                    'low_risk_transactions': 0,
                    'scams_prevented': 0,
                    'feedback_count': 0,
                    'recent_transactions': []
                }
                
            # Get transactions collection
            transactions = self.db.transactions
            
            # Get all transactions for this user
            user_transactions = list(transactions.find({"user_id": user_id}))
            
            # Calculate metrics
            total_transactions = len(user_transactions)
            high_risk_transactions = len([tx for tx in user_transactions if tx.get('risk_score', 0) >= 70])
            medium_risk_transactions = len([tx for tx in user_transactions if 40 <= tx.get('risk_score', 0) < 70])
            low_risk_transactions = len([tx for tx in user_transactions if tx.get('risk_score', 0) < 40])
            
            # Scams prevented (transactions with risk score >= 70 that were cancelled)
            scams_prevented = high_risk_transactions  # For now, we'll assume high risk transactions are prevented
            
            # Get feedback count
            feedback_collection = self.db.feedback
            feedback_count = feedback_collection.count_documents({"user_id": user_id})
            
            # Get recent transactions (last 5)
            recent_transactions = list(transactions.find({"user_id": user_id})
                                     .sort("created_at", -1)
                                     .limit(5))
            
            # Convert ObjectId to string for JSON serialization
            for tx in recent_transactions:
                if '_id' in tx:
                    tx['id'] = str(tx['_id'])
                    del tx['_id']
            
            return {
                'total_transactions': total_transactions,
                'high_risk_transactions': high_risk_transactions,
                'medium_risk_transactions': medium_risk_transactions,
                'low_risk_transactions': low_risk_transactions,
                'scams_prevented': scams_prevented,
                'feedback_count': feedback_count,
                'recent_transactions': recent_transactions
            }
        except Exception as e:
            logger.error(f"Error fetching user analytics: {e}")
            return {
                'total_transactions': 0,
                'high_risk_transactions': 0,
                'medium_risk_transactions': 0,
                'low_risk_transactions': 0,
                'scams_prevented': 0,
                'feedback_count': 0,
                'recent_transactions': []
            }
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """
        Get global analytics data across all users
        
        Returns:
            Dictionary containing global analytics data
        """
        try:
            if self.db is None:
                logger.warning("Database not connected")
                return {
                    'total_transactions': 0,
                    'total_users': 0,
                    'scams_detected': 0,
                    'feedback_count': 0
                }
                
            # Get collections
            transactions = self.db.transactions
            users = self.db.users
            feedback = self.db.feedback
            
            # Calculate global metrics
            total_transactions = transactions.count_documents({})
            total_users = users.count_documents({})
            
            # Scams detected (transactions with risk score >= 70)
            scams_detected = transactions.count_documents({"risk_score": {"$gte": 70}})
            
            # Total feedback count
            feedback_count = feedback.count_documents({})
            
            return {
                'total_transactions': total_transactions,
                'total_users': total_users,
                'scams_detected': scams_detected,
                'feedback_count': feedback_count
            }
        except Exception as e:
            logger.error(f"Error fetching global analytics: {e}")
            return {
                'total_transactions': 0,
                'total_users': 0,
                'scams_detected': 0,
                'feedback_count': 0
            }

# Global instance
transaction_service = None

def init_transaction_service(socketio):
    """Initialize the global transaction service instance"""
    global transaction_service
    transaction_service = TransactionService(socketio)
    return transaction_service

def get_transaction_service():
    """Get the global transaction service instance"""
    global transaction_service
    return transaction_service