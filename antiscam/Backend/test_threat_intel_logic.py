"""
Tests for threat intel recording logic
Verifies that:
1. Analyze endpoint does NOT automatically record to threat intel
2. Report endpoint DOES record to threat intel
3. Feedback endpoint records to threat intel when was_scam=true
4. Duplicate prevention works correctly
5. Error handling for invalid transaction IDs
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app after path setup
# Note: This assumes app.py is in the same directory or in Python path
try:
    from app import app
except ImportError:
    # If direct import fails, try importing the module
    # sys and os are already imported at the top
    # Add current directory explicitly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from app import app

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_token():
    """Mock JWT token"""
    return "mock_token_123"

@pytest.fixture
def mock_user_id():
    """Mock user ID"""
    return "user_123"

@pytest.fixture
def mock_agents():
    """Mock agent results"""
    return [
        {'risk_score': 50, 'message': 'Pattern risk detected'},
        {'risk_score': 60, 'message': 'Network risk detected'},
        {'risk_score': 40, 'message': 'Behavior risk detected'},
        {'risk_score': 30, 'message': 'Biometric risk detected'}
    ]

@pytest.fixture
def mock_transaction():
    """Mock transaction data"""
    return {
        'receiver': 'test@upi',
        'amount': 1000.0,
        'reason': 'Test transaction',
        'time': '10:00 AM',
        'user_id': 'user_123',
        'typing_speed': None,
        'hesitation_count': None
    }

class TestAnalyzeEndpoint:
    """Test that analyze endpoint does NOT automatically record to threat intel"""
    
    @patch('app.get_current_user_id')
    @patch('app.pattern_agent')
    @patch('app.network_agent')
    @patch('app.behavior_agent')
    @patch('app.biometric_agent')
    @patch('app.threat_intel_service')
    def test_analyze_does_not_record_to_threat_intel(
        self, mock_threat_intel, mock_biometric, mock_behavior, 
        mock_network, mock_pattern, mock_get_user_id, client, mock_agents
    ):
        """Verify analyze endpoint does NOT call record_agent_outputs"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_pattern.analyze.return_value = mock_agents[0]
        mock_network.analyze.return_value = mock_agents[1]
        mock_behavior.analyze.return_value = mock_agents[2]
        mock_biometric.analyze.return_value = mock_agents[3]
        
        mock_threat_intel.get_receiver_threat_score.return_value = 0.0
        mock_threat_intel.get_receiver_snapshot.return_value = {}
        
        # Make request
        response = client.post(
            '/api/analyze',
            json={
                'receiver': 'test@upi',
                'amount': 1000,
                'reason': 'Test transaction'
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert 'overallRisk' in data
        assert '_agentOutputs' in data  # Should include agent outputs for reporting
        assert '_transaction' in data  # Should include transaction data
        
        # Verify record_agent_outputs was NOT called
        mock_threat_intel.record_agent_outputs.assert_not_called()
        mock_threat_intel.update_and_get_score.assert_not_called()
    
    @patch('app.get_current_user_id')
    @patch('app.pattern_agent')
    @patch('app.network_agent')
    @patch('app.behavior_agent')
    @patch('app.biometric_agent')
    @patch('app.threat_intel_service')
    def test_analyze_reads_existing_threat_intel(
        self, mock_threat_intel, mock_biometric, mock_behavior,
        mock_network, mock_pattern, mock_get_user_id, client, mock_agents
    ):
        """Verify analyze endpoint reads existing threat intel for alerts"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_pattern.analyze.return_value = mock_agents[0]
        mock_network.analyze.return_value = mock_agents[1]
        mock_behavior.analyze.return_value = mock_agents[2]
        mock_biometric.analyze.return_value = mock_agents[3]
        
        # Mock existing threat intel
        mock_threat_intel.get_receiver_threat_score.return_value = 75.0
        mock_threat_intel.get_receiver_snapshot.return_value = {
            'threat_score': 75.0,
            'total_reports': 10
        }
        mock_threat_intel.check_receiver_in_trending.return_value = None
        mock_threat_intel.check_receiver_in_clusters.return_value = None
        mock_threat_intel.check_cluster_match.return_value = None
        
        # Make request
        response = client.post(
            '/api/analyze',
            json={
                'receiver': 'test@upi',
                'amount': 1000,
                'reason': 'Test transaction'
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify it read existing threat intel
        mock_threat_intel.get_receiver_threat_score.assert_called_once()
        mock_threat_intel.get_receiver_snapshot.assert_called_once()
        
        # But did NOT record new data
        mock_threat_intel.record_agent_outputs.assert_not_called()
        mock_threat_intel.update_and_get_score.assert_not_called()


class TestReportEndpoint:
    """Test that report endpoint DOES record to threat intel"""
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    def test_report_records_to_threat_intel(
        self, mock_threat_intel, mock_get_db, mock_get_user_id, 
        client, mock_agents, mock_transaction
    ):
        """Verify report endpoint records to threat intel"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_scam_reports = MagicMock()
        mock_scam_reports.find_one.return_value = None
        mock_db.scam_reports = mock_scam_reports
        
        # Mock threat intel service
        mock_history_collection = MagicMock()
        mock_history_collection.find_one.return_value = None  # Not already reported
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request
        response = client.post(
            '/api/report',
            json={
                'receiver': 'test@upi',
                'reason': 'High risk scam detected',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['recorded_to_threat_intel'] is True
        
        # Verify it recorded to threat intel
        mock_threat_intel.record_agent_outputs.assert_called_once()
        mock_threat_intel.update_and_get_score.assert_called_once()
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    def test_report_prevents_duplicates(
        self, mock_threat_intel, mock_get_db, mock_get_user_id,
        client, mock_agents, mock_transaction
    ):
        """Verify report endpoint prevents duplicate recording"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_scam_reports = MagicMock()
        mock_scam_reports.find_one.return_value = None
        mock_db.scam_reports = mock_scam_reports
        
        # Mock threat intel service - already reported
        mock_history_collection = MagicMock()
        mock_history_collection.find_one.return_value = {
            'receiver': 'test@upi',
            'transaction': {'user_id': 'user_123', 'amount': 1000.0, 'reason': 'Test transaction'}
        }
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request
        response = client.post(
            '/api/report',
            json={
                'receiver': 'test@upi',
                'reason': 'High risk scam detected',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['recorded_to_threat_intel'] is False  # Already reported
        
        # Verify it did NOT record again
        mock_threat_intel.record_agent_outputs.assert_not_called()
        mock_threat_intel.update_and_get_score.assert_not_called()


class TestFeedbackEndpoint:
    """Test that feedback endpoint records to threat intel when was_scam=true"""
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    @patch('app.save_feedback_and_check_retrain')
    @patch('app.save_pattern_feedback_and_retrain')
    def test_feedback_records_when_was_scam_true(
        self, mock_save_pattern, mock_save_feedback, mock_threat_intel,
        mock_get_db, mock_get_user_id, client, mock_agents, mock_transaction
    ):
        """Verify feedback endpoint records to threat intel when was_scam=true"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_feedback = MagicMock()
        mock_transactions = MagicMock()
        mock_db.feedback = mock_feedback
        mock_db.transactions = mock_transactions
        
        # Mock transaction document
        from bson import ObjectId
        mock_tx_doc = {
            '_id': ObjectId(),
            'amount': 1000.0,
            'reason': 'Test transaction',
            'time': '10:00 AM'
        }
        mock_transactions.find_one.return_value = mock_tx_doc
        
        # Mock threat intel service - not already reported
        mock_history_collection = MagicMock()
        mock_history_collection.find_one.return_value = None
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request
        response = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': True,
                'transaction_id': str(mock_tx_doc['_id']),
                'comment': 'This was a scam',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify it recorded to threat intel
        mock_threat_intel.record_agent_outputs.assert_called_once()
        mock_threat_intel.update_and_get_score.assert_called_once()
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    @patch('app.save_feedback_and_check_retrain')
    @patch('app.save_pattern_feedback_and_retrain')
    def test_feedback_does_not_record_when_was_scam_false(
        self, mock_save_pattern, mock_save_feedback, mock_threat_intel,
        mock_get_db, mock_get_user_id, client
    ):
        """Verify feedback endpoint does NOT record when was_scam=false"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_feedback = MagicMock()
        mock_db.feedback = mock_feedback
        
        # Make request
        response = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': False,
                'transaction_id': 'tx_123',
                'comment': 'This was safe'
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify it did NOT record to threat intel
        mock_threat_intel.record_agent_outputs.assert_not_called()
        mock_threat_intel.update_and_get_score.assert_not_called()
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    @patch('app.save_feedback_and_check_retrain')
    @patch('app.save_pattern_feedback_and_retrain')
    def test_feedback_prevents_duplicates(
        self, mock_save_pattern, mock_save_feedback, mock_threat_intel,
        mock_get_db, mock_get_user_id, client, mock_agents, mock_transaction
    ):
        """Verify feedback endpoint prevents duplicate recording"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_feedback = MagicMock()
        mock_transactions = MagicMock()
        mock_db.feedback = mock_feedback
        mock_db.transactions = mock_transactions
        
        # Mock transaction document
        from bson import ObjectId
        mock_tx_doc = {
            '_id': ObjectId(),
            'amount': 1000.0,
            'reason': 'Test transaction'
        }
        mock_transactions.find_one.return_value = mock_tx_doc
        
        # Mock threat intel service - already reported
        mock_history_collection = MagicMock()
        mock_history_collection.find_one.return_value = {
            'receiver': 'test@upi',
            'transaction': {'user_id': 'user_123', 'amount': 1000.0, 'reason': 'Test transaction'}
        }
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request
        response = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': True,
                'transaction_id': str(mock_tx_doc['_id']),
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify it did NOT record again
        mock_threat_intel.record_agent_outputs.assert_not_called()
        mock_threat_intel.update_and_get_score.assert_not_called()
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    @patch('app.save_feedback_and_check_retrain')
    @patch('app.save_pattern_feedback_and_retrain')
    def test_feedback_handles_invalid_transaction_id(
        self, mock_save_pattern, mock_save_feedback, mock_threat_intel,
        mock_get_db, mock_get_user_id, client, mock_agents, mock_transaction
    ):
        """Verify feedback endpoint handles invalid transaction_id gracefully"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_feedback = MagicMock()
        mock_db.feedback = mock_feedback
        
        # Mock threat intel service
        mock_history_collection = MagicMock()
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request with invalid transaction_id but valid agent_outputs and transaction
        response = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': True,
                'transaction_id': 'invalid_id',  # Invalid ObjectId format
                'comment': 'This was a scam',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response still succeeds (feedback is saved)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify it still recorded to threat intel using provided data
        mock_threat_intel.record_agent_outputs.assert_called_once()
        mock_threat_intel.update_and_get_score.assert_called_once()
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    @patch('app.save_feedback_and_check_retrain')
    @patch('app.save_pattern_feedback_and_retrain')
    def test_feedback_works_without_transaction_id(
        self, mock_save_pattern, mock_save_feedback, mock_threat_intel,
        mock_get_db, mock_get_user_id, client, mock_agents, mock_transaction
    ):
        """Verify feedback endpoint works when transaction_id is None"""
        # Setup mocks
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_feedback = MagicMock()
        mock_db.feedback = mock_feedback
        
        # Mock threat intel service
        mock_history_collection = MagicMock()
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Make request without transaction_id but with agent_outputs and transaction
        response = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': True,
                'transaction_id': None,
                'comment': 'This was a scam',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        
        # Verify response succeeds
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify it still recorded to threat intel using provided data
        mock_threat_intel.record_agent_outputs.assert_called_once()
        mock_threat_intel.update_and_get_score.assert_called_once()


class TestDynamicClusteringIntegration:
    """Integration tests for dynamic clustering with report and feedback"""
    
    @patch('app.get_current_user_id')
    @patch('app.get_db')
    @patch('app.threat_intel_service')
    def test_report_then_feedback_prevents_duplicate(
        self, mock_threat_intel, mock_get_db, mock_get_user_id,
        client, mock_agents, mock_transaction
    ):
        """Test that reporting via button then feedback doesn't create duplicate"""
        mock_get_user_id.return_value = "user_123"
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collections
        mock_scam_reports = MagicMock()
        mock_scam_reports.find_one.return_value = None
        mock_feedback = MagicMock()
        mock_transactions = MagicMock()
        mock_db.scam_reports = mock_scam_reports
        mock_db.feedback = mock_feedback
        mock_db.transactions = mock_transactions
        
        # Mock threat intel - first call returns None (not reported), second returns existing
        mock_history_collection = MagicMock()
        call_count = {'count': 0}
        def find_one_side_effect(*args, **kwargs):
            call_count['count'] += 1
            if call_count['count'] == 1:
                return None  # First check (report) - not found
            else:
                return {'receiver': 'test@upi'}  # Second check (feedback) - found
        
        mock_history_collection.find_one.side_effect = find_one_side_effect
        mock_threat_intel._get_collection.return_value = mock_history_collection
        
        # Step 1: Report via button
        response1 = client.post(
            '/api/report',
            json={
                'receiver': 'test@upi',
                'reason': 'High risk scam',
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        assert response1.status_code == 200
        assert response1.get_json()['recorded_to_threat_intel'] is True
        
        # Step 2: Submit feedback (should not record again)
        from bson import ObjectId
        mock_tx_doc = {
            '_id': ObjectId(),
            'amount': 1000.0,
            'reason': 'Test transaction'
        }
        mock_transactions.find_one.return_value = mock_tx_doc
        
        response2 = client.post(
            '/api/feedback',
            json={
                'receiver': 'test@upi',
                'was_scam': True,
                'transaction_id': str(mock_tx_doc['_id']),
                'agent_outputs': mock_agents,
                'transaction': mock_transaction
            },
            headers={'Authorization': 'Bearer mock_token'}
        )
        assert response2.status_code == 200
        
        # Verify record_agent_outputs was called only once (from report)
        assert mock_threat_intel.record_agent_outputs.call_count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

