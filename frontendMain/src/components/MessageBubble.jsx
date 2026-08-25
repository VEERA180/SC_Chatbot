import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  RiRobot2Line, 
  RiUser3Line, 
  RiFileCopyLine, 
  RiThumbUpLine, 
  RiThumbDownLine 
} from 'react-icons/ri';
import { FiExternalLink, FiFolder } from 'react-icons/fi';

// Custom components for ReactMarkdown
const MarkdownComponents = {
  // Code blocks and inline code
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';

    if (!inline) {
      // This assistant answers in prose/lists/tables, not code. A block WITHOUT a
      // language is almost always accidental (indented text or a stray ``` fence),
      // so render it as a soft, readable box instead of a jarring black terminal strip.
      if (!language) {
        return (
          <span className="bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-1.5 py-0.5 rounded text-sm font-medium">
            {children}
          </span>
        );
      }
      return (
        <div className="relative group my-3">
          <div className="absolute top-0 right-0 px-2 py-1 text-xs text-slate-400 bg-slate-800 rounded-bl">
            {language}
          </div>
          <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm">
            <code className={className} {...props}>
              {children}
            </code>
          </pre>
        </div>
      );
    }
    return (
      <code className="bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
        {children}
      </code>
    );
  },
  // Links
  a({ node, children, href, ...props }) {
    return (
      <a 
        href={href} 
        target="_blank" 
        rel="noopener noreferrer" 
        className="text-[#014f86] dark:text-blue-400 hover:underline"
        {...props}
      >
        {children}
      </a>
    );
  },
  // Tables
  table({ node, children, ...props }) {
    return (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full border-collapse border border-slate-300 dark:border-slate-600" {...props}>
          {children}
        </table>
      </div>
    );
  },
  th({ node, children, ...props }) {
    return (
      <th className="border border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700 px-3 py-2 text-left font-semibold" {...props}>
        {children}
      </th>
    );
  },
  td({ node, children, ...props }) {
    return (
      <td className="border border-slate-300 dark:border-slate-600 px-3 py-2" {...props}>
        {children}
      </td>
    );
  },
  // Lists
  ul({ node, children, ...props }) {
    return (
      <ul className="list-disc list-outside pl-5 my-3 space-y-2" {...props}>
        {children}
      </ul>
    );
  },
  ol({ node, children, ...props }) {
    return (
      <ol className="list-decimal list-outside pl-5 my-3 space-y-3" {...props}>
        {children}
      </ol>
    );
  },
  li({ node, children, ...props }) {
    return (
      <li className="text-slate-700 dark:text-slate-300 leading-relaxed pl-1" {...props}>
        {children}
      </li>
    );
  },
  // Headings
  h1({ node, children, ...props }) {
    return <h1 className="text-2xl font-bold mt-6 mb-3 text-slate-800 dark:text-slate-100" {...props}>{children}</h1>;
  },
  h2({ node, children, ...props }) {
    return <h2 className="text-xl font-bold mt-6 mb-3 text-slate-800 dark:text-slate-100" {...props}>{children}</h2>;
  },
  h3({ node, children, ...props }) {
    return <h3 className="text-lg font-semibold mt-5 mb-2 text-slate-800 dark:text-slate-100" {...props}>{children}</h3>;
  },
  h4({ node, children, ...props }) {
    return <h4 className="text-base font-semibold mt-4 mb-2 text-slate-800 dark:text-slate-100" {...props}>{children}</h4>;
  },
  // Paragraphs
  p({ node, children, ...props }) {
    return <p className="my-3 leading-relaxed" {...props}>{children}</p>;
  },
  // Blockquotes
  blockquote({ node, children, ...props }) {
    return (
      <blockquote className="border-l-4 border-[#014f86] dark:border-blue-400 pl-4 py-1 my-4 italic text-slate-600 dark:text-slate-400" {...props}>
        {children}
      </blockquote>
    );
  },
  // Horizontal rule
  hr({ node, ...props }) {
    return <hr className="my-4 border-slate-300 dark:border-slate-600" {...props} />;
  },
  // Strong/Bold
  strong({ node, children, ...props }) {
    return <strong className="font-semibold text-slate-800 dark:text-slate-200" {...props}>{children}</strong>;
  },
  // Emphasis/Italic
  em({ node, children, ...props }) {
    return <em className="italic" {...props}>{children}</em>;
  },
};

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-6">
        <div className="flex flex-col items-end max-w-2xl">
          {/* User Message with Icon on right */}
          <div className="flex items-start gap-3">
            {/* User Message Bubble */}
            <div className="bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
              {message.content}
            </div>
            {/* User Icon */}
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-white dark:bg-slate-800 rounded-full border-2 border-[#014f86] flex items-center justify-center text-[#014f86]">
              <RiUser3Line className="w-6 h-6" />
            </div>
          </div>
          {/* Time below the bubble */}
          <div className="text-xs text-slate-400 mt-1.5 mr-11">
            {message.timestamp}
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message
  return (
    <div className="flex gap-3 mb-6">
      <div className="flex-shrink-0 mt-1">
        <div className="w-10 h-10 rounded-full border-2 border-[#014f86] flex items-center justify-center text-[#014f86] bg-white dark:bg-slate-800">
          <RiRobot2Line className="w-6 h-6" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        {/* Content - starts inline with icon */}
        <div className="text-slate-700 dark:text-slate-300 mb-4">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={MarkdownComponents}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Actions Footer */}
        <div className="flex items-center gap-2 text-slate-400 mb-4">
          <button 
            onClick={handleCopy}
            className="p-1.5 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors" 
            title="Copy"
          >
            <RiFileCopyLine className="w-4 h-4" />
          </button>
          <button className="p-1.5 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/30 rounded transition-colors" title="Helpful">
            <RiThumbUpLine className="w-4 h-4" />
          </button>
          <button className="p-1.5 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors" title="Not Helpful">
            <RiThumbDownLine className="w-4 h-4" />
          </button>
        </div>

        {/* Inline Sources Section */}
        {message.sources && message.sources.length > 0 && (
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Sources</h4>
            <div className="space-y-3">
              {message.sources.slice(0, 1).map((source, index) => {
                const fileName = source.file || source.file_name || 'Document';
                const documentLocation = source.document_location || '';
                const sharePointUrl = source.url || (documentLocation ? `https://volvogroup.sharepoint.com/${documentLocation}` : '#');
                const locationPath = documentLocation || 'Unknown location';
                
                return (
                  <div key={index} className="text-sm">
                    <div className="font-medium text-slate-800 dark:text-slate-200">
                      {fileName}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs">
                      <a 
                        href={sharePointUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#014f86] hover:text-[#013a63] dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
                      >
                        <FiExternalLink className="w-3 h-3" /> Open in SharePoint
                      </a>
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1">
                        <FiFolder className="w-3 h-3" /> Location: {locationPath}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;