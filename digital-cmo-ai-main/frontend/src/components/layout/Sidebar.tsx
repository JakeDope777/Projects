import { NavLink } from 'react-router-dom';
import {
  MessageSquare,
  LayoutDashboard,
  Search,
  Palette,
  Users,
  Settings,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { label: 'Chat', path: '/chat', icon: MessageSquare },
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Analysis', path: '/analysis', icon: Search },
  { label: 'Creative', path: '/creative', icon: Palette },
  { label: 'CRM', path: '/crm', icon: Users },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-200">
        <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-tight">Digital CMO</h1>
          <p className="text-xs text-gray-500">AI Marketing Assistant</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200">
        <p className="text-xs text-gray-400">Digital CMO AI v0.1.0</p>
      </div>
    </aside>
  );
}
