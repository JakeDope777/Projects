import { Bell, User } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 rounded-lg hover:bg-gray-100">
          <User className="w-5 h-5" />
          <span className="hidden sm:inline">Account</span>
        </button>
      </div>
    </header>
  );
}
