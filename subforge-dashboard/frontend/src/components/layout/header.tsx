'use client'

import { Bell, Search, Sun, Moon, User } from 'lucide-react'
import { useTheme } from '@/components/providers/theme-provider'
import { ConnectionStatus } from '@/components/ui/connection-status'
import { useState } from 'react'

export function Header() {
  const { theme, setTheme } = useTheme()
  const [notifications, setNotifications] = useState(3)

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search agents, tasks, or metrics..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <ConnectionStatus className="mr-2" />
          
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {/* Notifications */}
          <button className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400">
            <Bell size={18} />
            {notifications > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {notifications}
              </span>
            )}
          </button>

          {/* User Menu */}
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Admin User
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                System Administrator
              </div>
            </div>
            <button className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
              <User size={18} />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}