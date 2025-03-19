import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import * as d3 from 'd3';
import TreeReconstructor from "@/components/TreeReconstructor";

// Define types for our tree nodes
interface TreeNode {
  id: string;
  name: string;
  children?: TreeNode[];
  visited?: boolean;
  current?: boolean;
}

// Sample tree data
const sampleTree: TreeNode = {
  id: "1",
  name: "Root",
  children: [
    {
      id: "2",
      name: "Child 1",
      children: [
        { id: "5", name: "Grandchild 1" },
        { id: "6", name: "Grandchild 2" }
      ]
    },
    {
      id: "3",
      name: "Child 2",
      children: [
        { id: "7", name: "Grandchild 3" }
      ]
    },
    {
      id: "4",
      name: "Child 3",
      children: [
        { id: "8", name: "Grandchild 4" },
        { id: "9", name: "Grandchild 5" }
      ]
    }
  ]
};

// Define a type for tree messages
interface TreeMessage {
  type: string;
  nodeId?: string;
  content?: TreeNode;
  timestamp?: string;
}

const D3Playground = () => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<{content: string; type: 'incoming' | 'outgoing'; timestamp: string}[]>([]);
  const [backendUrl, setBackendUrl] = useState<string>('');
  const [treeData, setTreeData] = useState<TreeNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const treeContainerRef = useRef<HTMLDivElement>(null);
  const [treeMessages, setTreeMessages] = useState<TreeMessage[]>([]);

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

  // Generate a new random tree
  const generateTree = () => {
    // For simplicity, we'll use the sample tree
    setTreeData(JSON.parse(JSON.stringify(sampleTree)));
    logMessage("Generated new tree", "outgoing");
  };

  // Connect to WebSocket
  const connect = () => {
    if (!treeData) {
      logMessage("Please generate a tree first", "incoming");
      return;
    }

    const wsUrl = `${backendUrl.replace('http', 'ws')}/tree-ws`;
    console.log(`Connecting to Tree WebSocket at: ${wsUrl}`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        logMessage('Connected to Tree WebSocket server');
        setConnected(true);
        
        // Send the tree data to the server
        const data = {
          type: 'tree',
          content: treeData,
          timestamp: new Date().toISOString()
        };
        
        wsRef.current?.send(JSON.stringify(data));
        logMessage(data, 'outgoing');
        
        // Clear previous tree messages when starting a new connection
        setTreeMessages([]);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          logMessage(data);
          
          // Check if this is a tree traversal message
          if (data.type === 'traversal' && data.nodeId) {
            updateTreeVisualization(data.nodeId);
            
            // Store traversal messages for tree reconstruction
            setTreeMessages(prev => [...prev, data]);
          }
          
          // Also handle node messages for traversal visualization
          if (data.type === 'node' && data.nodeId) {
            updateTreeVisualization(data.nodeId);
            
            // Store node messages for tree reconstruction
            setTreeMessages(prev => [...prev, data]);
          }
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

  // Update tree visualization when a node is visited
  const updateTreeVisualization = (nodeId: string) => {
    if (!treeData) return;
    
    // Create a deep copy of the tree data
    const updatedTree = JSON.parse(JSON.stringify(treeData));
    
    // Helper function to update node status
    const updateNode = (node: TreeNode): boolean => {
      // Reset current flag for all nodes
      node.current = false;
      
      if (node.id === nodeId) {
        node.visited = true;
        node.current = true;
        return true;
      }
      
      if (node.children) {
        for (const child of node.children) {
          if (updateNode(child)) {
            return true;
          }
        }
      }
      
      return false;
    };
    
    updateNode(updatedTree);
    setTreeData(updatedTree);
  };

  // Render D3 tree visualization
  useEffect(() => {
    if (!treeData || !treeContainerRef.current) return;

    // Clear previous visualization
    d3.select(treeContainerRef.current).selectAll("*").remove();

    const width = 600;
    const height = 400;
    const margin = { top: 20, right: 90, bottom: 30, left: 90 };

    // Create SVG element if it doesn't exist
    const svg = d3.select(treeContainerRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create a tree layout
    const treeLayout = d3.tree<TreeNode>()
      .size([height - margin.top - margin.bottom, width - margin.left - margin.right]);

    // Create a hierarchy from the tree data
    const root = d3.hierarchy(treeData);
    
    // Assign x and y coordinates to each node
    const treeData2 = treeLayout(root);
    
    // Add links between nodes
    svg.selectAll(".link")
      .data(treeData2.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("d", d3.linkHorizontal<d3.HierarchyPointLink<TreeNode>, d3.HierarchyPointNode<TreeNode>>()
        .x(d => d.y)
        .y(d => d.x))
      .style("fill", "none")
      .style("stroke", "#ccc")
      .style("stroke-width", 2);

    // Add nodes
    const nodes = svg.selectAll(".node")
      .data(treeData2.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.y},${d.x})`);

    // Add circles for nodes
    nodes.append("circle")
      .attr("r", 10)
      .style("fill", d => {
        if (d.data.current) return "#ff0000"; // Current node (red)
        if (d.data.visited) return "#4caf50"; // Visited node (green)
        return "#fff"; // Unvisited node (white)
      })
      .style("stroke", "#2196f3")
      .style("stroke-width", 2);

    // Add labels for nodes
    nodes.append("text")
      .attr("dy", ".35em")
      .attr("x", d => d.children ? -13 : 13)
      .style("text-anchor", d => d.children ? "end" : "start")
      .text(d => d.data.name);

  }, [treeData]);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">D3 Tree Visualization Playground</h1>
      
      {/* Controls section */}
      <div className="mb-6 flex gap-4">
        <Button onClick={generateTree} disabled={connected}>
          Generate Tree
        </Button>
        <Button onClick={connect} disabled={connected || !treeData}>
          Connect & Start Traversal
        </Button>
        <Button onClick={disconnect} disabled={!connected}>
          Disconnect
        </Button>
      </div>
      
      {/* Visualization section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Original tree visualization */}
        <div className="border rounded p-4 bg-card">
          <h2 className="text-xl font-semibold mb-2">Original Tree</h2>
          <div ref={treeContainerRef} className="w-full h-[400px]"></div>
        </div>
        
        {/* Tree reconstruction visualization */}
        <div className="border rounded p-4 bg-card">
          <h2 className="text-xl font-semibold mb-2">Tree Reconstruction</h2>
          <TreeReconstructor 
            messages={treeMessages} 
            width={400} 
            height={400} 
          />
        </div>
      </div>
      
      {/* Log section */}
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Message Log</h2>
        <div className="border rounded p-4 bg-card h-[300px] overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className={`mb-2 ${msg.type === 'outgoing' ? 'text-blue-500' : ''}`}>
              <pre className="whitespace-pre-wrap">{msg.content}</pre>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
};

export default D3Playground; 