import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Info, ChevronDown, ChevronUp } from "lucide-react";
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
            <Label htmlFor="algorithm" className="text-slate-700 dark:text-slate-300 font-medium">Algorithm</Label>
            <select
              id="algorithm"
              value={(searchParams as BFSSearchParams).algorithm}
              onChange={(e) => handleParamChange('algorithm', e.target.value as 'bfs' | 'dfs')}
              className="w-full p-2 border rounded bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value="bfs">Breadth-First Search (BFS)</option>
              <option value="dfs">Depth-First Search (DFS)</option>
            </select>
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
                className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
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
                className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
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
                className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
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
    <div className="bg-white dark:bg-slate-800 shadow-sm border-b sticky top-0 z-10">
      <div className="py-3 px-4 max-w-full">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-sky-950 dark:text-sky-100">{getTitle()}</h1>
          
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
          
          {showParameters && (
            <div className="p-4 border-t border-sky-200 dark:border-sky-800 bg-white/90 dark:bg-slate-800/90">
              {/* Instructions */}
              <div className="mb-4 ml-1 text-sm text-slate-700 dark:text-slate-300">
                <ol className="list-decimal list-inside space-y-1">
                  <li>Click the &quot;Start&quot; button above to connect and begin the search.</li>
                  <li>Configure your search parameters below.</li>
                  <li>The tree of possible actions will appear on the right, while the resulting web page will display on the left.</li>
                  <li>You can drag the divider to resize the panels as needed.</li>
                </ol>
              </div>
              
              {/* Parameters Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="startingUrl" className="text-slate-700 dark:text-slate-300 font-medium">Starting URL</Label>
                  <Input
                    id="startingUrl"
                    value={searchParams.startingUrl}
                    onChange={(e) => handleParamChange('startingUrl', e.target.value)}
                    className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="e.g., http://xwebarena.pathonai.org:7770/"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    The starting URL for the web browser. This is where the search will begin.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="goal" className="text-slate-700 dark:text-slate-300 font-medium">Goal</Label>
                  <Input
                    id="goal"
                    value={searchParams.goal}
                    onChange={(e) => handleParamChange('goal', e.target.value)}
                    className="border-slate-300 dark:border-slate-600 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="e.g., search for running shoes and click the first result"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Describe what you want the agent to do in natural language. Examples:
                    <ul className="list-disc list-inside mt-1">
                      <li>Search for running shoes and click the first result</li>
                      <li>Find the price of the latest iPhone</li>
                      <li>Look up the weather in New York</li>
                    </ul>
                  </p>
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
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Maximum number of steps the agent can take to reach the goal. Higher values allow for more complex tasks but may take longer.
                  </p>
                </div>

                {renderAlgorithmSpecificParams()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
