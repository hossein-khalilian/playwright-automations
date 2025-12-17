'use client';

import { useState } from 'react';
import { useTasks } from '@/contexts/TaskContext';

export default function TaskStatusPanel() {
  const { tasks, pendingCount, clearCompleted } = useTasks();
  const [open, setOpen] = useState(false);

  if (tasks.length === 0) {
    return null;
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center rounded-md border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        title="View background tasks"
      >
        <span className="mr-1">Tasks</span>
        {pendingCount > 0 && (
          <span className="inline-flex items-center justify-center rounded-full bg-indigo-600 px-1.5 text-[10px] font-semibold text-white">
            {pendingCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <span className="text-xs font-semibold text-gray-700">Background tasks</span>
            <button
              type="button"
              onClick={clearCompleted}
              className="text-[11px] text-gray-500 hover:text-gray-700"
            >
              Clear completed
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {tasks.map((task) => (
              <div key={task.id} className="border-b px-3 py-2 last:border-b-0">
                <div className="flex items-center justify-between">
                  <div className="mr-2 flex-1">
                    <div className="text-xs font-medium text-gray-900">
                      {task.label || task.type || 'NotebookLM task'}
                    </div>
                    {task.message && task.status === 'success' && (
                      <div className="mt-0.5 text-[11px] text-gray-500 line-clamp-2">
                        {task.message}
                      </div>
                    )}
                    {task.errorMessage && task.status === 'failure' && (
                      <div className="mt-0.5 text-[11px] text-red-600 line-clamp-3">
                        {task.errorMessage}
                      </div>
                    )}
                  </div>
                  <span
                    className={`ml-1 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      task.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : task.status === 'success'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {task.status === 'pending'
                      ? 'Pending'
                      : task.status === 'success'
                      ? 'Success'
                      : 'Failed'}
                  </span>
                </div>
                {task.notebookId && (
                  <div className="mt-0.5 text-[10px] text-gray-400">
                    Notebook: {task.notebookId}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}




