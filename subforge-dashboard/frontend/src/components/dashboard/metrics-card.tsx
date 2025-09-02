import { 
  Users, 
  CheckCircle, 
  Cpu, 
  HardDrive, 
  TrendingUp, 
  TrendingDown,
  Activity 
} from 'lucide-react'

interface MetricsCardProps {
  title: string
  value: number | string
  total?: number | string
  trend?: string
  icon: 'users' | 'check-circle' | 'cpu' | 'hard-drive' | 'activity'
  color: 'blue' | 'green' | 'orange' | 'purple'
  suffix?: string
}

const icons = {
  users: Users,
  'check-circle': CheckCircle,
  cpu: Cpu,
  'hard-drive': HardDrive,
  activity: Activity,
}

const colorClasses = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  orange: 'bg-orange-500',
  purple: 'bg-purple-500',
}

export function MetricsCard({ 
  title, 
  value, 
  total, 
  trend, 
  icon, 
  color, 
  suffix = '' 
}: MetricsCardProps) {
  const IconComponent = icons[icon]
  const isPositiveTrend = trend?.startsWith('+')
  const isNegativeTrend = trend?.startsWith('-')

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            <IconComponent className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
          </div>
        </div>
        {trend && (
          <div className="flex items-center space-x-1">
            {isPositiveTrend ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : isNegativeTrend ? (
              <TrendingDown className="w-4 h-4 text-red-500" />
            ) : null}
            <span className={`text-xs ${
              isPositiveTrend 
                ? 'text-green-600' 
                : isNegativeTrend 
                ? 'text-red-600' 
                : 'text-gray-600'
            }`}>
              {trend}
            </span>
          </div>
        )}
      </div>
      
      <div className="mt-4">
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-bold text-gray-900 dark:text-white">
            {value}{suffix}
          </span>
          {total && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              / {total}{suffix}
            </span>
          )}
        </div>
        
        {total && typeof value === 'number' && typeof total === 'number' && (
          <div className="mt-3">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${colorClasses[color]}`}
                style={{ width: `${Math.min((value / total) * 100, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}