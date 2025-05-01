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
  isSimulated?: boolean;
}

interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface TreeVisualProps {
  messages: Message[];
  visualType?: 'full' | 'mcts' | 'lats' | 'simple';
  className?: string;
  title?: string;
  onStart?: () => void;
}

const TreeVisual: React.FC<TreeVisualProps> = ({ 
  messages, 
  visualType = 'full',
  className = "w-[30%]",
  title = "Tree Visualization",
  onStart
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const { theme } = useTheme();
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [simulationStartNodeId, setSimulationStartNodeId] = useState<number | null>(null);
  const [treeNodes, setTreeNodes] = useState<TreeNode[]>([]);
  const [containerWidth, setContainerWidth] = useState<number>(0);
  const [simulatedNodes, setSimulatedNodes] = useState<number[]>([]);

  // Reset function to clear the tree view
  const resetTreeView = () => {
    setSelectedNodeId(null);
    setSimulationStartNodeId(null);
    setTreeNodes([]);
    setSimulatedNodes([]);
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();
    }
  };

  // Listen for start event
  useEffect(() => {
    if (onStart) {
      resetTreeView();
    }
  }, [onStart]);

  // Reset tree view when messages array is empty
  useEffect(() => {
    if (messages.length === 0) {
      resetTreeView();
    }
  }, [messages]);

  // Determine if we should use simulation features based on visualType
  const useSimulationFeatures = visualType !== 'simple';
  
  // Determine if we should show simulation legend items
  const showSimulationLegend = visualType === 'full' || visualType === 'lats';

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
    let newSimulationStartNodeId = simulationStartNodeId;
    let newSimulatedNodes = [...simulatedNodes];
    let hasChanges = false;

    messages.forEach(msg => {
      try {
        const data = JSON.parse(msg.content);
        
        // Handle regular node selection (during tree expansion/evaluation)
        if (data.type === 'node_selected' && data.node_id !== undefined) {
          newSelectedNodeId = data.node_id;
          hasChanges = true;
        }
        
        // Process simulation-related messages only if simulation features are enabled
        if (useSimulationFeatures) {
          // Handle simulation start node selection
          if (data.type === 'node_selected_for_simulation' && data.node_id !== undefined) {
            newSimulationStartNodeId = data.node_id;
            hasChanges = true;
          }
          
          // Handle simulated node creation
          if (data.type === 'node_simulated' && data.node_id !== undefined && data.parent_id !== undefined) {
            // Check if the node already exists in the tree
            const nodeExists = updatedTreeNodes.some(node => node.id === data.node_id);
            
            if (!nodeExists) {
              // Add the new simulated node to the tree
              updatedTreeNodes.push({
                id: data.node_id,
                parent_id: data.parent_id,
                action: data.action,
                description: data.description,
                isSimulated: true, // Mark as simulated
              });
              
              // Add to our list of simulated nodes
              newSimulatedNodes.push(data.node_id);
              hasChanges = true;
            } else {
              // If node already exists, update it to mark as simulated
              updatedTreeNodes = updatedTreeNodes.map(node => 
                node.id === data.node_id ? { ...node, isSimulated: true } : node
              );
              
              if (!newSimulatedNodes.includes(data.node_id)) {
                newSimulatedNodes.push(data.node_id);
                hasChanges = true;
              }
            }
          }
          
          // Handle simulation removal
          if (data.type === 'removed_simulation') {
            // Remove all simulated nodes from the tree
            updatedTreeNodes = updatedTreeNodes.filter(node => !node.isSimulated);
            
            newSimulatedNodes = []; // Clear simulated nodes list
            newSimulationStartNodeId = null; // Clear simulation start node
            hasChanges = true;
          }
        }
        
        // Handle tree structure updates
        // Process tree updates based on message type, handling both simple and simulation visualizations
        const isTreeUpdate = 
          data.type === 'tree_update_node_expansion' || 
          data.type === 'tree_update_node_children_evaluation' ||
          data.type === 'tree_update_node_backpropagation' ||
          data.type === 'tree_update_node_evaluation';
          
        if (isTreeUpdate && Array.isArray(data.tree)) {
          if (useSimulationFeatures && updatedTreeNodes.some(node => node.isSimulated)) {
            // Preserve simulation flags when updating from tree
            const simulatedNodeMap = new Map();
            updatedTreeNodes.forEach(node => {
              if (node.isSimulated) {
                simulatedNodeMap.set(node.id, true);
              }
            });
            
            // Apply the flag to the updated tree
            updatedTreeNodes = data.tree.map((node: TreeNode) => ({
              ...node,
              isSimulated: simulatedNodeMap.has(node.id) ? true : false
            }));
          } else {
            updatedTreeNodes = data.tree;
          }
          hasChanges = true;
        }
      } catch {
        // Skip messages that can't be parsed
      }
    });

    if (hasChanges) {
      setTreeNodes(updatedTreeNodes);
      setSelectedNodeId(newSelectedNodeId);
      if (useSimulationFeatures) {
        setSimulationStartNodeId(newSimulationStartNodeId);
        setSimulatedNodes(newSimulatedNodes);
      }
    }
  }, [messages, useSimulationFeatures]);

  // Render the tree visualization
  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous content
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // If no tree nodes but we have messages, show loading state
    if (!treeNodes.length && messages.length > 0) {
      const width = 400;
      const height = 700;
      const margin = { top: 40, right: 30, bottom: 40, left: 140 };
      
      // Create container group
      const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

      // Add loading text with a subtle animation
      g.append("text")
        .attr("x", width / 2 - margin.left - margin.right)
        .attr("y", height / 2 - margin.top - margin.bottom)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .attr("font-weight", "500")
        .attr("fill", theme === 'dark' ? "#E5E7EB" : "#4B5563")
        .text("Initializing search");

      // Add three dots that animate
      const dots = g.append("text")
        .attr("x", width / 2 - margin.left - margin.right + 80)
        .attr("y", height / 2 - margin.top - margin.bottom)
        .attr("text-anchor", "start")
        .attr("font-size", "16px")
        .attr("font-weight", "500")
        .attr("fill", theme === 'dark' ? "#60A5FA" : "#3B82F6")
        .text("");

      // Animate the dots
      const animateDots = () => {
        const states = ["", ".", "..", "..."];
        let currentState = 0;
        
        const updateDots = () => {
          dots.text(states[currentState]);
          currentState = (currentState + 1) % states.length;
        };

        updateDots();
        const intervalId = setInterval(updateDots, 500);
        return () => clearInterval(intervalId);
      };

      animateDots();
      return;
    }

    if (!treeNodes.length) return;

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
        .style("line-height", "1.5")
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
      .attr("stroke", d => {
        if (!useSimulationFeatures) {
          return theme === 'dark' ? "#9CA3AF" : "#6B7280";
        }
        
        // Link to a simulated node gets an orange color
        if (d.target.data.isSimulated) {
          return theme === 'dark' ? "#F97316" : "#FB923C"; // Orange for simulated paths
        }
        
        // Link from simulation start node
        if (d.source.data.id === simulationStartNodeId) {
          return theme === 'dark' ? "#10B981" : "#34D399"; // Green for simulation start path
        }
        
        // Default link color
        return theme === 'dark' ? "#9CA3AF" : "#6B7280";
      })
      .attr("stroke-width", d => {
        if (!useSimulationFeatures) {
          return 1.5;
        }
        
        // Thicker link for simulation paths
        if (d.target.data.isSimulated || d.source.data.id === simulationStartNodeId) {
          return 2.5;
        }
        return 1.5;
      })
      .attr("stroke-opacity", d => {
        if (!useSimulationFeatures) {
          return 0.7;
        }
        
        // More visible for simulation paths
        if (d.target.data.isSimulated || d.source.data.id === simulationStartNodeId) {
          return 0.9;
        }
        return 0.7;
      })
      .attr("stroke-dasharray", d => {
        if (!useSimulationFeatures) {
          return null;
        }
        
        // Dashed line for simulation paths
        if (d.target.data.isSimulated) {
          return "5,3";
        }
        return null;
      });

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
        if (!useSimulationFeatures) {
          // Simple visual mode
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
        }
        
        // Full visual mode with simulation features
        // Simulated node (orange)
        if (d.data.isSimulated) {
          return theme === 'dark' ? "#F97316" : "#FDBA74"; // Orange for simulated nodes
        }
        
        // Simulation start node (green)
        if (d.data.id === simulationStartNodeId) {
          return theme === 'dark' ? "#10B981" : "#34D399"; // Green for simulation start node
        }
        
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
        if (!useSimulationFeatures) {
          if (d.data.id === selectedNodeId) {
            return theme === 'dark' ? "#93C5FD" : "#2563EB";
          }
          return theme === 'dark' ? "#374151" : "#D1D5DB";
        }
        
        if (d.data.isSimulated) {
          return theme === 'dark' ? "#EA580C" : "#F97316"; // Darker orange stroke for simulated nodes
        }
        
        if (d.data.id === simulationStartNodeId) {
          return theme === 'dark' ? "#059669" : "#10B981"; // Darker green stroke for simulation start
        }
        
        if (d.data.id === selectedNodeId) {
          return theme === 'dark' ? "#93C5FD" : "#2563EB";
        }
        
        return theme === 'dark' ? "#374151" : "#D1D5DB";
      })
      .attr("stroke-width", d => {
        if (!useSimulationFeatures) {
          if (d.data.id === selectedNodeId) {
            return 3;
          }
          return 2;
        }
        
        if (d.data.isSimulated || d.data.id === simulationStartNodeId || d.data.id === selectedNodeId) {
          return 3;
        }
        return 2;
      });

    // Add node labels with tooltips
    nodes.append("text")
      .attr("dy", ".35em")
      .attr("x", d => {
        // Calculate the position based on node type and children
        const baseOffset = d.children ? -18 : 18;
        return baseOffset;
      })
      .attr("y", d => {
        // Add vertical offset to prevent overlapping
        return d.children ? -5 : 5;
      })
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
        if (!useSimulationFeatures) {
          if (d.data.id === selectedNodeId) {
            return theme === 'dark' ? "#93C5FD" : "#1D4ED8";
          }
          return theme === 'dark' ? "#FFFFFF" : "#111827";
        }
        
        if (d.data.isSimulated) {
          return theme === 'dark' ? "#FDBA74" : "#C2410C";
        }
        
        if (d.data.id === simulationStartNodeId) {
          return theme === 'dark' ? "#A7F3D0" : "#047857";
        }
        
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
          
          if (useSimulationFeatures) {
            if (d.data.id === simulationStartNodeId) {
              nodeInfo.push(`<span class="font-semibold text-green-600 dark:text-green-400">Simulation Starting Node</span>`);
            }
            
            if (d.data.isSimulated) {
              nodeInfo.push(`<span class="font-semibold text-orange-600 dark:text-orange-400">Simulated Node</span>`);
            }
          }
          
          if (d.data.id === selectedNodeId) {
            nodeInfo.push(`<span class="font-semibold text-blue-600 dark:text-blue-400">Selected Node</span>`);
          }
          
          if (nodeInfo.length > 0) {
            tooltipContent += `<div class="mt-2">${nodeInfo.join(' | ')}</div>`;
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

          // Add is_terminal info if available
          if (typeof d.data.is_terminal === 'boolean') {
            tooltipContent += `<div>Is Terminal: <span class="font-bold">${d.data.is_terminal ? 'Yes' : 'No'}</span></div>`;
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
      .translateExtent([[-1000, -1000], [1000, 1000]]) // Allow more freedom in movement
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    // Initialize zoom with identity transform
    svg.call(zoom)
      .call(zoom.transform, d3.zoomIdentity);

    // Enable dragging
    svg.style("cursor", "grab")
      .on("mousedown", function() {
        svg.style("cursor", "grabbing");
      })
      .on("mouseup", function() {
        svg.style("cursor", "grab");
      })
      .on("mouseleave", function() {
        svg.style("cursor", "grab");
      });

  }, [treeNodes, selectedNodeId, simulationStartNodeId, simulatedNodes, theme, containerWidth, useSimulationFeatures, messages.length]);

  return (
    <div className={`${className} bg-white dark:bg-slate-800 rounded-r-lg overflow-hidden`}>
      <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
          </svg>
          {title}
        </h2>
        
        {/* Integrated Legend and Workflow */}
        <div className="mt-2 space-y-1">
          {/* Color Legend */}
          <div className="flex flex-wrap gap-2 text-xs">
            <div className="flex items-center">
              <span className="w-3 h-3 rounded-full inline-block mr-1 bg-blue-500 dark:bg-blue-600"></span>
              <span className="text-gray-700 dark:text-gray-300">Selected</span>
            </div>
            {useSimulationFeatures && showSimulationLegend && (
              <>
                <div className="flex items-center">
                  <span className="w-3 h-3 rounded-full inline-block mr-1 bg-green-500 dark:bg-green-600"></span>
                  <span className="text-gray-700 dark:text-gray-300">Sim Start</span>
                </div>
                <div className="flex items-center">
                  <span className="w-3 h-3 rounded-full inline-block mr-1 bg-orange-500 dark:bg-orange-600"></span>
                  <span className="text-gray-700 dark:text-gray-300">Simulated</span>
                </div>
              </>
            )}
          </div>

          {/* Workflow Steps */}
          <div className="text-xs text-gray-600 dark:text-gray-400">
            {visualType === 'simple' && (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Select</span>
                <span className="text-gray-400">→</span>
                <span className="text-gray-500 dark:text-gray-400">●</span>
                <span>Expand</span>
                <span className="text-gray-400">→</span>
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Next</span>
              </div>
            )}
            {visualType === 'mcts' && (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Select</span>
                <span className="text-gray-400">→</span>
                <span className="text-gray-500 dark:text-gray-400">●</span>
                <span>Expand</span>
                <span className="text-gray-400">→</span>
                <span className="text-gray-500 dark:text-gray-400">●</span>
                <span>Simulate</span>
                <span className="text-gray-400">→</span>
                <span className="text-gray-500 dark:text-gray-400">●</span>
                <span>Update</span>
                <span className="text-gray-400">→</span>
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Repeat</span>
              </div>
            )}
            {visualType === 'lats' && (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Select</span>
                <span className="text-gray-400">→</span>
                <span className="text-orange-500 dark:text-orange-400">●</span>
                <span>Simulate</span>
                <span className="text-gray-400">→</span>
                <span className="text-green-500 dark:text-green-400">●</span>
                <span>Evaluate</span>
                <span className="text-gray-400">→</span>
                <span className="text-orange-500 dark:text-orange-400">●</span>
                <span>Remove</span>
                <span className="text-gray-400">→</span>
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Repeat</span>
              </div>
            )}
            {visualType === 'full' && (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Select</span>
                <span className="text-gray-400">→</span>
                <span className="text-orange-500 dark:text-orange-400">●</span>
                <span>Simulate</span>
                <span className="text-gray-400">→</span>
                <span className="text-green-500 dark:text-green-400">●</span>
                <span>Evaluate</span>
                <span className="text-gray-400">→</span>
                <span className="text-orange-500 dark:text-orange-400">●</span>
                <span>Remove</span>
                <span className="text-gray-400">→</span>
                <span className="text-blue-500 dark:text-blue-400">●</span>
                <span>Repeat</span>
              </div>
            )}
          </div>
        </div>
      </div>
      <div 
        ref={containerRef} 
        className="h-[calc(100%-48px)] w-full overflow-hidden bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800"
      >
        <svg 
          ref={svgRef} 
          width="100%" 
          height="700" 
          viewBox="0 0 400 700"
          className="overflow-visible"
        ></svg>
      </div>
    </div>
  );
};

export default TreeVisual;