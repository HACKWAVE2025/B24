import { createContext, useContext } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

const SocketContext = createContext(null);

export const SocketProvider = ({ children, isAuthenticated }) => {
  const socketValue = useWebSocket(isAuthenticated);
  return (
    <SocketContext.Provider value={socketValue}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocketContext = () => {
  const context = useContext(SocketContext);
  if (context === null) {
    console.warn('useSocketContext must be used within SocketProvider');
  }
  return context;
};

