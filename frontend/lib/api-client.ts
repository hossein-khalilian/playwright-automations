import api from './api';
import { retryWithBackoff } from './retry';
import type {
  LoginRequest,
  RegisterRequest,
  Token,
  RegisterResponse,
  NotebookListResponse,
  NotebookCreateResponse,
  SourceListResponse,
  SourceUploadResponse,
  SourceReviewResponse,
  SourceRenameRequest,
  ChatHistoryResponse,
  NotebookQueryRequest,
  NotebookQueryResponse,
  ArtifactListResponse,
  AudioOverviewCreateRequest,
  AudioOverviewCreateResponse,
  VideoOverviewCreateRequest,
  VideoOverviewCreateResponse,
  FlashcardCreateRequest,
  FlashcardCreateResponse,
  QuizCreateRequest,
  QuizCreateResponse,
  InfographicCreateRequest,
  InfographicCreateResponse,
  SlideDeckCreateRequest,
  SlideDeckCreateResponse,
  ReportCreateRequest,
  ReportCreateResponse,
  GoogleLoginStatusResponse,
} from './types';

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
};

// Notebook API
export const notebookApi = {
  list: async (): Promise<NotebookListResponse> => {
    const response = await api.get<NotebookListResponse>('/notebooklm/notebooks');
    return response.data;
  },

  create: async (): Promise<NotebookCreateResponse> => {
    const response = await api.post<NotebookCreateResponse>('/notebooklm/notebooks');
    return response.data;
  },

  delete: async (notebookId: string): Promise<{ status: string; message: string }> => {
    const response = await api.delete(`/notebooklm/notebooks/${notebookId}`);
    return response.data;
  },
};

// Source API
export const sourceApi = {
  list: async (notebookId: string): Promise<SourceListResponse> => {
    return retryWithBackoff(async () => {
      const response = await api.get<SourceListResponse>(
        `/notebooklm/notebooks/${notebookId}/sources`
      );
      return response.data;
    });
  },

  upload: async (
    notebookId: string,
    file: File
  ): Promise<SourceUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<SourceUploadResponse>(
      `/notebooklm/notebooks/${notebookId}/sources`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  delete: async (
    notebookId: string,
    sourceName: string
  ): Promise<{ status: string; message: string }> => {
    const response = await api.delete(
      `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}`
    );
    return response.data;
  },

  rename: async (
    notebookId: string,
    sourceName: string,
    newName: string
  ): Promise<{ status: string; message: string }> => {
    const response = await api.put(
      `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}/rename`,
      { new_name: newName } as SourceRenameRequest
    );
    return response.data;
  },

  review: async (notebookId: string, sourceName: string): Promise<SourceReviewResponse> => {
    return retryWithBackoff(async () => {
      const response = await api.get<SourceReviewResponse>(
        `/notebooklm/notebooks/${notebookId}/sources/${encodeURIComponent(sourceName)}/review`
      );
      return response.data;
    });
  },
};

// Chat API
export const chatApi = {
  getHistory: async (notebookId: string): Promise<ChatHistoryResponse> => {
    return retryWithBackoff(async () => {
      const response = await api.get<ChatHistoryResponse>(
        `/notebooklm/notebooks/${notebookId}/chat`
      );
      return response.data;
    });
  },

  query: async (
    notebookId: string,
    query: string
  ): Promise<NotebookQueryResponse> => {
    return retryWithBackoff(async () => {
      const response = await api.post<NotebookQueryResponse>(
        `/notebooklm/notebooks/${notebookId}/query`,
        { query } as NotebookQueryRequest
      );
      return response.data;
    }, {
      maxRetries: 2, // Fewer retries for user-initiated actions
      initialDelay: 2000, // Longer initial delay for queries
    });
  },

  deleteHistory: async (notebookId: string): Promise<{ status: string; message: string }> => {
    const response = await api.delete(`/notebooklm/notebooks/${notebookId}/chat`);
    return response.data;
  },
};

// Artifact API
export const artifactApi = {
  list: async (notebookId: string): Promise<ArtifactListResponse> => {
    return retryWithBackoff(async () => {
      const response = await api.get<ArtifactListResponse>(
        `/notebooklm/notebooks/${notebookId}/artifacts`
      );
      return response.data;
    });
  },

  delete: async (
    notebookId: string,
    artifactName: string
  ): Promise<{ status: string; message: string }> => {
    const response = await api.delete(
      `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}`
    );
    return response.data;
  },

  rename: async (
    notebookId: string,
    artifactName: string,
    newName: string
  ): Promise<{ status: string; message: string }> => {
    const response = await api.put(
      `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}/rename`,
      { new_name: newName }
    );
    return response.data;
  },

  download: async (notebookId: string, artifactName: string): Promise<Blob> => {
    return retryWithBackoff(async () => {
      const response = await api.get(
        `/notebooklm/notebooks/${notebookId}/artifacts/${encodeURIComponent(artifactName)}/download`,
        { responseType: 'blob' }
      );
      return response.data;
    });
  },

  createAudioOverview: async (
    notebookId: string,
    data: AudioOverviewCreateRequest
  ): Promise<AudioOverviewCreateResponse> => {
    const response = await api.post<AudioOverviewCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/audio-overview`,
      data
    );
    return response.data;
  },

  createVideoOverview: async (
    notebookId: string,
    data: VideoOverviewCreateRequest
  ): Promise<VideoOverviewCreateResponse> => {
    const response = await api.post<VideoOverviewCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/video-overview`,
      data
    );
    return response.data;
  },

  createFlashcards: async (
    notebookId: string,
    data: FlashcardCreateRequest
  ): Promise<FlashcardCreateResponse> => {
    const response = await api.post<FlashcardCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/flashcards`,
      data
    );
    return response.data;
  },

  createQuiz: async (
    notebookId: string,
    data: QuizCreateRequest
  ): Promise<QuizCreateResponse> => {
    const response = await api.post<QuizCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/quiz`,
      data
    );
    return response.data;
  },

  createInfographic: async (
    notebookId: string,
    data: InfographicCreateRequest
  ): Promise<InfographicCreateResponse> => {
    const response = await api.post<InfographicCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/infographic`,
      data
    );
    return response.data;
  },

  createSlideDeck: async (
    notebookId: string,
    data: SlideDeckCreateRequest
  ): Promise<SlideDeckCreateResponse> => {
    const response = await api.post<SlideDeckCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/slide-deck`,
      data
    );
    return response.data;
  },

  createReport: async (
    notebookId: string,
    data: ReportCreateRequest
  ): Promise<ReportCreateResponse> => {
    const response = await api.post<ReportCreateResponse>(
      `/notebooklm/notebooks/${notebookId}/report`,
      data
    );
    return response.data;
  },
};

// Google API
export const googleApi = {
  getLoginStatus: async (): Promise<GoogleLoginStatusResponse> => {
    const response = await api.get<GoogleLoginStatusResponse>('/google/login-status');
    return response.data;
  },
};

