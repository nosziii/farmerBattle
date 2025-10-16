import { ref } from 'vue';

const socket = ref<WebSocket | null>(null);

export const useWebSocket = () => {
  const connect = (clientId: string) => {
    socket.value = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    socket.value.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.value.onclose = () => {
      console.log('WebSocket disconnected');
    };

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.close();
    }
  };

  const onMessage = (callback: (event: MessageEvent) => void) => {
    if (socket.value) {
      socket.value.onmessage = callback;
    }
  };

  const sendMessage = (message: string) => {
    if (socket.value) {
      socket.value.send(message);
    }
  };

  return {
    connect,
    disconnect,
    onMessage,
    sendMessage,
  };
};
