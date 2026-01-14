import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Building2,
  MessageSquare,
  Settings,
  LogOut
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/staff', icon: LayoutDashboard },
  { name: 'Leads', href: '/staff/leads', icon: Users },
  { name: 'Analytics', href: '/staff/analytics', icon: BarChart3 },
  { name: 'Properties', href: '/staff/properties', icon: Building2 },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-aurora-900 text-white">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-aurora-800">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
            <span className="text-aurora-900 font-bold text-lg">A</span>
          </div>
          <div>
            <h1 className="font-semibold">Aurora EDC</h1>
            <p className="text-xs text-aurora-300">Staff Portal</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-3">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === '/staff'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-colors',
                  isActive
                    ? 'bg-aurora-800 text-white'
                    : 'text-aurora-200 hover:bg-aurora-800/50 hover:text-white'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-aurora-800">
          <a
            href="/"
            target="_blank"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-aurora-200 hover:bg-aurora-800/50 hover:text-white transition-colors"
          >
            <MessageSquare className="w-5 h-5" />
            Open Chatbot
          </a>
          <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-aurora-200 hover:bg-aurora-800/50 hover:text-white transition-colors w-full">
            <Settings className="w-5 h-5" />
            Settings
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Welcome back</h2>
              <p className="text-sm text-gray-500">Here's what's happening with your leads today.</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Staff User</p>
                <p className="text-xs text-gray-500">staff@auroragov.org</p>
              </div>
              <div className="w-10 h-10 bg-aurora-100 rounded-full flex items-center justify-center">
                <span className="text-aurora-700 font-medium">SU</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
