import React, { useState, useEffect } from 'react';
import { FiChevronRight } from 'react-icons/fi';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';
import { chatService } from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Apply dark mode class to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await chatService.healthCheck();
        setIsOnline(true);
      } catch (error) {
        console.error('Backend health check failed:', error);
        setIsOnline(false);
      }
    };
    checkHealth();
  }, []);

  // Handle responsive sidebar behavior
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };

    // Set initial state
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };
 
  const formatTimestamp = () => {
    return new Date().toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSendMessage = async (content) => {
    if (!content.trim()) {
      return;
    }

    // Add user message
    const userMessage = {
      role: 'user',
      content,
      timestamp: formatTimestamp(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call API using chatService
      const response = await chatService.sendMessage(content);

      // Add assistant message with all fields including top_sources_formatted
      const assistantMessage = {
        role: 'assistant',
        content: response.answer || 'Sorry, I could not process your request.',
        sources: response.sources || [],
        top_sources_formatted: response.top_sources_formatted || '', 
        type: response.type || 'rag',
        document_count: response.document_count || 0,
        timestamp: formatTimestamp(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message to chat
      const errorMessage = {
        role: 'assistant',
        content: `❌ **Error:** ${error.message || 'No response from server. Please check your connection and try again.'}`,
        sources: [],
        top_sources_formatted: '',
        type: 'error',
        timestamp: formatTimestamp(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    chatService.createNewSession();
    setMessages([]);
  };

  return (
    <div className={`h-screen flex flex-col bg-[#fcfcfc] dark:bg-slate-800`}>
      {/* Header */}
      <Header 
        darkMode={darkMode} 
        toggleDarkMode={toggleDarkMode}
      />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mobile Backdrop */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 md:hidden glass-backdrop"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Sidebar (Left) */}
        {/* On desktop, we want it relative so it takes space. On mobile, fixed. */}
        <div className={`flex-shrink-0 h-full z-40 relative transition-all duration-300 ease-in-out ${isSidebarOpen ? 'w-0 md:w-48 xl:w-72' : 'w-0'}`}>
             <Sidebar 
              isOpen={isSidebarOpen} 
              toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} 
              onNewChat={handleNewChat}
            />
        </div>

        {/* Re-open Sidebar Button */}
        {!isSidebarOpen && (
          <button 
            onClick={() => setIsSidebarOpen(true)} 
            className="absolute left-4 top-4 z-10 p-2 bg-white shadow-md rounded-lg text-vgimt-header hover:bg-slate-100 dark:bg-slate-700 dark:text-white transition-opacity duration-300"
            title="Open Sidebar"
          >
            <FiChevronRight className="w-5 h-5" />
          </button>
        )}

        {/* Chat area */}
        <div className="flex-1 flex flex-col relative w-full min-w-0 bg-transparent">
          <ChatContainer 
            messages={messages} 
            isLoading={isLoading} 
            onSendMessage={handleSendMessage}
          />
          
          <div className="w-full">
            <ChatInput 
              onSendMessage={handleSendMessage} 
              isLoading={isLoading}
              disabled={!isOnline}
            />
          </div>
        </div>
      </div>

      {/* Offline indicator */}
      {!isOnline && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          Backend is offline. Please check the server connection.
        </div>
      )}
    </div>
  );
}

export default App;