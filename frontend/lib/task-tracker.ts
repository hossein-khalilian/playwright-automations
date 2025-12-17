export type TrackedTaskStatus = 'pending' | 'success' | 'failure';

export interface TrackedTaskMeta {
  label?: string;
  type?: string;
  notebookId?: string;
}

export interface TrackedTask extends TrackedTaskMeta {
  id: string;
  status: TrackedTaskStatus;
  message?: string | null;
  errorMessage?: string | null;
  createdAt: number;
  updatedAt: number;
}

type Listener = (tasks: TrackedTask[]) => void;

let tasks: TrackedTask[] = [];
const listeners = new Set<Listener>();

function notify() {
  for (const listener of listeners) {
    listener([...tasks]);
  }
}

export function subscribeToTasks(listener: Listener): () => void {
  listeners.add(listener);
  // Emit current state immediately
  listener([...tasks]);
  return () => {
    listeners.delete(listener);
  };
}

export function trackTaskStart(id: string, meta?: TrackedTaskMeta) {
  const now = Date.now();
  const existing = tasks.find((t) => t.id === id);
  if (existing) {
    existing.status = 'pending';
    existing.updatedAt = now;
    existing.message = null;
    existing.errorMessage = null;
    Object.assign(existing, meta || {});
  } else {
    tasks = [
      {
        id,
        status: 'pending',
        createdAt: now,
        updatedAt: now,
        message: null,
        errorMessage: null,
        ...(meta || {}),
      },
      ...tasks,
    ];
  }
  notify();
}

export function trackTaskSuccess(id: string, message?: string | null) {
  const now = Date.now();
  const task = tasks.find((t) => t.id === id);
  if (task) {
    task.status = 'success';
    task.updatedAt = now;
    task.message = message ?? task.message ?? null;
    task.errorMessage = null;
  }
  notify();
}

export function trackTaskFailure(id: string, errorMessage?: string | null) {
  const now = Date.now();
  const task = tasks.find((t) => t.id === id);
  if (task) {
    task.status = 'failure';
    task.updatedAt = now;
    task.errorMessage = errorMessage ?? task.errorMessage ?? null;
  }
  notify();
}

export function clearCompletedTasks() {
  tasks = tasks.filter((t) => t.status === 'pending');
  notify();
}




