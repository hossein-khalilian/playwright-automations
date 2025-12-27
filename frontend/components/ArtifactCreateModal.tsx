'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

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
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('artifacts');
  const tCommon = useTranslations('common');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state based on artifact type
  // Default language based on platform locale
  const defaultLanguage = isRTL ? 'persian' : 'english';
  // Audio defaults: Deep Dive, Default language, Default length
  const [audioFormat, setAudioFormat] = useState<string>('Deep Dive');
  const [audioLanguage, setAudioLanguage] = useState<string>(defaultLanguage);
  const [audioLength, setAudioLength] = useState<string>('Default');
  // Video defaults: Explainer, Default language, Auto-select
  const [videoFormat, setVideoFormat] = useState<string>('Explainer');
  const [videoLanguage, setVideoLanguage] = useState<string>(defaultLanguage);
  const [visualStyle, setVisualStyle] = useState<string>('Auto-select');
  const [customStyleDescription, setCustomStyleDescription] = useState('');
  // Slide deck defaults: Detailed Deck, Default language, Default length
  const [slideDeckFormat, setSlideDeckFormat] = useState<string>('Detailed Deck');
  const [slideDeckLanguage, setSlideDeckLanguage] = useState<string>(defaultLanguage);
  const [slideDeckLength, setSlideDeckLength] = useState<string>('Default');
  // Defaults: Standard for count, Medium for difficulty
  const [cardCount, setCardCount] = useState<string>('Standard');
  const [questionCount, setQuestionCount] = useState<string>('Standard');
  const [difficulty, setDifficulty] = useState<string>('Medium');
  // Defaults: Default language, Landscape, Standard
  const [infographicLanguage, setInfographicLanguage] = useState<string>(defaultLanguage);
  const [orientation, setOrientation] = useState<string>('Landscape');
  const [detailLevel, setDetailLevel] = useState<string>('Standard');
  // Report defaults: Create Your Own, Default language
  const [reportFormat, setReportFormat] = useState<ReportFormat>('Create Your Own');
  const [reportLanguage, setReportLanguage] = useState<AudioLanguage>(defaultLanguage as AudioLanguage);
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
            setError(t('reportDescriptionRequired'));
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
              <label className="block text-sm font-medium text-gray-700 mb-3">{t('audioFormat')}</label>
              <div className="space-y-3">
                {[
                  { value: 'Deep Dive', label: t('audioFormatDeepDive'), description: t('audioFormatDeepDiveDesc') },
                  { value: 'Brief', label: t('audioFormatBrief'), description: t('audioFormatBriefDesc') },
                  { value: 'Critique', label: t('audioFormatCritique'), description: t('audioFormatCritiqueDesc') },
                  { value: 'Debate', label: t('audioFormatDebate'), description: t('audioFormatDebateDesc') },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start ${isRTL ? 'flex-row-reverse' : ''} p-4 border-2 rounded-lg cursor-pointer transition-colors ${
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
                      className={`mt-1 ${isRTL ? 'ml-3' : 'mr-3'}`}
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
                <Label>{t('chooseLanguage')}</Label>
                <Select
                  value={audioLanguage}
                  onValueChange={setAudioLanguage}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="english">{t('languageEnglish')}</SelectItem>
                    <SelectItem value="persian">{t('languagePersian')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {audioFormat === 'Deep Dive' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('audioLength')}</label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      onClick={() => setAudioLength('Short')}
                      variant={audioLength === 'Short' ? 'default' : 'outline'}
                      className="flex-1"
                    >
                      {t('audioLengthShort')}
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setAudioLength('Default')}
                      variant={audioLength === 'Default' ? 'default' : 'outline'}
                      className="flex-1"
                    >
                      {t('audioLengthDefault')}
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setAudioLength('Long')}
                      variant={audioLength === 'Long' ? 'default' : 'outline'}
                      className="flex-1"
                    >
                      {t('audioLengthLong')}
                    </Button>
                  </div>
                </div>
              )}
              {(audioFormat === 'Critique' || audioFormat === 'Debate') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('audioLength')}</label>
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
                      {t('audioLengthShort')}
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
                      {t('audioLengthDefault')}
                    </button>
                  </div>
                </div>
              )}
              {audioFormat === 'Brief' && <div></div>}
            </div>
            <div>
              <Label>{t('audioFocusLabel')}</Label>
              <Textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('audioFocusPlaceholder')}
              />
            </div>
          </>
        );

      case 'video-overview':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">{t('videoFormat')}</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Explainer', label: t('videoFormatExplainer'), description: t('videoFormatExplainerDesc') },
                  { value: 'Brief', label: t('videoFormatBrief'), description: t('videoFormatBriefDesc') },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start ${isRTL ? 'flex-row-reverse' : ''} p-4 border-2 rounded-lg cursor-pointer transition-colors ${
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
                      className={`mt-1 ${isRTL ? 'ml-3' : 'mr-3'}`}
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
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseLanguage')}</label>
              <select
                value={videoLanguage}
                onChange={(e) => setVideoLanguage(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              >
                <option value="english">{t('languageEnglish')}</option>
                <option value="persian">{t('languagePersian')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseVisualStyle')}</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'Auto-select', label: t('visualStyleAutoSelect') },
                  { value: 'Custom', label: t('visualStyleCustom') },
                  { value: 'Classic', label: t('visualStyleClassic') },
                  { value: 'Whiteboard', label: t('visualStyleWhiteboard') },
                  { value: 'Kawaii', label: t('visualStyleKawaii') },
                  { value: 'Anime', label: t('visualStyleAnime') },
                  { value: 'Watercolor', label: t('visualStyleWatercolor') },
                  { value: 'Retro print', label: t('visualStyleRetroPrint') },
                  { value: 'Heritage', label: t('visualStyleHeritage') },
                  { value: 'Paper-craft', label: t('visualStylePaperCraft') },
                ].map((style) => (
                  <label
                    key={style.value}
                    className={`flex items-center ${isRTL ? 'flex-row-reverse justify-center' : 'justify-center'} gap-2 p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                      visualStyle === style.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    >
                    <input
                      type="radio"
                      name="visualStyle"
                      value={style.value}
                      checked={visualStyle === style.value}
                      onChange={(e) => setVisualStyle(e.target.value)}
                      className="shrink-0"
                    />
                    <span className="text-sm font-medium text-gray-700">{style.label}</span>
                  </label>
                ))}
              </div>
            </div>
            {visualStyle === 'Custom' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('customStyleDescription')}
                </label>
                <textarea
                  value={customStyleDescription}
                  onChange={(e) => setCustomStyleDescription(e.target.value)}
                  rows={5}
                  maxLength={5000}
                  required
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('videoFocusLabel')}</label>
              <textarea
                value={focusText}
                onChange={(e) => setFocusText(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('videoFocusPlaceholder')}
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
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('numberOfCards')}</label>
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
                    {t('cardCountFewer')}
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
                    {t('cardCountStandard')}
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
                    {t('cardCountMore')}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('levelOfDifficulty')}</label>
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
                    {t('difficultyEasy')}
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
                    {t('difficultyMedium')}
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
                    {t('difficultyHard')}
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('flashcardTopicLabel')}</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('flashcardTopicPlaceholder')}
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
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('numberOfQuestions')}</label>
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
                    {t('questionCountFewer')}
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
                    {t('questionCountStandard')}
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
                    {t('questionCountMore')}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('levelOfDifficulty')}</label>
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
                    {t('difficultyEasy')}
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
                    {t('difficultyMedium')}
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
                    {t('difficultyHard')}
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('quizTopicLabel')}</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('quizTopicPlaceholder')}
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
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseLanguage')}</label>
                <select
                  value={infographicLanguage}
                  onChange={(e) => setInfographicLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">{t('languageEnglish')}</option>
                  <option value="persian">{t('languagePersian')}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseOrientation')}</label>
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
                    {t('orientationLandscape')}
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
                    {t('orientationPortrait')}
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
                    {t('orientationSquare')}
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('levelOfDetail')}</label>
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
                  {t('detailLevelConcise')}
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
                  {t('detailLevelStandard')}
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
                  {t('detailLevelDetailedBeta')}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('infographicDescriptionLabel')}</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('infographicDescriptionPlaceholder')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'slide-deck':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">{t('slideDeckFormat')}</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Detailed Deck', label: t('slideDeckFormatDetailedDeck'), description: t('slideDeckFormatDetailedDeckDesc') },
                  { value: 'Presenter Slides', label: t('slideDeckFormatPresenterSlides'), description: t('slideDeckFormatPresenterSlidesDesc') },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-start ${isRTL ? 'flex-row-reverse' : ''} p-4 border-2 rounded-lg cursor-pointer transition-colors ${
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
                      className={`mt-1 ${isRTL ? 'ml-3' : 'mr-3'}`}
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
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseLanguage')}</label>
                <select
                  value={slideDeckLanguage}
                  onChange={(e) => setSlideDeckLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">{t('languageEnglish')}</option>
                  <option value="persian">{t('languagePersian')}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('slideDeckLength')}</label>
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
                    {t('slideDeckLengthShort')}
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
                    {t('slideDeckLengthDefault')}
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('slideDeckDescriptionLabel')}</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                maxLength={5000}
                placeholder={t('slideDeckDescriptionPlaceholder')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'report':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">{t('reportFormat')}</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'Create Your Own', title: t('reportFormatCreateYourOwn'), description: t('reportFormatCreateYourOwnDesc') },
                  { value: 'Briefing Doc', title: t('reportFormatBriefingDoc'), description: t('reportFormatBriefingDocDesc') },
                  { value: 'Study Guide', title: t('reportFormatStudyGuide'), description: t('reportFormatStudyGuideDesc') },
                  { value: 'Blog Post', title: t('reportFormatBlogPost'), description: t('reportFormatBlogPostDesc') },
                  { value: 'Design Document', title: t('reportFormatDesignDocument'), description: t('reportFormatDesignDocumentDesc') },
                  { value: 'Strategy Memo', title: t('reportFormatStrategyMemo'), description: t('reportFormatStrategyMemoDesc') },
                  { value: 'Concept Explainer', title: t('reportFormatConceptExplainer'), description: t('reportFormatConceptExplainerDesc') },
                  { value: 'Comparative Overview', title: t('reportFormatComparativeOverview'), description: t('reportFormatComparativeOverviewDesc') },
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
                        <span className="text-xs text-indigo-700 font-semibold">{t('selected')}</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-2">{format.description}</div>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('chooseLanguage')}</label>
                <select
                  value={reportLanguage}
                  onChange={(e) => setReportLanguage(e.target.value as AudioLanguage)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
                >
                  <option value="english">{t('languageEnglish')}</option>
                  <option value="persian">{t('languagePersian')}</option>
                </select>
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('reportDescriptionLabel')}
                {reportFormat === 'Create Your Own' && <span className="text-red-500 ml-1">*</span>}
              </label>
              {reportFormat !== 'Create Your Own' && reportFormatDefaults[reportFormat] && (
                <p className="text-xs text-gray-500 mb-2">
                  {t('reportDescriptionHelper')}
                </p>
              )}
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={reportFormat === 'Create Your Own' ? 6 : 8}
                maxLength={5000}
                required={reportFormat === 'Create Your Own'}
                placeholder={
                  reportFormat === 'Create Your Own'
                    ? t('reportDescriptionPlaceholderCreateYourOwn')
                    : t('reportDescriptionPlaceholderDefault')
                }
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          </>
        );

      case 'mindmap':
        return (
          <div className="text-sm text-gray-600">
            {t('mindMapDescription')}
          </div>
        );

      default:
        return null;
    }
  };

  const getTitle = () => {
    const titles: Record<string, string> = {
      'audio-overview': t('createAudioOverview'),
      'video-overview': t('createVideoOverview'),
      flashcards: t('createFlashcards'),
      quiz: t('createQuiz'),
      infographic: t('createInfographic'),
      'slide-deck': t('createSlideDeck'),
      report: t('createReport'),
      mindmap: t('createMindMap'),
    };
    return titles[artifactType] || 'Create Artifact';
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{getTitle()}</DialogTitle>
          </DialogHeader>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4 py-4">{renderForm()}</div>

          <DialogFooter>
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
            >
              {tCommon('cancel')}
            </Button>
            <Button
              type="submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t('creating')}
                </>
              ) : (
                tCommon('create')
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

