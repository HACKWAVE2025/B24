import { Shield, Menu, Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';

const TopNav = ({ onMenuClick, darkMode, onDarkModeToggle }) => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-30 glass-dark border-b border-indigo-200/50" data-testid="topnav">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            data-testid="menu-btn"
            className="text-gray-700 hover:text-indigo-600 hover:bg-indigo-50"
          >
            <Menu className="w-6 h-6" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">FIGMENT</span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onDarkModeToggle}
          data-testid="dark-mode-toggle"
          className="text-gray-700 hover:text-indigo-600 hover:bg-indigo-50"
        >
          {darkMode ? <Sun className="w-6 h-6 text-yellow-400" /> : <Moon className="w-6 h-6" />}
        </Button>
      </div>
    </nav>
  );
};

export default TopNav;
