'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  clearCompletedTasks,
  subscribeToTasks,
  type TrackedTask,
} from '@/lib/task-tracker';

interface TaskContextValue {
  tasks: TrackedTask[];
  pendingCount: number;
  clearCompleted: () => void;
}

const TaskContext = createContext<TaskContextValue | undefined>(undefined);

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const [tasks, setTasks] = useState<TrackedTask[]>([]);

  useEffect(() => {
    const unsubscribe = subscribeToTasks(setTasks);
    return () => unsubscribe();
  }, []);

  const pendingCount = tasks.filter((t) => t.status === 'pending').length;

  const value: TaskContextValue = {
    tasks,
    pendingCount,
    clearCompleted: clearCompletedTasks,
  };

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
}

export function useTasks(): TaskContextValue {
  const ctx = useContext(TaskContext);
  if (!ctx) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return ctx;
}




