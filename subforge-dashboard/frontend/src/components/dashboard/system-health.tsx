'use client'

import { useEffect, useState } from 'react'
import { formatTime, formatBytes } from '@/lib/utils'
import { Cpu, HardDrive, Clock, Users } from 'lucide-react'

interface SystemHealthProps {
  data: {
    uptime: number
    cpu: number
    memory: number
    connections: number
  }
}

export function SystemHealth({ data }: SystemHealthProps) {
  const [currentData, setCurrentData] = useState(data)

  useEffect(() => {
    setCurrentData(data)
  }, [data])

  const getHealthStatus = () => {
    const { cpu, memory } = currentData
    if (cpu > 80 || memory > 80) return { status: 'critical', color: 'text-red-500' }
    if (cpu > 60 || memory > 60) return { status: 'warning', color: 'text-yellow-500' }
    return { status: 'good', color: 'text-green-500' }
  }

  const health = getHealthStatus()

  const metrics = [
    {
      label: 'Uptime',
      value: formatTime(currentData.uptime),
      icon: Clock,
      color: 'text-blue-500'
    },
    {
      label: 'CPU Usage',
      value: `${currentData.cpu}%`,
      icon: Cpu,
      color: currentData.cpu > 70 ? 'text-red-500' : 'text-green-500'
    },
    {
      label: 'Memory',
      value: `${currentData.memory}%`,
      icon: HardDrive,
      color: currentData.memory > 70 ? 'text-red-500' : 'text-green-500'
    },
    {
      label: 'Connections',
      value: currentData.connections.toString(),
      icon: Users,
      color: 'text-purple-500'
    },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            System Health
          </h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              health.status === 'good' ? 'bg-green-500' :
              health.status === 'warning' ? 'bg-yellow-500' :
              'bg-red-500'
            }`} />
            <span className={`text-sm font-medium ${health.color}`}>
              {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
            </span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <metric.icon className={`w-5 h-5 ${metric.color}`} />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {metric.label}
              </span>
            </div>
            <span className="text-sm font-bold text-gray-900 dark:text-white">
              {metric.value}
            </span>
          </div>
        ))}

        {/* System load bars */}
        <div className="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-600">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 dark:text-gray-400">CPU</span>
              <span className="text-gray-900 dark:text-white">{currentData.cpu}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  currentData.cpu > 70 ? 'bg-red-500' :
                  currentData.cpu > 40 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(currentData.cpu, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 dark:text-gray-400">Memory</span>
              <span className="text-gray-900 dark:text-white">{currentData.memory}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  currentData.memory > 70 ? 'bg-red-500' :
                  currentData.memory > 40 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(currentData.memory, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}