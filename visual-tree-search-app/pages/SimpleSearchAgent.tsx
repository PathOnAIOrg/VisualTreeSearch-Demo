import React from 'react';
import { useEffect, useRef, useState } from 'react';
import TreeReconstructor from "../components/TreeReconstructor_d3";
import ControlPanel from '../components/ControlPanel';
import MessageLogPanel from '../components/MessageLogPanel';
import LiveBrowserView from '../components/LiveBrowserView';

// Define types for our messages
interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface SearchParams {
  startingUrl: string;
  goal: string;
  algorithm: 'bfs' | 'dfs';
  maxDepth: number;
}

// Define type for tree messages used by TreeReconstructor - simpler version matching d3-playground
interface TreeMessage {
  type: string;
  nodeId?: string;
  nodeName?: string;
  parentId?: string;
  isRoot?: boolean;
  timestamp?: string;
  description?: string | null;
}

interface TreeNode {
  id: number;
  parent_id: number | null;
  action: string;
  description: string | null;
  depth: number;
  is_terminal: boolean;
}

interface BaseMessage {
  type: string;
  timestamp: string;
}

interface NodeProcessingMessage extends BaseMessage {
  type: 'node_processing';
  node_id: number;
  depth: number;
}

interface NodeExpandingMessage extends BaseMessage {
  type: 'node_expanding';
  node_id: number;
}

interface NodeQueuedMessage extends BaseMessage {
  type: 'node_queued';
  node_id: number;
  parent_id: number;
}

interface TreeUpdateMessage extends BaseMessage {
  type: 'tree_update';
  tree: TreeNode[];
}

type WebSocketMessage = NodeProcessingMessage | NodeExpandingMessage | NodeQueuedMessage | TreeUpdateMessage;

const TreeSearchPlayground = () => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [backendUrl, setBackendUrl] = useState<string>('');
  const [liveBrowserUrl, setLiveBrowserUrl] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Tree visualization state
  const [treeMessages, setTreeMessages] = useState<TreeMessage[]>([]);
  const [resetTree, setResetTree] = useState(false);

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
    console.log(`Backend URL from env: ${envBackendUrl}`);
  }, []);

  // Format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  // Extract live browser URL from message content if present
  const extractLiveBrowserUrl = (content: string): string | null => {
    try {
      // Try to parse JSON content
      const data = JSON.parse(content);
      return data.live_browser_url || null;
    } catch {
      // If not JSON, try to find URL in string
      const match = content.match(/"live_browser_url":\s*"([^"]+)"/);
      return match ? match[1] : null;
    }
  };

  // Log message to UI
  const logMessage = (message: unknown, type: 'incoming' | 'outgoing' = 'incoming') => {
    const content = typeof message === 'object' ? JSON.stringify(message, null, 2) : String(message);

    // Check for live browser URL and update state if found
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

  // Process messages for tree visualization - simpler logic like d3-playground
  const processTreeMessage = (data: WebSocketMessage) => {
    // Handle tree initialization when we see the root node for the first time
    if (data.type === 'node_processing' && data.depth === 0) {
      // This is the root node, reset the tree and add the root
      setTreeMessages([]);
      setResetTree(true);
      setTimeout(() => setResetTree(false), 100);

      // Create the root node message
      const rootMessage: TreeMessage = {
        type: 'node',
        nodeId: data.node_id.toString(),
        nodeName: 'ROOT',
        isRoot: true,
        timestamp: data.timestamp
      };
      
      setTreeMessages([rootMessage]);
    }

    // Handle any node traversal (processing or expanding)
    else if ((data.type === 'node_processing' || data.type === 'node_expanding') && data.node_id) {
      const traversalMessage: TreeMessage = {
        type: 'traversal',
        nodeId: data.node_id.toString(),
        timestamp: data.timestamp
      };

      setTreeMessages(prev => [...prev, traversalMessage]);
    }

    // Handle node queued - add a new node to the tree
    else if (data.type === 'node_queued' && data.node_id && data.parent_id) {
      const nodeMessage: TreeMessage = {
        type: 'node',
        nodeId: data.node_id.toString(),
        nodeName: `Action ${data.node_id}`,
        parentId: data.parent_id.toString(),
        timestamp: data.timestamp
      };

      setTreeMessages(prev => [...prev, nodeMessage]);
    }

    // Handle tree update - extract node information
    else if (data.type === 'tree_update' && Array.isArray(data.tree)) {
      // Update node names and actions based on the tree update
      data.tree.forEach((node: TreeNode) => {
        if (node.id) {
          // Create a message to update the node name and description
          const updateMessage: TreeMessage = {
            type: 'node',
            nodeId: node.id.toString(),
            nodeName: node.action,
            description: node.description,
            timestamp: data.timestamp
          };

          // If it's a root node
          if (node.parent_id === null) {
            updateMessage.isRoot = true;
          } else {
            // If it's a child node
            updateMessage.parentId = node.parent_id.toString();
          }

          setTreeMessages(prev => [...prev, updateMessage]);
        }
      });
    }
  };

  // Combined connect and start search in one function without delay
  const handleStart = () => {
    if (!connected) {
      // Setup websocket connection
      const wsUrl = `${backendUrl.replace('http', 'ws')}/tree-search-ws`;
      console.log(`Connecting to Tree Search WebSocket at: ${wsUrl}`);
      
      setIsSearching(true);

      try {
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          logMessage('Connected to Tree Search WebSocket server');
          setConnected(true);
          
          // Immediately start search after connection
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
          
          // Reset tree visualization
          setTreeMessages([]);
          setResetTree(true);
          setTimeout(() => setResetTree(false), 100);
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            logMessage(data);

            // Extract session ID if present in the message
            if (data.type === 'browser_setup' && data.status === 'success' && data.session_id) {
              setSessionId(data.session_id);
              console.log('Session ID set:', data.session_id);
            }

            // Process message for tree visualization
            processTreeMessage(data);
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
      // Already connected, just start search
      setIsSearching(true);
      
      // Reset tree visualization
      setTreeMessages([]);
      setResetTree(true);
      setTimeout(() => setResetTree(false), 100);

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

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Reset states
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
      
      {/* Main content area - Split View */}
      <div className="flex-1 px-4 mt-4 overflow-hidden">
        <div className="flex h-[calc(100vh-270px)] rounded-lg overflow-hidden shadow-lg">
          {/* Browser View Container */}
          <LiveBrowserView 
            liveBrowserUrl={liveBrowserUrl}
            width="70%"
          />

          {/* Tree Visualization Container */}
          <div className="w-[30%] bg-white dark:bg-slate-800 rounded-r-lg overflow-hidden">
            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
              <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                </svg>
                Tree Visualization
              </h2>
            </div>
            <div className="h-[calc(100%-48px)] w-full overflow-auto bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
              <TreeReconstructor
                messages={treeMessages}
                width={400}
                height={700}
                reset={resetTree}
              />
            </div>
          </div>
        </div>
        
        <MessageLogPanel
          messages={messages}
          messagesEndRef={messagesEndRef}
        />
      </div>
    </div>
  );
};

export default TreeSearchPlayground;
