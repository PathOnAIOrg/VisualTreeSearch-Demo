import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import TreeReconstructor from "../components/TreeReconstructor_d3";
import { Info, ChevronDown, ChevronUp, Play, StopCircle, Search, CheckCircle, XCircle, ArrowRight, ArrowDown, PlusCircle } from "lucide-react";

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

// Add new interface for parsed message
interface ParsedMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

// Update MessageCard component
const MessageCard: React.FC<{ message: ParsedMessage }> = ({ message }) => {
  const [expanded, setExpanded] = useState(false);
  
  const getCardStyle = () => {
    switch (message.type) {
      case 'iteration_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'step_start':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'search_complete':
        return message.status === 'success' 
          ? "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800" 
          : "bg-gradient-to-r from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800";
      case 'node_expanding':
        return "bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800";
      case 'node_created':
        return "bg-gradient-to-r from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-800/20 border-indigo-200 dark:border-indigo-800";
      case 'node_processing':
        return "bg-gradient-to-r from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 border-cyan-200 dark:border-cyan-800";
      case 'node_scored':
        return "bg-gradient-to-r from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-200 dark:border-amber-800";
      case 'tree_update':
        return "bg-gradient-to-r from-teal-50 to-teal-100 dark:from-teal-900/20 dark:to-teal-800/20 border-teal-200 dark:border-teal-800";
      case 'browser_setup':
        return "bg-gradient-to-r from-sky-50 to-sky-100 dark:from-sky-900/20 dark:to-sky-800/20 border-sky-200 dark:border-sky-800";
      case 'feedback_generated':
        return "bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-emerald-200 dark:border-emerald-800";
      case 'replaying_action':
        return "bg-gradient-to-r from-violet-50 to-violet-100 dark:from-violet-900/20 dark:to-violet-800/20 border-violet-200 dark:border-violet-800";
      case 'generating_actions':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'level_complete':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'level_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'account_reset':
        return "bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800";
      case 'connection_established':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'status_update':
        return "bg-gradient-to-r from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800";
      case 'best_path_update':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      default:
        return "bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900/20 dark:to-gray-800/20 border-gray-200 dark:border-gray-800";
    }
  };

  const getIconBgColor = () => {
    switch (message.type) {
      case 'iteration_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'step_start':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'search_complete':
        return message.status === 'success' 
          ? "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400" 
          : "bg-yellow-100 dark:bg-yellow-800/30 text-yellow-600 dark:text-yellow-400";
      case 'node_expanding':
        return "bg-purple-100 dark:bg-purple-800/30 text-purple-600 dark:text-purple-400";
      case 'node_created':
        return "bg-indigo-100 dark:bg-indigo-800/30 text-indigo-600 dark:text-indigo-400";
      case 'node_processing':
        return "bg-cyan-100 dark:bg-cyan-800/30 text-cyan-600 dark:text-cyan-400";
      case 'node_scored':
        return "bg-amber-100 dark:bg-amber-800/30 text-amber-600 dark:text-amber-400";
      case 'tree_update':
        return "bg-teal-100 dark:bg-teal-800/30 text-teal-600 dark:text-teal-400";
      case 'browser_setup':
        return "bg-sky-100 dark:bg-sky-800/30 text-sky-600 dark:text-sky-400";
      case 'feedback_generated':
        return "bg-emerald-100 dark:bg-emerald-800/30 text-emerald-600 dark:text-emerald-400";
      case 'replaying_action':
        return "bg-violet-100 dark:bg-violet-800/30 text-violet-600 dark:text-violet-400";
      case 'generating_actions':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'level_complete':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'level_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'account_reset':
        return "bg-red-100 dark:bg-red-800/30 text-red-600 dark:text-red-400";
      case 'connection_established':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'status_update':
        if (message.status === 'running') return <Play className="h-5 w-5 text-green-500" />;
        if (message.status === 'initializing' || message.status === 'setting_up') return <Search className="h-5 w-5 text-blue-500" />;
        return <Info className="h-5 w-5 text-orange-500" />;
      case 'best_path_update':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getIcon = () => {
    switch (message.type) {
      case 'iteration_start':
        return <Play className="h-5 w-5 text-blue-500" />;
      case 'step_start':
        return <ArrowRight className="h-5 w-5 text-green-500" />;
      case 'search_complete':
        return message.status === 'success' ? 
          <CheckCircle className="h-5 w-5 text-green-500" /> : 
          <XCircle className="h-5 w-5 text-yellow-500" />;
      case 'node_expanding':
        return <ArrowDown className="h-5 w-5 text-purple-500" />;
      case 'node_created':
        return <PlusCircle className="h-5 w-5 text-indigo-500" />;
      case 'node_processing':
        return <Search className="h-5 w-5 text-cyan-500" />;
      case 'node_scored':
        return <CheckCircle className="h-5 w-5 text-amber-500" />;
      case 'node_queued':
        return <StopCircle className="h-5 w-5 text-orange-500" />;
      case 'tree_update':
        return <ChevronDown className="h-5 w-5 text-teal-500" />;
      case 'browser_setup':
        return <Play className="h-5 w-5 text-sky-500" />;
      case 'feedback_generated':
        return <Info className="h-5 w-5 text-emerald-500" />;
      case 'replaying_action':
        return <Play className="h-5 w-5 text-violet-500" />;
      case 'generating_actions':
        return <Search className="h-5 w-5 text-blue-500" />;
      case 'level_complete':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'level_start':
        return <Play className="h-5 w-5 text-blue-500" />;
      case 'account_reset':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'connection_established':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'status_update':
        if (message.status === 'running') return <Play className="h-5 w-5 text-green-500" />;
        if (message.status === 'initializing' || message.status === 'setting_up') return <Search className="h-5 w-5 text-blue-500" />;
        return <Info className="h-5 w-5 text-orange-500" />;
      case 'best_path_update':
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getTitle = () => {
    switch (message.type) {
      case 'iteration_start':
        return `Iteration ${message.iteration}`;
      case 'step_start': 
        return `Step ${message.step}`;
      case 'search_complete':
        return `Search ${message.status === 'success' ? 'Completed' : 'Partially Completed'}`;
      case 'node_expanding':
        return `Expanding Node`;
      case 'node_created': {
        // Extract short action name without parameters
        const actionBase = message.action?.split('(')[0];
        return `New Node: ${actionBase || 'Action'}`;
      }
      case 'node_processing':
        return `Processing Node`;
      case 'node_scored':
        return `Node Scored`;
      case 'node_queued':
        return `Node Queued`;
      case 'tree_update':
        return `Tree Updated`;
      case 'browser_setup':
        return `Browser Setup`;
      case 'feedback_generated':
        return `Feedback`;
      case 'replaying_action': {
        // Extract short action name without parameters
        const actionBase = message.action?.split('(')[0];
        return `Replaying: ${actionBase || 'Action'}`;
      }
      case 'generating_actions':
        return `Generating Actions`;
      case 'level_complete':
        return `Level ${message.level} Completed`;
      case 'level_start':
        return `Level ${message.level} Started`;
      case 'account_reset':
        return `Account Reset`;
      case 'connection_established':
        return `Connection Established`;
      case 'status_update':
        return `Status Update`;
      case 'best_path_update':
        return `Best Path Updated`;
      default:
        return message.type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
  };

  const getContent = () => {
    // Helper function to create parameter tags for short parameters only
    const createParamTag = (label: string, value: any, color: string = "blue") => {
      if (value === undefined || value === null) return null;
      if (typeof value === 'string' && value.length > 50) return null;
      
      const colors: Record<string, string> = {
        blue: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-700/50",
        green: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 border-green-200 dark:border-green-700/50",
        red: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700/50",
        yellow: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700/50",
        purple: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200 dark:border-purple-700/50",
        indigo: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border-indigo-200 dark:border-indigo-700/50",
        cyan: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300 border-cyan-200 dark:border-cyan-700/50",
        teal: "bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300 border-teal-200 dark:border-teal-700/50",
        gray: "bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300 border-gray-200 dark:border-gray-700/50"
      };
      
      const className = `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${colors[color]} mr-2 mb-2`;
      
      return (
        <span className={className}>
          <span className="font-semibold mr-1">{label}:</span> 
          <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
        </span>
      );
    };

    // Function to display longer text content with proper formatting
    const createTextContent = (text: string) => {
      if (!text) return null;
      return (
        <div className="text-sm text-slate-600 dark:text-slate-300 p-2 bg-white/80 dark:bg-slate-800/80 rounded border border-slate-200 dark:border-slate-700">
          {text}
        </div>
      );
    };

    // Create progress bar component
    const ProgressBar = ({ value, maxValue, color = "blue" }: { value: number, maxValue: number, color?: string }) => {
      const percentage = Math.min(Math.max((value / maxValue) * 100, 0), 100);
      
      const colors: Record<string, string> = {
        blue: "bg-blue-500",
        green: "bg-green-500",
        yellow: "bg-yellow-500",
        red: "bg-red-500",
        purple: "bg-purple-500",
        cyan: "bg-cyan-500",
        teal: "bg-teal-500",
        indigo: "bg-indigo-500"
      };
      
      return (
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mb-2">
          <div 
            className={`${colors[color]} h-2 rounded-full transition-all duration-300 ease-in-out`} 
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      );
    };
    
    // Node processing visualization
    if (message.type === 'node_processing') {
      return (
        <div className="w-full">
          <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
            <span>Depth: {message.depth}</span>
          </div>
          <ProgressBar value={message.depth} maxValue={5} color="cyan" />
        </div>
      );
    }
    
    // Node scoring visualization
    if (message.type === 'node_scored') {
      const score = parseFloat(message.score);
      const scoreColor = score >= 0.7 ? "green" : score >= 0.4 ? "yellow" : "red";
      
      return (
        <div className="w-full">
          <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
            <span>Score: {score.toFixed(2)}</span>
          </div>
          <ProgressBar value={score} maxValue={1} color={scoreColor} />
        </div>
      );
    }
    
    // Tree update visualization
    if (message.type === 'tree_update') {
      const nodeCount = message.tree?.length || 0;
      
      return (
        <div className="w-full">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-teal-500"></div>
            <span className="text-sm">{nodeCount} nodes in tree</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {nodeCount > 0 && Array(Math.min(nodeCount, 20)).fill(0).map((_, i) => (
              <div 
                key={i} 
                className="w-3 h-3 rounded-full bg-teal-500 opacity-80"
                style={{ animationDelay: `${i * 0.05}s` }}
              ></div>
            ))}
          </div>
        </div>
      );
    }
    
    // Search completion visualization
    if (message.type === 'search_complete') {
      return (
        <div className="w-full">
          <div className="flex items-center mb-3">
            {message.status === 'success' ? (
              <div className="flex items-center text-green-600 dark:text-green-400">
                <CheckCircle className="h-4 w-4 mr-1" />
                <span className="font-medium">Search successful</span>
                {message.score !== undefined && 
                  <span className="ml-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 rounded-full text-xs">{parseFloat(message.score).toFixed(2)}</span>
                }
              </div>
            ) : (
              <div className="flex items-center text-yellow-600 dark:text-yellow-400">
                <XCircle className="h-4 w-4 mr-1" />
                <span className="font-medium">Search partially complete</span>
                {message.score !== undefined && 
                  <span className="ml-1 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 rounded-full text-xs">{parseFloat(message.score).toFixed(2)}</span>
                }
              </div>
            )}
          </div>
          
          {message.path && message.path.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Path ({message.path.length} steps):</div>
              <div className="text-sm text-slate-600 dark:text-slate-300 p-2 bg-white/80 dark:bg-slate-800/80 rounded border border-slate-200 dark:border-slate-700 max-h-[150px] overflow-y-auto">
                {message.path.map((node: any, index: number) => (
                  <div key={index} className="flex items-center mb-1 last:mb-0">
                    <div className="mr-1 text-xs text-slate-500 dark:text-slate-400">{index + 1}.</div>
                    <div className="flex-1 truncate">{node.action}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }
    
    // Browser setup visualization
    if (message.type === 'browser_setup') {
      return (
        <div className="flex items-center space-x-2">
          {message.status === 'success' ? (
            <>
              <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
              <span className="text-green-600 dark:text-green-400">Browser ready</span>
            </>
          ) : (
            <>
              <div className="w-3 h-3 rounded-full bg-red-400 animate-pulse"></div>
              <span className="text-red-600 dark:text-red-400">Browser setup failed</span>
            </>
          )}
        </div>
      );
    }
    
    // Feedback visualization
    if (message.type === 'feedback_generated') {
      if (!message.feedback) return null;
      
      return (
        <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded border border-emerald-200 dark:border-emerald-800/50 text-sm text-slate-700 dark:text-slate-300 italic relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-emerald-400 dark:bg-emerald-600"></div>
          <div className="pl-2">{message.feedback}</div>
        </div>
      );
    }
    
    // Action-related message visualization (node_created and replaying_action)
    if (message.type === 'node_created' || message.type === 'replaying_action') {
      const actionBase = message.action?.split('(')[0] || '';
      
      // Try to extract special display for DOM element operations
      let actionType = 'generic';
      let actionTarget = '';
      
      if (message.action) {
        if (message.action.includes('click')) actionType = 'click';
        else if (message.action.includes('type')) actionType = 'type';
        else if (message.action.includes('scroll')) actionType = 'scroll';
        else if (message.action.includes('hover')) actionType = 'hover';
        
        // Try to extract target element
        const match = message.action.match(/\(["'](.+?)["']/);
        if (match) actionTarget = match[1];
      }
      
      return (
        <div>
          <div className="mb-2 flex items-center">
            {message.type === 'node_created' ? (
              <span className="mr-2 text-xs px-2 py-1 rounded-md bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
                New Node
              </span>
            ) : (
              <span className="mr-2 text-xs px-2 py-1 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300">
                Replaying
              </span>
            )}
            
            {actionType === 'click' && (
              <div className="flex items-center text-xs text-slate-600 dark:text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 mr-1">
                  <path d="M6.672 1.911a1 1 0 10-1.932.518l.259.966a1 1 0 001.932-.518l-.26-.966zM2.429 4.74a1 1 0 10-.517 1.932l.966.259a1 1 0 00.517-1.932l-.966-.26zm8.814-.569a1 1 0 00-1.415-1.414l-.707.707a1 1 0 101.415 1.415l.707-.708zm-7.071 7.072l.707-.707A1 1 0 003.465 9.12l-.708.707a1 1 0 001.415 1.415zm3.2-5.171a1 1 0 00-1.3 1.3l4 10a1 1 0 001.823.075l1.38-2.759 3.018 3.02a1 1 0 001.414-1.415l-3.019-3.02 2.76-1.379a1 1 0 00-.076-1.822l-10-4z" />
                </svg>
                Click on {actionTarget || "element"}
              </div>
            )}
            
            {actionType === 'type' && (
              <div className="flex items-center text-xs text-slate-600 dark:text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 mr-1">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" />
                </svg>
                Type text {actionTarget ? `in ${actionTarget}` : ""}
              </div>
            )}
            
            {actionType === 'scroll' && (
              <div className="flex items-center text-xs text-slate-600 dark:text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 mr-1">
                  <path d="M11 4a1 1 0 112 0v7.586l.293-.293a1 1 0 011.414 1.414l-2 2a1 1 0 01-1.414 0l-2-2a1 1 0 111.414-1.414l.293.293V4z" />
                  <path d="M5 4a1 1 0 00-1 1v10a7 7 0 0014 0V5a1 1 0 00-1-1h-1a1 1 0 000 2h.01v8a5 5 0 01-10 0V6H7a1 1 0 100-2H5z" />
                </svg>
                Scroll {actionTarget || "page"}
              </div>
            )}
            
            {actionType === 'hover' && (
              <div className="flex items-center text-xs text-slate-600 dark:text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 mr-1">
                  <path d="M8 16a.5.5 0 0 1-.5-.5v-1.293l-.646.647a.5.5 0 0 1-.707-.708L7.5 12.793V8.866l-3.4 1.963-.496 1.85a.5.5 0 1 1-.966-.26l.237-.882-1.12.646a.5.5 0 0 1-.5-.866l1.12-.646-.883-.237a.5.5 0 1 1 .258-.966l1.85.495L7 5.434v-1.26L5.147 2.9a.5.5 0 1 1 .707-.708l1.146 1.147h1.293a.5.5 0 1 1 0 1h-1.293l-1.146 1.147a.5.5 0 0 1-.708-.708L7 3.605v1.26l3.4 1.963 1.85-.495a.5.5 0 0 1 .258.966l-.883.237 1.12.646a.5.5 0 0 1-.5.866l-1.12-.646.237.882a.5.5 0 1 1-.966.26l-.495-1.85-3.4-1.963v3.927l1.353 1.353a.5.5 0 0 1-.707.708l-.647-.647V15.5a.5.5 0 0 1-.5.5z" />
                </svg>
                Hover over {actionTarget || "element"}
              </div>
            )}
            
            {actionType === 'generic' && (
              <div className="text-xs text-slate-600 dark:text-slate-400">
                {actionBase}
              </div>
            )}
          </div>
          
          {message.action && (
            <div className="mb-2">
              <code className="text-xs block px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 whitespace-nowrap overflow-x-auto">
                {message.action}
              </code>
            </div>
          )}
          
          {message.description && createTextContent(message.description)}
        </div>
      );
    }

    // Best Path Update visualization
    if (message.type === 'best_path_update') {
      const score = parseFloat(message.score || "0");
      const scoreColor = score >= 0.7 ? "green" : score >= 0.4 ? "yellow" : "red";
      
      return (
        <div className="w-full">
          <div className="flex items-center mb-2">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-500" />
            <span className="font-medium text-sm">Best Path Found</span>
            <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
              Score: {score.toFixed(2)}
            </span>
          </div>
          <ProgressBar value={score} maxValue={1} color={scoreColor} />
          
          {message.path && message.path.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Path ({message.path.length} steps):</div>
              <div className="text-sm text-slate-600 dark:text-slate-300 p-2 bg-blue-50/80 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800/50 max-h-[150px] overflow-y-auto">
                {message.path.map((node: any, index: number) => (
                  <div key={index} className="mb-2 last:mb-0">
                    <div className="flex items-center">
                      <div className="mr-2 bg-blue-100 dark:bg-blue-800/50 text-blue-800 dark:text-blue-300 w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </div>
                      <div className="font-medium text-blue-800 dark:text-blue-300">
                        {node.natural_language_description}
                      </div>
                    </div>
                    <div className="mt-1 ml-7 font-mono text-xs bg-white/80 dark:bg-slate-800/80 p-1 rounded border border-blue-100 dark:border-blue-800/30">
                      {node.action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    // Level-related message visualization
    if (message.type === 'level_complete' || message.type === 'level_start') {
      const isComplete = message.type === 'level_complete';
      
      return (
        <div className="flex items-center">
          <div className="flex items-center">
            {isComplete ? (
              <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 flex items-center justify-center mr-2">
                <CheckCircle className="h-5 w-5" />
              </div>
            ) : (
              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center mr-2">
                <Play className="h-5 w-5" />
              </div>
            )}
            <div>
              <div className="font-medium text-sm">{isComplete ? `Level ${message.level} Completed` : `Level ${message.level} Started`}</div>
            </div>
          </div>
        </div>
      );
    }
    
    // Step start visualization
    if (message.type === 'step_start') {
      return (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 flex items-center justify-center mr-2">
            <span className="text-sm font-bold">{message.step}</span>
          </div>
          <div className="text-sm">{message.step_name}</div>
        </div>
      );
    }

    // For other message types, use the previous logic
    switch (message.type) {
      case 'generating_actions':
        return (
          <div className="flex items-center">
            <div className="flex space-x-1 mr-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping" style={{ animationDelay: "0s" }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping" style={{ animationDelay: "0.2s" }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping" style={{ animationDelay: "0.4s" }}></div>
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">Generating possible actions...</span>
          </div>
        );
        
      case 'node_expanding':
        return (
          <div className="flex items-center">
            <ArrowDown className="h-4 w-4 mr-2 text-purple-500" />
            <span className="text-sm text-slate-600 dark:text-slate-400">Expanding node</span>
          </div>
        );
        
      case 'connection_established':
        return (
          <div className="flex items-center">
            <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 mr-2">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 dark:bg-green-400 animate-pulse"></div>
            </div>
            <span className="text-sm font-medium text-green-600 dark:text-green-400">Connected successfully</span>
          </div>
        );
        
      case 'status_update':
        return (
          <div className="flex items-center">
            <div className={`px-2 py-1 rounded-full text-xs mr-2 ${
              message.status === 'running' ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' :
              message.status === 'initializing' || message.status === 'setting_up' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300' :
              message.status === 'started' ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300' :
              'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300'
            }`}>
              {message.status}
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">{message.message}</span>
          </div>
        );
        
      case 'account_reset':
        return (
          <div className="flex items-center">
            <div className={`px-2 py-1 rounded-full text-xs mr-2 ${
              message.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' :
              message.status === 'started' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300' :
              'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
            }`}>
              {message.status}
            </div>
            {message.reason && <span className="text-sm text-slate-600 dark:text-slate-400">{message.reason}</span>}
          </div>
        );
        
      default:
        // Extract key parameters for other message types
        const relevantParams = Object.entries(message)
          .filter(([key, value]) => {
            if (['type', 'timestamp', 'node_id', 'parent_id', 'session_id', 'message', 'connection_id'].includes(key)) return false;
            if (typeof value === 'object') return false;
            if (typeof value === 'string' && value.length > 50) return false;
            return true;
          })
          .slice(0, 2); // Limit to first 2 parameters to reduce clutter
        
        return relevantParams.length > 0 ? (
          <div className="flex flex-wrap">
            {relevantParams.map(([key, value], idx) => 
              <React.Fragment key={key}>
                {createParamTag(key.replace(/_/g, ' '), value, "gray")}
              </React.Fragment>
            )}
          </div>
        ) : null;
    }
  };
  
  return (
    <div className={`rounded-lg shadow-md border p-3 mb-2 hover:shadow-lg transition-all ${getCardStyle()}`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${getIconBgColor()}`}>
          {getIcon()}
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-medium text-slate-900 dark:text-slate-100">{getTitle()}</h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-white/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
              {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ""}
            </span>
          </div>
          
          {getContent() && (
            <div className="mb-2">
              {getContent()}
            </div>
          )}
          
          <button 
            className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 hover:bg-white/70 dark:hover:bg-slate-700/70 transition-colors ${
              expanded 
                ? "bg-white/50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300" 
                : "bg-white/30 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400"
            }`}
            onClick={() => setExpanded(prev => !prev)}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3 w-3" /> Hide
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" /> Details
              </>
            )}
          </button>
          
          {expanded && (
            <div className="mt-2 animate-fadeIn">
              <pre className="p-2 bg-white/50 dark:bg-slate-800/50 rounded-md text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap border border-slate-200 dark:border-slate-700 max-h-[200px] overflow-auto">
                {JSON.stringify(message, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Update the MessageFilter component to be a dropdown
const MessageFilter: React.FC<{
  messageTypes: string[];
  activeFilters: string[];
  onFilterChange: (filters: string[]) => void;
}> = ({ messageTypes, activeFilters, onFilterChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const toggleFilter = (type: string) => {
    if (activeFilters.includes(type)) {
      onFilterChange(activeFilters.filter(t => t !== type));
    } else {
      onFilterChange([...activeFilters, type]);
    }
  };

  const selectAll = () => {
    onFilterChange(messageTypes);
  };

  const clearAll = () => {
    onFilterChange([]);
  };
  
  // Count of active filters
  const activeCount = activeFilters.length;
  const totalCount = messageTypes.length;

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs px-2 py-1 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded hover:bg-sky-200 dark:hover:bg-sky-800/50 transition-colors flex items-center gap-1"
      >
        Filter {activeCount > 0 && `(${activeCount}/${totalCount})`}
        <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-56 bg-white dark:bg-slate-800 rounded-md shadow-lg border border-slate-200 dark:border-slate-700 z-50">
          <div className="p-2 border-b border-slate-200 dark:border-slate-700 flex justify-between">
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">Filter messages</span>
            <div className="space-x-2">
              <button 
                onClick={selectAll} 
                className="text-xs px-1.5 py-0.5 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded hover:bg-sky-200 dark:hover:bg-sky-800/50 transition-colors"
              >
                All
              </button>
              <button 
                onClick={clearAll}
                className="text-xs px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              >
                None
              </button>
            </div>
          </div>
          <div className="p-2 max-h-64 overflow-y-auto">
            {messageTypes.map(type => (
              <div key={type} className="flex items-center py-1">
                <input
                  type="checkbox"
                  id={`filter-${type}`}
                  checked={activeFilters.includes(type)}
                  onChange={() => toggleFilter(type)}
                  className="mr-2 h-3.5 w-3.5 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                <label 
                  htmlFor={`filter-${type}`}
                  className="text-xs text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  {type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </label>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

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

  // Add state for expandedStartSearch
  const [expandedStartSearch, setExpandedStartSearch] = useState<number | null>(null);

  // Search parameters
  const [searchParams, setSearchParams] = useState<SearchParams>({
    startingUrl: 'http://xwebarena.pathonai.org:7770/',
    goal: 'search running shoes, click on the first result',
    algorithm: 'bfs',
    maxDepth: 3
  });

  // Add sessionId state
  const [sessionId, setSessionId] = useState<string | null>(null);

  // New state for the collapsible parameters section
  const [showParameters, setShowParameters] = useState(true);
  const [verticalSplitPosition, setVerticalSplitPosition] = useState(70);
  const [horizontalSplitPosition, setHorizontalSplitPosition] = useState(70);
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const [isHorizontalDragging, setIsHorizontalDragging] = useState(false);
  const verticalSplitRef = useRef<HTMLDivElement>(null);
  const horizontalSplitRef = useRef<HTMLDivElement>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Add state for message filters
  const [messageTypes, setMessageTypes] = useState<string[]>([]);
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

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
      const wsUrl = `${backendUrl.replace('http', 'ws')}/new-tree-search-ws`;
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

  // Add new handlers for vertical and horizontal resizing
  const handleVerticalMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsVerticalDragging(true);
  };

  const handleHorizontalMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsHorizontalDragging(true);
  };

  useEffect(() => {
    const handleVerticalMouseMove = (e: MouseEvent) => {
      if (!isVerticalDragging || !verticalSplitRef.current) return;
      
      const containerRect = verticalSplitRef.current.getBoundingClientRect();
      const newPosition = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      
      // Limit the split position between 30% and 70%
      if (newPosition >= 30 && newPosition <= 70) {
        setVerticalSplitPosition(newPosition);
      }
    };
    
    const handleHorizontalMouseMove = (e: MouseEvent) => {
      if (!isHorizontalDragging || !horizontalSplitRef.current) return;
      
      const containerRect = horizontalSplitRef.current.getBoundingClientRect();
      const newPosition = ((e.clientY - containerRect.top) / containerRect.height) * 100;
      
      // Limit the split position between 30% and 70%
      if (newPosition >= 30 && newPosition <= 70) {
        setHorizontalSplitPosition(newPosition);
      }
    };
    
    const handleMouseUp = () => {
      setIsVerticalDragging(false);
      setIsHorizontalDragging(false);
    };
    
    if (isVerticalDragging) {
      document.addEventListener('mousemove', handleVerticalMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    
    if (isHorizontalDragging) {
      document.addEventListener('mousemove', handleHorizontalMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    
    return () => {
      document.removeEventListener('mousemove', handleVerticalMouseMove);
      document.removeEventListener('mousemove', handleHorizontalMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isVerticalDragging, isHorizontalDragging]);

  // Add auto-scroll effect
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Extract and update message types
  useEffect(() => {
    const types = Array.from(new Set(messages.map(msg => {
      try {
        const data = JSON.parse(msg.content) as ParsedMessage;
        return data.type || null;
      } catch {
        return null;
      }
    }).filter((type): type is string => type !== null)));
    
    setMessageTypes(types);
    
    // Always initialize active filters with all types when types change
    if (types.length > 0) {
      setActiveFilters(types);
    }
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-white dark:from-slate-900 dark:to-slate-800 pb-4 w-full flex flex-col">
      {/* Add custom style for TreeReconstructor at the top of the component */}
      <style jsx global>{`
        .tree-reconstructor .border {
          border: none !important;
          background: transparent !important;
          box-shadow: none !important;
          padding: 0 !important;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out forwards;
        }
      `}</style>
      
      {/* Header with title and guidance */}
      <div className="bg-white dark:bg-slate-800 shadow-sm border-b sticky top-0 z-10">
        <div className="py-3 px-4 max-w-full">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-sky-950 dark:text-sky-100">Visual Tree Search</h1>
            
            <div className="flex gap-2">
              <Button 
                onClick={handleStart} 
                disabled={isSearching}
                className="bg-cyan-600 hover:bg-cyan-700 text-white disabled:bg-cyan-300 dark:disabled:bg-cyan-900"
              >
                Start
              </Button>
              <Button 
                onClick={disconnect} 
                disabled={!connected} 
                variant="destructive"
                className="bg-rose-600 hover:bg-rose-700 text-white"
              >
                End
              </Button>
            </div>
          </div>
          
          {/* Introduction & Parameters Section */}
          <div className="mt-3 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800 rounded-lg overflow-hidden">
            <div 
              className="p-3 flex justify-between items-center cursor-pointer hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-colors"
              onClick={() => setShowParameters(!showParameters)}
            >
              <div className="flex items-start gap-2">
                <Info className="h-5 w-5 text-cyan-600 dark:text-cyan-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-sky-800 dark:text-sky-300">How to use this playground</h3>
                  <p className="text-sm text-sky-700 dark:text-sky-400">
                    Configure your search parameters and visualize web browsing automation with tree search algorithms.
                  </p>
                </div>
              </div>
              {showParameters ? <ChevronUp className="text-cyan-600" /> : <ChevronDown className="text-cyan-600" />}
            </div>
            
            {/* Search Parameters - Expanded by default */}
            {showParameters && (
              <div className="p-4 border-t border-sky-200 dark:border-sky-800 bg-white/90 dark:bg-slate-800/90">
                <div className="mb-4 ml-1 text-sm text-slate-700 dark:text-slate-300">
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Click the &quot;Start&quot; button above to connect and begin the search.</li>
                    <li>Configure your search parameters below.</li>
                    <li>The tree of possible actions will appear on the right, while the resulting web page will display on the left.</li>
                    <li>You can drag the divider to resize the panels as needed.</li>
                  </ol>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="startingUrl" className="text-slate-700 dark:text-slate-300 font-medium">Starting URL</Label>
                    <Input
                      id="startingUrl"
                      value={searchParams.startingUrl}
                      onChange={(e) => handleParamChange('startingUrl', e.target.value)}
                      className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="goal" className="text-slate-700 dark:text-slate-300 font-medium">Goal</Label>
                    <Input
                      id="goal"
                      value={searchParams.goal}
                      onChange={(e) => handleParamChange('goal', e.target.value)}
                      className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="algorithm" className="text-slate-700 dark:text-slate-300 font-medium">Algorithm</Label>
                    <select
                      id="algorithm"
                      value={searchParams.algorithm}
                      onChange={(e) => handleParamChange('algorithm', e.target.value as 'bfs' | 'dfs')}
                      className="w-full p-2 border rounded bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    >
                      <option value="bfs">Breadth-First Search (BFS)</option>
                      <option value="dfs">Depth-First Search (DFS)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="maxDepth" className="text-slate-700 dark:text-slate-300 font-medium">Max Depth</Label>
                    <Input
                      id="maxDepth"
                      type="number"
                      min={1}
                      max={10}
                      value={searchParams.maxDepth}
                      onChange={(e) => handleParamChange('maxDepth', parseInt(e.target.value))}
                      className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Main content area - Three panel layout */}
      <div className="flex-1 px-4 mt-4 overflow-hidden">
        <div ref={verticalSplitRef} className="relative h-[calc(100vh-270px)] rounded-lg overflow-hidden shadow-lg">
          {/* Left panel - Live Browser */}
          <div 
            className="absolute top-0 bottom-0 left-0 overflow-hidden bg-white dark:bg-slate-800 rounded-l-lg"
            style={{ width: `${verticalSplitPosition}%` }}
          >
            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
              <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.083 9h1.946c.089-1.546.383-2.97.837-4.118A6.004 6.004 0 004.083 9zM10 2a8 8 0 100 16 8 8 0 000-16zm0 2c-.076 0-.232.032-.465.262-.238.234-.497.623-.737 1.182-.389.907-.673 2.142-.766 3.556h3.936c-.093-1.414-.377-2.649-.766-3.556-.24-.56-.5-.948-.737-1.182C10.232 4.032 10.076 4 10 4zm3.971 5c-.089-1.546-.383-2.97-.837-4.118A6.004 6.004 0 0115.917 9h-1.946zm-2.003 2H8.032c.093 1.414.377 2.649.766 3.556.24.56.5.948.737 1.182.233.23.389.262.465.262.076 0 .232-.032.465-.262.238-.234.498-.623.737-1.182.389-.907.673-2.142.766-3.556zm1.166 4.118c.454-1.147.748-2.572.837-4.118h1.946a6.004 6.004 0 01-2.783 4.118zm-6.268 0C6.412 13.97 6.118 12.546 6.03 11H4.083a6.004 6.004 0 002.783 4.118z" clipRule="evenodd" />
                </svg>
                Live Browser View
              </h2>
            </div>
            <div className="h-[calc(100%-48px)] w-full overflow-auto">
              {liveBrowserUrl ? (
                <iframe
                  src={liveBrowserUrl}
                  className="w-full h-full"
                  title="Live Browser View"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800 text-slate-500 dark:text-slate-400">
                  <p>Browser view will appear here when search starts</p>
                </div>
              )}
            </div>
          </div>

          {/* Vertical resizable handle */}
          <div 
            className="absolute top-0 bottom-0 w-4 cursor-col-resize flex items-center justify-center hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-colors z-10"
            style={{ left: `calc(${verticalSplitPosition}% - 8px)` }}
            onMouseDown={handleVerticalMouseDown}
          >
            <div className="h-16 w-1 bg-sky-300 dark:bg-sky-600 rounded"></div>
          </div>

          {/* Right panel - Tree View and Message Log */}
          <div 
            className="absolute top-0 bottom-0 right-0 overflow-hidden bg-white dark:bg-slate-800 rounded-r-lg"
            style={{ width: `${100 - verticalSplitPosition}%` }}
          >
            <div ref={horizontalSplitRef} className="relative h-full">
              {/* Top panel - Tree View */}
              <div 
                className="absolute top-0 left-0 right-0 overflow-hidden bg-white dark:bg-slate-800 rounded-tr-lg"
                style={{ height: `${horizontalSplitPosition}%` }}
              >
                <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
                  <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                    </svg>
                    Tree Visualization
                  </h2>
                </div>
                <div className="h-[calc(100%-48px)] w-full overflow-auto">
                  <TreeReconstructor
                    messages={treeMessages}
                    width={400}
                    height={700}
                    reset={resetTree}
                  />
                </div>
              </div>

              {/* Horizontal resizable handle */}
              <div 
                className="absolute left-0 right-0 h-4 cursor-row-resize flex items-center justify-center hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-colors z-10"
                style={{ top: `calc(${horizontalSplitPosition}% - 8px)` }}
                onMouseDown={handleHorizontalMouseDown}
              >
                <div className="w-16 h-1 bg-sky-300 dark:bg-sky-600 rounded"></div>
              </div>

              {/* Bottom panel - Message Log */}
              <div 
                className="absolute bottom-0 left-0 right-0 overflow-hidden bg-white dark:bg-slate-800 rounded-br-lg"
                style={{ height: `${100 - horizontalSplitPosition}%` }}
              >
                <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
                  <div className="flex justify-between items-center">
                    <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-2.759C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                      </svg>
                      Message Log
                    </h2>
                    
                    {messageTypes.length > 0 && (
                      <MessageFilter 
                        messageTypes={messageTypes}
                        activeFilters={activeFilters}
                        onFilterChange={setActiveFilters}
                      />
                    )}
                  </div>
                </div>
                <div className="h-[calc(100%-48px)] overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
                  <div className="space-y-2">
                    {messages.map((msg, index) => {
                      try {
                        const parsedMessage = JSON.parse(msg.content) as ParsedMessage;
                        // Filter messages based on active filters
                        if (parsedMessage.type && !activeFilters.includes(parsedMessage.type)) {
                          return null;
                        }
                        
                        // Special handling for start_search messages to always show full content
                        if (parsedMessage.type === 'start_search') {
                          return (
                            <div key={index} className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 rounded-lg shadow-sm border p-3 mb-2 hover:shadow-md transition-shadow">
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400">
                                  <Play className="h-5 w-5 text-blue-500" />
                                </div>
                                <div className="flex-1">
                                  <div className="flex justify-between items-center mb-2">
                                    <h3 className="font-medium text-slate-900 dark:text-slate-100">Start Search</h3>
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                                      {msg.timestamp}
                                    </span>
                                  </div>
                                  
                                  <div className="mb-2 space-y-2">
                                    <div className="flex flex-wrap gap-2">
                                      {parsedMessage.goal && (
                                        <div className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-md">
                                          <span className="font-medium">Goal:</span> {parsedMessage.goal}
                                        </div>
                                      )}
                                      {parsedMessage.starting_url && (
                                        <div className="px-3 py-1 text-sm bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-md">
                                          <span className="font-medium">URL:</span> {parsedMessage.starting_url}
                                        </div>
                                      )}
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                      {parsedMessage.agent_type && (
                                        <div className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded-full">
                                          Agent: {parsedMessage.agent_type}
                                        </div>
                                      )}
                                      {parsedMessage.search_algorithm && (
                                        <div className="px-2 py-0.5 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 rounded-full">
                                          Algorithm: {parsedMessage.search_algorithm}
                                        </div>
                                      )}
                                      {parsedMessage.max_depth && (
                                        <div className="px-2 py-0.5 text-xs bg-cyan-100 dark:bg-cyan-900/30 text-cyan-800 dark:text-cyan-300 rounded-full">
                                          Max Depth: {parsedMessage.max_depth}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  
                                  <button 
                                    className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1 bg-white/30 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400 hover:bg-white/70 dark:hover:bg-slate-700/70 transition-colors"
                                    onClick={() => {
                                      // Create an expanded card view for this message to show in MessageCard format
                                      setExpandedStartSearch(index === expandedStartSearch ? null : index);
                                    }}
                                  >
                                    <ChevronDown className="h-3 w-3" /> Raw JSON
                                  </button>
                                  
                                  {expandedStartSearch === index && (
                                    <div className="mt-2 animate-fadeIn">
                                      <pre className="p-2 bg-white/50 dark:bg-slate-800/50 rounded-md text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap border border-slate-200 dark:border-slate-700 max-h-[200px] overflow-auto">
                                        {JSON.stringify(parsedMessage, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        }
                        
                        return <MessageCard key={index} message={parsedMessage} />;
                      } catch {
                        // For unparsable messages, improve raw message display
                        return (
                          <div key={index} className="bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800 rounded-lg shadow-sm border p-3 mb-2 hover:shadow-md transition-shadow">
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400">
                                <Info className="h-5 w-5 text-slate-500" />
                              </div>
                              <div className="flex-1">
                                <div className="flex justify-between items-center mb-2">
                                  <h3 className="font-medium text-slate-900 dark:text-slate-100">
                                    {msg.type === 'outgoing' ? 'Outgoing Request' : 'Raw Message'}
                                  </h3>
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                                    {msg.timestamp}
                                  </span>
                                </div>
                                
                                {/* Detect if content could be text or a connection message */}
                                {msg.content.includes('Connected to Tree Search WebSocket server') ? (
                                  <div className="flex items-center p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800/50">
                                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 mr-2">
                                      <div className="w-2.5 h-2.5 rounded-full bg-green-500 dark:bg-green-400 animate-pulse"></div>
                                    </div>
                                    <span className="text-sm font-medium text-green-600 dark:text-green-400">Connected successfully</span>
                                  </div>
                                ) : (
                                  <pre className="mt-2 p-2 bg-white/50 dark:bg-slate-800/50 rounded text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap border border-slate-200 dark:border-slate-700 max-h-[200px] overflow-auto">
                                    {msg.content}
                                  </pre>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      }
                    })}
                    <div ref={messagesEndRef} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TreeSearchPlayground;
