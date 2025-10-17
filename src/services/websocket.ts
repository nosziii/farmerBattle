import { ref } from 'vue';

const socket = ref<WebSocket | null>(null);
const listeners = new Set<(event: MessageEvent) => void>();
let currentClientId: string | null = null;

export const useWebSocket = () => {
  const connect = (clientId: string) => {
    if (
      socket.value &&
      (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING) &&
      currentClientId === clientId
    ) {
      return;
    }

    if (socket.value) {
      socket.value.close();
    }

    currentClientId = clientId;
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
    socket.value = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onclose = () => {
      if (socket.value === ws) {
        socket.value = null;
        currentClientId = null;
      }
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event: MessageEvent) => {
      listeners.forEach((listener) => {
        try {
          listener(event);
        } catch (err) {
          console.error('WebSocket listener error:', err);
        }
      });
    };
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.close();
      socket.value = null;
      currentClientId = null;
    }
  };

  const onMessage = (callback: (event: MessageEvent) => void) => {
    listeners.add(callback);
    return () => listeners.delete(callback);
  };

  const offMessage = (callback: (event: MessageEvent) => void) => {
    listeners.delete(callback);
  };

  const sendMessage = (message: string) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(message);
    }
  };

  return {
    connect,
    disconnect,
    onMessage,
    offMessage,
    sendMessage,
  };
};
