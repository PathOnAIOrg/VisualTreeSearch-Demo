import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Info, ChevronDown, ChevronUp } from "lucide-react";

interface SearchParams {
  startingUrl: string;
  goal: string;
  algorithm: 'bfs' | 'dfs';
  maxDepth: number;
}

interface ControlPanelProps {
  searchParams: SearchParams;
  handleParamChange: (param: keyof SearchParams, value: string | boolean | number) => void;
  handleStart: () => void;
  disconnect: () => void;
  isSearching: boolean;
  connected: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  searchParams,
  handleParamChange,
  handleStart,
  disconnect,
  isSearching,
  connected,
}) => {
  const [showParameters, setShowParameters] = React.useState(true);

  return (
    <div className="bg-white dark:bg-slate-800 shadow-sm border-b sticky top-0 z-10">
      <div className="py-3 px-4 max-w-full">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-sky-950 dark:text-sky-100">Visual Tree Search: Simple Search (BFS/DFS)</h1>
          
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
  );
};

export default ControlPanel;
