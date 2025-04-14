import React from 'react';

interface Message {
  content: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
}

interface MessageLogPanelProps {
  messages: Message[];
  messagesEndRef?: React.RefObject<HTMLDivElement | null>;
}

const MessageLogPanel: React.FC<MessageLogPanelProps> = ({ messages, messagesEndRef }) => {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 p-3 mt-4">
      <h2 className="text-lg font-semibold mb-2 text-sky-950 dark:text-sky-100 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-cyan-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
        </svg>
        Message Log
      </h2>
      <div className="h-[150px] overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-md p-2 bg-gradient-to-r from-sky-50 to-white dark:from-slate-900 dark:to-slate-800">
        {messages.map((msg, index) => (
          <div key={index} className={`mb-2 ${msg.type === 'outgoing' ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-800 dark:text-slate-200'}`}>
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{msg.timestamp} - {msg.type}</div>
            <pre className="whitespace-pre-wrap bg-white dark:bg-slate-800 p-2 rounded text-sm border border-slate-200 dark:border-slate-700">{msg.content}</pre>
          </div>
        ))}
        {messagesEndRef && <div ref={messagesEndRef} />}
      </div>
    </div>
  );
};

export default MessageLogPanel;
