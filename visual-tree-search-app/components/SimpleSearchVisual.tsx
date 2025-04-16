import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useTheme } from 'next-themes';

interface TreeNode {
  id: number;
  parent_id: number | null;
  action: string;
  description: string | null;
  depth?: number;
  is_terminal?: boolean;
  value?: number;
  visits?: number;
  feedback?: string;
  reward?: number;
}

interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface SimpleSearchVisualProps {
  messages: Message[];
}

const SimpleSearchVisual: React.FC<SimpleSearchVisualProps> = ({ messages }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const { theme } = useTheme();
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [treeNodes, setTreeNodes] = useState<TreeNode[]>([]);
  const [containerWidth, setContainerWidth] = useState<number>(0);

  // Set up resize observer to make the visualization responsive
  useEffect(() => {
    if (!containerRef.current) return;
    
    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        if (entry.target === containerRef.current) {
          const newWidth = entry.contentRect.width;
          if (newWidth > 0) {
            setContainerWidth(newWidth);
          }
        }
      }
    });
    
    resizeObserver.observe(containerRef.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // Cleanup tooltip on unmount
  useEffect(() => {
    return () => {
      if (tooltipRef.current) {
        tooltipRef.current.remove();
      }
    };
  }, []);

  // Process messages to extract tree data
  useEffect(() => {
    if (!messages.length) return;

    let updatedTreeNodes: TreeNode[] = [...treeNodes];
    let newSelectedNodeId = selectedNodeId;
    let hasChanges = false;

    messages.forEach(msg => {
      try {
        const data = JSON.parse(msg.content);
        
        // Handle node selection updates
        if (data.type === 'node_selected' && data.node_id !== undefined) {
          newSelectedNodeId = data.node_id;
          hasChanges = true;
        }
        
        // Handle tree structure updates
        if (data.type === 'tree_update_node_expansion' && Array.isArray(data.tree)) {
          updatedTreeNodes = data.tree;
          hasChanges = true;
        }
        
        // Handle node evaluation updates
        if (data.type === 'tree_update_node_evaluation' && Array.isArray(data.tree)) {
          updatedTreeNodes = data.tree;
          hasChanges = true;
        }
      } catch {
        // Skip messages that can't be parsed
      }
    });

    if (hasChanges) {
      setTreeNodes(updatedTreeNodes);
      setSelectedNodeId(newSelectedNodeId);
    }
  }, [messages]);

  // Render the tree visualization
  useEffect(() => {
    if (!svgRef.current || !treeNodes.length) return;

    // Clear previous content
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create or update tooltip
    const createTooltip = () => {
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
        .style("padding", "12px 16px")
        .style("font-size", "14px")
        .style("color", theme === 'dark' ? "#FFFFFF" : "#111827")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("max-width", "400px")
        .style("box-shadow", "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)")
        .node() as HTMLDivElement;
    };

    createTooltip();

    // Create hierarchical data structure
    const stratify = d3.stratify<TreeNode>()
      .id(d => d.id.toString())
      .parentId(d => d.parent_id !== null ? d.parent_id.toString() : null);

    // Try to create hierarchy, fall back to simple layout if it fails
    let root;
    try {
      root = stratify(treeNodes);
    } catch (error) {
      console.error("Failed to create hierarchy:", error);
      return;
    }

    // Set up dimensions
    const width = 400;
    const height = 700;
    const margin = { top: 40, right: 30, bottom: 40, left: 140 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create tree layout - horizontal tree
    const treeLayout = d3.tree<TreeNode>()
      .size([innerHeight, innerWidth]);
    
    // Apply the tree layout
    treeLayout(root);

    // Create container group
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add links
    g.selectAll(".link")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("d", d => {
        const sourceY = d.source.y ?? 0; // Default to 0 if undefined
        const sourceX = d.source.x ?? 0; // Default to 0 if undefined
        const targetY = d.target.y ?? 0; // Default to 0 if undefined
        const targetX = d.target.x ?? 0; // Default to 0 if undefined
        return `M${sourceY},${sourceX}C${(sourceY + targetY) / 2},${sourceX} ${(sourceY + targetY) / 2},${targetX} ${targetY},${targetX}`;
      })
      .attr("fill", "none")
      .attr("stroke", theme === 'dark' ? "#9CA3AF" : "#6B7280")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.7);

    // Create node groups
    const nodes = g.selectAll(".node")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", d => `node ${d.children ? "node--internal" : "node--leaf"}`)
      .attr("transform", d => `translate(${d.y},${d.x})`);

    // Add node circles
    nodes.append("circle")
      .attr("r", 12)
      .attr("fill", d => {
        // Selected node (blue)
        if (d.data.id === selectedNodeId) {
          return theme === 'dark' ? "#3B82F6" : "#60A5FA";
        }
        
        // Root node (gray)
        if (d.data.parent_id === null) {
          return theme === 'dark' ? "#6B7280" : "#D1D5DB";
        }
        
        // Action node (default)
        return theme === 'dark' ? "#4B5563" : "#E5E7EB";
      })
      .attr("stroke", d => {
        if (d.data.id === selectedNodeId) {
          return theme === 'dark' ? "#93C5FD" : "#2563EB";
        }
        return theme === 'dark' ? "#374151" : "#D1D5DB";
      })
      .attr("stroke-width", d => {
        if (d.data.id === selectedNodeId) {
          return 3;
        }
        return 2;
      });

    // Add node labels with tooltips
    nodes.append("text")
      .attr("dy", ".35em")
      .attr("x", d => d.children ? -18 : 18)
      .attr("text-anchor", d => d.children ? "end" : "start")
      .text(d => {
        // For root node
        if (d.data.parent_id === null) return "ROOT";
        
        // Show full action string
        if (d.data.action) {
          return d.data.action;
        }
        
        return d.data.id.toString().slice(-4);
      })
      .attr("font-size", "15px")
      .attr("font-weight", "500")
      .attr("fill", d => {
        if (d.data.id === selectedNodeId) {
          return theme === 'dark' ? "#93C5FD" : "#1D4ED8";
        }
        return theme === 'dark' ? "#FFFFFF" : "#111827";
      });

    // Add tooltip interactions
    nodes
    .on("mouseover", function(event, d) {
      if (tooltipRef.current) {
        let tooltipContent = '';
        
        // Add description if available
        if (d.data.description) {
          tooltipContent += `<p>${d.data.description}</p>`;
        }
        
        // Add node status information
        const nodeInfo = [];
        
        
        if (d.data.id === selectedNodeId) {
          nodeInfo.push(`<span class="font-semibold text-blue-600 dark:text-blue-400">Selected Node</span>`);
        }
        
        if (nodeInfo.length > 0) {
          tooltipContent += `<div class="mt-2">${nodeInfo.join(' | ')}</div>`;
        }
        
        // Add reward info if available
        if (typeof d.data.reward === 'number') {
          tooltipContent += `<div class="mt-1">Reward: <span class="font-bold">${d.data.reward.toFixed(2)}</span></div>`;
        }
        
        // Add value info if available
        if (typeof d.data.value === 'number') {
          tooltipContent += `<div>Value: <span class="font-bold">${d.data.value.toFixed(2)}</span></div>`;
        }
        
        // Add visits info if available
        if (typeof d.data.visits === 'number') {
          tooltipContent += `<div>Visits: <span class="font-bold">${d.data.visits}</span></div>`;
        }
        
        // Add depth info if available
        if (typeof d.data.depth === 'number') {
          tooltipContent += `<div>Depth: <span class="font-bold">${d.data.depth}</span></div>`;
        }
        
        const tooltip = d3.select(tooltipRef.current);
        tooltip.transition()
          .duration(200)
          .style("opacity", .9);
        tooltip.html(tooltipContent)
          .style("left", (event.pageX + 15) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
      .on("mousemove", function(event) {
        if (tooltipRef.current) {
          d3.select(tooltipRef.current)
            .style("left", (event.pageX + 15) + "px")
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

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

  }, [treeNodes, selectedNodeId, theme, containerWidth]);

  return (
    <div className="w-[30%] bg-white dark:bg-slate-800 rounded-r-lg overflow-hidden">
      <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
          </svg>
          Tree Visualization
        </h2>
        
        {/* Legend */}
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full inline-block mr-1 bg-blue-500 dark:bg-blue-600"></span>
            <span className="text-gray-700 dark:text-gray-300">Selected</span>
          </div>
        </div>
      </div>
      <div 
        ref={containerRef} 
        className="h-[calc(100%-48px)] w-full overflow-auto bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800"
      >
        <svg 
          ref={svgRef} 
          width="100%" 
          height="700" 
          className="overflow-visible"
        ></svg>
      </div>
    </div>
  );
};

export default SimpleSearchVisual;