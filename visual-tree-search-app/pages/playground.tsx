import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const WebSocketTest = () => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<{content: string; type: 'incoming' | 'outgoing'; timestamp: string}[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [backendUrl, setBackendUrl] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize backend URL from env variable
  useEffect(() => {
    const envBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3000';
    setBackendUrl(envBackendUrl);
    console.log(`Backend URL from env: ${envBackendUrl}`);
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  // Log message to UI
  const logMessage = (message: unknown, type: 'incoming' | 'outgoing' = 'incoming') => {
    const content = typeof message === 'object' ? JSON.stringify(message) : String(message);
    setMessages(prev => [...prev, {
      content,
      type,
      timestamp: formatTime(new Date())
    }]);
  };

  // Connect to WebSocket
  const connect = () => {
    const wsUrl = `${backendUrl}/ws`;
    console.log(`Connecting to WebSocket at: ${wsUrl}`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        logMessage('Connected to WebSocket server');
        setConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          logMessage(data);
        } catch {
          logMessage(event.data);
        }
      };
      
      wsRef.current.onclose = () => {
        logMessage('Disconnected from WebSocket server');
        setConnected(false);
        wsRef.current = null;
      };
      
      wsRef.current.onerror = (error) => {
        logMessage(`WebSocket error: ${error instanceof Error ? error.message : String(error)}`);
        setConnected(false);
      };
    } catch (error) {
      logMessage(`Failed to connect: ${error instanceof Error ? error.message : String(error)}`);
      setConnected(false);
    }
  };

  // Disconnect from WebSocket
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  // Send a message
  const sendMessage = () => {
    if (inputMessage.trim() && wsRef.current) {
      const data = {
        type: 'message',
        content: inputMessage.trim(),
        timestamp: new Date().toISOString()
      };
      
      wsRef.current.send(JSON.stringify(data));
      logMessage(data, 'outgoing');
      setInputMessage('');
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col space-y-4 p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-center">WebSocket Test Client</h1>
      
      <div className="mb-4">
        <span className="font-semibold mr-2">Backend URL:</span>
        <span>{backendUrl}</span>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle className={connected ? "text-green-600" : "text-red-600"}>
            {connected ? "Connected" : "Disconnected"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-2 mb-4">
            <Button 
              onClick={connect} 
              disabled={connected}
              variant="default"
            >
              Connect
            </Button>
            <Button 
              onClick={disconnect} 
              disabled={!connected}
              variant="destructive"
            >
              Disconnect
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Messages</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md p-4 bg-gray-50 dark:bg-gray-900">
            {messages.map((msg, index) => (
              <div 
                key={index} 
                className={`mb-2 p-2 rounded ${
                  msg.type === 'incoming' 
                    ? 'bg-gray-100 dark:bg-gray-800' 
                    : 'bg-blue-100 dark:bg-blue-900 text-right'
                }`}
              >
                <div>{msg.content}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{msg.timestamp}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>
      
      <div className="flex space-x-2">
        <Input
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          disabled={!connected}
          className="flex-1"
        />
        <Button 
          onClick={sendMessage} 
          disabled={!connected || !inputMessage.trim()}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default WebSocketTest;