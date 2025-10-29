'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

// TypeScript interfaces for analysis data
interface Emotion {
  time: number;
  emotion: string;
  confidence: number;
}

interface Gesture {
  time: number;
  type: string;
  description: string;
  confidence?: number;
}

interface TranscriptSegment {
  time: number;
  end_time?: number;
  text: string;
  confidence?: number;
}

interface Summary {
  total_duration: number;
  emotional_range: string[];
  key_moments: Array<{ time: number; description: string; type?: string }>;
  top_themes: string[];
}

interface LLMInsights {
  main_topics: string[];
  rhetorical_techniques: string[];
  argument_structure?: string;
  persuasive_elements?: string[];
  persuasion_score: number;
  overall_tone: string;
  transcript_summary?: string;
}

interface AnalysisData {
  emotions: Emotion[];
  gestures: Gesture[];
  transcript: TranscriptSegment[];
  summary: Summary;
  llm_insights: LLMInsights;
}


export default function AnalysisPage() {
  const params = useParams();
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(75);
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastUpdateRef = useRef<number>(0);

  // Load analysis data from sessionStorage or backend
  useEffect(() => {
    const loadData = async () => {
      try {
        // Try to get data from sessionStorage first
        const storedData = sessionStorage.getItem(`analysis_${params.id}`);
        const storedVideoPath = sessionStorage.getItem(`video_${params.id}`);

        if (storedData) {
          const data = JSON.parse(storedData);
          setAnalysisData(data);
          if (storedVideoPath) {
            setVideoPath(storedVideoPath);
          }
          setLoading(false);
          console.log('[Analysis] Loaded data from sessionStorage');
          return;
        }

        // If not in sessionStorage, try to fetch from backend
        console.log('[Analysis] Fetching data from backend...');
        const response = await fetch(`http://localhost:8000/api/results/${params.id}`);
        const result = await response.json();

        if (result.status === 'completed') {
          setAnalysisData(result.data);
          if (result.video_path) {
            setVideoPath(result.video_path);
          }
          setLoading(false);
          console.log('[Analysis] Loaded data from backend');
        } else {
          console.error('[Analysis] Analysis not found or still processing');
          setLoading(false);
        }
      } catch (error) {
        console.error('[Analysis] Error loading data:', error);
        setLoading(false);
      }
    };

    loadData();
  }, [params.id]);

  // Handle video time updates (throttled to prevent excessive re-renders)
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const now = Date.now();
      const newTime = Math.floor(videoRef.current.currentTime);

      // Only update if time has changed AND at least 250ms has passed
      if (newTime !== currentTime && now - lastUpdateRef.current >= 250) {
        setCurrentTime(newTime);
        lastUpdateRef.current = now;
      }
    }
  };

  // Handle when video metadata is loaded
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(Math.floor(videoRef.current.duration));
    }
  };

  // Handle play/pause
  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Handle seeking
  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current) {
      const rect = e.currentTarget.getBoundingClientRect();
      const pos = (e.clientX - rect.left) / rect.width;
      const time = pos * duration;
      videoRef.current.currentTime = time;
      setCurrentTime(Math.floor(time));
    }
  };

  const currentEmotion = useMemo((): Emotion => {
    if (!analysisData?.emotions?.length) return { emotion: 'neutral', confidence: 0, time: 0 };
    const current = analysisData.emotions.find((e, i) => {
      const next = analysisData.emotions[i + 1];
      return currentTime >= e.time && (!next || currentTime < next.time);
    });
    return current || analysisData.emotions[0];
  }, [analysisData?.emotions, currentTime]);

  const recentGestures = useMemo((): Gesture[] => {
    if (!analysisData?.gestures) return [];
    return analysisData.gestures.filter(
      (g) => currentTime >= g.time && currentTime < g.time + 10
    );
  }, [analysisData?.gestures, currentTime]);

  // Get unique emotions and map them to Y-axis values (memoized to avoid recalculation)
  const emotionChartData = analysisData ? (() => {
    const uniqueEmotions = Array.from(new Set(analysisData.emotions.map(e => e.emotion)));
    const emotionMap: { [key: string]: number } = {};
    uniqueEmotions.forEach((emotion, index) => {
      emotionMap[emotion] = index;
    });

    const chartData = analysisData.emotions.map(e => ({
      time: e.time,
      emotionValue: emotionMap[e.emotion],
      emotion: e.emotion,
      emoji: getEmotionEmoji(e.emotion),
      confidence: e.confidence,
    }));

    return { data: chartData, emotionMap, uniqueEmotions };
  })() : { data: [], emotionMap: {}, uniqueEmotions: [] };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600 dark:text-slate-400">No analysis data found</p>
          <Link href="/" className="text-blue-500 hover:underline mt-4 inline-block">
            Upload a new video
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Analysis Dashboard
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                ID: {params.id}
              </p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              New Analysis
            </Link>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content - Video and Timeline */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Player */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                Video Player
              </h2>
              <div className="bg-slate-900 rounded-lg aspect-video overflow-hidden">
                {videoPath ? (
                  <video
                    ref={videoRef}
                    className="w-full h-full object-contain"
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={handleLoadedMetadata}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  >
                    <source src={videoPath} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <p className="text-slate-400">No video available</p>
                  </div>
                )}
              </div>
              <div className="mt-4 flex items-center gap-4">
                <button
                  onClick={togglePlayPause}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-slate-400 disabled:cursor-not-allowed"
                  disabled={!videoPath}
                >
                  {isPlaying ? 'Pause' : 'Play'}
                </button>
                <div
                  className="flex-1 bg-slate-200 dark:bg-slate-700 h-2 rounded-full cursor-pointer"
                  onClick={handleSeek}
                >
                  <div
                    className="bg-blue-500 h-full rounded-full transition-all"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>
            </div>

            {/* Emotion Timeline Chart */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                Emotion Timeline
              </h2>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={emotionChartData.data}
                    margin={{ top: 10, right: 30, left: 60, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} vertical={false} />
                    <XAxis
                      dataKey="time"
                      stroke="#6b7280"
                      tick={{ fill: '#9ca3af', fontSize: 12 }}
                      label={{ value: 'Time (seconds)', position: 'insideBottom', offset: -10, fill: '#6b7280', fontSize: 12 }}
                    />
                    <YAxis
                      stroke="#6b7280"
                      tick={(props: { x?: number; y?: number; payload?: { value: number } }) => {
                        const { x = 0, y = 0, payload } = props;
                        const emotionName = payload ? emotionChartData.uniqueEmotions[payload.value] : undefined;
                        if (emotionName) {
                          return (
                            <g transform={`translate(${x},${y})`}>
                              <text x={0} y={0} dy={4} textAnchor="end" fill="#9ca3af" fontSize={12}>
                                {getEmotionEmoji(emotionName)} {emotionName}
                              </text>
                            </g>
                          );
                        }
                        return <g />;
                      }}
                      domain={[0, Math.max(0, emotionChartData.uniqueEmotions.length - 1)]}
                      ticks={Array.from({ length: emotionChartData.uniqueEmotions.length }, (_, i) => i)}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#f3f4f6',
                        padding: '8px 12px',
                        fontSize: '14px'
                      }}
                      formatter={(_value: number, _name: string, props: { payload?: { emoji: string; emotion: string; confidence: number } }) => {
                        if (!props.payload) return ['', ''];
                        return [
                          `${props.payload.emoji} ${props.payload.emotion}`,
                          `Confidence: ${(props.payload.confidence * 100).toFixed(0)}%`
                        ];
                      }}
                      labelFormatter={(label) => `${label}s`}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="emotionValue"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, fill: '#3b82f6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Transcript */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                Transcript
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {analysisData.transcript.map((line: TranscriptSegment, i: number) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg cursor-pointer transition-all ${
                      currentTime >= line.time &&
                      (i === analysisData.transcript.length - 1 ||
                        currentTime < analysisData.transcript[i + 1].time)
                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-700'
                    }`}
                  >
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                      {formatTime(line.time)}
                    </span>
                    <p className="text-slate-900 dark:text-white mt-1">{line.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar - Insights */}
          <div className="space-y-6">
            {/* Current State */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                Current State
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                    Emotion
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-3xl">{getEmotionEmoji(currentEmotion.emotion)}</span>
                    <span className="font-semibold text-slate-900 dark:text-white capitalize">
                      {currentEmotion.emotion}
                    </span>
                  </div>
                </div>

                {recentGestures.length > 0 && (
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                      Recent Gestures
                    </p>
                    {recentGestures.map((gesture: Gesture, i: number) => (
                      <div
                        key={i}
                        className="text-sm bg-slate-50 dark:bg-slate-700 p-2 rounded mb-2"
                      >
                        <span className="text-2xl mr-2">👐</span>
                        {gesture.description}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Summary Statistics */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                Summary Statistics
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Duration
                  </p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {Math.floor(Math.round(analysisData.summary.total_duration) / 60)}:
                    {(Math.round(analysisData.summary.total_duration) % 60)
                      .toString()
                      .padStart(2, '0')}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Emotional Range
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {analysisData.summary.emotional_range.map((emotionName: string, i: number) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full text-sm capitalize"
                      >
                        {emotionName}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Top Themes
                  </p>
                  <div className="space-y-1">
                    {analysisData.summary.top_themes.map((theme: string, i: number) => (
                      <span
                        key={i}
                        className="inline-block px-3 py-1 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white rounded text-sm mr-2 mb-2"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* LLM Insights */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                AI Insights
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Persuasion Score
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-200 dark:bg-slate-700 h-3 rounded-full">
                      <div
                        className="bg-linear-to-r from-green-500 to-blue-500 h-full rounded-full"
                        style={{
                          width: `${(analysisData.llm_insights.persuasion_score / 10) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-lg font-bold text-slate-900 dark:text-white">
                      {analysisData.llm_insights.persuasion_score}/10
                    </span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Rhetorical Techniques
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {analysisData.llm_insights.rhetorical_techniques.map((tech: string, i: number) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded-full text-sm"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Overall Tone
                  </p>
                  <p className="text-sm text-slate-900 dark:text-white">
                    {analysisData.llm_insights.overall_tone}
                  </p>
                </div>
              </div>
            </div>

            {/* AI Summary */}
            {analysisData.llm_insights.transcript_summary && (
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4 text-blue-600 dark:text-blue-500">
                  AI Summary
                </h2>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  {analysisData.llm_insights.transcript_summary}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function getEmotionEmoji(emotion: string): string {
  const emojiMap: { [key: string]: string } = {
    neutral: '😐',
    happy: '😊',
    serious: '😐',
    passionate: '🔥',
    confident: '💪',
    hopeful: '🌟',
  };
  return emojiMap[emotion] || '😐';
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
