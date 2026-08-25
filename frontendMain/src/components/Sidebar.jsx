import React from 'react';
import { 
  FiFolder, 
  FiClipboard, 
  FiUser, 
  FiBarChart2,
  FiEdit,
  FiChevronLeft,
  FiCheckCircle
} from 'react-icons/fi';

const Sidebar = ({ isOpen, toggleSidebar, onNewChat }) => {
  const quickActions = [
    { icon: FiFolder, label: 'Global Key User', link: 'https://volvogroup.sharepoint.com/sites/coll-score-global/SitePages/SCORE-Global-Key-Users.aspx' },
    { icon: FiClipboard, label: 'Manuals & Training', link: 'https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?csf=1&web=1&e=OVtfgx%2F&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A&id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users' },
    { icon: FiUser, label: 'Information for key Users', link: 'https://volvogroup.sharepoint.com/sites/coll-score-global/Key%20User%20Information/Forms/AllItems.aspx' },
    { icon: FiCheckCircle, label: 'Key User Support', link: 'https://volvogroup.sharepoint.com/:x:/r/sites/coll-score-global/_layouts/15/Doc.aspx?sourcedoc=%7BC9431BC8-3976-4397-B055-554076024E62%7D&file=SM35%20KU%20per%20companies%20in%20SCORE.xlsx&action=default&mobileredirect=true' },
    { icon: FiBarChart2, label: 'SCORE Calendar', link: '' },
  ];



   const mockChats = [
  //   "Add disclaimer to chatbot",
  //   "Meet with boss about dashboard",
  //   "Buy eggs, bread and peanuts",
  //   "Fix login authentication issue",
  //   "Review annual budget report",
  //   "Update user permission roles",
  //   "Schedule team building event",
  //   "Draft project proposal v2",
  //   "Client meeting preparation",
  //   "System maintenance downtime",
  //   "API documentation update",
  //   "Monthly expense tracking",
  //   "Quarterly performance review"
   ]

  const handleActionClick = (link) => {
    if (link && link !== '#') {
      window.open(link, '_blank');
    }
  };

  return (
    <aside 
      className={`
        fixed z-40 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 
        transition-all duration-300 ease-in-out flex flex-col shadow-2xl md:shadow-none
        pt-6 pl-4 xl:pt-8 xl:pl-6
        ${isOpen ? 'translate-x-0 w-48 md:w-48 xl:w-72 md:translate-x-0' : '-translate-x-full w-48 md:w-0 md:translate-x-0 md:overflow-hidden md:border-r-0 md:pl-0'}
      `}
    >
      {/* Collapse Button */}
      {isOpen && (
        <button 
          onClick={toggleSidebar}
          className="absolute top-4 right-4 p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-vgimt-header dark:text-blue-400 transition-colors"
        >
          <FiChevronLeft className="w-5 h-5" />
        </button>
      )}

      {/* FIXED TOP SECTION: New Chat */}
      <div className="flex-shrink-0 pr-4">
        {/* Top Actions */}
        <div className="mb-4 md:mb-8 mt-2">
          <button 
            onClick={onNewChat}
            className="flex items-center gap-3 xl:gap-4 text-slate-700 dark:text-slate-200 hover:text-vgimt-header dark:hover:text-blue-400 font-medium w-full text-left transition-colors"
          >
            <FiEdit className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-vgimt-header dark:text-blue-400" />
            <span className="text-xs xl:text-sm">New chat</span>
          </button>
        </div>
      </div>

      {/* SCROLLABLE SECTION: Quick Actions + Your Chats */}
      <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar min-h-[100px] mb-4 md:mb-6">
        
        {/* Quick Actions */}
        <div className="mb-4 md:mb-6">
          <h2 className="text-sm xl:text-base font-bold text-vgimt-header dark:text-blue-400 mb-2 md:mb-3">
            Quick Actions
          </h2>
          <div className="space-y-1 md:space-y-2">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleActionClick(action.link)}
                className="w-full flex items-center gap-3 xl:gap-4 py-1 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left"
              >
                <action.icon className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-vgimt-header dark:text-blue-400" />
                <span className="text-xs xl:text-sm text-slate-700 dark:text-slate-300 font-medium whitespace-nowrap overflow-hidden text-ellipsis">
                  {action.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Your Chats */}
        <div>
          <h2 className="text-sm xl:text-base font-bold text-vgimt-header dark:text-blue-400 mb-2 md:mb-3 sticky top-0 bg-white dark:bg-slate-900 z-10 py-1">
           
          
          </h2>
          <div className="space-y-1 md:space-y-2">
            {mockChats.map((chat, index) => (
              <button
                key={index}
                className="w-full flex items-center gap-3 xl:gap-4 py-1 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left group"
              >
                <span className="text-xs xl:text-sm text-slate-700 dark:text-slate-300 truncate w-full group-hover:text-vgimt-accent dark:group-hover:text-blue-400 font-medium transition-colors">
                  {chat}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>


    </aside>
  );
};

export default Sidebar;