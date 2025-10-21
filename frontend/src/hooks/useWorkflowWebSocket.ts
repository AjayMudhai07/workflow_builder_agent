import { useEffect, useRef, useState, useCallback } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface WebSocketMessage {
  event_type: string;
  workflow_id: string;
  data: any;
  timestamp: string;
}

export interface UseWorkflowWebSocketOptions {
  workflowId: string;
  onPhaseChange?: (phase: string) => void;
  onPlannerResponse?: (response: string, responseType: string) => void;
  onProgress?: (current: number, total: number, percentage: number) => void;
  onError?: (error: string) => void;
  onConnected?: () => void;
}

export function useWorkflowWebSocket({
  workflowId,
  onPhaseChange,
  onPlannerResponse,
  onProgress,
  onError,
  onConnected,
}: UseWorkflowWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;

  const connect = useCallback(() => {
    if (!workflowId) return;

    try {
      // Create WebSocket URL
      const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
      const url = `${wsUrl}/ws/workflows/${workflowId}`;

      console.log(`[WS] Connecting to: ${url}`);

      // Create WebSocket connection
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;

        if (onConnected) {
          onConnected();
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('[WS] Message received:', message);

          // Handle different event types
          switch (message.event_type) {
            case 'connected':
              console.log('[WS] Connection confirmed:', message.data);
              break;

            case 'phase_change':
              console.log('[WS] Phase changed:', message.data.phase);
              if (onPhaseChange) {
                onPhaseChange(message.data.phase);
              }
              break;

            case 'planner_response':
              console.log('[WS] Planner response:', message.data.response_type);
              if (onPlannerResponse) {
                onPlannerResponse(message.data.response, message.data.response_type);
              }
              break;

            case 'progress':
              console.log(
                `[WS] Progress: ${message.data.current}/${message.data.total} (${message.data.percentage}%)`
              );
              if (onProgress) {
                onProgress(message.data.current, message.data.total, message.data.percentage);
              }
              break;

            case 'error':
              console.error('[WS] Error:', message.data.error);
              setConnectionError(message.data.error);
              if (onError) {
                onError(message.data.error);
              }
              break;

            case 'status':
              console.log('[WS] Status update:', message.data);
              break;

            default:
              console.log('[WS] Unknown event type:', message.event_type, message);
          }
        } catch (err) {
          console.error('[WS] Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('[WS] Disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect if not a normal closure and haven't exceeded max attempts
        if (event.code !== 1000 && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${MAX_RECONNECT_ATTEMPTS})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setConnectionError('Max reconnection attempts reached');
        }
      };
    } catch (err) {
      console.error('[WS] Connection error:', err);
      setConnectionError('Failed to create WebSocket connection');
    }
  }, [workflowId, onPhaseChange, onPlannerResponse, onProgress, onError, onConnected]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log('[WS] Disconnecting');
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      console.warn('[WS] Cannot send message: WebSocket not connected');
    }
  }, []);

  const requestStatus = useCallback(() => {
    sendMessage('status');
  }, [sendMessage]);

  const ping = useCallback(() => {
    sendMessage('ping');
  }, [sendMessage]);

  // Connect on mount and disconnect on unmount
  useEffect(() => {
    // Only connect if we have a valid workflowId
    if (!workflowId) return;

    connect();

    return () => {
      disconnect();
    };
  }, [workflowId]); // Only reconnect if workflowId changes

  // Set up ping interval to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      ping();
    }, 30000); // Ping every 30 seconds

    return () => {
      clearInterval(pingInterval);
    };
  }, [isConnected, ping]);

  return {
    isConnected,
    connectionError,
    sendMessage,
    requestStatus,
    ping,
    reconnect: connect,
    disconnect,
  };
}
