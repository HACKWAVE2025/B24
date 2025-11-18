const noop = () => {};

module.exports = {
  useWebSocket: () => ({
    alerts: [],
    isConnected: false,
    dismissAlert: noop,
    analysisResults: [],
    clearAnalysisResults: noop,
    recentTransactions: [],
    joinUserRoom: noop,
    leaveUserRoom: noop,
    requestRecentTransactions: noop,
    threatIntelAlerts: [],
    dismissThreatIntelAlert: noop,
  }),
};

