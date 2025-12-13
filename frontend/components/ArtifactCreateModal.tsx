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
  ReportFormat,
  AudioLanguage,
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
  // Audio defaults: Deep Dive, English, Default length
  const [audioFormat, setAudioFormat] = useState<string>('Deep Dive');
  const [audioLanguage, setAudioLanguage] = useState<string>('english');
  const [audioLength, setAudioLength] = useState<string>('Default');
  // Video defaults: Explainer, English, Auto-select
  const [videoFormat, setVideoFormat] = useState<string>('Explainer');
  const [videoLanguage, setVideoLanguage] = useState<string>('english');
  const [visualStyle, setVisualStyle] = useState<string>('Auto-select');
  const [customStyleDescription, setCustomStyleDescription] = useState('');
  // Slide deck defaults: Detailed Deck, English, Default length
  const [slideDeckFormat, setSlideDeckFormat] = useState<string>('Detailed Deck');
  const [slideDeckLanguage, setSlideDeckLanguage] = useState<string>('english');
  const [slideDeckLength, setSlideDeckLength] = useState<string>('Default');
  // Defaults: Standard for count, Medium for difficulty
  const [cardCount, setCardCount] = useState<string>('Standard');
  const [questionCount, setQuestionCount] = useState<string>('Standard');
  const [difficulty, setDifficulty] = useState<string>('Medium');
  // Defaults: English, Landscape, Standard
  const [infographicLanguage, setInfographicLanguage] = useState<string>('english');
  const [orientation, setOrientation] = useState<string>('Landscape');
  const [detailLevel, setDetailLevel] = useState<string>('Standard');
  // Report defaults: Create Your Own, English
  const [reportFormat, setReportFormat] = useState<ReportFormat>('Create Your Own');
  const [reportLanguage, setReportLanguage] = useState<AudioLanguage>('english');
  const [focusText, setFocusText] = useState('');
  const [topic, setTopic] = useState('');
  const [description, setDescription] = useState('');

  // Default descriptions for report formats
  const reportFormatDefaults: Record<string, string> = {
    'Briefing Doc': 'Create a comprehensive briefing document that synthesizes the main themes and ideas from the sources. Start with a concise Executive Summary that presents the most critical takeaways upfront. The body of the document must provide a detailed and thorough examination of the main themes, evidence, and conclusions found in the sources. This analysis should be structured logically with headings and bullet points to ensure clarity. The tone must be objective and incisive.',
    'Study Guide': 'You are a highly capable research assistant and tutor. Create a detailed study guide designed to review understanding of the sources. Create a quiz with ten short-answer questions (2-3 sentences each) and include a separate answer key. Suggest five essay format questions, but do not supply answers. Also conclude with a comprehensive glossary of key terms with definitions.',
    'Blog Post': 'Act as a thoughtful writer and synthesizer of ideas, tasked with creating an engaging and readable blog post for a popular online publishing platform known for its clean aesthetic and insightful content. Your goal is to distill the top most surprising, counter-intuitive, or impactful takeaways from the provided source materials into a compelling listicle. The writing style should be clean, accessible, and highly scannable, employing a conversational yet intelligent tone. Craft a compelling, click-worthy headline. Begin the article with a short introduction that hooks the reader by establishing a relatable problem or curiosity, then present each of the takeaway points as a distinct section with a clear, bolded subheading. Within each section, use short paragraphs to explain the concept clearly, and don\'t just summarize; offer a brief analysis or a reflection on why this point is so interesting or important, and if a powerful quote exists in the sources, feature it in a blockquote for emphasis. Conclude the post with a brief, forward-looking summary that leaves the reader with a final thought-provoking question or a powerful takeaway to ponder.',
    'Create Your Own': '',
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      switch (artifactType) {
        case 'audio-overview': {
          const data: AudioOverviewCreateRequest = {
            audio_format: audioFormat ? (audioFormat as any) : undefined,
            language: audioLanguage ? (audioLanguage as any) : undefined,
            // Brief format doesn't support length
            length: audioFormat === 'Brief' ? undefined : (audioLength ? (audioLength as any) : undefined),
            focus_text: focusText || undefined,
          };
          await artifactApi.createAudioOverview(notebookId, data);
          break;
        }
        case 'video-overview': {
          const data: VideoOverviewCreateRequest = {
            video_format: videoFormat ? (videoFormat as any) : undefined,
            language: videoLanguage ? (videoLanguage as any) : undefined,
            visual_style: visualStyle ? (visualStyle as any) : undefined,
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
            format: slideDeckFormat ? (slideDeckFormat as any) : undefined,
            length: slideDeckLength ? (slideDeckLength as any) : undefined,
            language: slideDeckLanguage ? (slideDeckLanguage as any) : undefined,
            description: description || undefined,
          };
          await artifactApi.createSlideDeck(notebookId, data);
          break;
        }
        case 'report': {
          // For "Create Your Own", description is mandatory
          if (reportFormat === 'Create Your Own' && !description.trim()) {
            setError('Description is required for "Create Your Own" format');
            setLoading(false);
            return;
          }
          // For other formats, use default description if empty
          let finalDescription = description;
          if (reportFormat && reportFormat !== 'Create Your Own' && !description.trim()) {
            finalDescription = reportFormatDefaults[reportFormat] || description;
          }
          const data: ReportCreateRequest = {
            format: reportFormat,
            language: reportLanguage || undefined,
            description: finalDescription || undefined,
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
              <label className="block text-sm font-medium text-gray-700 mb-3">Format</label>
              <div className="space-y-3">
                {[
                  { value: 'Deep Dive', label: 'Deep Dive', description: 'A lively conversation between two hosts, unpacking and connecting topics in your sources' },
                  { value: 'Brief', label: 'Brief', description: 'A bite-sized overview to help you grasp the core ideas from your sources quickly' },
                  { value: 'Critique', label: 'Critique', description: 'An expert review of your sources, offering constructive feedback to help you improve your material' },
                  { value: 'Debate', label: 'Debate', description: 'A thoughtful debate between two hosts, illuminating different perspectives on your sources' },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      audioFormat === format.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="audioFormat"
                      value={format.value}
                      checked={audioFormat === format.value}
                      onChange={(e) => setAudioFormat(e.target.value)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{format.label}</div>
                      <div className="text-sm text-gray-600 mt-1">{format.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose language</label>
                <select
                  value={audioLanguage}
                  onChange={(e) => setAudioLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">English</option>
                  <option value="persian">Persian</option>
                </select>
              </div>
              {audioFormat === 'Deep Dive' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Length</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setAudioLength('Short')}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        audioLength === 'Short'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      Short
                    </button>
                    <button
                      type="button"
                      onClick={() => setAudioLength('Default')}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        audioLength === 'Default'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      Default
                    </button>
                    <button
                      type="button"
                      onClick={() => setAudioLength('Long')}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        audioLength === 'Long'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      Long
                    </button>
                  </div>
                </div>
              )}
              {(audioFormat === 'Critique' || audioFormat === 'Debate') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Length</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setAudioLength('Short')}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        audioLength === 'Short'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      Short
                    </button>
                    <button
                      type="button"
                      onClick={() => setAudioLength('Default')}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        audioLength === 'Default'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      Default
                    </button>
                  </div>
                </div>
              )}
              {audioFormat === 'Brief' && <div></div>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">What should the AI hosts focus on in this episode?</label>
              <textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder={`Things to try

 • Focus on a specific source ("only cover the article about Italy")
 • Focus on a specific topic ("just discuss the novel's main character")
 • Target a specific audience ("explain to someone new to biology")`}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'video-overview':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Format</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Explainer', label: 'Explainer', description: 'A structured, comprehensive overview that connects the dots within your sources' },
                  { value: 'Brief', label: 'Brief', description: 'A bite-sized overview to help you quickly grasp core ideas from your sources' },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      videoFormat === format.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="videoFormat"
                      value={format.value}
                      checked={videoFormat === format.value}
                      onChange={(e) => setVideoFormat(e.target.value)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{format.label}</div>
                      <div className="text-sm text-gray-600 mt-1">{format.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Choose language</label>
              <select
                value={videoLanguage}
                onChange={(e) => setVideoLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="english">English</option>
                <option value="persian">Persian</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Choose visual style</label>
              <div className="grid grid-cols-3 gap-2">
                {['Auto-select', 'Custom', 'Classic', 'Whiteboard', 'Kawaii', 'Anime', 'Watercolor', 'Retro print', 'Heritage', 'Paper-craft'].map((style) => (
                  <label
                    key={style}
                    className={`flex items-center justify-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                      visualStyle === style
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="visualStyle"
                      value={style}
                      checked={visualStyle === style}
                      onChange={(e) => setVisualStyle(e.target.value)}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">{style}</span>
                  </label>
                ))}
              </div>
            </div>
            {visualStyle === 'Custom' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
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
              <label className="block text-sm font-medium text-gray-700 mb-2">What should the AI hosts focus on?</label>
              <textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder={`Things to try

 • Target a specific use case ("present this to a book club", "help me review for a quiz")
 • Focus on a specific source ("show the photos from the album", "focus on the biology paper")
 • Describe the show structure ("start by talking about the mission", "end with next steps")`}
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
              <label className="block text-sm font-medium text-gray-700 mb-3">Format</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Detailed Deck', label: 'Detailed Deck', description: 'A comprehensive deck with full text and details, perfect for emailing or reading on its own.' },
                  { value: 'Presenter Slides', label: 'Presenter Slides', description: 'Clean, visual slides with key talking points to support you while you speak.' },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      slideDeckFormat === format.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="slideDeckFormat"
                      value={format.value}
                      checked={slideDeckFormat === format.value}
                      onChange={(e) => setSlideDeckFormat(e.target.value)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{format.label}</div>
                      <div className="text-sm text-gray-600 mt-1">{format.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose language</label>
                <select
                  value={slideDeckLanguage}
                  onChange={(e) => setSlideDeckLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">English</option>
                  <option value="persian">Persian</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Length</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setSlideDeckLength('Short')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      slideDeckLength === 'Short'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Short
                  </button>
                  <button
                    type="button"
                    onClick={() => setSlideDeckLength('Default')}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      slideDeckLength === 'Default'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Default
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Describe the slide deck you want to create</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={5000}
                placeholder={`Add a high-level outline, or guide the audience, style, and focus: "Create a deck for beginners using a bold and playful style with a focus on step-by-step instructions."`}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'report':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Format</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Create Your Own', title: 'Create Your Own', description: 'Craft reports your way by specifying structure, style, tone, and more' },
                  { value: 'Briefing Doc', title: 'Briefing Doc', description: 'Overview of your sources featuring key insights and quotes' },
                  { value: 'Study Guide', title: 'Study Guide', description: 'Short-answer quiz, suggested essay questions, and glossary of key terms' },
                  { value: 'Blog Post', title: 'Blog Post', description: 'Insightful takeaways distilled into a highly readable article' },
                  { value: 'Design Document', title: 'Design Document', description: 'A technical document comparing data models for a new data-intensive application.' },
                  { value: 'Strategy Memo', title: 'Strategy Memo', description: 'A memo outlining a strategy for evolving a system to a distributed architecture.' },
                  { value: 'Concept Explainer', title: 'Concept Explainer', description: 'Learn the essential principles for building strong and lasting data applications.' },
                  { value: 'Comparative Overview', title: 'Comparative Overview', description: 'Discover the main differences between how databases store and organize information.' },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      reportFormat === format.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="reportFormat"
                      value={format.value}
                      checked={reportFormat === format.value}
                      onChange={(e) => {
                        const newFormat = e.target.value as ReportFormat;
                        setReportFormat(newFormat);
                        // Auto-populate default description when format changes
                        if (reportFormatDefaults[newFormat]) {
                          setDescription(reportFormatDefaults[newFormat]);
                        } else {
                          setDescription('');
                        }
                      }}
                      className="sr-only"
                    />
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">{format.title}</div>
                      {reportFormat === format.value && (
                        <span className="text-xs text-indigo-700 font-semibold">Selected</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-2">{format.description}</div>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose language</label>
                <select
                  value={reportLanguage}
                  onChange={(e) => setReportLanguage(e.target.value as AudioLanguage)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">English (default)</option>
                  <option value="persian">Persian</option>
                </select>
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Describe the report you want to create
                {reportFormat === 'Create Your Own' && <span className="text-red-500 ml-1">*</span>}
              </label>
              {reportFormat !== 'Create Your Own' && reportFormatDefaults[reportFormat] && (
                <p className="text-xs text-gray-500 mb-2">
                  Default description is pre-filled. You can edit it if needed.
                </p>
              )}
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={reportFormat === 'Create Your Own' ? 4 : 6}
                maxLength={5000}
                required={reportFormat === 'Create Your Own'}
                placeholder={
                  reportFormat === 'Create Your Own'
                    ? 'For example:\n\nCreate a formal competitive review of the 2026 functional beverage market for a new wellness drink. The tone should be analytical and strategic, focusing on the distribution and pricing of key competitors to inform our launch strategy.'
                    : 'Edit the default description or use as-is.'
                }
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

