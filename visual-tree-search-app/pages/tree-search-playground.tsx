import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import TreeReconstructor from "../components/TreeReconstructor_d3";
import { Info } from "lucide-react";

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

  // Tree visualization state - simpler, just like d3-playground
  const [treeMessages, setTreeMessages] = useState<TreeMessage[]>([]);
  const [resetTree, setResetTree] = useState(false);

  // Search parameters
  const [searchParams, setSearchParams] = useState<SearchParams>({
    startingUrl: 'http://128.105.145.205:7770/',
    goal: 'search running shoes, click on the first result',
    algorithm: 'bfs',
    maxDepth: 3
  });

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

  // Connect to WebSocket
  const connect = () => {
    const wsUrl = `${backendUrl.replace('http', 'ws')}/tree-search-ws`;
    console.log(`Connecting to Tree Search WebSocket at: ${wsUrl}`);

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        logMessage('Connected to Tree Search WebSocket server');
        setConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          logMessage(data);

          // Process message for tree visualization
          processTreeMessage(data);
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

  // Start search
  const startSearch = () => {
    if (!connected || !wsRef.current) {
      logMessage("Please connect to the WebSocket server first", "incoming");
      return;
    }

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

    wsRef.current.send(JSON.stringify(request));
    logMessage(request, 'outgoing');
  };

  // Handle parameter changes
  const handleParamChange = (param: keyof SearchParams, value: string | boolean | number) => {
    setSearchParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-8">
      {/* Header with title and guidance */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b sticky top-0 z-10">
        <div className="container mx-auto py-4 px-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Visual Tree Search</h1>
          
          {/* Introduction/Guidance Section */}
          <div className="mt-2 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4 flex gap-2">
            <Info className="h-5 w-5 text-blue-500 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-800 dark:text-blue-300">How to use this playground</h3>
              <p className="text-sm text-blue-700 dark:text-blue-400">
                1. Connect to the websocket server using the controls below.<br />
                2. Configure your search parameters.<br />
                3. Click &quot;Start Search&quot; to begin the visualization.<br />
                4. The tree of possible actions will appear on the left, while the resulting web page will display on the right.
              </p>
            </div>
          </div>
          
          {/* Controls section */}
          <div className="flex gap-4 mt-4">
            <Button onClick={connect} disabled={connected} className="bg-green-600 hover:bg-green-700">
              Connect
            </Button>
            <Button onClick={disconnect} disabled={!connected} variant="destructive">
              Disconnect
            </Button>
            <Button onClick={startSearch} disabled={!connected} variant="secondary" className="bg-blue-600 hover:bg-blue-700 text-white">
              Start Search
            </Button>
          </div>
        </div>
      </div>
      
      {/* Main content area - two column layout */}
      <div className="container mx-auto px-6 mt-6">
        <div className="flex flex-col lg:flex-row gap-6">
          
          {/* Left column - Tree Visualization */}
          <div className="lg:w-1/2 h-full flex flex-col">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4 h-full flex-grow">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                </svg>
                Tree Visualization
              </h2>
              <div className="h-[800px] rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                <TreeReconstructor
                  messages={treeMessages}
                  width={600}
                  height={800}
                  reset={resetTree}
                />
              </div>
            </div>
          </div>
          
          {/* Right column - Browser View & Controls */}
          <div className="lg:w-1/2 h-full flex flex-col gap-6">
            
            {/* Live Browser View */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-purple-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.083 9h1.946c.089-1.546.383-2.97.837-4.118A6.004 6.004 0 004.083 9zM10 2a8 8 0 100 16 8 8 0 000-16zm0 2c-.076 0-.232.032-.465.262-.238.234-.497.623-.737 1.182-.389.907-.673 2.142-.766 3.556h3.936c-.093-1.414-.377-2.649-.766-3.556-.24-.56-.5-.948-.737-1.182C10.232 4.032 10.076 4 10 4zm3.971 5c-.089-1.546-.383-2.97-.837-4.118A6.004 6.004 0 0115.917 9h-1.946zm-2.003 2H8.032c.093 1.414.377 2.649.766 3.556.24.56.5.948.737 1.182.233.23.389.262.465.262.076 0 .232-.032.465-.262.238-.234.498-.623.737-1.182.389-.907.673-2.142.766-3.556zm1.166 4.118c.454-1.147.748-2.572.837-4.118h1.946a6.004 6.004 0 01-2.783 4.118zm-6.268 0C6.412 13.97 6.118 12.546 6.03 11H4.083a6.004 6.004 0 002.783 4.118z" clipRule="evenodd" />
                </svg>
                Live Browser View
              </h2>
              <div className="rounded-md overflow-hidden border border-gray-300 dark:border-gray-600 bg-white">
                {liveBrowserUrl ? (
                  <iframe
                    src={liveBrowserUrl}
                    className="w-full rounded-md"
                    style={{ height: '400px' }}
                    title="Live Browser View"
                  />
                ) : (
                  <div className="h-[400px] flex items-center justify-center bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
                    <p>Browser view will appear here once the search starts</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Search Parameters */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                Search Parameters
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="startingUrl" className="text-gray-700 dark:text-gray-300">Starting URL</Label>
                  <Input
                    id="startingUrl"
                    value={searchParams.startingUrl}
                    onChange={(e) => handleParamChange('startingUrl', e.target.value)}
                    className="border-gray-300 dark:border-gray-600"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="goal" className="text-gray-700 dark:text-gray-300">Goal</Label>
                  <Input
                    id="goal"
                    value={searchParams.goal}
                    onChange={(e) => handleParamChange('goal', e.target.value)}
                    className="border-gray-300 dark:border-gray-600"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="algorithm" className="text-gray-700 dark:text-gray-300">Algorithm</Label>
                  <select
                    id="algorithm"
                    value={searchParams.algorithm}
                    onChange={(e) => handleParamChange('algorithm', e.target.value as 'bfs' | 'dfs')}
                    className="w-full p-2 border rounded bg-white dark:bg-gray-950 border-gray-300 dark:border-gray-600"
                  >
                    <option value="bfs">Breadth-First Search (BFS)</option>
                    <option value="dfs">Depth-First Search (DFS)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxDepth" className="text-gray-700 dark:text-gray-300">Max Depth</Label>
                  <Input
                    id="maxDepth"
                    type="number"
                    min={1}
                    max={10}
                    value={searchParams.maxDepth}
                    onChange={(e) => handleParamChange('maxDepth', parseInt(e.target.value))}
                    className="border-gray-300 dark:border-gray-600"
                  />
                </div>
              </div>
            </div>
            
            {/* Message Log */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
                Message Log
              </h2>
              <div className="h-[200px] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md p-2 bg-gray-50 dark:bg-gray-900">
                {messages.map((msg, index) => (
                  <div key={index} className={`mb-2 ${msg.type === 'outgoing' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-800 dark:text-gray-200'}`}>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{msg.timestamp} - {msg.type}</div>
                    <pre className="whitespace-pre-wrap bg-gray-100 dark:bg-gray-800 p-2 rounded text-sm border border-gray-200 dark:border-gray-700">{msg.content}</pre>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TreeSearchPlayground;
