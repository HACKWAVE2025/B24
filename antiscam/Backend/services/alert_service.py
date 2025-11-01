"""
Alert Service - Manages and schedules transaction alerts
"""
import time
from threading import Thread

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

