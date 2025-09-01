import { useDroppable } from '@dnd-kit/core'
import { cn } from '@/lib/utils'
import type { Task } from '@/app/tasks/page'

interface TaskColumnProps {
  id: string
  title: string
  count: number
  highPriorityCount: number
  status: Task['status']
  children: React.ReactNode
}

const statusColors = {
  todo: 'bg-gray-100 dark:bg-gray-700',
  in_progress: 'bg-blue-100 dark:bg-blue-900/20',
  review: 'bg-yellow-100 dark:bg-yellow-900/20',
  done: 'bg-green-100 dark:bg-green-900/20',
}

const statusBadgeColors = {
  todo: 'bg-gray-500',
  in_progress: 'bg-blue-500',
  review: 'bg-yellow-500',
  done: 'bg-green-500',
}

export function TaskColumn({ 
  id, 
  title, 
  count, 
  highPriorityCount, 
  status, 
  children 
}: TaskColumnProps) {
  const { isOver, setNodeRef } = useDroppable({
    id,
  })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'rounded-lg p-4 min-h-[500px] transition-colors',
        statusColors[status],
        isOver && 'ring-2 ring-blue-500 ring-opacity-50'
      )}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${statusBadgeColors[status]}`} />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          <span className="bg-white dark:bg-gray-600 text-gray-600 dark:text-gray-300 text-xs font-medium px-2 py-1 rounded-full">
            {count}
          </span>
        </div>
        {highPriorityCount > 0 && (
          <span className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full">
            {highPriorityCount} high
          </span>
        )}
      </div>

      {/* Tasks */}
      <div className="space-y-3">
        {children}
      </div>

      {/* Drop zone indicator */}
      {isOver && (
        <div className="mt-4 p-4 border-2 border-dashed border-blue-400 rounded-lg bg-blue-50 dark:bg-blue-900/10">
          <p className="text-center text-blue-600 dark:text-blue-400 text-sm">
            Drop task here
          </p>
        </div>
      )}
    </div>
  )
}