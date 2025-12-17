// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  message: string;
  username: string;
}

// Task / Celery types
export interface TaskSubmissionResponse {
  task_id: string;
  status: string;
}

export interface TaskStatusResponse<T = any> {
  task_id: string;
  state: string;
  status: 'pending' | 'success' | 'failure' | string;
  message?: string;
  result?: T;
}

// Notebook types
export interface Notebook {
  notebook_id: string;
  notebook_url: string;
  created_at: string;
  email?: string;
}

export interface NotebookListResponse {
  notebooks: Notebook[];
}

export interface NotebookCreateResponse {
  status: string;
  message: string;
  notebook_url?: string;
  notebook_id?: string;
}

// Source types
export interface Source {
  name: string;
  status: string;
}

export interface SourceListResponse {
  status: string;
  message: string;
  sources: Source[];
}

export interface SourceUploadResponse {
  status: string;
  message: string;
}

export interface SourceReviewResponse {
  status: string;
  message: string;
  title?: string;
  summary?: string;
  key_topics: string[];
  content?: string;
  images: Array<{
    base64?: string;
    mime_type?: string;
  }>;
}

export interface SourceRenameRequest {
  new_name: string;
}

export interface UrlSourceAddRequest {
  urls: string;
}

// Chat types
export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatHistoryResponse {
  status: string;
  message: string;
  messages: ChatMessage[];
}

export interface NotebookQueryRequest {
  query: string;
}

export interface NotebookQueryResponse {
  status: string;
  message: string;
  query: string;
}

// Artifact types
export interface ArtifactInfo {
  type?: string;
  name?: string;
  details?: string;
  status: string;
  is_generating: boolean;
  has_play: boolean;
  has_interactive: boolean;
}

export interface ArtifactListResponse {
  status: string;
  message: string;
  artifacts: ArtifactInfo[];
}

// Audio Overview types
export type AudioFormat = 'Deep Dive' | 'Brief' | 'Critique' | 'Debate';
export type AudioLanguage = 'english' | 'persian';

export interface AudioOverviewCreateRequest {
  audio_format?: AudioFormat;
  language?: AudioLanguage;
  length?: string;
  focus_text?: string;
}

export interface AudioOverviewCreateResponse {
  status: string;
  message: string;
}

// Video Overview types
export type VideoFormat = 'Explainer' | 'Brief';
export type VideoVisualStyle =
  | 'Auto-select'
  | 'Custom'
  | 'Classic'
  | 'Whiteboard'
  | 'Kawaii'
  | 'Anime'
  | 'Watercolor'
  | 'Retro print'
  | 'Heritage'
  | 'Paper-craft';

export interface VideoOverviewCreateRequest {
  video_format?: VideoFormat;
  language?: AudioLanguage;
  visual_style?: VideoVisualStyle;
  custom_style_description?: string;
  focus_text?: string;
}

export interface VideoOverviewCreateResponse {
  status: string;
  message: string;
}

// Flashcard types
export type FlashcardCardCount = 'Fewer' | 'Standard' | 'More';
export type FlashcardDifficulty = 'Easy' | 'Medium' | 'Hard';

export interface FlashcardCreateRequest {
  card_count?: FlashcardCardCount;
  difficulty?: FlashcardDifficulty;
  topic?: string;
}

export interface FlashcardCreateResponse {
  status: string;
  message: string;
}

// Quiz types
export type QuizQuestionCount = 'Fewer' | 'Standard' | 'More';

export interface QuizCreateRequest {
  question_count?: QuizQuestionCount;
  difficulty?: FlashcardDifficulty;
  topic?: string;
}

export interface QuizCreateResponse {
  status: string;
  message: string;
}

// Infographic types
export type InfographicOrientation = 'Landscape' | 'Portrait' | 'Square';
export type InfographicDetailLevel = 'Concise' | 'Standard' | 'Detailed BETA';

export interface InfographicCreateRequest {
  language?: AudioLanguage;
  orientation?: InfographicOrientation;
  detail_level?: InfographicDetailLevel;
  description?: string;
}

export interface InfographicCreateResponse {
  status: string;
  message: string;
}

// Slide Deck types
export type SlideDeckFormat = 'Detailed Deck' | 'Presenter Slides';
export type SlideDeckLength = 'Short' | 'Default';

export interface SlideDeckCreateRequest {
  format?: SlideDeckFormat;
  length?: SlideDeckLength;
  language?: AudioLanguage;
  description?: string;
}

export interface SlideDeckCreateResponse {
  status: string;
  message: string;
}

// Report types
export type ReportFormat = 'Create Your Own' | 'Briefing Doc' | 'Study Guide' | 'Blog Post' | 'Design Document' | 'Strategy Memo' | 'Concept Explainer' | 'Comparative Overview';

export interface ReportCreateRequest {
  format?: ReportFormat;
  language?: AudioLanguage;
  description?: string;
}

export interface ReportCreateResponse {
  status: string;
  message: string;
}

// Mindmap types
export interface MindmapCreateRequest {
  // No optional parameters for mindmap
}

export interface MindmapCreateResponse {
  status: string;
  message: string;
}

// Google types
export interface GoogleLoginStatusResponse {
  is_logged_in: boolean;
}

