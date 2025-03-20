import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useTheme } from 'next-themes';

interface TreeNode {
  id: string;
  name: string;
  description?: string | null;
  children?: TreeNode[];
  _highlighted?: boolean;
}

interface TreeUpdateNode {
  id: number;
  parent_id: number | null;
  action: string;
  description: string | null;
  depth: number;
  is_terminal: boolean;
}

interface TreeReconstructorProps {
  messages: {
    type: string;
    nodeId?: string;
    nodeName?: string;
    parentId?: string;
    isRoot?: boolean;
    description?: string | null;
    tree?: Array<{
      id: number;
      parent_id: number | null;
      action: string;
      description: string | null;
      depth: number;
      is_terminal: boolean;
    }>;
  }[];
  width?: number;
  height?: number;
  reset?: boolean;
}

const TreeReconstructor: React.FC<TreeReconstructorProps> = ({ 
  messages, 
  width = 800, 
  height = 600,
  reset = false
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [nodeMap, setNodeMap] = useState<Map<string, TreeNode>>(new Map());
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const { theme } = useTheme();

  // Cleanup tooltip on unmount
  useEffect(() => {
    return () => {
      if (tooltipRef.current) {
        tooltipRef.current.remove();
      }
    };
  }, []);

  // Reset tree when reset prop changes to true
  useEffect(() => {
    if (reset) {
      setTree(null);
      setNodeMap(new Map());
      setCurrentNodeId(null);
      
      // Clear the SVG
      if (svgRef.current) {
        d3.select(svgRef.current).selectAll("*").remove();
      }
    }
  }, [reset]);

  // Process messages to build tree
  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const newNodeMap = new Map<string, TreeNode>(nodeMap);
    let rootNode: TreeNode | null = null;
    let shouldUpdateTree = false;

    // Process node and traversal messages
    const treeMessages = messages.filter(msg => msg.type === 'node' || msg.type === 'traversal' || msg.type === 'tree_update');
    
    for (const message of treeMessages) {
      if (message.type === 'tree_update' && Array.isArray(message.tree)) {
        console.log("Processing tree update:", message.tree); // Debug log
        // Handle tree update messages
        message.tree.forEach((node: TreeUpdateNode) => {
          if (node.id) {
            const existingNode = newNodeMap.get(node.id.toString());
            if (existingNode) {
              // Update existing node with description and name
              existingNode.description = node.description;
              existingNode.name = node.action || existingNode.name;
              console.log("Updated existing node:", existingNode); // Debug log
            } else {
              // Create new node with description
              const newNode: TreeNode = {
                id: node.id.toString(),
                name: node.action || 'Unnamed Node',
                description: node.description,
                children: []
              };
              console.log("Created new node:", newNode); // Debug log
              
              if (node.parent_id === null) {
                newNodeMap.set(node.id.toString(), newNode);
                rootNode = newNode;
                shouldUpdateTree = true;
              } else if (newNodeMap.has(node.parent_id.toString())) {
                newNodeMap.set(node.id.toString(), newNode);
                const parent = newNodeMap.get(node.parent_id.toString());
                if (parent) {
                  parent.children = parent.children || [];
                  parent.children.push(newNode);
                  shouldUpdateTree = true;
                }
              }
            }
          }
        });
      } else if (message.isRoot) {
        // Create root node if it doesn't exist
        if (message.nodeId && !newNodeMap.has(message.nodeId)) {
          const root: TreeNode = {
            id: message.nodeId,
            name: message.nodeName || 'Root',
            description: message.description || null,
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
            description: message.description || null,
            children: []
          };
          
          newNodeMap.set(message.nodeId, newNode);
          const parent = newNodeMap.get(message.parentId);
          if (parent) {
            parent.children = parent.children || [];
            parent.children.push(newNode);
            shouldUpdateTree = true;
          }
        } else {
          // Update existing node with new description if provided
          const existingNode = newNodeMap.get(message.nodeId);
          if (existingNode && message.description !== undefined) {
            existingNode.description = message.description;
            shouldUpdateTree = true;
          }
        }
      }
      
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
  }, [messages]);

  // Render tree with D3
  useEffect(() => {
    if (!tree || !svgRef.current) return;

    // Clear previous rendering
    d3.select(svgRef.current).selectAll("*").remove();

    // Remove existing tooltip if any
    if (tooltipRef.current) {
      tooltipRef.current.remove();
    }

    // Create tooltip
    tooltipRef.current = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background-color", theme === 'dark' ? "#1F2937" : "#FFFFFF")
      .style("border", `1px solid ${theme === 'dark' ? "#374151" : "#E5E7EB"}`)
      .style("border-radius", "4px")
      .style("padding", "8px 12px")
      .style("font-size", "14px")
      .style("color", theme === 'dark' ? "#FFFFFF" : "#111827")
      .style("pointer-events", "none")
      .style("z-index", "1000")
      .style("box-shadow", theme === 'dark' 
        ? "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
        : "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)")
      .node() as HTMLDivElement;

    // Increase right margin to accommodate labels
    const margin = { top: 20, right: 150, bottom: 30, left: 90 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create D3 hierarchy
    const root = d3.hierarchy(tree);
    
    // Create tree layout
    const treeLayout = d3.tree<TreeNode>()
      .size([innerHeight, innerWidth]);
    
    // Apply layout
    treeLayout(root);

    // Create SVG container with overflow handling
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("overflow", "visible")
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
      .attr("stroke", theme === 'dark' ? "#9CA3AF" : "#6B7280")
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

    // Add node labels with tooltips
    nodes.append("text")
      .attr("dy", ".35em")
      .attr("x", d => d.children ? -15 : 15)
      .attr("text-anchor", d => d.children ? "end" : "start")
      .text(d => d.data.name)
      .attr("font-size", "14px")
      .attr("font-weight", "500")
      .attr("fill", d => {
        if (d.data.id === currentNodeId) {
          return "#ff5722"; // Orange for current node
        }
        return theme === 'dark' ? "#FFFFFF" : "#111827"; // White for dark mode, dark gray for light mode
      });

    // Add tooltip interactions with debug logging
    nodes
      .on("mouseover", function(event, d) {
        if (d.data.description && tooltipRef.current) {
          const tooltip = d3.select(tooltipRef.current);
          tooltip.transition()
            .duration(200)
            .style("opacity", .9);
          tooltip.html(d.data.description)
            .style("left", (event.pageX +10 ) + "px")
            .style("top", (event.pageY - 50) + "px");
        }
      })
      .on("mousemove", function(event) {
        if (tooltipRef.current) {
          d3.select(tooltipRef.current)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        }
      })
      .on("mouseout", function() {
        if (tooltipRef.current) {
          d3.select(tooltipRef.current)
            .transition()
            .duration(500)
            .style("opacity", 0);
        }
      });

  }, [tree, width, height, currentNodeId, theme]);

  return (
    <div className="tree-reconstructor">
      <div className="border rounded p-2 bg-card overflow-visible">
        <svg ref={svgRef} width={width} height={height} className="overflow-visible"></svg>
      </div>
    </div>
  );
};

export default TreeReconstructor; 