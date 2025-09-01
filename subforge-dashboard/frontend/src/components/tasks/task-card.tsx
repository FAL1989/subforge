import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Clock, User, AlertCircle, Calendar, Tag } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Task } from '@/app/tasks/page'

interface TaskCardProps {
  task: Task
  onUpdate: (task: Task) => void
  isDragging?: boolean
}

const priorityColors = {
  low: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  high: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
}

const priorityIcons = {
  low: '●',
  medium: '●●',
  high: '●●●',
}

export function TaskCard({ task, onUpdate, isDragging }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({
    id: task.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const formatEstimatedTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const isOverdue = task.dueDate && new Date(task.dueDate) < new Date()

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-600 cursor-grab hover:shadow-md transition-shadow',
        (isDragging || isSortableDragging) && 'opacity-50 rotate-3 shadow-lg'
      )}
    >
      {/* Priority and Due Date */}
      <div className="flex items-center justify-between mb-2">
        <span className={cn(
          'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
          priorityColors[task.priority]
        )}>
          <span className="mr-1">{priorityIcons[task.priority]}</span>
          {task.priority}
        </span>
        {task.dueDate && (
          <div className={cn(
            'flex items-center space-x-1 text-xs',
            isOverdue ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'
          )}>
            <Calendar className="w-3 h-3" />
            <span>{new Date(task.dueDate).toLocaleDateString()}</span>
            {isOverdue && <AlertCircle className="w-3 h-3" />}
          </div>
        )}
      </div>

      {/* Title and Description */}
      <div className="mb-3">
        <h4 className="font-medium text-gray-900 dark:text-white text-sm mb-1 line-clamp-2">
          {task.title}
        </h4>
        <p className="text-gray-600 dark:text-gray-400 text-xs line-clamp-2">
          {task.description}
        </p>
      </div>

      {/* Tags */}
      {task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {task.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
            >
              <Tag className="w-2 h-2 mr-1" />
              {tag}
            </span>
          ))}
          {task.tags.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
              +{task.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center space-x-3">
          {task.assignee && (
            <div className="flex items-center space-x-1">
              <User className="w-3 h-3" />
              <span>{task.assignee}</span>
            </div>
          )}
          {task.estimatedTime && (
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>{formatEstimatedTime(task.estimatedTime)}</span>
            </div>
          )}
        </div>
        {task.dependencies && task.dependencies.length > 0 && (
          <div className="flex items-center space-x-1">
            <span className="text-orange-500">⚡</span>
            <span>{task.dependencies.length} deps</span>
          </div>
        )}
      </div>

      {/* Progress indicator for in-progress tasks */}
      {task.status === 'in_progress' && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
            <div
              className="bg-blue-500 h-1 rounded-full transition-all duration-300"
              style={{ 
                width: task.actualTime && task.estimatedTime 
                  ? `${Math.min((task.actualTime / task.estimatedTime) * 100, 100)}%` 
                  : '30%'
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}