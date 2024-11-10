// hooks/useWebSocket.ts
import { useState, useEffect } from 'react';

export const useWebSocket = (url: string) => {
  const [data, setData] = useState(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const websocket = new WebSocket(url);

    websocket.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setData(newData);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [url]);

  return { data, ws };
};