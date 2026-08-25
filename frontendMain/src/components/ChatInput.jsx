import React, { useState } from 'react';
import { FiSend } from 'react-icons/fi';

const ChatInput = ({ onSendMessage, isLoading, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="px-4 pb-3 pt-2 w-full max-w-2xl 2xl:max-w-4xl mx-auto">
      <form 
        onSubmit={handleSubmit} 
        className="relative flex items-center bg-white dark:bg-slate-800 rounded-xl shadow-lg shadow-slate-900/10 dark:shadow-black/40 border border-slate-200 dark:border-slate-600 transition-all duration-200 focus-within:border-[#014f86] focus-within:shadow-[#014f86]/10"
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything related to SCORE workitems..."
          disabled={isLoading || disabled}
          autoComplete="off"
          autoFocus
          className="flex-1 px-4 py-3 bg-transparent border-none text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-400 focus:outline-none focus:ring-0 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!message.trim() || isLoading || disabled}
          className="absolute right-2 p-2 z-20 text-[#014f86] dark:text-blue-400 hover:text-[#014f86]/80 dark:hover:text-blue-300 disabled:text-slate-300 dark:disabled:text-slate-600 disabled:cursor-not-allowed transition-colors"
        >
          <FiSend className="w-4 h-4" />
        </button>
      </form>
      <p className="text-[9px] text-slate-400 text-center mt-1.5">
        AI can make mistakes. Verify important info.
      </p>
    </div>
  );
};

export default ChatInput;
