import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { toast } from 'sonner';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const useWebSocket = (isAuthenticated = false) => {
  const [alerts, setAlerts] = useState([]);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [threatIntelAlerts, setThreatIntelAlerts] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;

  useEffect(() => {
    // Only connect if authenticated
    if (!isAuthenticated) {
      // Disconnect if not authenticated
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    // Check if server is available before connecting
    const checkServerAvailability = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
        
        const response = await fetch(`${API_BASE_URL}/health`, {
          method: 'GET',
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        return response.ok;
      } catch (error) {
        return false;
      }
    };

    const initializeSocket = async () => {
      // Check if server is available
      const serverAvailable = await checkServerAvailability();
      if (!serverAvailable) {
        console.log('⚠️ Server is not available, skipping WebSocket connection');
        setIsConnected(false);
        return;
      }

      // Initialize socket connection
      // Start with polling (more reliable), then upgrade to websocket
      socketRef.current = io(API_BASE_URL, {
        transports: ['polling', 'websocket'],  // Polling first - more reliable for initial connection
        upgrade: true,  // Allow upgrade to websocket after initial connection
        reconnection: true,
        reconnectionDelay: 2000,
        reconnectionAttempts: maxReconnectAttempts,
        rememberUpgrade: true,  // Remember websocket upgrade for future connections
        timeout: 10000,
        forceNew: false
      });

      const socket = socketRef.current;

      // Connection events
      socket.on('connect', () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0; // Reset on successful connection
        socket.emit('request_alerts');
      });

      socket.on('disconnect', (reason) => {
        console.log('❌ WebSocket disconnected:', reason);
        setIsConnected(false);
        
        // If server closed connection or transport close, don't reconnect
        if (reason === 'io server disconnect' || reason === 'transport close') {
          socket.disconnect();
          socketRef.current = null;
        }
      });

      socket.on('connect_error', (error) => {
        console.log('❌ WebSocket connection error:', error.message);
        reconnectAttemptsRef.current += 1;
        
        // If max attempts reached or server is down, stop trying
        if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.log('⚠️ Max reconnection attempts reached, stopping WebSocket connection');
          socket.disconnect();
          socketRef.current = null;
          setIsConnected(false);
        }
      });

      socket.on('connected', (data) => {
        console.log('Server confirmation:', data);
      });

      socket.on('alerts_enabled', (data) => {
        console.log('Alerts enabled:', data);
      });

      // Receive new alerts
      socket.on('new_alert', (alert) => {
        console.log('📢 New alert received:', alert);
        setAlerts((prev) => [...prev, alert]);
      });

      // Receive real-time analysis results
      socket.on('analysis_result', (result) => {
        console.log('🔬 New analysis result received:', result);
        setAnalysisResults((prev) => [...prev, result]);

        const ctihScore = result?.threatIntel?.threatScore ?? result?.threatIntel?.score ?? 0;
        if (ctihScore > 70) {
          toast.warning("⚠ High Threat Intelligence Warning", {
            description: "This receiver matches ongoing scam activity reported by CTIH.",
          });
        }
      });

      socket.on('threat_intel_alert', (payload) => {
        console.log('🛰️ Threat intel alert received:', payload);
        const alertPayload = {
          ...payload,
          id: payload.generated_at || Date.now(),
        };
        setThreatIntelAlerts((prev) => [...prev, alertPayload]);
      });

      // Receive cluster match alerts
      socket.on('cluster_match_alert', (alert) => {
        console.log('🎯 Cluster match alert received:', alert);
        setAlerts((prev) => [alert, ...prev]);
        toast.warning("⚠️ Known Scam Pattern Detected", {
          description: alert.message || `This transaction matches a known scam pattern: ${alert.cluster?.name || 'Unknown'}`,
          duration: 6000,
        });
      });

      // Receive trending threat alerts
      socket.on('trending_threat_alert', (alert) => {
        console.log('🔥 Trending threat alert received:', alert);
        setAlerts((prev) => [alert, ...prev]);
        toast.error("🚨 Trending Threat Detected", {
          description: alert.message || `This receiver is in the trending threats list!`,
          duration: 8000,
        });
      });

      // Receive cluster member alerts
      socket.on('cluster_member_alert', (alert) => {
        console.log('🎯 Cluster member alert received:', alert);
        setAlerts((prev) => [alert, ...prev]);
        toast.warning("⚠️ Known Scam Cluster Member", {
          description: alert.message || `This receiver is part of a known scam cluster: ${alert.cluster?.name || 'Unknown'}`,
          duration: 6000,
        });
      });

      // Receive recent transactions
      socket.on('recent_transactions', (data) => {
        console.log('📋 Recent transactions received:', data);
        setRecentTransactions(data.transactions);
      });

      // Room management
      socket.on('room_joined', (data) => {
        console.log('🚪 Joined room:', data);
      });

      socket.on('room_left', (data) => {
        console.log('🚪 Left room:', data);
      });
    };

    initializeSocket();

    // Cleanup on unmount or when authentication changes
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
        setIsConnected(false);
        reconnectAttemptsRef.current = 0;
      }
    };
  }, [isAuthenticated]);

  const dismissAlert = (alertId) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const dismissThreatIntelAlert = (alertId) => {
    setThreatIntelAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const clearAnalysisResults = () => {
    setAnalysisResults([]);
  };

  const joinUserRoom = (userId) => {
    if (socketRef.current) {
      socketRef.current.emit('join_user_room', { user_id: userId });
    }
  };

  const leaveUserRoom = (userId) => {
    if (socketRef.current) {
      socketRef.current.emit('leave_user_room', { user_id: userId });
    }
  };

  const requestRecentTransactions = (userId, limit = 10) => {
    if (socketRef.current) {
      socketRef.current.emit('request_recent_transactions', { user_id: userId, limit });
    }
  };

  return {
    alerts,
    isConnected,
    dismissAlert,
    analysisResults,
    clearAnalysisResults,
    recentTransactions,
    joinUserRoom,
    leaveUserRoom,
    requestRecentTransactions,
    threatIntelAlerts,
    dismissThreatIntelAlert,
  };
};