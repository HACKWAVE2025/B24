import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, Sparkles, BarChart3, LogOut, X } from 'lucide-react';
import { Button } from './ui/button';

const Sidebar = ({ isOpen, onClose, onLogout }) => {
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { name: 'Try Demo', path: '/demo', icon: <Sparkles className="w-5 h-5" /> },
    { name: 'AI Analysis', path: '/ai-analysis', icon: <BarChart3 className="w-5 h-5" /> },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
            data-testid="sidebar-overlay"
          />

          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 h-full w-80 glass z-50 shadow-2xl border-r border-indigo-200 dark:border-gray-700"
            data-testid="sidebar"
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-6 border-b border-indigo-200/50 dark:border-gray-700 bg-gradient-to-r from-indigo-50/50 to-blue-50/50 dark:from-gray-800 dark:to-gray-900">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-blue-500 rounded-lg flex items-center justify-center shadow-lg">
                    <Shield className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">FIGMENT</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="hover:bg-indigo-100 dark:hover:bg-gray-700"
                  data-testid="close-sidebar-btn"
                >
                  <X className="w-6 h-6 text-gray-900 dark:text-white" />
                </Button>
              </div>

              <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    data-testid={`sidebar-link-${item.name.toLowerCase().replace(/ /g, '-')}`}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all ${location.pathname === item.path
                      ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-500/50'
                      : 'text-gray-700 hover:bg-indigo-50 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                  >
                    {item.icon}
                    <span>{item.name}</span>
                  </Link>
                ))}
              </nav>

              <div className="p-4 border-t border-indigo-200/50 dark:border-gray-700">
                <Button
                  onClick={onLogout}
                  variant="outline"
                  className="w-full justify-start gap-3 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-900/50 dark:hover:text-red-300 dark:hover:border-red-700"
                  data-testid="logout-btn"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default Sidebar;
