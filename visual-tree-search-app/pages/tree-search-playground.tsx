import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import TreeReconstructor from "@/components/TreeReconstructor_d3";

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
  headless: boolean;
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
    headless: true,
    maxDepth: 3
  });

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
    const content = typeof message === 'object' ? JSON.stringify(message, null, 2) : String(message);
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
      headless: searchParams.headless,
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
    <div className="container mx-auto p-4 max-h-screen overflow-y-auto">
      <div className="sticky top-0 z-10 bg-background pb-4">
        <h1 className="text-2xl font-bold mb-4">Tree Search Playground</h1>
        
        {/* Controls section - fixed at the top */}
        <div className="mb-6 flex gap-4">
          <Button onClick={connect} disabled={connected}>
            Connect
          </Button>
          <Button onClick={disconnect} disabled={!connected} variant="destructive">
            Disconnect
          </Button>
          <Button onClick={startSearch} disabled={!connected} variant="secondary">
            Start Search
          </Button>
        </div>
      </div>
      
      {/* Parameters section */}
      <div className="border rounded p-4 bg-card mb-6">
        <h2 className="text-xl font-semibold mb-4">Search Parameters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="startingUrl">Starting URL</Label>
            <Input 
              id="startingUrl"
              value={searchParams.startingUrl}
              onChange={(e) => handleParamChange('startingUrl', e.target.value)}
              disabled={connected}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="goal">Goal</Label>
            <Input 
              id="goal"
              value={searchParams.goal}
              onChange={(e) => handleParamChange('goal', e.target.value)}
              disabled={connected}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="algorithm">Algorithm</Label>
            <select 
              id="algorithm"
              value={searchParams.algorithm}
              onChange={(e) => handleParamChange('algorithm', e.target.value as 'bfs' | 'dfs')}
              disabled={connected}
              className="w-full p-2 border rounded bg-background"
            >
              <option value="bfs">Breadth-First Search (BFS)</option>
              <option value="dfs">Depth-First Search (DFS)</option>
            </select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="maxDepth">Max Depth</Label>
            <Input 
              id="maxDepth"
              type="number"
              min={1}
              max={10}
              value={searchParams.maxDepth}
              onChange={(e) => handleParamChange('maxDepth', parseInt(e.target.value))}
              disabled={connected}
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="headless" 
              checked={searchParams.headless}
              onCheckedChange={(checked) => handleParamChange('headless', !!checked)}
              disabled={connected}
            />
            <Label htmlFor="headless">Run in Headless Mode</Label>
          </div>
        </div>
      </div>
      
      {/* Tree Visualization section */}
      <div className="border rounded p-4 bg-card mb-6">
        <h2 className="text-xl font-semibold mb-2">Tree Visualization</h2>
        <div className="w-full h-[800px]">
          <TreeReconstructor 
            messages={treeMessages} 
            width={1200} 
            height={800}
            reset={resetTree}
          />
        </div>
      </div>
      
      {/* Log section */}
      <div>
        <h2 className="text-xl font-semibold mb-2">Message Log</h2>
        <div className="border rounded p-4 bg-card h-[400px] overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className={`mb-4 ${msg.type === 'outgoing' ? 'text-blue-500' : ''}`}>
              <div className="text-xs text-gray-500 mb-1">{msg.timestamp} - {msg.type}</div>
              <pre className="whitespace-pre-wrap bg-gray-100 dark:bg-gray-800 p-2 rounded">{msg.content}</pre>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
};

export default TreeSearchPlayground; 