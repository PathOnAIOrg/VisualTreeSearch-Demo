import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface TreeNode {
  id: string;
  name: string;
  children?: TreeNode[];
  _highlighted?: boolean;
}

interface TreeReconstructorProps {
  messages: {
    type: string;
    nodeId?: string;
    nodeName?: string;
    parentId?: string;
    isRoot?: boolean;
  }[];
  width?: number;
  height?: number;
}

const TreeReconstructor: React.FC<TreeReconstructorProps> = ({ 
  messages, 
  width = 800, 
  height = 600 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [nodeMap, setNodeMap] = useState<Map<string, TreeNode>>(new Map());
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);

  // Process messages to build tree
  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const newNodeMap = new Map<string, TreeNode>(nodeMap);
    let rootNode: TreeNode | null = null;
    let shouldUpdateTree = false;

    // Process node and traversal messages
    const treeMessages = messages.filter(msg => msg.type === 'node' || msg.type === 'traversal');
    
    for (const message of treeMessages) {
      if (message.isRoot) {
        // Create root node if it doesn't exist
        if (message.nodeId && !newNodeMap.has(message.nodeId)) {
          const root: TreeNode = {
            id: message.nodeId,
            name: message.nodeName || 'Root',
            children: []
          };
          newNodeMap.set(message.nodeId, root);
          rootNode = root;
          shouldUpdateTree = true;
        }
      } else if (message.parentId && message.nodeId && newNodeMap.has(message.parentId)) {
        // Add child node if parent exists
        if (!newNodeMap.has(message.nodeId)) {
          const newNode: TreeNode = {
            id: message.nodeId,
            name: message.nodeName || 'Unnamed Node',
            children: []
          };
          
          // Add to node map
          newNodeMap.set(message.nodeId, newNode);
          
          // Add as child to parent
          const parent = newNodeMap.get(message.parentId);
          if (parent) {
            parent.children = parent.children || [];
            parent.children.push(newNode);
            shouldUpdateTree = true;
          }
        }
      }
      
      // Set current node for highlighting only if nodeId exists
      if (message.nodeId) {
        setCurrentNodeId(message.nodeId);
      }
    }

    if (shouldUpdateTree) {
      setNodeMap(newNodeMap);
      if (rootNode) {
        setTree(rootNode);
      }
    }
  }, [messages, nodeMap]);

  // Render tree with D3
  useEffect(() => {
    if (!tree || !svgRef.current) return;

    // Clear previous rendering
    d3.select(svgRef.current).selectAll("*").remove();

    const margin = { top: 20, right: 90, bottom: 30, left: 90 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create D3 hierarchy
    const root = d3.hierarchy(tree);
    
    // Create tree layout
    const treeLayout = d3.tree<TreeNode>()
      .size([innerHeight, innerWidth]);
    
    // Apply layout
    treeLayout(root);

    // Create SVG container
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add links
    svg.selectAll(".link")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("d", function(d) {
        const linkGenerator = d3.linkHorizontal();
        return linkGenerator({
          source: [d.source.y, d.source.x] as [number, number],
          target: [d.target.y, d.target.x] as [number, number]
        });
      })
      .attr("fill", "none")
      .attr("stroke", "#555")
      .attr("stroke-width", 1.5);

    // Add nodes
    const nodes = svg.selectAll(".node")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", d => `node ${d.children ? "node--internal" : "node--leaf"}`)
      .attr("transform", d => `translate(${d.y},${d.x})`);

    // Add node circles
    nodes.append("circle")
      .attr("r", 10)
      .attr("fill", d => d.data.id === currentNodeId ? "#ff5722" : "#69b3a2")
      .attr("stroke", d => d.data.id === currentNodeId ? "#ff0000" : "#2c3e50")
      .attr("stroke-width", d => d.data.id === currentNodeId ? 3 : 1.5);

    // Add node labels
    nodes.append("text")
      .attr("dy", ".35em")
      .attr("x", d => d.children ? -15 : 15)
      .attr("text-anchor", d => d.children ? "end" : "start")
      .text(d => d.data.name)
      .attr("font-size", "12px")
      .attr("fill", "#333");

  }, [tree, width, height, currentNodeId]);

  return (
    <div className="tree-reconstructor">
      <div className="border rounded p-2 bg-card">
        <svg ref={svgRef} width={width} height={height}></svg>
      </div>
    </div>
  );
};

export default TreeReconstructor; 