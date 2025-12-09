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
  // Defaults: Standard for count, Medium for difficulty
  const [cardCount, setCardCount] = useState<string>('Standard');
  const [questionCount, setQuestionCount] = useState<string>('Standard');
  const [difficulty, setDifficulty] = useState<string>('Medium');
  // Defaults: English, Landscape, Standard
  const [infographicLanguage, setInfographicLanguage] = useState<string>('english');
  const [orientation, setOrientation] = useState<string>('Landscape');
  const [detailLevel, setDetailLevel] = useState<string>('Standard');
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
            audio_format: audioFormat || undefined,
            language: language || undefined,
            length: length || undefined,
            focus_text: focusText || undefined,
          };
          await artifactApi.createAudioOverview(notebookId, data);
          break;
        }
        case 'video-overview': {
          const data: VideoOverviewCreateRequest = {
            video_format: videoFormat || undefined,
            language: language || undefined,
            visual_style: visualStyle || undefined,
            custom_style_description: customStyleDescription || undefined,
            focus_text: focusText || undefined,
          };
          await artifactApi.createVideoOverview(notebookId, data);
          break;
        }
        case 'flashcards': {
          const data: FlashcardCreateRequest = {
            card_count: cardCount ? (cardCount as any) : undefined,
            difficulty: difficulty ? (difficulty as any) : undefined,
            topic: topic || undefined,
          };
          await artifactApi.createFlashcards(notebookId, data);
          break;
        }
        case 'quiz': {
          const data: QuizCreateRequest = {
            question_count: questionCount ? (questionCount as any) : undefined,
            difficulty: difficulty ? (difficulty as any) : undefined,
            topic: topic || undefined,
          };
          await artifactApi.createQuiz(notebookId, data);
          break;
        }
        case 'infographic': {
          const data: InfographicCreateRequest = {
            language: infographicLanguage ? (infographicLanguage as any) : undefined,
            orientation: orientation ? (orientation as any) : undefined,
            detail_level: detailLevel ? (detailLevel as any) : undefined,
            description: description || undefined,
          };
          await artifactApi.createInfographic(notebookId, data);
          break;
        }
        case 'slide-deck': {
          const data: SlideDeckCreateRequest = {
            format: slideDeckFormat || undefined,
            length: slideDeckLength || undefined,
            language: language || undefined,
            description: description || undefined,
          };
          await artifactApi.createSlideDeck(notebookId, data);
          break;
        }
        case 'report': {
          const data: ReportCreateRequest = {
            format: reportFormat || undefined,
            language: language || undefined,
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
      // Handle FastAPI validation errors which come as an array of error objects
      let errorMessage = 'Failed to create artifact';
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        
        // Check if detail is an array (validation errors)
        if (Array.isArray(detail)) {
          // Format validation errors into a readable message
          errorMessage = detail
            .map((error: any) => {
              const field = error.loc?.slice(1).join('.') || 'field';
              return `${field}: ${error.msg}`;
            })
            .join('; ');
        } else if (typeof detail === 'string') {
          // Simple string error
          errorMessage = detail;
        } else {
          // Try to stringify if it's an object
          errorMessage = JSON.stringify(detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
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
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Number of Cards</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setCardCount('Fewer')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      cardCount === 'Fewer'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Fewer
                  </button>
                  <button
                    type="button"
                    onClick={() => setCardCount('Standard')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      cardCount === 'Standard'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Standard (Default)
                  </button>
                  <button
                    type="button"
                    onClick={() => setCardCount('More')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      cardCount === 'More'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    More
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Level of Difficulty</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setDifficulty('Easy')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Easy'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Easy
                  </button>
                  <button
                    type="button"
                    onClick={() => setDifficulty('Medium')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Medium'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Medium (Default)
                  </button>
                  <button
                    type="button"
                    onClick={() => setDifficulty('Hard')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Hard'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Hard
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">What should the topic be?</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder={`Things to try

 • The flashcards must be restricted to a specific source (e.g. "the article about Italy")
 • The flashcards must focus on a specific topic like "Newton's second law"
 • The card fronts must be short (1-5 words) for memorization`}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'quiz':
        return (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Number of Questions</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setQuestionCount('Fewer')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      questionCount === 'Fewer'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Fewer
                  </button>
                  <button
                    type="button"
                    onClick={() => setQuestionCount('Standard')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      questionCount === 'Standard'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Standard (Default)
                  </button>
                  <button
                    type="button"
                    onClick={() => setQuestionCount('More')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      questionCount === 'More'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    More
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Level of Difficulty</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setDifficulty('Easy')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Easy'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Easy
                  </button>
                  <button
                    type="button"
                    onClick={() => setDifficulty('Medium')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Medium'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Medium (Default)
                  </button>
                  <button
                    type="button"
                    onClick={() => setDifficulty('Hard')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      difficulty === 'Hard'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Hard
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">What should the topic be?</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder={`Things to try

 • The quiz must be restricted to a specific source (e.g. "the article about Italy")
 • The quiz must focus solely on the key concepts of physics
 • Create a quiz to help me prepare for my history exam on Ancient Egypt`}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'infographic':
        return (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose language</label>
                <select
                  value={infographicLanguage}
                  onChange={(e) => setInfographicLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">English</option>
                  <option value="persian">Persian</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose orientation</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setOrientation('Landscape')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      orientation === 'Landscape'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Landscape
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrientation('Portrait')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      orientation === 'Portrait'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Portrait
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrientation('Square')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      orientation === 'Square'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Square
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Level of detail</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setDetailLevel('Concise')}
                  className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    detailLevel === 'Concise'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Concise
                </button>
                <button
                  type="button"
                  onClick={() => setDetailLevel('Standard')}
                  className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    detailLevel === 'Standard'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Standard
                </button>
                <button
                  type="button"
                  onClick={() => setDetailLevel('Detailed BETA')}
                  className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    detailLevel === 'Detailed BETA'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Detailed <span className="text-xs">BETA</span>
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Describe the infographic you want to create</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder='Guide the style, color, or focus: "Use a blue color theme and highlight the 3 key stats."'
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

