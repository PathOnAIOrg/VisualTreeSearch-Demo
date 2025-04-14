import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useTheme } from 'next-themes';

interface Message {
  content: string | {
    type: string;
    tree?: Array<{
      id: number;
      parent_id: number | null;
      action: string;
      description: string | null;
    }>;
  };
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface SimpleSearchVisualProps {
  messages: Message[];
}

const SimpleSearchVisual: React.FC<SimpleSearchVisualProps> = ({ messages }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  // Simple placeholder visualization
  useEffect(() => {
    if (!svgRef.current || !messages.length) return;

    // Clear previous content
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create a simple placeholder visualization
    const width = 400;
    const height = 700;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    // Filter tree_update messages
    const treeUpdates = messages.filter(msg => {
      try {
        const data = typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content;
        return data.type === 'tree_update';
      } catch {
        return false;
      }
    });

    // Draw placeholder circles for each tree update
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    g.selectAll("circle")
      .data(treeUpdates)
      .enter()
      .append("circle")
      .attr("cx", (d, i) => (i % 3) * 100 + 50)
      .attr("cy", (d, i) => Math.floor(i / 3) * 100 + 50)
      .attr("r", 20)
      .attr("fill", theme === 'dark' ? "#4B5563" : "#9CA3AF")
      .attr("stroke", theme === 'dark' ? "#374151" : "#E5E7EB");

    // Add placeholder text
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("text-anchor", "middle")
      .attr("fill", theme === 'dark' ? "#FFFFFF" : "#111827")
      .text(`Tree Updates: ${treeUpdates.length}`);

  }, [messages, theme]);

  return (
    <div className="w-[30%] bg-white dark:bg-slate-800 rounded-r-lg overflow-hidden">
      <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
          </svg>
          Tree Visualization
        </h2>
      </div>
      <div ref={containerRef} className="h-[calc(100%-48px)] w-full overflow-auto bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        <svg 
          ref={svgRef} 
          width="400" 
          height="700" 
          className="overflow-visible"
        ></svg>
      </div>
    </div>
  );
};

export default SimpleSearchVisual;
