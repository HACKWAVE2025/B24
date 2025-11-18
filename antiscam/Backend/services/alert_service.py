"""
Alert Service - Manages and schedules transaction alerts
"""
import time
from threading import Thread
from typing import Dict, Any

# Alert data
ALERTS = [
    {
        "upi_id": "loanhelp@upi",
        "amount": 10000,
        "message": "Get instant loan at 0% interest! Transfer ₹10,000 as verification deposit.",
    },
    {
        "upi_id": "urgentmoney@paytm",
        "amount": 5000,
        "message": "Need urgent money? Send ₹5000 to receive ₹10,000 instantly!",
    },
    {
        "upi_id": "kycupdate@bank",
        "amount": 2000,
        "message": "Your KYC is pending. Pay ₹2000 now to prevent account freeze.",
    },
    {
        "upi_id": "father@icici",
        "amount": 2500,
        "message": "Dinner payment to Dad ❤️",
    },
    {
        "upi_id": "grocery@upi",
        "amount": 1200,
        "message": "Monthly groceries payment",
    }
]

# Time intervals between alerts (in seconds)
# 2 minutes (120 seconds) between each alert
ALERT_INTERVALS = [120, 120, 120, 120, 120]  # 2 minutes between each alert


class AlertService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False
        self.thread = None
        self.alert_index = 0
        self.has_sent_first_alert = False
        self.threat_intel_service = None
        
    def start(self):
        """Start the alert service"""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._send_alerts_loop, daemon=True)
        self.thread.start()
        print("🚨 Alert service started")
        
    def stop(self):
        """Stop the alert service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("🚨 Alert service stopped")
    
    def send_first_alert_if_needed(self):
        """Send the first alert if it hasn't been sent yet (called when client connects)"""
        if not self.has_sent_first_alert and self.alert_index < len(ALERTS):
            alert = ALERTS[self.alert_index].copy()
            alert['id'] = f"alert_{self.alert_index}_{int(time.time())}"
            alert['timestamp'] = time.time()
            
            self.socketio.emit('new_alert', alert)
            print(f"📢 Sent first alert {self.alert_index + 1}/{len(ALERTS)}: {alert['upi_id']}")
            
            self.has_sent_first_alert = True
            # Increment index so next alert is ready
            self.alert_index += 1
        
    def _send_alerts_loop(self):
        """Main loop that sends alerts at intervals"""
        # Wait a bit for clients to connect before sending first alert via loop
        time.sleep(2)
        
        while self.running:
            try:
                # Wait for the interval before sending next alert
                # Skip wait for first alert (it will be sent when client connects)
                if self.alert_index > 0:
                    interval = ALERT_INTERVALS[(self.alert_index - 1) % len(ALERT_INTERVALS)]
                    time.sleep(interval)
                
                if not self.running:
                    break
                
                # Skip first alert if already sent via send_first_alert_if_needed
                # (alert_index was already incremented in send_first_alert_if_needed)
                if not self.has_sent_first_alert and self.alert_index == 0:
                    # First alert will be sent when client connects
                    # Wait a bit for client connection
                    time.sleep(1)
                    continue
                
                # Send current alert
                if self.alert_index < len(ALERTS):
                    alert = ALERTS[self.alert_index].copy()
                    alert['id'] = f"alert_{self.alert_index}_{int(time.time())}"
                    alert['timestamp'] = time.time()
                    
                    # Emit to all connected clients
                    # In newer python-socketio versions, socketio.emit() broadcasts by default
                    # when called outside a request context, so no 'broadcast' parameter needed
                    self.socketio.emit('new_alert', alert)
                    print(f"📢 Sent alert {self.alert_index + 1}/{len(ALERTS)}: {alert['upi_id']}")
                    
                    self.alert_index += 1
                else:
                    # All alerts sent, wait a bit and restart
                    print("✅ All alerts sent. Restarting cycle in 60 seconds...")
                    time.sleep(60)
                    self.alert_index = 0
                    self.has_sent_first_alert = False
                    
            except Exception as e:
                print(f"❌ Error in alert service: {e}")
                time.sleep(5)  # Wait before retrying
    
    def reset(self):
        """Reset alert index (for testing)"""
        self.alert_index = 0
        print("🔄 Alert service reset")

    def set_threat_intel_service(self, threat_intel_service):
        """Inject CTIH reference after initialization."""
        self.threat_intel_service = threat_intel_service

    def push_threat_alerts(self):
        """
        Broadcast trending threats from CTIH.
        Intended to be called when fresh intel is available.
        """
        if not self.threat_intel_service:
            return

        trending = self.threat_intel_service.get_trending_threats(limit=3)
        if not trending:
            return

        payload = {
            "type": "threat_intel",
            "generated_at": time.time(),
            "threats": [
                {
                    "receiver": item.get("receiver"),
                    "threatScore": item.get("threat_score", 0),
                    "patternFlags": item.get("pattern_flags", []),
                    "lastSeen": item.get("last_seen"),
                }
                for item in trending
            ],
        }
        self.socketio.emit("threat_intel_alert", payload)

    def send_cluster_match_alert(
        self,
        user_id: str,
        transaction: dict,
        cluster_match: dict,
    ):
        """
        Send alert when a transaction matches an existing cluster pattern.
        
        Args:
            user_id: User ID to send alert to
            transaction: Transaction details (receiver, amount, reason)
            cluster_match: Matched cluster information from check_cluster_match()
        """
        if not cluster_match:
            return

        alert_payload = {
            "id": f"cluster_match_{int(time.time())}_{user_id}",
            "type": "cluster_match",
            "timestamp": time.time(),
            "transaction": {
                "receiver": transaction.get("receiver", ""),
                "amount": transaction.get("amount", 0),
                "reason": transaction.get("reason", ""),
            },
            "cluster": {
                "name": cluster_match.get("name", "Unknown Cluster"),
                "avgScore": cluster_match.get("avgScore", 0),
                "count": cluster_match.get("count", 0),
                "topKeywords": cluster_match.get("topKeywords", []),
                "similarity": cluster_match.get("similarity", 0),
            },
            "message": (
                f"⚠️ This transaction matches a known scam pattern: '{cluster_match.get('name', 'Unknown')}'. "
                f"This pattern has been reported {cluster_match.get('count', 0)} times with an average threat score of {cluster_match.get('avgScore', 0)}. "
                f"Please review carefully before proceeding."
            ),
        }

        # Broadcast to all connected clients (user rooms may not be set up)
        # The frontend will filter alerts based on user context if needed
        try:
            self.socketio.emit("cluster_match_alert", alert_payload, broadcast=True)
            print(f"📢 Sent cluster match alert (broadcast): {cluster_match.get('name')} for transaction to {transaction.get('receiver', 'unknown')}")
        except Exception as e:
            print(f"⚠️ Error sending cluster alert: {e}")

    def send_trending_threat_alert(
        self,
        user_id: str,
        transaction: Dict[str, Any],
        trending_info: Dict[str, Any],
    ) -> None:
        """Send alert when receiver is in trending threats."""
        if not trending_info:
            return

        alert_payload = {
            "id": f"trending_threat_{int(time.time())}_{user_id}",
            "type": "trending_threat",
            "timestamp": time.time(),
            "transaction": {
                "receiver": transaction.get("receiver", ""),
                "amount": transaction.get("amount", 0),
                "reason": transaction.get("reason", ""),
            },
            "trending": {
                "receiver": trending_info.get("receiver", ""),
                "threatScore": trending_info.get("threatScore", 0),
                "totalReports": trending_info.get("totalReports", 0),
                "patternFlags": trending_info.get("patternFlags", []),
            },
            "message": (
                f"🚨 WARNING: This receiver '{trending_info.get('receiver', 'Unknown')}' is in the trending threats list! "
                f"It has been reported {trending_info.get('totalReports', 0)} times with a threat score of {trending_info.get('threatScore', 0):.1f}. "
                f"Please exercise extreme caution before proceeding."
            ),
        }

        try:
            self.socketio.emit("trending_threat_alert", alert_payload, broadcast=True)
            print(f"📢 Sent trending threat alert (broadcast): {trending_info.get('receiver')} with {trending_info.get('totalReports', 0)} reports")
        except Exception as e:
            print(f"⚠️ Error sending trending threat alert: {e}")

    def send_cluster_member_alert(
        self,
        user_id: str,
        transaction: Dict[str, Any],
        cluster_info: Dict[str, Any],
    ) -> None:
        """Send alert when receiver is a member of a known cluster."""
        if not cluster_info:
            return

        alert_payload = {
            "id": f"cluster_member_{int(time.time())}_{user_id}",
            "type": "cluster_member",
            "timestamp": time.time(),
            "transaction": {
                "receiver": transaction.get("receiver", ""),
                "amount": transaction.get("amount", 0),
                "reason": transaction.get("reason", ""),
            },
            "cluster": {
                "clusterId": cluster_info.get("clusterId"),
                "name": cluster_info.get("name", "Unknown Cluster"),
                "avgScore": cluster_info.get("avgScore", 0),
                "count": cluster_info.get("count", 0),
                "topKeywords": cluster_info.get("topKeywords", []),
            },
            "message": (
                f"⚠️ This receiver is part of a known scam cluster: '{cluster_info.get('name', 'Unknown')}'. "
                f"This cluster has {cluster_info.get('count', 0)} similar scam reports with an average threat score of {cluster_info.get('avgScore', 0):.1f}. "
                f"Please review carefully before proceeding."
            ),
        }

        try:
            self.socketio.emit("cluster_member_alert", alert_payload, broadcast=True)
            print(f"📢 Sent cluster member alert (broadcast): {cluster_info.get('name')} for receiver {transaction.get('receiver', 'unknown')}")
        except Exception as e:
            print(f"⚠️ Error sending cluster member alert: {e}")

