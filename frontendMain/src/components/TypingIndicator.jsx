import React from 'react';
import { RiRobot2Line } from 'react-icons/ri';

const TypingIndicator = () => {
  return (
    <div className="flex gap-3 mb-6">
      {/* Bot Avatar */}
      <div className="flex-shrink-0 mt-1">
        <div className="w-10 h-10 rounded-full border-2 border-[#014f86] flex items-center justify-center text-[#014f86] bg-white dark:bg-slate-800">
          <RiRobot2Line className="w-6 h-6" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        {/* Skeleton Loading */}
        <div className="space-y-3 animate-pulse">
          {/* Title skeleton */}
          <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
          
          {/* Paragraph skeletons */}
          <div className="space-y-2 mt-3">
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
          </div>

          {/* List item skeletons */}
          <div className="space-y-2 mt-4">
            <div className="flex gap-2 items-center">
              <div className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full flex-shrink-0"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-4/5"></div>
            </div>
            <div className="flex gap-2 items-center">
              <div className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full flex-shrink-0"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
            </div>
            <div className="flex gap-2 items-center">
              <div className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full flex-shrink-0"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
