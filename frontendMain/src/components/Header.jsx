import React from 'react';
import { FiMoon, FiSun, FiHelpCircle } from 'react-icons/fi';

const Header = ({ darkMode, toggleDarkMode }) => {
  return (
    <header className="bg-gradient-to-r from-[#014f86] to-[#013f6b] dark:from-slate-900 dark:to-slate-800 border-b border-blue-800/50 dark:border-slate-700 px-4 md:px-6 py-4 shadow-md sticky top-0 z-50">
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center flex-1">
          <div className="flex flex-col">
            <h1 className="text-2xl font-bold text-white flex items-center">
              SC<img src="/vgimtlogo1.png" alt="O" className="h-5 w-5 inline-block mx-0.5" />RE AI Assistant
            </h1>
            <p className="text-xs text-white/90">
              SCheduling COst and REsources Management Tool
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Help Button */}
          <button
            className="p-2 rounded-full hover:bg-white/20 transition-colors"
            aria-label="Help"
            title="Help"
          >
            <FiHelpCircle className="w-5 h-5 text-white" />
          </button>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-full hover:bg-white/20 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? (
              <FiSun className="w-5 h-5 text-white" />
            ) : (
              <FiMoon className="w-5 h-5 text-white" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;