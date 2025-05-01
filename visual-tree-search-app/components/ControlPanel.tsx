import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Info, ChevronDown, ChevronUp, Globe, Target, Layers, Network, Settings, RefreshCw } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";

type AlgorithmType = 'bfs' | 'dfs' | 'lats' | 'mcts';

interface BaseSearchParams {
  startingUrl: string;
  goal: string;
  maxDepth: number;
}

interface BFSSearchParams extends BaseSearchParams {
  type: 'bfs' | 'dfs';
  algorithm: 'bfs' | 'dfs';
}

interface LATSSearchParams extends BaseSearchParams {
  type: 'lats';
  num_simulations: number;
  iterations: number;
}

interface MCTSSearchParams extends BaseSearchParams {
  type: 'mcts';
  iterations: number;
  set_prior_value: boolean;
}

type SearchParams = BFSSearchParams | LATSSearchParams | MCTSSearchParams;

interface ControlPanelProps {
  algorithmType: AlgorithmType;
  searchParams: SearchParams;
  handleParamChange: (param: string, value: string | number | boolean) => void;
  handleStart: () => void;
  disconnect: () => void;
  isSearching: boolean;
  connected: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  algorithmType,
  searchParams,
  handleParamChange,
  handleStart,
  disconnect,
  isSearching,
  connected,
}) => {
  const [showParameters, setShowParameters] = React.useState(true);

  const getTitle = () => {
    switch (algorithmType) {
      case 'bfs':
      case 'dfs':
        return 'Visual Tree Search: Simple Search (BFS/DFS)';
      case 'lats':
        return 'Visual Tree Search: LATS';
      case 'mcts':
        return 'Visual Tree Search: RMCTS';
      default:
        return 'Visual Tree Search';
    }
  };

  const renderAlgorithmSpecificParams = () => {
    switch (algorithmType) {
      case 'bfs':
      case 'dfs':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="algorithm" className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Network className="h-3.5 w-3.5 text-primary" />
                  Algorithm
                </Label>
                <div className="flex h-6 rounded-md border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <Button
                    variant={(searchParams as BFSSearchParams).algorithm === 'bfs' ? 'default' : 'ghost'}
                    size="sm"
                    className="h-6 px-2 text-[10px] rounded-none border-0"
                    onClick={() => handleParamChange('algorithm', 'bfs')}
                  >
                    BFS
                  </Button>
                  <Button
                    variant={(searchParams as BFSSearchParams).algorithm === 'dfs' ? 'default' : 'ghost'}
                    size="sm"
                    className="h-6 px-2 text-[10px] rounded-none border-0"
                    onClick={() => handleParamChange('algorithm', 'dfs')}
                  >
                    DFS
                  </Button>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">
                {(searchParams as BFSSearchParams).algorithm === 'bfs' 
                  ? 'Explores all nodes at current depth before moving deeper'
                  : 'Explores as far as possible along each branch before backtracking'}
              </span>
            </div>
          </div>
        );
      case 'lats':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="num_simulations" className="text-slate-700 dark:text-slate-300 font-medium">Number of Simulations</Label>
              <Input
                id="num_simulations"
                type="number"
                min={1}
                max={100}
                value={(searchParams as LATSSearchParams).num_simulations}
                onChange={(e) => handleParamChange('num_simulations', parseInt(e.target.value))}
                className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="iterations" className="text-slate-700 dark:text-slate-300 font-medium">Iterations</Label>
              <Input
                id="iterations"
                type="number"
                min={1}
                max={10}
                value={(searchParams as LATSSearchParams).iterations}
                onChange={(e) => handleParamChange('iterations', parseInt(e.target.value))}
                className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900"
              />
            </div>
          </>
        );
      case 'mcts':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="iterations" className="text-slate-700 dark:text-slate-300 font-medium">Iterations</Label>
              <Input
                id="iterations"
                type="number"
                min={1}
                max={10}
                value={(searchParams as MCTSSearchParams).iterations}
                onChange={(e) => handleParamChange('iterations', parseInt(e.target.value))}
                className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900"
              />
            </div>
            <div className="mt-4">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="set_prior_value" 
                  checked={(searchParams as MCTSSearchParams).set_prior_value}
                  onCheckedChange={(checked) => handleParamChange('set_prior_value', checked === true)}
                />
                <Label 
                  htmlFor="set_prior_value" 
                  className="text-slate-700 dark:text-slate-300 font-medium cursor-pointer"
                >
                  Use Prior Value
                </Label>
              </div>
              <p className="mt-1 ml-6 text-xs text-slate-500 dark:text-slate-400">
                When enabled, RMCTS will use an LLM to generate an initial value as a prior value for each newly generated node.
              </p>
            </div>
          </>
        );
    }
  };

  return (
    <div className="bg-gradient-to-b from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 shadow-md border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10">
      <div className="py-2 px-4 max-w-full">
        <div className="flex justify-between items-center">
          <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">{getTitle()}</h1>
          
          <div className="flex items-center gap-3">
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-700"></div>
            <div className="flex gap-2">
              <Button 
                onClick={handleStart} 
                disabled={isSearching}
                className="bg-primary hover:bg-primary/90 text-white disabled:bg-primary/50 dark:disabled:bg-primary/30 transition-colors duration-200 text-sm h-8"
              >
                Start
              </Button>
              <Button 
                onClick={disconnect} 
                disabled={!connected} 
                variant="destructive"
                className="bg-red-600 hover:bg-red-700 text-white transition-colors duration-200 text-sm h-8 dark:bg-red-500 dark:hover:bg-red-600"
              >
                End
              </Button>
            </div>
          </div>
        </div>
        
        <div className="mt-2 bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden shadow-sm">
          <div 
            className="p-2 flex justify-between items-center cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition-colors duration-200"
            onClick={() => setShowParameters(!showParameters)}
          >
            <div className="flex items-start gap-2">
              <Info className="h-3.5 w-3.5 text-primary dark:text-primary/80 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-xs font-medium text-slate-800 dark:text-slate-200">How to use this playground</h3>
                <p className="text-[11px] text-slate-600 dark:text-slate-400">
                  Configure your search parameters and visualize web browsing automation with tree search algorithms.
                </p>
              </div>
            </div>
            {showParameters ? <ChevronUp className="h-3.5 w-3.5 text-primary" /> : <ChevronDown className="h-3.5 w-3.5 text-primary" />}
          </div>
          
          {showParameters && (
            <div className="p-3 border-t border-slate-200 dark:border-slate-700 bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900">
              {/* Quick Start Guide */}
              <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 shadow-sm mb-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5 text-primary" />
                    Quick Start Guide
                  </h3>
                </div>
                <ol className="space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">1</span>
                    <span className="text-xs text-slate-700 dark:text-slate-300">
                      Review and adjust the <span className="font-semibold text-primary dark:text-primary/80 bg-primary/5 dark:bg-primary/10 px-1.5 py-0.5 rounded">search parameters</span> below if needed.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">2</span>
                    <span className="text-xs text-slate-700 dark:text-slate-300">
                      Click the <span className="font-semibold text-primary dark:text-primary/80 bg-primary/5 dark:bg-primary/10 px-1.5 py-0.5 rounded">Start</span> button to begin the search.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">3</span>
                    <span className="text-xs text-slate-700 dark:text-slate-300">
                      Watch the <span className="font-semibold text-primary dark:text-primary/80 bg-primary/5 dark:bg-primary/10 px-1.5 py-0.5 rounded">tree</span> and <span className="font-semibold text-primary dark:text-primary/80 bg-primary/5 dark:bg-primary/10 px-1.5 py-0.5 rounded">web page</span> update in real-time.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">4</span>
                    <span className="text-xs text-slate-700 dark:text-slate-300">
                      Check the <span className="font-semibold text-primary dark:text-primary/80 bg-primary/5 dark:bg-primary/10 px-1.5 py-0.5 rounded">message log</span> for detailed progress.
                    </span>
                  </li>
                </ol>
              </div>

              {/* Main Parameters */}
              <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Settings className="h-3.5 w-3.5 text-primary" />
                    Configuration Parameters
                  </h3>
                  <Button 
                    variant="outline"
                    size="sm"
                    className="h-5 px-2 text-[10px] border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-primary hover:border-primary hover:bg-primary/5 dark:hover:bg-primary/10"
                    onClick={() => {
                      handleParamChange('startingUrl', 'http://xwebarena.pathonai.org:7770/');
                      handleParamChange('goal', 'Search for running shoes and click the first result');
                      handleParamChange('maxDepth', 3);
                    }}
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Reset to Default
                  </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Left Column: Essential Parameters */}
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 hover:shadow-md transition-all duration-200 hover:border-primary/20 dark:hover:border-primary/20">
                      <div className="flex justify-between items-start mb-2">
                        <Label htmlFor="startingUrl" className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Globe className="h-3.5 w-3.5 text-primary" />
                          Starting URL
                        </Label>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400">The starting point for web browsing</span>
                      </div>
                      <Input
                        id="startingUrl"
                        value={searchParams.startingUrl}
                        onChange={(e) => handleParamChange('startingUrl', e.target.value)}
                        className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900 text-xs h-8"
                        placeholder="e.g., http://xwebarena.pathonai.org:7770/"
                      />
                    </div>

                    <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 hover:shadow-md transition-all duration-200 hover:border-primary/20 dark:hover:border-primary/20">
                      <div className="flex justify-between items-start mb-2">
                        <Label htmlFor="goal" className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Target className="h-3.5 w-3.5 text-primary" />
                          Goal
                        </Label>
                        <div className="flex gap-1.5">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-5 px-2 text-[10px] border-slate-200 dark:border-slate-700 hover:border-primary hover:text-primary hover:bg-primary/5 dark:hover:bg-primary/10"
                            onClick={() => handleParamChange('goal', 'Search for running shoes and click the first result')}
                          >
                            Example 1
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-5 px-2 text-[10px] border-slate-200 dark:border-slate-700 hover:border-primary hover:text-primary hover:bg-primary/5 dark:hover:bg-primary/10"
                            onClick={() => handleParamChange('goal', 'Find the price of the latest iPhone')}
                          >
                            Example 2
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-5 px-2 text-[10px] border-slate-200 dark:border-slate-700 hover:border-primary hover:text-primary hover:bg-primary/5 dark:hover:bg-primary/10"
                            onClick={() => handleParamChange('goal', 'Look up the weather in New York')}
                          >
                            Example 3
                          </Button>
                        </div>
                      </div>
                      <Input
                        id="goal"
                        value={searchParams.goal}
                        onChange={(e) => handleParamChange('goal', e.target.value)}
                        className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900 text-xs h-8"
                        placeholder="Describe what you want the agent to do"
                      />
                    </div>
                  </div>

                  {/* Right Column: Advanced Settings */}
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 hover:shadow-md transition-all duration-200 hover:border-primary/20 dark:hover:border-primary/20">
                      <div className="flex justify-between items-start mb-2">
                        <Label htmlFor="maxDepth" className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5 text-primary" />
                          Max Depth
                        </Label>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400">Maximum steps to reach goal</span>
                      </div>
                      <Input
                        id="maxDepth"
                        type="number"
                        min={1}
                        max={10}
                        value={searchParams.maxDepth}
                        onChange={(e) => handleParamChange('maxDepth', parseInt(e.target.value))}
                        className="border-slate-300 dark:border-slate-600 focus:ring-primary focus:border-primary bg-white dark:bg-slate-900 text-xs h-8"
                      />
                    </div>

                    <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-600 hover:shadow-md transition-all duration-200 hover:border-primary/20 dark:hover:border-primary/20">
                      {renderAlgorithmSpecificParams()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
