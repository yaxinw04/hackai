'use client';

import { useState, useEffect } from 'react';
import { apiService, ProcessResponse, JobStatusResponse } from '../services/apiClient';

// Application state types
type AppState = 'idle' | 'processing' | 'complete' | 'error';

interface FormData {
  url: string;
  prompt: string;
}

export default function Home() {
  // State management
  const [appState, setAppState] = useState<AppState>('idle');
  const [formData, setFormData] = useState<FormData>({ url: '', prompt: '' });
  const [jobId, setJobId] = useState<string>('');
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form validation
  const isFormValid = formData.url.trim() !== '' && formData.prompt.trim() !== '';

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isFormValid || isSubmitting) return;

    setIsSubmitting(true);
    setError('');

    try {
      const response: ProcessResponse = await apiService.startProcessing(
        formData.url,
        formData.prompt
      );
      
      setJobId(response.job_id);
      setAppState('processing');
      setJobStatus({
        status: response.status,
        message: response.message,
        results: null
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setAppState('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Poll job status when in processing state
  useEffect(() => {
    if (appState !== 'processing' || !jobId) return;

    const pollStatus = async () => {
      try {
        const status = await apiService.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'complete') {
          setAppState('complete');
        } else if (status.status === 'failed') {
          setError(status.message);
          setAppState('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get job status');
        setAppState('error');
      }
    };

    // Poll immediately, then every 3 seconds
    pollStatus();
    const interval = setInterval(pollStatus, 3000);

    return () => clearInterval(interval);
  }, [appState, jobId]);

  // Reset to start a new job
  const handleReset = () => {
    setAppState('idle');
    setFormData({ url: '', prompt: '' });
    setJobId('');
    setJobStatus(null);
    setError('');
  };

  // Render status indicator
  const renderStatusIndicator = () => {
    if (appState === 'processing' && jobStatus) {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
            <div>
              <h3 className="text-lg font-medium text-blue-900">Processing...</h3>
              <p className="text-blue-700">{jobStatus.message}</p>
              <p className="text-sm text-blue-600 mt-1">Job ID: {jobId}</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Render results
  const renderResults = () => {
    if (appState === 'complete' && jobStatus?.results && jobStatus.results.length > 0) {
      return (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-green-900 mb-4">
            🎉 Processing Complete!
          </h3>
          <p className="text-green-700 mb-4">{jobStatus.message}</p>
          
          <div className="space-y-4">
            <h4 className="font-medium text-green-900">Generated Clips:</h4>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {jobStatus.results.map((clipPath, index) => (
                <div key={index} className="bg-white rounded-lg p-4 shadow-sm border">
                  <h5 className="font-medium text-gray-900 mb-2">
                    Clip {index + 1}
                  </h5>
                  <video
                    controls
                    className="w-full rounded-lg mb-3"
                    style={{ maxHeight: '200px' }}
                  >
                    <source src={apiService.getClipUrl(clipPath)} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                  <a
                    href={apiService.getClipUrl(clipPath)}
                    download
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Download Clip
                  </a>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleReset}
            className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Process Another Video
          </button>
        </div>
      );
    }
    return null;
  };

  // Render error state
  const renderError = () => {
    if (appState === 'error') {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400 text-xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-red-800">Error</h3>
              <p className="text-red-700">{error}</p>
              <button
                onClick={handleReset}
                className="mt-3 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Status indicators */}
      {renderStatusIndicator()}
      {renderResults()}
      {renderError()}

      {/* Main form - only show when idle or error */}
      {(appState === 'idle' || appState === 'error') && (
        <div className="bg-white shadow-xl rounded-lg p-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Create Short Clips from YouTube Videos
            </h2>
            <p className="text-gray-600">
              Enter a YouTube URL and describe what kind of clips you'd like to create.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* YouTube URL Input */}
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                YouTube URL
              </label>
              <input
                type="url"
                id="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                required
              />
            </div>

            {/* Prompt Input */}
            <div>
              <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                Clip Creation Prompt
              </label>
              <textarea
                id="prompt"
                value={formData.prompt}
                onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                placeholder="Describe what kind of clips you want to create (e.g., 'Create 3 engaging clips highlighting the main points', 'Extract funny moments', etc.)"
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                required
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!isFormValid || isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting Processing...
                </div>
              ) : (
                'Create Clips'
              )}
            </button>
          </form>

          {/* Instructions */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Instructions:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Paste any YouTube video URL</li>
              <li>• Describe what kind of clips you want (topics, style, length, etc.)</li>
              <li>• Processing may take several minutes depending on video length</li>
              <li>• You'll be able to preview and download the generated clips</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
} 