'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { FileUpload } from '@/components/ui/file-upload';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const progressContainerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Connect to SSE for progress updates
  useEffect(() => {
    if (analysisId) {
      const eventSource = new EventSource(`http://localhost:8000/api/progress/${analysisId}`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.message === 'DONE') {
          eventSource.close();
        } else {
          setProgressMessages((prev) => [...prev, data.message]);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    }
  }, [analysisId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (progressContainerRef.current) {
      progressContainerRef.current.scrollTop = progressContainerRef.current.scrollHeight;
    }
  }, [progressMessages]);

  const handleFileChange = (files: File[]) => {
    if (files && files[0]) {
      const selectedFile = files[0];
      if (selectedFile.type.startsWith('video/')) {
        setFile(selectedFile);
      } else {
        alert('Please upload a video file');
      }
    }
  };

  const pollForResults = async (analysisId: string) => {
    // Poll for results every 2 seconds
    const checkResults = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/results/${analysisId}`);
        const data = await response.json();

        if (data.status === 'completed') {
          // Store analysis data and video path
          sessionStorage.setItem(`analysis_${analysisId}`, JSON.stringify(data.data));
          if (data.video_path) {
            sessionStorage.setItem(`video_${analysisId}`, data.video_path);
          }

          // Redirect to analysis page
          setTimeout(() => {
            router.push(`/analysis/${analysisId}`);
          }, 1000);
        } else {
          // Still processing, check again
          setTimeout(checkResults, 2000);
        }
      } catch (error) {
        console.error('Error checking results:', error);
        setTimeout(checkResults, 2000);
      }
    };

    checkResults();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setProgressMessages([]);

    try {
      const formData = new FormData();
      formData.append('video', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // Start listening to progress updates immediately
        setAnalysisId(data.id);

        // Start polling for results
        pollForResults(data.id);
      } else {
        const errorMsg = data.error + (data.howToFix ? `\n\n${data.howToFix}` : '');
        alert('Upload failed: ' + errorMsg);
        setUploading(false);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed');
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-16">
      {/* Hero Section */}
      <div className="relative mx-auto mb-16 flex max-w-7xl flex-col items-center justify-center">
        <div className="absolute inset-y-0 left-0 h-full w-px bg-neutral-200/80 dark:bg-neutral-800/80">
          <div className="absolute top-0 h-40 w-px bg-linear-to-b from-transparent via-blue-500 to-transparent" />
        </div>
        <div className="absolute inset-y-0 right-0 h-full w-px bg-neutral-200/80 dark:bg-neutral-800/80">
          <div className="absolute h-40 w-px bg-linear-to-b from-transparent via-blue-500 to-transparent" />
        </div>
        <div className="absolute inset-x-0 bottom-0 h-px w-full bg-neutral-200/80 dark:bg-neutral-800/80">
          <div className="absolute mx-auto h-px w-40 bg-linear-to-r from-transparent via-blue-500 to-transparent" />
        </div>
        <div className="px-4 py-10 md:py-20">
          <h1 className="relative z-10 mx-auto max-w-4xl text-center text-2xl font-bold text-slate-700 md:text-4xl lg:text-7xl dark:text-slate-300">
            {"AI-Powered Video Analysis"
              .split(" ")
              .map((word, index) => (
                <motion.span
                  key={index}
                  initial={{ opacity: 0, filter: "blur(4px)", y: 10 }}
                  animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
                  transition={{
                    duration: 0.3,
                    delay: index * 0.1,
                    ease: "easeInOut",
                  }}
                  className={`mr-2 inline-block ${word === "AI-Powered" ? "text-blue-600 dark:text-blue-500" : ""}`}
                >
                  {word}
                </motion.span>
              ))}
          </h1>
          <motion.p
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
            transition={{
              duration: 0.3,
              delay: 0.4,
            }}
            className="relative z-10 mx-auto max-w-xl py-4 text-center text-lg font-normal text-neutral-600 dark:text-neutral-400"
          >
            Analyze speaker emotions, gestures, and content using AI-powered computer vision and natural language processing
          </motion.p>
        </div>
      </div>

        {/* Upload Card */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
            <form onSubmit={handleSubmit}>
              {/* File Upload Component */}
              <FileUpload onChange={handleFileChange} />

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!file || uploading}
                className={`w-full mt-6 py-4 px-6 rounded-xl font-semibold text-white transition-all ${
                  !file || uploading
                    ? 'bg-slate-300 dark:bg-slate-600 cursor-not-allowed'
                    : 'bg-linear-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl'
                }`}
              >
                {uploading ? 'Analyzing...' : 'Analyze Video'}
              </button>
            </form>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow">
              <div className="text-3xl mb-3">😀</div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Emotion Analysis
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Track facial expressions and emotional journey throughout the video
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow">
              <div className="text-3xl mb-3">👐</div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Gesture Tracking
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Analyze body language, hand movements, and overall presence
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow">
              <div className="text-3xl mb-3">🧠</div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Content Insights
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                AI-powered analysis of speech patterns, themes, and key messages
              </p>
            </div>
          </div>
        </div>

        {/* Progress Modal */}
        {uploading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-blue-500 dark:text-white">
                  Analyzing Your Video
                </h2>
                <div className="shrink-0">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
                </div>
              </div>
              <div
                ref={progressContainerRef}
                className="flex-1 overflow-y-auto space-y-2 mb-4 scroll-smooth"
              >
                {progressMessages.length === 0 ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                  </div>
                ) : (
                  progressMessages.map((message, index) => {
                    const isLastMessage = index === progressMessages.length - 1;
                    const isInProgress = !message.includes('✅') && !message.includes('❌');
                    const showSpinner = isLastMessage && isInProgress;

                    return (
                      <div
                        key={index}
                        className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700 rounded-lg animate-fadeIn"
                      >
                        <div className="text-lg shrink-0">{message.split(' ')[0]}</div>
                        <div className="flex-1 text-sm text-slate-700 dark:text-slate-300">
                          {message.split(' ').slice(1).join(' ')}
                        </div>
                        {showSpinner && (
                          <div className="shrink-0">
                            <div className="inline-block animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
              <div className="text-center text-sm text-slate-500 dark:text-slate-400">
                This may take a few minutes depending on video length...
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
