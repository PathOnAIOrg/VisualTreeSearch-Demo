import React, { useEffect } from 'react';
import { 
  Info, 
  CheckCircle, 
  XCircle, 
  Globe,
  AlertCircle,
  Code,
  Settings,
  RefreshCw,
  Loader2,
  Network,
  MessageSquare,
  AlertTriangle,
  HelpCircle,
  Clock,
  Cpu,
  Brain,
  Target,
  Flag,
  Award,
  Trophy,
  Star,
  ThumbsUp,
  ThumbsDown,
  Meh,
  ArrowRight,
  PlusCircle,
  Expand,
  ArrowUp,
  Play,
  Route,
  Trash,
  StepForward
} from 'lucide-react';

interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface MessageLogPanelProps {
  messages: Message[];
  messagesEndRef?: React.RefObject<HTMLDivElement | null>;
  onSessionIdChange?: (sessionId: string) => void;
  variant?: 'default' | 'mcts' | 'lats';
}

interface ParsedMessage {
  type?: string;
  info?: string;
  content?: string;
  status?: string;
  message?: string;
  goal?: string;
  search_algorithm?: string;
  max_depth?: number;
  browser_type?: string;
  page_info?: {
    url?: string;
    title?: string;
  };
  description?: string;
  action?: string;
  reason?: string;
  score?: number;
  tree?: unknown[];
  path?: PathStep[];
  server_info?: {
    hostname?: string;
  };
  node_id?: string;
  value?: number;
  visits?: number;
  terminal_node_description?: string;
  reward?: number;
  step?: number;
  step_name?: string;
  iteration?: number;
  session_id?: string;
  node_action?: string;
  children?: ChildNodeData[];
  children_count?: number;
  node_info?: {
    action?: string;
    description?: string;
    depth?: number;
    value?: number;
    visits?: number;
  };
  trajectory?: Array<{
    natural_language_description: string;
    action: string;
    feedback?: string;
  }>;
}

interface PathStep {
  natural_language_description: string;
  action: string;
}

interface ChildNodeData {
  id: number;
  parent_id: number;
  action: string;
  description: string;
  is_terminal: boolean;
  prob: number;
  depth: number;
}

const MessageLogPanel: React.FC<MessageLogPanelProps> = ({ 
  messages, 
  messagesEndRef, 
  onSessionIdChange,
  variant = 'default'
}) => {
  const prevMessagesLengthRef = React.useRef(messages.length);

  useEffect(() => {
    // Only scroll if new messages were added
    if (messages.length > prevMessagesLengthRef.current && messagesEndRef?.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages, messagesEndRef]);

  useEffect(() => {
    if (!messages.length || !onSessionIdChange) return;
    
    const latestMessage = messages[messages.length - 1];
    try {
      const data = JSON.parse(latestMessage.content);
      if (data.type === 'browser_setup' && data.status === 'success' && data.session_id) {
        onSessionIdChange(data.session_id);
      }
    } catch {
      // Not JSON or doesn't contain session info, ignore
    }
  }, [messages, onSessionIdChange]);

  const getCardStyle = (type: string) => {
    // Ignore tree update messages
    if (type === 'tree_update_node_expansion' || 
        type === 'tree_update_node_evaluation' ||
        type === 'tree_update_node_children_evaluation') {
      return "hidden";
    }

    switch (type) {
      // System Status Messages
      case 'reflection_backtracking':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'server_connection':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'start_search':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'connection_established':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'error':
      case 'browser_error':
      case 'system_error':
        return "bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800";
      case 'status_update':
        return "bg-gradient-to-r from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800";
      case 'timeout':
        return "bg-gradient-to-r from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-200 dark:border-amber-800";
      case 'warning':
        return "bg-gradient-to-r from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800";
      case 'info':
        return "bg-gradient-to-r from-sky-50 to-sky-100 dark:from-sky-900/20 dark:to-sky-800/20 border-sky-200 dark:border-sky-800";
      case 'debug':
        return "bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/20 dark:to-slate-800/20 border-slate-200 dark:border-slate-800";
      case 'loading':
      case 'waiting':
        return "bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900/20 dark:to-gray-800/20 border-gray-200 dark:border-gray-800";

      // Tree Search Related Messages
      case 'node_processing':
        return "bg-gradient-to-r from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 border-cyan-200 dark:border-cyan-800";
      case 'node_expanding':
        return "bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800";
      case 'node_created':
        return "bg-gradient-to-r from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-800/20 border-indigo-200 dark:border-indigo-800";
      case 'node_scored':
        return "bg-gradient-to-r from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-200 dark:border-amber-800";
      case 'tree_update':
        return "bg-gradient-to-r from-teal-50 to-teal-100 dark:from-teal-900/20 dark:to-teal-800/20 border-teal-200 dark:border-teal-800";
      case 'best_path_update':
        return "bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-emerald-200 dark:border-emerald-800";

      // Browser and Action Related Messages
      case 'browser_setup':
        return "bg-gradient-to-r from-sky-50 to-sky-100 dark:from-sky-900/20 dark:to-sky-800/20 border-sky-200 dark:border-sky-800";
      case 'replaying_action':
        return "bg-gradient-to-r from-violet-50 to-violet-100 dark:from-violet-900/20 dark:to-violet-800/20 border-violet-200 dark:border-violet-800";
      case 'generating_actions':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";

      // Progress and Achievement Messages
      case 'level_complete':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'level_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'search_complete':
        return "bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-emerald-200 dark:border-emerald-800";
      case 'iteration_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'step_start':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";

      // Feedback and User Interaction Messages
      case 'feedback_generated':
        return "bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-emerald-200 dark:border-emerald-800";
      case 'question':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'positive':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";
      case 'negative':
        return "bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800";
      case 'neutral':
        return "bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/20 dark:to-slate-800/20 border-slate-200 dark:border-slate-800";

      // MCTS specific updates
      case 'tree_update_node_children_evaluation':
      case 'tree_update_node_backpropagation':
      case 'tree_update_simulation':
      case 'trajectory_update':
      case 'removed_simulation':
      case 'tree_update_node_expansion':
      case 'tree_update_node_evaluation':
        return "bg-gradient-to-r from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 border-cyan-200 dark:border-cyan-800";
      
      case 'iteration_start':
      case 'step_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      
      case 'node_selected':
      case 'node_selected_for_simulation':
      case 'node_created':
      case 'node_simulated':
      case 'node_terminal':
      case 'node_expansion_start':
      case 'node_expansion_complete':
      case 'evaluation_start':
      case 'child_evaluated':
      case 'node_evaluation_start':
      case 'node_evaluation_complete':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";

      case 'simulation_result':
        return "bg-gradient-to-r from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-200 dark:border-amber-800";

      default:
        return "bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/20 dark:to-slate-800/20 border-slate-200 dark:border-slate-800";
    }
  };

  const getIcon = (message: ParsedMessage) => {
    // Ignore tree update messages
    if (message.type === 'tree_update_node_expansion' || 
        message.type === 'tree_update_node_evaluation' ||
        message.type === 'tree_update_node_children_evaluation') {
      return null;
    }

    switch (message.type) {
      case 'reflection_backtracking':
        return <Brain className="h-4 w-4 text-blue-500" />;
      case 'server_connection':
        return <Globe className="h-4 w-4 text-green-500 animate-pulse" />;
      case 'start_search':
        return <Target className="h-4 w-4 text-blue-500" />;
      case 'connection_established':
        return (
          <div className="relative">
            <Globe className="h-4 w-4 text-green-500 animate-pulse" />
            <div className="absolute -top-1 -right-1">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-ping" />
            </div>
          </div>
        );
      case 'status_update':
        if (message.status === 'running') return <Loader2 className="h-4 w-4 text-orange-500 animate-spin" />;
        if (message.status === 'initializing') return <Settings className="h-4 w-4 text-orange-500" />;
        return <Info className="h-4 w-4 text-orange-500" />;
      case 'browser_setup':
        if (message.status === 'loading') return <Loader2 className="h-4 w-4 text-sky-500 animate-spin" />;
        return <Globe className="h-4 w-4 text-sky-500" />;
      case 'node_created':
        return <PlusCircle className="h-4 w-4 text-indigo-500" />;
      case 'node_selected':
        return <Target className="h-4 w-4 text-purple-500" />;
      case 'node_processing':
        return <Cpu className="h-4 w-4 text-cyan-500" />;
      case 'node_expanding':
        return <Expand className="h-4 w-4 text-purple-500" />;
      case 'node_scored':
        return <Star className="h-4 w-4 text-amber-500" />;
      case 'tree_update':
        return <Network className="h-4 w-4 text-teal-500" />;
      case 'tree_update_node_expansion':
      case 'tree_update_node_evaluation':
        return <Network className="h-4 w-4 text-teal-500" />;
      case 'browser_error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'system_error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'timeout':
        return <Clock className="h-4 w-4 text-amber-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'debug':
        return <Code className="h-4 w-4 text-slate-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failure':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'loading':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'waiting':
        return <Clock className="h-4 w-4 text-slate-500" />;
      case 'question':
        return <HelpCircle className="h-4 w-4 text-blue-500" />;
      case 'positive':
        return <ThumbsUp className="h-4 w-4 text-green-500" />;
      case 'negative':
        return <ThumbsDown className="h-4 w-4 text-red-500" />;
      case 'neutral':
        return <Meh className="h-4 w-4 text-slate-500" />;
      case 'search_complete':
        return <Award className="h-4 w-4 text-emerald-500" />;
      case 'account_reset':
        return <RefreshCw className="h-4 w-4 text-red-500" />;
      case 'browser_setup':
        return <Globe className="h-4 w-4 text-sky-500" />;
      case 'feedback_generated':
        return <MessageSquare className="h-4 w-4 text-emerald-500" />;
      case 'replaying_action':
        return <RefreshCw className="h-4 w-4 text-violet-500" />;
      case 'generating_actions':
        return <Brain className="h-4 w-4 text-blue-500" />;
      case 'level_complete':
        return <Trophy className="h-4 w-4 text-green-500" />;
      case 'level_start':
        return <Flag className="h-4 w-4 text-blue-500" />;
      case 'best_path_update':
        return <Target className="h-4 w-4 text-blue-500" />;
      case 'tree_update_node_children_evaluation':
        return <Brain className="h-4 w-4 text-cyan-500" />;
      case 'tree_update_node_backpropagation':
        return <ArrowUp className="h-4 w-4 text-cyan-500" />;
      case 'tree_update_simulation':
        return <Play className="h-4 w-4 text-cyan-500" />;
      case 'trajectory_update':
        return <Route className="h-4 w-4 text-cyan-500" />;
      case 'removed_simulation':
        return <Trash className="h-4 w-4 text-cyan-500" />;
      case 'iteration_start':
        return <RefreshCw className="h-4 w-4 text-blue-500" />;
      case 'step_start':
        return <StepForward className="h-4 w-4 text-blue-500" />;
      case 'node_selected':
        return <Target className="h-4 w-4 text-green-500" />;
      case 'node_selected_for_simulation':
        return <Target className="h-4 w-4 text-green-500" />;
      case 'node_created':
        return <PlusCircle className="h-4 w-4 text-green-500" />;
      case 'node_simulated':
        return <Play className="h-4 w-4 text-green-500" />;
      case 'node_terminal':
        return <Flag className="h-4 w-4 text-green-500" />;
      case 'simulation_result':
        return <Info className="h-4 w-4 text-amber-500" />;
      case 'node_expansion_start':
        return <Expand className="h-4 w-4 text-purple-500" />;
      case 'node_expansion_complete':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'evaluation_start':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            <div className="animate-slideIn">
              <div className="text-amber-600 dark:text-amber-400">
                Starting node evaluation
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {message.node_info?.description}
                {message.node_info?.action && message.node_info.action !== 'ROOT' && (
                  <span> | Action: {message.node_info.action}</span>
                )}
              </div>
            </div>
          </div>
        );
      case 'child_evaluated':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            <div className="animate-slideIn">
              <div className="text-amber-600 dark:text-amber-400">
                Child node evaluated
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Node ID: {message.node_id} | Score: {message.score?.toFixed(3)}
              </div>
            </div>
          </div>
        );
      case 'node_evaluation_start':
        return <Brain className="h-4 w-4 text-amber-500" />;
      case 'node_evaluation_complete':
        return <CheckCircle className="h-4 w-4 text-amber-500" />;
      case 'child_evaluated':
        return <Star className="h-4 w-4 text-amber-500" />;
      default:
        return <Info className="h-4 w-4 text-slate-500" />;
    }
  };

  const getIconBgColor = (type: string) => {
    switch (type) {
      // System Status Messages
      case 'reflection_backtracking':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      case 'server_connection':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'start_search':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'connection_established':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'error':
      case 'browser_error':
      case 'system_error':
        return "bg-red-100 dark:bg-red-800/30 text-red-600 dark:text-red-400";
      case 'status_update':
        return "bg-orange-100 dark:bg-orange-800/30 text-orange-600 dark:text-orange-400";
      case 'timeout':
        return "bg-amber-100 dark:bg-amber-800/30 text-amber-600 dark:text-amber-400";
      case 'warning':
        return "bg-yellow-100 dark:bg-yellow-800/30 text-yellow-600 dark:text-yellow-400";
      case 'info':
        return "bg-sky-100 dark:bg-sky-800/30 text-sky-600 dark:text-sky-400";
      case 'debug':
        return "bg-slate-100 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400";
      case 'loading':
      case 'waiting':
        return "bg-gray-100 dark:bg-gray-800/30 text-gray-600 dark:text-gray-400";

      // Tree Search Related Messages
      case 'node_processing':
        return "bg-cyan-100 dark:bg-cyan-800/30 text-cyan-600 dark:text-cyan-400";
      case 'node_expanding':
        return "bg-purple-100 dark:bg-purple-800/30 text-purple-600 dark:text-purple-400";
      case 'node_created':
        return "bg-indigo-100 dark:bg-indigo-800/30 text-indigo-600 dark:text-indigo-400";
      case 'node_scored':
        return "bg-amber-100 dark:bg-amber-800/30 text-amber-600 dark:text-amber-400";
      case 'tree_update':
        return "bg-teal-100 dark:bg-teal-800/30 text-teal-600 dark:text-teal-400";
      case 'best_path_update':
        return "bg-emerald-100 dark:bg-emerald-800/30 text-emerald-600 dark:text-emerald-400";

      // Browser and Action Related Messages
      case 'browser_setup':
        return "bg-sky-100 dark:bg-sky-800/30 text-sky-600 dark:text-sky-400";
      case 'replaying_action':
        return "bg-violet-100 dark:bg-violet-800/30 text-violet-600 dark:text-violet-400";
      case 'generating_actions':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";

      // Progress and Achievement Messages
      case 'level_complete':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'level_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'search_complete':
        return "bg-emerald-100 dark:bg-emerald-800/30 text-emerald-600 dark:text-emerald-400";
      case 'iteration_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'step_start':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";

      // Feedback and User Interaction Messages
      case 'feedback_generated':
        return "bg-emerald-100 dark:bg-emerald-800/30 text-emerald-600 dark:text-emerald-400";
      case 'question':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      case 'positive':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";
      case 'negative':
        return "bg-red-100 dark:bg-red-800/30 text-red-600 dark:text-red-400";
      case 'neutral':
        return "bg-slate-100 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400";

      // MCTS specific updates
      case 'tree_update_node_children_evaluation':
      case 'tree_update_node_backpropagation':
      case 'tree_update_simulation':
      case 'trajectory_update':
      case 'removed_simulation':
      case 'tree_update_node_expansion':
      case 'tree_update_node_evaluation':
        return "bg-cyan-100 dark:bg-cyan-800/30 text-cyan-600 dark:text-cyan-400";
      
      case 'iteration_start':
      case 'step_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      
      case 'node_selected':
      case 'node_selected_for_simulation':
      case 'node_created':
      case 'node_simulated':
      case 'node_terminal':
      case 'node_expansion_start':
      case 'node_expansion_complete':
      case 'evaluation_start':
      case 'child_evaluated':
      case 'node_evaluation_start':
      case 'node_evaluation_complete':
        return "bg-green-100 dark:bg-green-800/30 text-green-600 dark:text-green-400";

      case 'simulation_result':
        return "bg-amber-100 dark:bg-amber-800/30 text-amber-600 dark:text-amber-400";

      default:
        return "bg-slate-100 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400";
    }
  };

  const getTitle = (message: ParsedMessage) => {
    if (message.type) {
      return message.type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    }
    return message.status || 'Message';
  };

  const parseMessage = (content: string): ParsedMessage => {
    try {
      return JSON.parse(content);
    } catch {
      return { content };
    }
  };

  const formatMessageContent = (message: ParsedMessage) => {
    // Ignore tree update messages
    if (message.type === 'tree_update_node_expansion' || 
        message.type === 'tree_update_node_evaluation' ||
        message.type === 'tree_update_node_children_evaluation') {
      return null;
    }

    switch (message.type) {
      case 'reflection_backtracking':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-emerald-600 dark:text-emerald-400">
                Reflecting & backtracking | Node: {message.description}
              </div>
              {message.path && message.path.length > 0 && (
                <div className="mt-1">
                  {message.path.map((step: PathStep, index: number) => (
                    <div 
                      key={index} 
                      className="flex items-start gap-1 text-xs text-slate-500 dark:text-slate-400 animate-fadeIn"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <ArrowRight className="h-3 w-3 mt-0.5" />
                      {step.natural_language_description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 'server_connection':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-green-600 dark:text-green-400">
                {message.info?.replace(/Session [a-f0-9-]+ terminated successfully/, 'Session terminated successfully')}
              </div>
            </div>
          </div>
        );

      case 'start_search':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-blue-600 dark:text-blue-400">{message.goal}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {message.search_algorithm} | Depth: {message.max_depth}
              </div>
            </div>
          </div>
        );

      case 'connection_established':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            <div className="relative">
              <Globe className="h-4 w-4 text-green-500 animate-pulse" />
              <div className="absolute -top-1 -right-1">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-ping" />
              </div>
            </div>
            <div className="animate-slideIn">
              <div className="text-green-600 dark:text-green-400">
                Connected to Tree Search WebSocket server
              </div>
            </div>
          </div>
        );

      case 'status_update':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <span className="text-orange-600 dark:text-orange-400 animate-slideIn">
              {message.status}
              {message.message && `: ${message.message}`}
            </span>
          </div>
        );

      case 'browser_setup':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-sky-600 dark:text-sky-400">
                {message.browser_type} - {message.page_info?.url || (
                  <span className="inline-flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Loading...
                  </span>
                )}
              </div>
              {message.page_info?.title && (
                <div className="text-xs text-slate-500 dark:text-slate-400 animate-fadeIn">
                  {message.page_info.title}
                </div>
              )}
            </div>
          </div>
        );

      case 'node_created':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-indigo-600 dark:text-indigo-400">{message.description}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Action: {message.action}
              </div>
            </div>
          </div>
        );

      case 'node_selected':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-purple-600 dark:text-purple-400">
                {message.description ? `Select ${message.description}` : 'Select the root node'}
              </div>
            </div>
          </div>
        );

      case 'tree_update_node_expansion':
      case 'tree_update_node_evaluation':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-teal-600 dark:text-teal-400">
                {message.type === 'tree_update_node_expansion' ? 'Node Expanded' : 'Node Evaluated'}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
              {message.tree?.length && ` Number of nodes: ${message.tree.length}`}
              </div>
            </div>
          </div>
        );

      case 'search_complete':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-emerald-600 dark:text-emerald-400">
                Search Complete | Score: {message.score?.toFixed(3)}
              </div>
              {message.path && message.path.length > 0 && (
                <div className="mt-1">
                  {message.path.map((step: PathStep, index: number) => (
                    <div 
                      key={index} 
                      className="flex items-start gap-1 text-xs text-slate-500 dark:text-slate-400 animate-fadeIn"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <ArrowRight className="h-3 w-3 mt-0.5" />
                      {step.natural_language_description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 'account_reset':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-red-600 dark:text-red-400">
                Account reset completed
              </div>
            </div>
          </div>
        );

      case 'tree_update_node_children_evaluation':
      case 'tree_update_node_backpropagation':
      case 'tree_update_simulation':
      case 'trajectory_update':
      case 'removed_simulation':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-cyan-600 dark:text-cyan-400">
                {message.description || message.type.split('_').join(' ')}
              </div>
            </div>
          </div>
        );

      case 'node_selected':
      case 'node_selected_for_simulation':
      case 'node_created':
      case 'node_simulated':
      case 'node_terminal':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-green-600 dark:text-green-400">
                {message.description || message.type.split('_').join(' ')}
              </div>
              {message.action && (
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Action: {message.action}
                </div>
              )}
            </div>
          </div>
        );

      case 'simulation_result':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-amber-600 dark:text-amber-400">
                Simulation Result | Reward: {message.reward?.toFixed(3)}
              </div>
              {message.terminal_node_description && (
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {message.terminal_node_description}
                </div>
              )}
            </div>
          </div>
        );

      case 'step_start':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-blue-600 dark:text-blue-400">
                Step {message.step}: {message.step_name}
              </div>
            </div>
          </div>
        );

      case 'iteration_start':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-blue-600 dark:text-blue-400">
                Iteration {message.iteration}
              </div>
            </div>
          </div>
        );

      case 'node_expansion_start':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-purple-600 dark:text-purple-400">
                {message.node_info?.description || 'Starting node expansion'}
              </div>
              {message.node_info?.action && message.node_info.action !== 'ROOT' && (
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Action: {message.node_info.action}
                </div>
              )}
            </div>
          </div>
        );
      case 'node_expansion_complete':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <div className="animate-slideIn">
              <div className="text-green-600 dark:text-green-400">
                {message.node_info?.description || 'Node expansion complete'}
              </div>
              {message.node_info?.action && message.node_info.action !== 'ROOT' && (
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Action: {message.node_info.action}
                </div>
              )}
              {message.children && message.children.length > 0 && (
                <div className="mt-1">
                  {message.children.map((child: ChildNodeData, index: number) => (
                    <div 
                      key={index}
                      className="text-xs text-slate-500 dark:text-slate-400 pl-2 border-l-2 border-slate-200 dark:border-slate-700"
                    >
                      <div className="text-indigo-600 dark:text-indigo-400">
                        {child.description || 'No description'}
                      </div>
                      <div className="text-slate-500 dark:text-slate-400">
                        Action: {child.action || 'None'}
                      </div>
                      {child.prob && (
                        <div className="text-slate-500 dark:text-slate-400">
                          Probability: {child.prob.toFixed(3)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      case 'evaluation_start':
        return `Starting evaluation of ${message.children_count} children for node ${message.node_id}`;
      case 'child_evaluated':
        return `Child node ${message.node_id} evaluated with score ${message.score?.toFixed(3)}`;
      case 'node_evaluation_start':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            <div className="animate-slideIn">
              <div className="text-amber-600 dark:text-amber-400">
                Starting node evaluation
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {message.node_info?.description}
                {message.node_info?.action && message.node_info.action !== 'ROOT' && (
                  <span> | Action: {message.node_info.action}</span>
                )}
              </div>
            </div>
          </div>
        );
      case 'node_evaluation_complete':
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            <div className="animate-slideIn">
              <div className="text-amber-600 dark:text-amber-400 font-medium">
                Node evaluation complete
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {message.node_info?.description}
                {message.node_info?.action && message.node_info.action !== 'ROOT' && (
                  <span> | Action: {message.node_info.action}</span>
                )}
              </div>
              <div className="text-xs font-medium text-amber-600 dark:text-amber-400 mt-2">
                Score: {message.score?.toFixed(3)}
              </div>
              {message.trajectory && message.trajectory.length > 0 && (
                <div className="mt-2 pl-2 border-l-2 border-amber-200 dark:border-amber-800">
                  <div className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">
                    Trajectory:
                  </div>
                  {message.trajectory.map((step, index) => (
                    <div 
                      key={index} 
                      className="flex items-start gap-1 text-xs text-slate-500 dark:text-slate-400 animate-fadeIn mb-1.5"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <ArrowRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium">{step.natural_language_description}</div>
                        {step.feedback && (
                          <div className="text-slate-400 italic mt-0.5">
                            Feedback: {step.feedback}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="flex items-center gap-2 animate-fadeIn">
            {getIcon(message)}
            <span className="text-sm text-slate-600 dark:text-slate-300 animate-slideIn">
              {message.message || message.content || JSON.stringify(message, null, 2)}
            </span>
          </div>
        );
    }
  };

  return (
    <div className={`bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 p-2 ${variant === 'mcts' ? 'border-cyan-500' : variant === 'lats' ? 'border-purple-500' : ''}`}>
      <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center mb-2">
        <MessageSquare className="h-4 w-4 mr-1.5 text-primary" />
        Message Log {variant !== 'default' ? `(${variant.toUpperCase()})` : ''}
      </h2>
      <div className="h-[150px] overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-md p-1.5 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        {messages.map((msg, index) => {
          const parsedMessage = parseMessage(msg.content);
          
          // Skip tree update messages
          if (parsedMessage.type === 'tree_update_node_expansion' || 
              parsedMessage.type === 'tree_update_node_evaluation' ||
              parsedMessage.type === 'tree_update_node_children_evaluation') {
            return null;
          }
          
          return (
            <div 
              key={index} 
              className={`rounded-lg shadow-sm border p-2 mb-1.5 hover:shadow-md transition-shadow ${getCardStyle(parsedMessage.type || '')}`}
            >
              <div className="flex items-start gap-2">
                <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${getIconBgColor(parsedMessage.type || '')}`}>
                  {getIcon(parsedMessage)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {getTitle(parsedMessage)}
                    </h3>
                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-white/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                      {msg.timestamp}
                    </span>
                  </div>
                  
                  <div className="text-sm">
                    {formatMessageContent(parsedMessage)}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {messagesEndRef && <div ref={messagesEndRef} />}
      </div>
    </div>
  );
};

export default MessageLogPanel;
