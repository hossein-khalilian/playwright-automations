'use client';

import { useState } from 'react';
import { useTasks } from '@/contexts/TaskContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function TaskStatusPanel() {
  const { tasks, pendingCount, clearCompleted } = useTasks();
  const [open, setOpen] = useState(false);

  if (tasks.length === 0) {
    return null;
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" title="View background tasks">
          Tasks
          {pendingCount > 0 && (
            <Badge variant="default" className="ml-1">
              {pendingCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-2 py-1.5">
          <DropdownMenuLabel className="text-xs">Background tasks</DropdownMenuLabel>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.preventDefault();
              clearCompleted();
            }}
            className="h-auto px-2 py-1 text-[11px]"
          >
            Clear completed
          </Button>
        </div>
        <DropdownMenuSeparator />
        <div className="max-h-80 overflow-y-auto">
          {tasks.map((task) => (
            <DropdownMenuItem key={task.id} className="block p-0" onSelect={(e) => e.preventDefault()}>
              <div className="w-full border-b px-3 py-2 last:border-b-0">
                <div className="flex items-center justify-between">
                  <div className="mr-2 flex-1">
                    <div className="text-xs font-medium text-foreground">
                      {task.label || task.type || 'NotebookLM task'}
                    </div>
                    {task.message && task.status === 'success' && (
                      <div className="mt-0.5 text-[11px] text-muted-foreground line-clamp-2">
                        {task.message}
                      </div>
                    )}
                    {task.errorMessage && task.status === 'failure' && (
                      <div className="mt-0.5 text-[11px] text-destructive line-clamp-3">
                        {task.errorMessage}
                      </div>
                    )}
                  </div>
                  <Badge
                    variant={
                      task.status === 'pending'
                        ? 'secondary'
                        : task.status === 'success'
                        ? 'default'
                        : 'destructive'
                    }
                    className="ml-1 text-[10px]"
                  >
                    {task.status === 'pending'
                      ? 'Pending'
                      : task.status === 'success'
                      ? 'Success'
                      : 'Failed'}
                  </Badge>
                </div>
                {task.notebookId && (
                  <div className="mt-0.5 text-[10px] text-muted-foreground">
                    Notebook: {task.notebookId}
                  </div>
                )}
              </div>
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}




