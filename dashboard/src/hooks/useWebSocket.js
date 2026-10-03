import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook to connect to the real TraceWatt WebSocket alert stream.
 * Connects to VITE_WS_URL + '/ws/alerts' with 5-second automatic reconnection.
 *
 * @returns {{
 *   alerts: Array<Object>,
 *   connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error',
 *   clearAlerts: () => void
 * }}
 */
export function useWebSocket() {
  const [alerts, setAlerts] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const shouldConnectRef = useRef(true);

  const getWsUrl = () => {
    const rawUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const cleanUrl = rawUrl.endsWith('/') ? rawUrl.slice(0, -1) : rawUrl;
    return `${cleanUrl}/ws/alerts`;
  };

  const connect = useCallback(() => {
    if (!shouldConnectRef.current) return;

    const url = getWsUrl();
    setConnectionStatus('connecting');

    try {
      const socket = new WebSocket(url);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('connected');
        console.info(`[TraceWatt WS] Connected to ${url}`);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const alertItem = {
            id: payload.id || `ALT-${Date.now()}`,
            consumer_id: payload.consumer_id || 'UNKNOWN',
            ts: payload.ts || new Date().toISOString().replace('T', ' ').slice(0, 19),
            risk_level: payload.risk_level || 'Medium',
            cause: payload.cause || 'Theft Anomaly Detected',
            message: payload.message || 'Abnormal consumption deviation flagged by model',
          };
          setAlerts((prev) => [alertItem, ...prev].slice(0, 100));
        } catch (err) {
          console.warn('[TraceWatt WS] Received unparseable message:', event.data);
        }
      };

      socket.onerror = (error) => {
        console.warn('[TraceWatt WS] Error event on WebSocket:', error);
        setConnectionStatus('error');
      };

      socket.onclose = () => {
        setConnectionStatus('disconnected');
        console.info('[TraceWatt WS] Closed. Reconnecting in 5s...');

        // Reconnect after 5 seconds if still mounted
        if (shouldConnectRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };
    } catch (err) {
      console.error('[TraceWatt WS] Failed to create WebSocket:', err);
      setConnectionStatus('error');
      if (shouldConnectRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 5000);
      }
    }
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  useEffect(() => {
    shouldConnectRef.current = true;
    connect();

    return () => {
      shouldConnectRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    alerts,
    connectionStatus,
    clearAlerts,
  };
}

export default useWebSocket;
