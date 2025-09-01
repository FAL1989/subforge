'use client'

import { useState, useEffect } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { arrayMove, SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { TaskColumn } from './task-column'
import { TaskCard } from './task-card'
import type { Task } from '@/app/tasks/page'

interface TaskBoardProps {
  tasks: Task[]
  filters: {
    status: string
    priority: string
    agent: string
    search: string
  }
  onTaskUpdate: (task: Task) => void
  onTaskMove: (taskId: string, newStatus: Task['status']) => void
}

const columns = [
  { id: 'todo', title: 'To Do', status: 'todo' as const },
  { id: 'in_progress', title: 'In Progress', status: 'in_progress' as const },
  { id: 'review', title: 'Review', status: 'review' as const },
  { id: 'done', title: 'Done', status: 'done' as const },
]

export function TaskBoard({ tasks, filters, onTaskUpdate, onTaskMove }: TaskBoardProps) {
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([])
  const [activeTask, setActiveTask] = useState<Task | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // Filter tasks based on filters
  useEffect(() => {
    let filtered = tasks

    if (filters.status !== 'all') {
      filtered = filtered.filter(task => task.status === filters.status)
    }

    if (filters.priority !== 'all') {
      filtered = filtered.filter(task => task.priority === filters.priority)
    }

    if (filters.agent !== 'all') {
      filtered = filtered.filter(task => task.agent === filters.agent)
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(searchLower) ||
        task.description.toLowerCase().includes(searchLower) ||
        task.tags.some(tag => tag.toLowerCase().includes(searchLower))
      )
    }

    setFilteredTasks(filtered)
  }, [tasks, filters])

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const task = tasks.find(t => t.id === active.id)
    setActiveTask(task || null)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (!over) {
      setActiveTask(null)
      return
    }

    const taskId = active.id as string
    const overId = over.id as string

    // Check if dropped on a column
    const column = columns.find(col => col.id === overId)
    if (column) {
      onTaskMove(taskId, column.status)
    }

    setActiveTask(null)
  }

  const getTasksByStatus = (status: Task['status']) => {
    return filteredTasks.filter(task => task.status === status)
  }

  const getColumnStats = (status: Task['status']) => {
    const columnTasks = getTasksByStatus(status)
    return {
      total: columnTasks.length,
      highPriority: columnTasks.filter(task => task.priority === 'high').length,
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {columns.map((column) => {
            const columnTasks = getTasksByStatus(column.status)
            const stats = getColumnStats(column.status)

            return (
              <TaskColumn
                key={column.id}
                id={column.id}
                title={column.title}
                count={stats.total}
                highPriorityCount={stats.highPriority}
                status={column.status}
              >
                <SortableContext
                  items={columnTasks.map(task => task.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-3">
                    {columnTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onUpdate={onTaskUpdate}
                      />
                    ))}
                  </div>
                </SortableContext>
              </TaskColumn>
            )
          })}
        </div>

        <DragOverlay>
          {activeTask ? (
            <TaskCard task={activeTask} onUpdate={onTaskUpdate} isDragging />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}