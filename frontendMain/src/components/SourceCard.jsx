import React from 'react';
import { FiExternalLink } from 'react-icons/fi';

const SourceCard = ({ source }) => {
  const getTypeColor = (type) => {
    switch (type) {
      case 'Epic':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300';
      case 'Feature':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'User Story':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'Task':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
      case 'Bug':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-3 mb-2 hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors">
      {/* Main source info */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(source.type)}`}>
              {source.type}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              #{source.id}
            </span>
          </div>
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
            {source.title}
          </p>
        </div>
        
        {source.url && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 p-1.5 rounded hover:bg-slate-200 dark:hover:bg-slate-500 transition-colors"
            title="Open in Azure DevOps"
          >
            <FiExternalLink className="w-4 h-4 text-primary-500" />
          </a>
        )}
      </div>

      {/* Hierarchy breadcrumb with links */}
      {(source.epicUrl || source.featureUrl || source.storyUrl) && (
        <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-600">
          <div className="flex flex-wrap items-center gap-1 text-xs">
            {source.epicTitle && (
              <>
                {source.epicUrl ? (
                  <a
                    href={source.epicUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 dark:text-purple-400 hover:underline"
                  >
                    {source.epicTitle}
                  </a>
                ) : (
                  <span className="text-slate-500">{source.epicTitle}</span>
                )}
              </>
            )}
            
            {source.featureTitle && (
              <>
                <span className="text-slate-400">›</span>
                {source.featureUrl ? (
                  <a
                    href={source.featureUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {source.featureTitle}
                  </a>
                ) : (
                  <span className="text-slate-500">{source.featureTitle}</span>
                )}
              </>
            )}
            
            {source.storyTitle && (
              <>
                <span className="text-slate-400">›</span>
                {source.storyUrl ? (
                  <a
                    href={source.storyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 dark:text-green-400 hover:underline"
                  >
                    {source.storyTitle}
                  </a>
                ) : (
                  <span className="text-slate-500">{source.storyTitle}</span>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SourceCard;
