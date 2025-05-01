import React from 'react';
import { Globe } from 'lucide-react';

interface LiveBrowserViewProps {
  liveBrowserUrl: string | null;
  width: string;
}

const LiveBrowserView: React.FC<LiveBrowserViewProps> = ({ liveBrowserUrl, width }) => {
  return (
    <div 
      className="bg-white dark:bg-slate-800 rounded-l-lg overflow-hidden"
      style={{ width }}
    >
      <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        <h2 className="text-lg font-semibold text-sky-950 dark:text-sky-100 flex items-center">
          <Globe className="h-4 w-4 mr-1.5 text-primary" />
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
  );
};

export default LiveBrowserView;
