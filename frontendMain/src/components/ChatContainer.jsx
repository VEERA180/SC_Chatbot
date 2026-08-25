import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { FiCpu, FiFileText, FiHelpCircle, FiSearch } from 'react-icons/fi';

const ChatContainer = ({ messages, isLoading, onSendMessage }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const suggestions = [
    { 
      icon: FiSearch, 
      label: 'Check report time in SCORE', 
      desc: 'I cannot report time in SCORE, what should I do?',
      prompt: 'I cannot report time in SCORE what should I do?' 
    },
    { 
      icon: FiFileText, 
      label: 'Unlock Request', 
      desc: 'How to unlock user in GRC?',
      prompt: 'How to unlock user in GRC?' 
    },
    { 
      icon: FiHelpCircle, 
      label: 'User Guide', 
      desc: 'SCORE key User & Global Key User',
      prompt: 'Who is my SCORE Key User & Global Key User' 
    },
    { 
      icon: FiCpu, 
      label: 'Access request in GRC', 
      desc: 'How to check the access request status in GRC?',
      prompt: ' How to check the access request status in GRC?' 
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth custom-scrollbar">
      <div className="max-w-4xl mx-auto w-full h-full flex flex-col">
        {/* Welcome message */}
        {messages.length === 0 && !isLoading && (
          <div className="flex-1 flex flex-col items-center justify-center pb-20 xl:pb-0 2xl:-mt-20">
            
            <h1 className="text-3xl 2xl:text-5xl font-bold text-vgimt-header dark:text-white mb-6 2xl:mb-8 tracking-tight text-center">
              SCORE AI Assistant
            </h1>
            
            <div className="text-sm 2xl:text-lg text-slate-500 dark:text-slate-400 max-w-lg 2xl:max-w-2xl text-center leading-relaxed flex flex-col gap-1 2xl:gap-1 px-4 mb-8 2xl:mb-10">
              <p>Your intelligent companion for SCORE.</p>
              <p>Ask me about processes, documentation, or check your request status.</p>
            </div>

            {/* Suggestions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 2xl:gap-4 w-full max-w-xl 2xl:max-w-3xl px-4">
              {suggestions.map((item, index) => (
                <button
                  key={index}
                  onClick={() => onSendMessage && onSendMessage(item.prompt)}
                  className="group flex items-center gap-3 2xl:gap-4 p-3.5 2xl:p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl 2xl:rounded-2xl hover:border-vgimt-header/50 hover:shadow-md hover:shadow-vgimt-header/5 transition-all duration-300 text-left"
                >
                  <item.icon className="w-5 h-5 2xl:w-6 2xl:h-6 text-vgimt-header dark:text-blue-400 group-hover:text-[#013a63] dark:group-hover:text-blue-300 transition-colors flex-shrink-0" />
                  <div className="min-w-0">
                    <h3 className="text-sm 2xl:text-base font-semibold text-slate-800 dark:text-slate-200 group-hover:text-vgimt-header dark:group-hover:text-blue-400 transition-colors truncate">
                      {item.label}
                    </h3>
                    <p className="text-xs 2xl:text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                      {item.desc}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((message, index) => (
          <MessageBubble 
            key={index} 
            message={message} 
          />
        ))}

        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default ChatContainer;