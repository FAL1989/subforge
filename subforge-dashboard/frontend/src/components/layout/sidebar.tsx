'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Home, 
  Users, 
  Kanban, 
  BarChart3, 
  Clock, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Workflows', href: '/workflows', icon: Activity },
  { name: 'Agents', href: '/agents', icon: Users },
  { name: 'Tasks', href: '/tasks', icon: Kanban },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'History', href: '/history', icon: Clock },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <div className={cn(
      "bg-white dark:bg-gray-800 shadow-lg transition-all duration-300 ease-in-out",
      collapsed ? "w-16" : "w-64"
    )}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">SF</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                SubForge
              </span>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
                    : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700",
                  collapsed ? "justify-center" : "justify-start"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className={cn("flex-shrink-0", collapsed ? "h-5 w-5" : "h-5 w-5 mr-3")} />
                {!collapsed && item.name}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {!collapsed && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              <p>SubForge v1.0</p>
              <p>AI Agent Platform</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}