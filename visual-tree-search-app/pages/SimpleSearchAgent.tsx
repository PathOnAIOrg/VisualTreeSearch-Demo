import React from 'react';
import { useEffect, useRef, useState } from 'react';
import ControlPanel from '../components/ControlPanel';
import MessageLogPanel from '../components/MessageLogPanel';
import LiveBrowserView from '../components/LiveBrowserView';
import SimpleSearchVisual from '../components/SimpleSearchVisual';

interface SearchParams {
  startingUrl: string;
  goal: string;
  algorithm: "bfs" | "dfs";
  maxDepth: number;
}

interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

const SimpleSearchAgent = () => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [backendUrl, setBackendUrl] = useState<string>('');
  const [liveBrowserUrl, setLiveBrowserUrl] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Search parameters
  const [searchParams, setSearchParams] = useState<SearchParams>({
    startingUrl: 'http://xwebarena.pathonai.org:7770/',
    goal: 'search running shoes, click on the first result',
    algorithm: 'bfs',
    maxDepth: 3
  });

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Initialize backend URL from env variable
  useEffect(() => {
    const envBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3000';
    setBackendUrl(envBackendUrl);
  }, []);

  // Format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  // Extract live browser URL from message content if present
  const extractLiveBrowserUrl = (content: string): string | null => {
    try {
      const data = JSON.parse(content);
      return data.live_browser_url || null;
    } catch {
      const match = content.match(/"live_browser_url":\s*"([^"]+)"/);
      return match ? match[1] : null;
    }
  };

  // Log message to UI
  const logMessage = (message: unknown, type: 'incoming' | 'outgoing' = 'incoming') => {
    const content = typeof message === 'object' ? JSON.stringify(message, null, 2) : String(message);

    const url = extractLiveBrowserUrl(content);
    if (url) {
      setLiveBrowserUrl(url);
    }

    setMessages(prev => [...prev, {
      content,
      type,
      timestamp: formatTime(new Date())
    }]);
  };

  // Combined connect and start search in one function
  const handleStart = () => {
    if (!connected) {
      const wsUrl = `${backendUrl.replace('http', 'ws')}/tree-search-ws`;
      setIsSearching(true);

      try {
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          logMessage('Connected to Tree Search WebSocket server');
          setConnected(true);
          
          const request = {
            type: "start_search",
            agent_type: "SimpleSearchAgent",
            starting_url: searchParams.startingUrl,
            goal: searchParams.goal,
            search_algorithm: searchParams.algorithm,
            max_depth: searchParams.maxDepth
          };
          
          wsRef.current?.send(JSON.stringify(request));
          logMessage(request, 'outgoing');
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            logMessage(data);

            if (data.type === 'browser_setup' && data.status === 'success' && data.session_id) {
              setSessionId(data.session_id);
            }
          } catch {
            logMessage(event.data);
          }
        };

        wsRef.current.onclose = () => {
          logMessage('Disconnected from WebSocket server');
          setConnected(false);
          setIsSearching(false);
          wsRef.current = null;
        };

        wsRef.current.onerror = (error) => {
          logMessage(`WebSocket error: ${error instanceof Error ? error.message : String(error)}`);
          setConnected(false);
          setIsSearching(false);
        };
      } catch (error) {
        logMessage(`Failed to connect: ${error instanceof Error ? error.message : String(error)}`);
        setConnected(false);
        setIsSearching(false);
      }
    } else {
      setIsSearching(true);
      const request = {
        type: "start_search",
        agent_type: "SimpleSearchAgent",
        starting_url: searchParams.startingUrl,
        goal: searchParams.goal,
        search_algorithm: searchParams.algorithm,
        max_depth: searchParams.maxDepth
      };

      wsRef.current?.send(JSON.stringify(request));
      logMessage(request, 'outgoing');
    }
  };

  // Disconnect from WebSocket
  const disconnect = async () => {
    if (sessionId) {
      try {
        const response = await fetch(`${backendUrl}/api/terminate-session/${sessionId}`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error(`Failed to terminate session: ${response.statusText}`);
        }
        logMessage(`Session ${sessionId} terminated successfully`);
      } catch (error) {
        logMessage(`Failed to terminate session: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    setSessionId(null);
    setLiveBrowserUrl(null);
    setIsSearching(false);
  };

  // Handle parameter changes
  const handleParamChange = (param: keyof SearchParams, value: string | boolean | number) => {
    setSearchParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-white dark:from-slate-900 dark:to-slate-800 pb-4 w-full flex flex-col">
      <ControlPanel
        searchParams={searchParams}
        handleParamChange={handleParamChange}
        handleStart={handleStart}
        disconnect={disconnect}
        isSearching={isSearching}
        connected={connected}
      />
      
      <div className="flex-1 px-4 mt-4 overflow-hidden">
        <div className="flex h-[calc(100vh-270px)] rounded-lg overflow-hidden shadow-lg">
          <LiveBrowserView 
            liveBrowserUrl={liveBrowserUrl}
            width="70%"
          />
          <SimpleSearchVisual messages={messages} />
        </div>
        
        {/* In LATSAgent.tsx */}
        <MessageLogPanel
          messages={messages}
          messagesEndRef={messagesEndRef}
          onSessionIdChange={(newSessionId) => {
            // Handle session ID change
            if (sessionId && sessionId !== newSessionId) {
              // Terminate old session if needed
              // ...terminate code...
            }
            setSessionId(newSessionId);
          }}
        />
      </div>
    </div>
  );
};

export default SimpleSearchAgent;
