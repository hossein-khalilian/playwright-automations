import api from './api';
import { retryWithBackoff } from './retry';
import {
  clearCompletedTasks,
  trackTaskFailure,
  trackTaskStart,
  trackTaskSuccess,
  type TrackedTaskMeta,
} from './task-tracker';
import type {
  ArtifactListResponse,
  AudioOverviewCreateRequest,
  ChatHistoryResponse,
  FlashcardCreateRequest,
  GoogleLoginStatusResponse,
  InfographicCreateRequest,
  LoginRequest,
  MindmapCreateRequest,
  NotebookCreateResponse,
  NotebookListResponse,
  NotebookQueryRequest,
  NotebookQueryResponse,
  NotebookRenameRequest,
  NotebookRenameResponse,
  QuizCreateRequest,
  RegisterRequest,
  RegisterResponse,
  ReportCreateRequest,
  SlideDeckCreateRequest,
  SourceListResponse,
  SourceRenameRequest,
  SourceUploadResponse,
  Token,
  VideoOverviewCreateRequest,
  AudioOverviewCreateResponse,
  VideoOverviewCreateResponse,
  FlashcardCreateResponse,
  QuizCreateResponse,
  InfographicCreateResponse,
  SlideDeckCreateResponse,
  ReportCreateResponse,
  MindmapCreateResponse,
  SourceReviewResponse,
  TaskSubmissionResponse,
  TaskStatusResponse,
  UrlSourceAddRequest,
} from './types';

type TaskWaitOptions = {
  pollIntervalMs?: number;
  maxAttempts?: number;
};

const DEFAULT_TASK_OPTIONS: Required<TaskWaitOptions> = {
  pollIntervalMs: 2000,
  maxAttempts: 120,
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const ensureResult = <T>(status: TaskStatusResponse<T>): T => {
  if (status.result !== undefined && status.result !== null) {
    return status.result as T;
  }
  throw new Error(status.message || 'Task completed without a result payload.');
};

async function waitForTaskResult<T = any>(
  taskId: string,
  options: TaskWaitOptions = {}
): Promise<TaskStatusResponse<T>> {
  const { pollIntervalMs, maxAttempts } = { ...DEFAULT_TASK_OPTIONS, ...options };
  let lastStatus: TaskStatusResponse<T> | null = null;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const { data } = await api.get<TaskStatusResponse<T>>(`/notebooklm/tasks/${taskId}`);
    lastStatus = data;

    if (data.status === 'success') {
      return data;
    }

    if (data.status === 'failure') {
      throw new Error(data.message || 'Task failed');
    }

    await sleep(pollIntervalMs);
  }

  throw new Error(
    lastStatus?.message || 'Task is still pending. Please try again in a moment.'
  );
}

async function submitTask<T = any>(
  submitFn: () => Promise<TaskSubmissionResponse>,
  options?: TaskWaitOptions,
  meta?: TrackedTaskMeta
): Promise<TaskStatusResponse<T>> {
  const submission = await submitFn();
  if (!submission?.task_id) {
    throw new Error('Task submission did not return a task_id');
  }
  const taskId = submission.task_id;

  // Track task lifecycle for UI.
  trackTaskStart(taskId, meta);

  try {
    const status = await waitForTaskResult<T>(taskId, options);
    trackTaskSuccess(taskId, status.message);
    return status;
  } catch (error: any) {
    const errorMessage =
      error?.response?.data?.detail || error?.message || 'Task failed';
    trackTaskFailure(taskId, errorMessage);
    throw error;
  }
}

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await api.post<RegisterResponse>('/auth/register', data);
    return response.data;
  },

  getMe: async (): Promise<string> => {
    const response = await api.get<string>('/auth/me');
    return response.data;
  },

  adminTest: async (): Promise<{ message: string; username: string; role: string }> => {
    const response = await api.get<{ message: string; username: string; role: string }>('/auth/admin/test');
    return response.data;
  },
};

// Notebook API
export const notebookApi = {
  list: async (): Promise<NotebookListResponse> => {
    const response = await api.get<NotebookListResponse>('/notebooklm/notebooks');
    return response.data;
  },

  create: async (): Promise<TaskStatusResponse<NotebookCreateResponse>> => {
    return submitTask<NotebookCreateResponse>(
      () =>
        api
          .post<TaskSubmissionResponse>('/notebooklm/notebooks')
          .then((res) => res.data),
      undefined,
      { label: 'Create notebook', type: 'notebook.create' }
    );
  },

  rename: async (
    notebookId: string,
    newTitle: string
  ): Promise<TaskStatusResponse<NotebookRenameResponse>> => {
    return submitTask<NotebookRenameResponse>(
      () =>
        api
          .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/rename`, {
            new_title: newTitle,
          } as NotebookRenameRequest)
          .then((res) => res.data),
      undefined,
      { label: 'Rename notebook', type: 'notebook.rename', notebookId }
    );
  },

  delete: async (
    notebookId: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(
      () =>
        api
          .delete<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}`)
          .then((res) => res.data)
      ,
      undefined,
      { label: 'Delete notebook', type: 'notebook.delete', notebookId }
    );
  },
};

// Source API
export const sourceApi = {
  list: async (notebookId: string): Promise<SourceListResponse> => {
    const status = await retryWithBackoff(() =>
      submitTask<SourceListResponse>(() =>
        api
          .get<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/sources`)
          .then((res) => res.data)
        ,
        undefined,
        { label: 'List sources', type: 'source.list', notebookId }
      )
    );
    return ensureResult(status);
  },

  upload: async (notebookId: string, file: File): Promise<TaskStatusResponse<SourceUploadResponse>> => {
    const formData = new FormData();
    formData.append('file', file);
    return submitTask<SourceUploadResponse>(() =>
      api
        .post<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/sources/upload`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
          }
        )
        .then((res) => res.data),
      undefined,
      { label: `Upload source: ${file.name}`, type: 'source.upload', notebookId }
    );
  },

  addUrls: async (
    notebookId: string,
    urls: string
  ): Promise<TaskStatusResponse<SourceUploadResponse>> => {
    return submitTask<SourceUploadResponse>(() =>
      api
        .post<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/sources/urls`,
          { urls } as UrlSourceAddRequest
        )
        .then((res) => res.data),
      undefined,
      { label: 'Add URL sources', type: 'source.add_urls', notebookId }
    );
  },

  delete: async (
    notebookId: string,
    sourceName: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(() =>
      api
        .delete<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}`
        )
        .then((res) => res.data),
      undefined,
      { label: `Delete source: ${sourceName}`, type: 'source.delete', notebookId }
    );
  },

  rename: async (
    notebookId: string,
    sourceName: string,
    newName: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(() =>
      api
        .post<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}/rename`,
          { new_name: newName } as SourceRenameRequest
        )
        .then((res) => res.data),
      undefined,
      { label: `Rename source: ${sourceName}`, type: 'source.rename', notebookId }
    );
  },

  review: async (
    notebookId: string,
    sourceName: string
  ): Promise<TaskStatusResponse<SourceReviewResponse>> => {
    return submitTask<SourceReviewResponse>(() =>
      api
        .post<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}/review`
        )
        .then((res) => res.data),
      undefined,
      { label: `Review source: ${sourceName}`, type: 'source.review', notebookId }
    );
  },
};

// Chat API
export const chatApi = {
  getHistory: async (notebookId: string): Promise<ChatHistoryResponse> => {
    const status = await retryWithBackoff(() =>
      submitTask<ChatHistoryResponse>(() =>
        api
          .get<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/chat`)
          .then((res) => res.data)
        ,
        undefined,
        { label: 'Load chat history', type: 'chat.history', notebookId }
      )
    );
    return ensureResult(status);
  },

  query: async (
    notebookId: string,
    query: string
  ): Promise<TaskStatusResponse<NotebookQueryResponse>> => {
    return submitTask<NotebookQueryResponse>(
      () =>
        api
          .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/query`, {
            query,
          } as NotebookQueryRequest)
          .then((res) => res.data),
      {
        pollIntervalMs: 2000,
        maxAttempts: 80,
      },
      { label: 'Notebook query', type: 'chat.query', notebookId }
    );
  },

  deleteHistory: async (
    notebookId: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(() =>
      api
        .delete<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/chat`)
        .then((res) => res.data),
      undefined,
      { label: 'Delete chat history', type: 'chat.delete', notebookId }
    );
  },
};

// Artifact API
export const artifactApi = {
  list: async (notebookId: string): Promise<ArtifactListResponse> => {
    const status = await retryWithBackoff(() =>
      submitTask<ArtifactListResponse>(() =>
        api
          .get<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/artifacts`)
          .then((res) => res.data)
        ,
        undefined,
        { label: 'List artifacts', type: 'artifact.list', notebookId }
      )
    );
    const result = ensureResult(status);
    return {
      ...result,
      artifacts: (result.artifacts || []).map((artifact: any) => ({
        is_generating: Boolean(artifact.is_generating),
        ...artifact,
      })),
    };
  },

  delete: async (
    notebookId: string,
    artifactName: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(() =>
      api
        .delete<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}`
        )
        .then((res) => res.data),
      undefined,
      { label: `Delete artifact: ${artifactName}`, type: 'artifact.delete', notebookId }
    );
  },

  rename: async (
    notebookId: string,
    artifactName: string,
    newName: string
  ): Promise<TaskStatusResponse<{ status: string; message: string }>> => {
    return submitTask(() =>
      api
        .post<TaskSubmissionResponse>(
          `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}/rename`,
          { new_name: newName }
        )
        .then((res) => res.data),
      undefined,
      { label: `Rename artifact: ${artifactName}`, type: 'artifact.rename', notebookId }
    );
  },

  download: async (
    notebookId: string,
    artifactName: string
  ): Promise<void> => {
    // Download the file directly
    const response = await api.post(
      `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}/download`,
      {},
      {
        responseType: 'blob', // Important: tell axios to handle binary data
        headers: {
          'Content-Type': undefined, // Let browser set Content-Type for file download
        },
      }
    );
    
    // Get filename from Content-Disposition header or use artifact name
    let filename = artifactName;
    const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
    
    if (contentDisposition) {
      // Try multiple patterns to extract filename
      // Pattern 1: filename="value" or filename='value'
      let filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '').trim();
      } else {
        // Pattern 2: filename*=UTF-8''value (RFC 5987)
        filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          try {
            filename = decodeURIComponent(filenameMatch[1]);
          } catch (e) {
            // If decoding fails, use as-is
            filename = filenameMatch[1];
          }
        } else {
          // Pattern 3: filename=value (without quotes)
          filenameMatch = contentDisposition.match(/filename=([^;\n]+)/);
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].trim();
          }
        }
      }
    }
    
    // Clean up filename (remove any URL encoding, extra spaces, etc.)
    filename = filename.trim();
    
    // Ensure filename has an extension
    if (!filename.includes('.')) {
      // Try to get extension from Content-Type or default based on type
      const contentType = response.headers['content-type'] || response.headers['Content-Type'] || '';
      if (contentType.includes('csv') || contentType.includes('text/csv')) {
        filename = `${filename}.csv`;
      } else if (contentType.includes('png')) {
        filename = `${filename}.png`;
      } else if (contentType.includes('jpeg') || contentType.includes('jpg')) {
        filename = `${filename}.jpg`;
      } else if (contentType.includes('pdf')) {
        filename = `${filename}.pdf`;
      } else if (contentType.includes('mp4')) {
        filename = `${filename}.mp4`;
      } else if (contentType.includes('mpeg') || contentType.includes('mp3')) {
        filename = `${filename}.mp3`;
      } else if (contentType.includes('json')) {
        filename = `${filename}.json`;
      } else if (contentType.includes('text/plain')) {
        filename = `${filename}.txt`;
      } else {
        filename = `${filename}.png`; // Default to PNG for images
      }
    }
    
    // Remove any path separators that might have been included
    filename = filename.split('/').pop() || filename;
    filename = filename.split('\\').pop() || filename;
    
    // Create a blob URL and trigger download
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  createAudioOverview: async (
    notebookId: string,
    data: AudioOverviewCreateRequest
  ): Promise<TaskStatusResponse<AudioOverviewCreateResponse>> => {
    return submitTask<AudioOverviewCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/audio_overview`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Audio Overview', type: 'artifact.audio_overview', notebookId }
    );
  },

  createVideoOverview: async (
    notebookId: string,
    data: VideoOverviewCreateRequest
  ): Promise<TaskStatusResponse<VideoOverviewCreateResponse>> => {
    return submitTask<VideoOverviewCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/video_overview`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Video Overview', type: 'artifact.video_overview', notebookId }
    );
  },

  createFlashcards: async (
    notebookId: string,
    data: FlashcardCreateRequest
  ): Promise<TaskStatusResponse<FlashcardCreateResponse>> => {
    return submitTask<FlashcardCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/flashcards`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Flashcards', type: 'artifact.flashcards', notebookId }
    );
  },

  createQuiz: async (
    notebookId: string,
    data: QuizCreateRequest
  ): Promise<TaskStatusResponse<QuizCreateResponse>> => {
    return submitTask<QuizCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/quiz`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Quiz', type: 'artifact.quiz', notebookId }
    );
  },

  createInfographic: async (
    notebookId: string,
    data: InfographicCreateRequest
  ): Promise<TaskStatusResponse<InfographicCreateResponse>> => {
    return submitTask<InfographicCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/infographic`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Infographic', type: 'artifact.infographic', notebookId }
    );
  },

  createSlideDeck: async (
    notebookId: string,
    data: SlideDeckCreateRequest
  ): Promise<TaskStatusResponse<SlideDeckCreateResponse>> => {
    return submitTask<SlideDeckCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/slide_deck`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Slide Deck', type: 'artifact.slide_deck', notebookId }
    );
  },

  createReport: async (
    notebookId: string,
    data: ReportCreateRequest
  ): Promise<TaskStatusResponse<ReportCreateResponse>> => {
    return submitTask<ReportCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/report`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Report', type: 'artifact.report', notebookId }
    );
  },

  createMindmap: async (
    notebookId: string,
    data: MindmapCreateRequest
  ): Promise<TaskStatusResponse<MindmapCreateResponse>> => {
    return submitTask<MindmapCreateResponse>(() =>
      api
        .post<TaskSubmissionResponse>(`/notebooklm/notebooks/${notebookId}/mindmap`, data)
        .then((res) => res.data),
      undefined,
      { label: 'Create Mind Map', type: 'artifact.mindmap', notebookId }
    );
  },
};

// Google API
export const googleApi = {
  getLoginStatus: async (): Promise<GoogleLoginStatusResponse> => {
    const response = await api.get<GoogleLoginStatusResponse>('/google/login-status');
    return response.data;
  },
};

// Admin API
import type {
  GoogleCredential,
  GoogleCredentialCreateRequest,
  GoogleCredentialCreateResponse,
  GoogleCredentialDeleteResponse,
  GoogleCredentialListResponse,
  GoogleCredentialUpdateRequest,
  GoogleCredentialUpdateResponse,
} from './types';

export const adminApi = {
  listGoogleCredentials: async (): Promise<GoogleCredentialListResponse> => {
    const response = await api.get<GoogleCredentialListResponse>('/admin/google-credentials');
    return response.data;
  },

  createGoogleCredential: async (
    data: GoogleCredentialCreateRequest
  ): Promise<GoogleCredentialCreateResponse> => {
    const response = await api.post<GoogleCredentialCreateResponse>(
      '/admin/google-credentials',
      data
    );
    return response.data;
  },

  updateGoogleCredential: async (
    email: string,
    data: GoogleCredentialUpdateRequest
  ): Promise<GoogleCredentialUpdateResponse> => {
    const response = await api.put<GoogleCredentialUpdateResponse>(
      `/admin/google-credentials/${encodeURIComponent(email)}`,
      data
    );
    return response.data;
  },

  deleteGoogleCredential: async (email: string): Promise<GoogleCredentialDeleteResponse> => {
    const response = await api.delete<GoogleCredentialDeleteResponse>(
      `/admin/google-credentials/${encodeURIComponent(email)}`
    );
    return response.data;
  },
};

