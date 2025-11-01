import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const useWebSocket = () => {
  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize socket connection
    // Start with polling (more reliable), then upgrade to websocket
    socketRef.current = io(API_BASE_URL, {
      transports: ['polling', 'websocket'],  // Polling first - more reliable for initial connection
      upgrade: true,  // Allow upgrade to websocket after initial connection
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      rememberUpgrade: true,  // Remember websocket upgrade for future connections
      timeout: 20000,
      forceNew: false
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      socket.emit('request_alerts');
    });

    socket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      setIsConnected(false);
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

    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  const dismissAlert = (alertId) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  return { alerts, isConnected, dismissAlert };
};

