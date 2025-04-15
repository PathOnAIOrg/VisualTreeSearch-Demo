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
}

interface ParsedMessage {
  type?: string;
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
  reward?: number;
  terminal_node_description?: string;
  step?: number;
  step_name?: string;
  iteration?: number;
}

interface PathStep {
  natural_language_description: string;
  action: string;
}

const MessageLogPanelLATS: React.FC<MessageLogPanelProps> = ({ messages, messagesEndRef }) => {
  useEffect(() => {
    if (messagesEndRef?.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, messagesEndRef]);

  const getCardStyle = (type: string) => {
    switch (type) {
      // System Status Messages
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
        return "bg-gradient-to-r from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 border-cyan-200 dark:border-cyan-800";
      
      case 'iteration_start':
      case 'step_start':
        return "bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800";
      
      case 'node_selected':
      case 'node_selected_for_simulation':
      case 'node_created':
      case 'node_simulated':
      case 'node_terminal':
        return "bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800";

      case 'simulation_result':
        return "bg-gradient-to-r from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-200 dark:border-amber-800";

      default:
        return "bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/20 dark:to-slate-800/20 border-slate-200 dark:border-slate-800";
    }
  };

  const getIcon = (message: ParsedMessage) => {
    switch (message.type) {
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
      default:
        return <Info className="h-4 w-4 text-slate-500" />;
    }
  };

  const getIconBgColor = (type: string) => {
    switch (type) {
      // System Status Messages
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
        return "bg-cyan-100 dark:bg-cyan-800/30 text-cyan-600 dark:text-cyan-400";
      
      case 'iteration_start':
      case 'step_start':
        return "bg-blue-100 dark:bg-blue-800/30 text-blue-600 dark:text-blue-400";
      
      case 'node_selected':
      case 'node_selected_for_simulation':
      case 'node_created':
      case 'node_simulated':
      case 'node_terminal':
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
    switch (message.type) {
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
              <div className="text-purple-600 dark:text-purple-400">{message.description}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Reason: {message.reason}
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
                Score: {message.score}
                {message.tree?.length && ` | Nodes: ${message.tree.length}`}
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
                Search Complete | Score: {message.score}
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
                Simulation Result | Reward: {message.reward}
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
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 p-3 mt-4">
      <h2 className="text-lg font-semibold mb-2 text-sky-950 dark:text-sky-100 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
        </svg>
        Message Log
      </h2>
      <div className="h-[150px] overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        {messages.map((msg, index) => {
          const parsedMessage = parseMessage(msg.content);
          
          return (
            <div 
              key={index} 
              className={`rounded-lg shadow-sm border p-3 mb-2 hover:shadow-md transition-shadow ${getCardStyle(parsedMessage.type || '')}`}
            >
              <div className="flex items-start gap-3">
                <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${getIconBgColor(parsedMessage.type || '')}`}>
                  {getIcon(parsedMessage)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-medium text-slate-900 dark:text-slate-100">
                      {getTitle(parsedMessage)}
                    </h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                      {msg.timestamp}
                    </span>
                  </div>
                  
                  <div>
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

export default MessageLogPanelLATS;