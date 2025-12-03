'use client';

import { useState } from 'react';
import { artifactApi } from '@/lib/api-client';
import type {
  AudioOverviewCreateRequest,
  VideoOverviewCreateRequest,
  FlashcardCreateRequest,
  QuizCreateRequest,
  InfographicCreateRequest,
  SlideDeckCreateRequest,
  ReportCreateRequest,
  MindmapCreateRequest,
} from '@/lib/types';

interface ArtifactCreateModalProps {
  notebookId: string;
  artifactType: string;
  onClose: () => void;
}

export default function ArtifactCreateModal({
  notebookId,
  artifactType,
  onClose,
}: ArtifactCreateModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state based on artifact type
  const [audioFormat, setAudioFormat] = useState<string>('');
  const [videoFormat, setVideoFormat] = useState<string>('');
  const [language, setLanguage] = useState<string>('');
  const [length, setLength] = useState<string>('');
  const [visualStyle, setVisualStyle] = useState<string>('');
  const [customStyleDescription, setCustomStyleDescription] = useState('');
  const [cardCount, setCardCount] = useState<string>('');
  const [questionCount, setQuestionCount] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('');
  const [orientation, setOrientation] = useState<string>('');
  const [detailLevel, setDetailLevel] = useState<string>('');
  const [slideDeckFormat, setSlideDeckFormat] = useState<string>('');
  const [slideDeckLength, setSlideDeckLength] = useState<string>('');
  const [reportFormat, setReportFormat] = useState<string>('');
  const [focusText, setFocusText] = useState('');
  const [topic, setTopic] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      switch (artifactType) {
        case 'audio-overview': {
          const data: AudioOverviewCreateRequest = {
            audio_format: audioFormat as any,
            language: language as any,
            length: length || undefined,
            focus_text: focusText || undefined,
          };
          await artifactApi.createAudioOverview(notebookId, data);
          break;
        }
        case 'video-overview': {
          const data: VideoOverviewCreateRequest = {
            video_format: videoFormat as any,
            language: language as any,
            visual_style: visualStyle as any,
            custom_style_description: customStyleDescription || undefined,
            focus_text: focusText || undefined,
          };
          await artifactApi.createVideoOverview(notebookId, data);
          break;
        }
        case 'flashcards': {
          const data: FlashcardCreateRequest = {
            card_count: cardCount as any,
            difficulty: difficulty as any,
            topic: topic || undefined,
          };
          await artifactApi.createFlashcards(notebookId, data);
          break;
        }
        case 'quiz': {
          const data: QuizCreateRequest = {
            question_count: questionCount as any,
            difficulty: difficulty as any,
            topic: topic || undefined,
          };
          await artifactApi.createQuiz(notebookId, data);
          break;
        }
        case 'infographic': {
          const data: InfographicCreateRequest = {
            language: language as any,
            orientation: orientation as any,
            detail_level: detailLevel as any,
            description: description || undefined,
          };
          await artifactApi.createInfographic(notebookId, data);
          break;
        }
        case 'slide-deck': {
          const data: SlideDeckCreateRequest = {
            format: slideDeckFormat as any,
            length: slideDeckLength as any,
            language: language as any,
            description: description || undefined,
          };
          await artifactApi.createSlideDeck(notebookId, data);
          break;
        }
        case 'report': {
          const data: ReportCreateRequest = {
            format: reportFormat as any,
            language: language as any,
            description: description || undefined,
          };
          await artifactApi.createReport(notebookId, data);
          break;
        }
        case 'mindmap': {
          const data: MindmapCreateRequest = {};
          await artifactApi.createMindmap(notebookId, data);
          break;
        }
      }
      onClose();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create artifact';
      setError(errorMessage);
      console.error('Create artifact error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderForm = () => {
    switch (artifactType) {
      case 'audio-overview':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Audio Format</label>
              <select
                value={audioFormat}
                onChange={(e) => setAudioFormat(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Deep Dive">Deep Dive</option>
                <option value="Brief">Brief</option>
                <option value="Critique">Critique</option>
                <option value="Debate">Debate</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            {audioFormat === 'Deep Dive' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Length</label>
                <select
                  value={length}
                  onChange={(e) => setLength(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="">Default</option>
                  <option value="Short">Short</option>
                  <option value="Default">Default</option>
                  <option value="Long">Long</option>
                </select>
              </div>
            )}
            {(audioFormat === 'Critique' || audioFormat === 'Debate') && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Length</label>
                <select
                  value={length}
                  onChange={(e) => setLength(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="">Default</option>
                  <option value="Short">Short</option>
                  <option value="Default">Default</option>
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Focus Text (optional)</label>
              <textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'video-overview':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Video Format</label>
              <select
                value={videoFormat}
                onChange={(e) => setVideoFormat(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Explainer">Explainer</option>
                <option value="Brief">Brief</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Visual Style</label>
              <select
                value={visualStyle}
                onChange={(e) => setVisualStyle(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Auto-select">Auto-select</option>
                <option value="Custom">Custom</option>
                <option value="Classic">Classic</option>
                <option value="Whiteboard">Whiteboard</option>
                <option value="Kawaii">Kawaii</option>
                <option value="Anime">Anime</option>
                <option value="Watercolor">Watercolor</option>
                <option value="Retro print">Retro print</option>
                <option value="Heritage">Heritage</option>
                <option value="Paper-craft">Paper-craft</option>
              </select>
            </div>
            {visualStyle === 'Custom' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Custom Style Description (required)
                </label>
                <textarea
                  value={customStyleDescription}
                  onChange={(e) => setCustomStyleDescription(e.target.value)}
                  rows={3}
                  maxLength={5000}
                  required
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Focus Text (optional)</label>
              <textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'flashcards':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Card Count</label>
              <select
                value={cardCount}
                onChange={(e) => setCardCount(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Fewer">Fewer</option>
                <option value="Standard">Standard</option>
                <option value="More">More</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Topic (optional)</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'quiz':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Question Count</label>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Fewer">Fewer</option>
                <option value="Standard">Standard</option>
                <option value="More">More</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Topic (optional)</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'infographic':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Orientation</label>
              <select
                value={orientation}
                onChange={(e) => setOrientation(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Landscape">Landscape</option>
                <option value="Portrait">Portrait</option>
                <option value="Square">Square</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Detail Level</label>
              <select
                value={detailLevel}
                onChange={(e) => setDetailLevel(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Concise">Concise</option>
                <option value="Standard">Standard</option>
                <option value="Detailed BETA">Detailed BETA</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description (optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'slide-deck':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Format</label>
              <select
                value={slideDeckFormat}
                onChange={(e) => setSlideDeckFormat(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Detailed Deck">Detailed Deck</option>
                <option value="Presenter Slides">Presenter Slides</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Length</label>
              <select
                value={slideDeckLength}
                onChange={(e) => setSlideDeckLength(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Short">Short</option>
                <option value="Default">Default</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description (optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'report':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">Format</label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="Create Your Own">Create Your Own</option>
                <option value="Briefing Doc">Briefing Doc</option>
                <option value="Study Guide">Study Guide</option>
                <option value="Blog Post">Blog Post</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="">Default</option>
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={5000}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'mindmap':
        return (
          <div className="text-sm text-gray-600">
            Click &quot;Create&quot; to generate a mind map for this notebook. No additional configuration is required.
          </div>
        );

      default:
        return null;
    }
  };

  const getTitle = () => {
    const titles: Record<string, string> = {
      'audio-overview': 'Create Audio Overview',
      'video-overview': 'Create Video Overview',
      flashcards: 'Create Flashcards',
      quiz: 'Create Quiz',
      infographic: 'Create Infographic',
      'slide-deck': 'Create Slide Deck',
      report: 'Create Report',
      mindmap: 'Create Mind Map',
    };
    return titles[artifactType] || 'Create Artifact';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        <div className="inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:align-middle">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium leading-6 text-gray-900">{getTitle()}</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              {error && (
                <div className="mb-4 rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <div className="space-y-4">{renderForm()}</div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

