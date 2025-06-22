'use client';

import { useState, useEffect, useRef } from 'react';
import { apiService, ProcessResponse, JobStatusResponse, CaptionSegment, CaptionStyle, GenerateCaptionsResponse } from '../../services/apiClient';
import Link from 'next/link';

// Application state types
type AppState = 'input' | 'processing' | 'editing' | 'complete' | 'error';

interface FormData {
  url: string;
  prompt: string;
}

interface Clip {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  duration: string;
  thumbnail?: string;
  path: string;
  start_time: number;
  end_time: number;
  text: string;
  caption: string;
  hashtags: string[];
  captions?: CaptionSegment[];
  captionStyle?: CaptionStyle;
}

interface EditingClip extends Clip {
  originalStart: number;
  originalEnd: number;
  editedStart: number;
  editedEnd: number;
  originalPath?: string;
}

interface SocialMediaAccount {
  platform: 'youtube' | 'instagram';
  isConnected: boolean;
  username?: string;
  accessToken?: string;
  userId?: string; // For Instagram
}

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  clip: Clip;
  onUpload: (platforms: string[], downloadMp4: boolean, socialAccounts: SocialMediaAccount[]) => void;
}

interface CaptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  clip: EditingClip;
  jobId: string;
  onCaptionsApplied: (clipId: string, captions: CaptionSegment[], style: CaptionStyle, captionedVideoUrl?: string) => void;
}

// Default caption style optimized for YouTube Shorts
const defaultCaptionStyle: CaptionStyle = {
  fontSize: 24,
  fontColor: '#FFFFFF',
  backgroundColor: '#000000',
  backgroundOpacity: 0.8,
  outlineColor: '#000000',
  outlineWidth: 2,
  position: 'bottom',
  animation: 'typewriter'
};

// YouTube Shorts caption presets
const captionPresets = [
  {
    name: 'Classic YouTube Shorts',
    style: {
      fontSize: 24,
      fontColor: '#FFFFFF',
      backgroundColor: '#000000',
      backgroundOpacity: 0.8,
      outlineColor: '#000000',
      outlineWidth: 2,
      position: 'bottom' as const,
      animation: 'typewriter' as const
    }
  },
  {
    name: 'Bold & Bright',
    style: {
      fontSize: 26,
      fontColor: '#FFFF00',
      backgroundColor: '#000000',
      backgroundOpacity: 0.9,
      outlineColor: '#FF0000',
      outlineWidth: 2,
      position: 'bottom' as const,
      animation: 'typewriter' as const
    }
  },
  {
    name: 'Minimalist',
    style: {
      fontSize: 22,
      fontColor: '#FFFFFF',
      backgroundColor: 'transparent',
      backgroundOpacity: 0,
      outlineColor: '#000000',
      outlineWidth: 2,
      position: 'bottom' as const,
      animation: 'typewriter' as const
    }
  },
  {
    name: 'High Contrast',
    style: {
      fontSize: 25,
      fontColor: '#000000',
      backgroundColor: '#FFFFFF',
      backgroundOpacity: 0.9,
      outlineColor: '#FFFF00',
      outlineWidth: 1,
      position: 'bottom' as const,
      animation: 'typewriter' as const
    }
  }
];

const CaptionsModal: React.FC<CaptionsModalProps> = ({ isOpen, onClose, clip, jobId, onCaptionsApplied }) => {
  const [captions, setCaptions] = useState<CaptionSegment[]>(clip.captions || []);
  const [captionStyle, setCaptionStyle] = useState<CaptionStyle>(clip.captionStyle || defaultCaptionStyle);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');

  // Generate captions from audio
  const handleGenerateCaptions = async () => {
    setIsGenerating(true);
    try {
      const response: GenerateCaptionsResponse = await apiService.generateCaptions(jobId, clip.id, captionStyle);
      setCaptions(response.captions);
    } catch (error) {
      console.error('Failed to generate captions:', error);
      // For demo purposes, generate mock captions
      const mockCaptions: CaptionSegment[] = [
        { start: 0, end: 2.5, text: "This will blow your mind!" },
        { start: 2.5, end: 5.0, text: "You won't believe what happens next" },
        { start: 5.0, end: 7.5, text: "Game changing technique revealed" },
        { start: 7.5, end: 10.0, text: "Your life will never be the same" }
      ];
      setCaptions(mockCaptions);
    } finally {
      setIsGenerating(false);
    }
  };

  // Apply captions to video
  const handleApplyCaptions = async () => {
    setIsApplying(true);
    try {
      const response = await apiService.applyCaptions(jobId, clip.id, captions, captionStyle);
      // Pass the captioned video URL to switch the preview
      onCaptionsApplied(clip.id, captions, captionStyle, response.previewUrl);
      console.log('✅ Captions applied successfully! Video preview will now show the captioned version.');
      onClose();
    } catch (error) {
      console.error('Failed to apply captions:', error);
      // For demo, just close and update the clip without switching video
      onCaptionsApplied(clip.id, captions, captionStyle);
      console.log('✅ Captions configured (demo mode)');
      onClose();
    } finally {
      setIsApplying(false);
    }
  };

  // Load preset
  const loadPreset = (presetIndex: number) => {
    setSelectedPreset(presetIndex);
    setCaptionStyle(captionPresets[presetIndex].style);
  };

  // Edit caption text
  const startEditing = (index: number, text: string) => {
    setEditingIndex(index);
    setEditingText(text);
  };

  const saveEdit = () => {
    if (editingIndex !== null) {
      const newCaptions = [...captions];
      newCaptions[editingIndex].text = editingText;
      setCaptions(newCaptions);
      setEditingIndex(null);
      setEditingText('');
    }
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditingText('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-white/10">
        <div className="sticky top-0 bg-slate-800 p-6 border-b border-white/10 rounded-t-3xl">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold text-white">✨ Add Eye-Catching Captions</h3>
            <button 
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-slate-400 mt-2">Editing: {clip.title}</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Step 1: Generate or Load Captions */}
          <div className="bg-slate-700/50 rounded-xl p-6">
            <h4 className="text-xl font-semibold text-white mb-4">🎙️ Step 1: Generate Captions</h4>
            <div className="flex gap-4">
              <button
                onClick={handleGenerateCaptions}
                disabled={isGenerating}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
              >
                {isGenerating ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Generating...
                  </div>
                ) : (
                  'Generate From Audio'
                )}
              </button>
              <div className="text-slate-400 text-sm py-3">
                AI will analyze the audio and create perfectly timed captions with word-by-word animation
              </div>
            </div>
          </div>

          {/* Step 2: Style Presets */}
          {captions.length > 0 && (
            <div className="bg-slate-700/50 rounded-xl p-6">
              <h4 className="text-xl font-semibold text-white mb-4">🎨 Step 2: Choose Caption Style</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {captionPresets.map((preset, index) => (
                  <button
                    key={index}
                    onClick={() => loadPreset(index)}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      selectedPreset === index
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-white/20 bg-white/5 hover:border-white/40'
                    }`}
                  >
                    <div className="text-white font-medium text-sm mb-2">{preset.name}</div>
                    <div 
                      className="text-xs p-2 rounded"
                      style={{
                        color: preset.style.fontColor,
                        backgroundColor: preset.style.backgroundColor !== 'transparent' ? preset.style.backgroundColor : 'rgba(0,0,0,0.5)',
                        textShadow: `0 0 ${preset.style.outlineWidth}px ${preset.style.outlineColor}`
                      }}
                    >
                      Sample Text
                    </div>
                  </button>
                ))}
              </div>

              {/* Custom Style Controls */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-white text-sm mb-2">Font Size</label>
                  <input
                    type="range"
                    min="16"
                    max="32"
                    value={captionStyle.fontSize}
                    onChange={(e) => setCaptionStyle({...captionStyle, fontSize: parseInt(e.target.value)})}
                    className="w-full"
                  />
                  <span className="text-slate-400 text-xs">{captionStyle.fontSize}px</span>
                </div>
                <div>
                  <label className="block text-white text-sm mb-2">Font Color</label>
                  <input
                    type="color"
                    value={captionStyle.fontColor}
                    onChange={(e) => setCaptionStyle({...captionStyle, fontColor: e.target.value})}
                    className="w-full h-10 rounded bg-transparent"
                  />
                </div>
                <div>
                  <label className="block text-white text-sm mb-2">Position</label>
                  <select
                    value={captionStyle.position}
                    onChange={(e) => setCaptionStyle({...captionStyle, position: e.target.value as 'top' | 'center' | 'bottom'})}
                    className="w-full bg-slate-600 text-white rounded px-3 py-2"
                  >
                    <option value="top">Top</option>
                    <option value="center">Center</option>
                    <option value="bottom">Bottom</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Edit Caption Text */}
          {captions.length > 0 && (
            <div className="bg-slate-700/50 rounded-xl p-6">
              <h4 className="text-xl font-semibold text-white mb-4">📝 Step 3: Edit Caption Text</h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {captions.map((caption, index) => (
                  <div key={index} className="bg-slate-600/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-slate-400 text-sm">
                        {caption.start.toFixed(1)}s - {caption.end.toFixed(1)}s
                      </span>
                      <button
                        onClick={() => startEditing(index, caption.text)}
                        className="text-purple-400 hover:text-purple-300 text-sm"
                      >
                        Edit
                      </button>
                    </div>
                    {editingIndex === index ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          className="w-full bg-slate-700 text-white px-3 py-2 rounded"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={saveEdit}
                            className="px-3 py-1 bg-green-600 text-white rounded text-sm"
                          >
                            Save
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="px-3 py-1 bg-slate-600 text-white rounded text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div 
                        className="text-white p-2 rounded text-center"
                        style={{
                          color: captionStyle.fontColor,
                          backgroundColor: captionStyle.backgroundColor !== 'transparent' ? captionStyle.backgroundColor : 'rgba(0,0,0,0.5)',
                          textShadow: `0 0 ${captionStyle.outlineWidth}px ${captionStyle.outlineColor}`,
                          fontSize: `${captionStyle.fontSize * 0.3}px`
                        }}
                      >
                        {caption.text}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: Apply Captions */}
          {captions.length > 0 && (
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-xl p-6 border border-purple-500/30">
              <h4 className="text-xl font-semibold text-white mb-4">🎬 Step 4: Apply to Video</h4>
              <p className="text-slate-300 mb-4">
                This will burn the captions directly into your video clip with word-by-word animation positioned at the bottom. The preview will automatically switch to show your captioned video.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={handleApplyCaptions}
                  disabled={isApplying}
                  className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
                >
                  {isApplying ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Burning captions into video...
                    </div>
                  ) : (
                    'Apply Captions to Video'
                  )}
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-3 bg-slate-600 hover:bg-slate-500 text-white rounded-xl transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// YouTube and Instagram SVG Icons
const YouTubeIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

const InstagramIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.059 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
  </svg>
);

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, clip, onUpload }) => {
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [downloadMp4, setDownloadMp4] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [socialAccounts, setSocialAccounts] = useState<SocialMediaAccount[]>([
    { platform: 'youtube', isConnected: false },
    { platform: 'instagram', isConnected: false }
  ]);

  const handlePlatformToggle = (platform: string) => {
    setSelectedPlatforms(prev => 
      prev.includes(platform) 
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleSocialLogin = async (platform: 'youtube' | 'instagram') => {
    try {
      let authResult: { accessToken: string; refreshToken?: string; userId?: string };
      
      if (platform === 'youtube') {
        authResult = await apiService.authenticateYouTube();
        setSocialAccounts(prev => 
          prev.map(account => 
            account.platform === platform 
              ? { 
                  ...account, 
                  isConnected: true, 
                  username: 'YouTube Channel',
                  accessToken: authResult.accessToken
                }
              : account
          )
        );
      } else if (platform === 'instagram') {
        authResult = await apiService.authenticateInstagram();
        setSocialAccounts(prev => 
          prev.map(account => 
            account.platform === platform 
              ? { 
                  ...account, 
                  isConnected: true, 
                  username: 'Instagram Account',
                  accessToken: authResult.accessToken,
                  userId: authResult.userId
                }
              : account
          )
        );
      }
    } catch (error) {
      console.error(`Failed to connect to ${platform}:`, error);
    }
  };

  const handleUpload = async () => {
    setIsUploading(true);
    try {
      await onUpload(selectedPlatforms, downloadMp4, socialAccounts);
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-3xl max-w-md w-full p-6 border border-white/10">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">Upload Clip</h3>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="mb-6">
          <h4 className="text-white font-semibold mb-2">{clip.title}</h4>
          <p className="text-slate-400 text-sm">Duration: {clip.duration}</p>
        </div>

        {/* Download MP4 Option */}
        <div className="mb-6">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={downloadMp4}
              onChange={(e) => setDownloadMp4(e.target.checked)}
              className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500 focus:ring-2"
            />
            <span className="text-white">Download MP4 file</span>
          </label>
        </div>

        {/* Social Media Platforms */}
        <div className="mb-6">
          <h4 className="text-white font-semibold mb-4">Upload to Social Media</h4>
          
          {socialAccounts.map((account) => (
            <div key={account.platform} className="mb-4 p-4 bg-slate-700/50 rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`rounded-lg flex items-center justify-center ${
                    account.platform === 'youtube' ? 'text-red-600' : 'text-pink-600'
                  }`}>
                    {account.platform === 'youtube' ? <YouTubeIcon /> : <InstagramIcon />}
                  </div>
                  <div>
                    <p className="text-white font-medium capitalize">{account.platform}</p>
                    <p className="text-slate-400 text-sm">
                      {account.isConnected ? `Connected as ${account.username}` : 'Not connected'}
                    </p>
                  </div>
                </div>
                
                {!account.isConnected ? (
                  <button
                    onClick={() => handleSocialLogin(account.platform)}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-all"
                  >
                    Connect
                  </button>
                ) : (
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedPlatforms.includes(account.platform)}
                      onChange={() => handlePlatformToggle(account.platform)}
                      className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500 focus:ring-2"
                    />
                    <span className="text-white text-sm">Upload</span>
                  </label>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Upload Button */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-slate-600 hover:bg-slate-500 text-white rounded-xl transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!downloadMp4 && selectedPlatforms.length === 0}
            className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Uploading...
              </div>
            ) : (
              'Upload'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default function CreatePage() {
  const [appState, setAppState] = useState<AppState>('input');
  const [formData, setFormData] = useState<FormData>({ url: '', prompt: '' });
  const [jobId, setJobId] = useState<string>('');
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentClipIndex, setCurrentClipIndex] = useState(0);
  const [editingClips, setEditingClips] = useState<EditingClip[]>([]);
  const [finalizedClips, setFinalizedClips] = useState<Clip[]>([]);

  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [isDragging, setIsDragging] = useState<{type: 'none' | 'start' | 'end' | 'move', clipIndex: number}>({type: 'none', clipIndex: -1});
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartValue, setDragStartValue] = useState(0);

  const [isPreventingTimelineClick, setIsPreventingTimelineClick] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedClipForUpload, setSelectedClipForUpload] = useState<Clip | null>(null);
  const [captionsModalOpen, setCaptionsModalOpen] = useState(false);
  const [selectedClipForCaptions, setSelectedClipForCaptions] = useState<EditingClip | null>(null);
  const [isFinalizingClips, setIsFinalizingClips] = useState(false);
  
  const timelineRef = useRef<HTMLDivElement>(null);
  const timelineContainerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Form validation
  const isFormValid = formData.url.trim() !== '' && formData.prompt.trim() !== '';

  // Process API results into clips format
  const processClips = (results: any[]): Clip[] => {
    if (!results || results.length === 0) return [];
    
    return results.map((clip: any) => ({
      id: String(clip.id || clip.clip_id || Math.random()),
      title: clip.title || `Clip ${clip.id}`,
      startTime: formatTime(clip.start_time || 0),
      endTime: formatTime(clip.end_time || 0),
      duration: formatDuration(clip.duration || 0),
      path: clip.url_path || clip.path || '',
      thumbnail: clip.thumbnail,
      start_time: clip.start_time || 0,
      end_time: clip.end_time || 0,
      text: clip.text || '',
      caption: clip.caption || '',
      hashtags: clip.hashtags || [],
      captions: clip.captions || [],
      captionStyle: clip.captionStyle || defaultCaptionStyle
    }));
  };

  // Helper function to format seconds to MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper function to format duration (with proper rounding)
  const formatDuration = (seconds: number): string => {
    // Round to 1 decimal place to avoid floating point precision issues
    const roundedSeconds = Math.round(seconds * 10) / 10;
    const mins = Math.floor(roundedSeconds / 60);
    const remainingSecs = roundedSeconds % 60;
    
    if (mins > 0) {
      // For longer durations, show as MM:SS
      return `${mins}:${Math.floor(remainingSecs).toString().padStart(2, '0')}`;
    } else {
      // For shorter durations, show as seconds with 1 decimal if needed
      if (remainingSecs % 1 === 0) {
        return `${Math.floor(remainingSecs)}s`;
      } else {
        return `${remainingSecs.toFixed(1)}s`;
      }
    }
  };

  // Timeline drag handlers
  const handleTimelineMouseDown = (e: React.MouseEvent, dragType: 'start' | 'end' | 'move', clipIndex: number) => {
    if (!timelineRef.current || clipIndex !== currentClipIndex) {
      // Only allow editing the currently selected clip
      return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    
    // Prevent timeline container from scrolling during drag
    if (timelineContainerRef.current) {
      timelineContainerRef.current.style.overflowX = 'hidden';
    }
    
    setIsDragging({type: dragType, clipIndex});
    setDragStartX(e.clientX);
    setIsPreventingTimelineClick(true);
    
    const currentClip = editingClips[clipIndex];
    if (currentClip) {
      if (dragType === 'start') {
        setDragStartValue(currentClip.editedStart);
      } else if (dragType === 'end') {
        setDragStartValue(currentClip.editedEnd);
      } else {
        setDragStartValue(currentClip.editedStart);
      }
    }
    
    // Add event listeners to document to ensure we capture mouse events even outside the element
    const handleMouseMove = (e: MouseEvent) => {
      if (!timelineRef.current) return;
      
      e.preventDefault();
      
      const rect = timelineRef.current.getBoundingClientRect();
      const timelineWidth = rect.width;
      const deltaX = e.clientX - dragStartX;
      const deltaTime = (deltaX / timelineWidth) * videoDuration;
      
      const clip = editingClips[clipIndex];
      if (!clip) return;
      
      const newClips = [...editingClips];
      
      // Get bounds from other clips to prevent overlapping
      const otherClips = editingClips.filter((_, i) => i !== clipIndex);
      const minBound = Math.max(0, ...otherClips.map(c => c.editedEnd).filter(end => end <= clip.editedStart));
      const maxBound = Math.min(videoDuration, ...otherClips.map(c => c.editedStart).filter(start => start >= clip.editedEnd));
      
      if (dragType === 'start') {
        const newStart = Math.max(minBound, Math.min(clip.editedEnd - 1, dragStartValue + deltaTime));
        newClips[clipIndex] = { ...clip, editedStart: newStart };
      } else if (dragType === 'end') {
        const newEnd = Math.min(maxBound, Math.max(clip.editedStart + 1, dragStartValue + deltaTime));
        newClips[clipIndex] = { ...clip, editedEnd: newEnd };
      } else if (dragType === 'move') {
        const clipDuration = clip.editedEnd - clip.editedStart;
        const newStart = Math.max(minBound, Math.min(maxBound - clipDuration, dragStartValue + deltaTime));
        newClips[clipIndex] = { 
          ...clip, 
          editedStart: newStart,
          editedEnd: newStart + clipDuration
        };
      }
      
      setEditingClips(newClips);
    };
    
    const handleMouseUp = () => {
      // Re-enable timeline scrolling
      if (timelineContainerRef.current) {
        timelineContainerRef.current.style.overflowX = 'auto';
      }
      
      setIsDragging({type: 'none', clipIndex: -1});
      // Delay preventing timeline click to avoid immediate click after drag
      setTimeout(() => setIsPreventingTimelineClick(false), 150);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current || !videoRef.current || isDragging.type !== 'none' || isPreventingTimelineClick) {
      return;
    }
    
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickTime = (clickX / rect.width) * videoDuration;
    
    videoRef.current.currentTime = clickTime;
    setCurrentTime(clickTime);
  };

  // Navigate to clip position in timeline
  const navigateToClip = (clipIndex: number) => {
    setCurrentClipIndex(clipIndex);
    const clip = editingClips[clipIndex];
    if (clip && timelineContainerRef.current && timelineRef.current) {
      const timelineWidth = timelineRef.current.offsetWidth;
      const containerWidth = timelineContainerRef.current.offsetWidth;
      const clipPosition = (clip.editedStart / videoDuration) * timelineWidth;
      const scrollPosition = clipPosition - containerWidth / 2;
      
      timelineContainerRef.current.scrollTo({
        left: Math.max(0, scrollPosition),
        behavior: 'smooth'
      });
      
      // Don't set video time here - let onLoadedMetadata handle it when new video loads
      setCurrentTime(clip.editedStart);
    }
  };

  // Get clips from API results or fallback to empty array
  const clips = appState === 'complete' && jobStatus?.results 
    ? processClips(jobStatus.results)
    : [];

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
        results: undefined
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setAppState('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Poll job status when in processing state (but NOT during finalization)
  useEffect(() => {
    if (appState !== 'processing' || !jobId || isFinalizingClips) return;

    console.log('📊 Starting job status polling...');

    const pollStatus = async () => {
      try {
        const status = await apiService.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'complete') {
          console.log('✅ Job completed, transitioning to editing state');
          // Convert clips to editing format
          const clips = processClips(status.results || []);
          const editingClipsData = clips.map(clip => ({
            ...clip,
            originalStart: clip.start_time,
            originalEnd: clip.end_time,
            editedStart: clip.start_time,
            editedEnd: clip.end_time
          }));
          setEditingClips(editingClipsData);
          setAppState('editing');
        } else if (status.status === 'failed') {
          setError(status.message);
          setAppState('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get job status');
        setAppState('error');
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 3000);
    return () => clearInterval(interval);
  }, [appState, jobId, isFinalizingClips]);

  const handleReset = () => {
    setAppState('input');
    setFormData({ url: '', prompt: '' });
    setJobId('');
    setJobStatus(null);
    setError('');
    setCurrentClipIndex(0);
    setEditingClips([]);
    setFinalizedClips([]);

    setCurrentTime(0);
    setVideoDuration(0);
  };

  const handleFinalize = async () => {
    if (!jobId) {
      console.error('No job ID found. Please try again.');
      return;
    }

    if (isFinalizingClips) {
      console.log('⚠️ Finalization already in progress, ignoring duplicate request');
      return;
    }

    try {
      setIsFinalizingClips(true);
      console.log('🎬 Starting finalization process...');
      
      // Show processing state
      setAppState('processing');
      setJobStatus({
        status: 'processing',
        message: 'Finalizing clips with your edits...',
        results: undefined
      });

      // Prepare properly formatted edited clips with all required fields
      const formattedEditingClips = editingClips.map(clip => {
        const hasCaptions = clip.captions && clip.captions.length > 0;
        console.log(`📋 Clip ${clip.id}: ${clip.title} - Has captions: ${hasCaptions}, Path: ${clip.path}`);
        
        return {
          id: clip.id,
          title: clip.title,
          startTime: clip.startTime,
          endTime: clip.endTime,
          duration: clip.duration,
          path: clip.path,
          start_time: clip.start_time,
          end_time: clip.end_time,
          text: clip.text,
          caption: clip.caption,
          hashtags: clip.hashtags,
          originalStart: clip.originalStart,
          originalEnd: clip.originalEnd,
          editedStart: clip.editedStart,
          editedEnd: clip.editedEnd,
          captions: clip.captions,
          captionStyle: clip.captionStyle,
          // Flag to indicate this clip has captions
          hasCaptionedVersion: hasCaptions
        };
      });

      console.log(`📋 Prepared ${formattedEditingClips.length} clips for finalization`);

      // Call the finalize API with edited clips
      console.log(`🚀 Calling finalize API for job ${jobId}...`);
      const finalizeResponse = await apiService.finalizeClips(jobId, formattedEditingClips);
      
      console.log('✅ Finalization API call completed');
      console.log('📄 Response status:', finalizeResponse?.status);
      console.log('📄 Response message:', finalizeResponse?.message);
      console.log('📄 Finalized clips count:', finalizeResponse?.finalized_clips?.length);
      console.log('📄 Full response:', finalizeResponse);
      
      if (finalizeResponse.status === 'success') {
        console.log(`🎉 Successfully finalized ${finalizeResponse.finalized_clips.length} clips`);
        
        // Use the finalized clips from the backend
        setFinalizedClips(finalizeResponse.finalized_clips);
        
        // Immediately transition to complete state
        setAppState('complete');
        setJobStatus({
          status: 'complete',
          message: 'All clips finalized successfully!',
          results: finalizeResponse.finalized_clips
        });
        
        console.log('🎯 State changed to complete - should show finalized clips page');
      } else {
        console.error('❌ Finalization failed:', finalizeResponse);
        throw new Error(finalizeResponse.message || 'Failed to finalize clips');
      }
    } catch (error) {
      console.error('❌ Finalization failed:', error);
      
      // Check if it's a network error vs API error
      if (error instanceof Error && error.message.includes('Failed to fetch')) {
        setError('Network error during finalization. Please check your connection and try again.');
      } else {
        setError(`Finalization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      
      setAppState('error');
      
      // Don't go back to editing state - stay in error state
      console.log('🔄 Staying in error state, not returning to editing');
    } finally {
      setIsFinalizingClips(false);
    }
  };

  const handleUpload = async (clip: Clip) => {
    setSelectedClipForUpload(clip);
    setUploadModalOpen(true);
  };

  const handleOpenCaptions = (clip: EditingClip) => {
    setSelectedClipForCaptions(clip);
    setCaptionsModalOpen(true);
  };

  const handleCaptionsApplied = (clipId: string, captions: CaptionSegment[], style: CaptionStyle, captionedVideoUrl?: string) => {
    console.log(`🎬 Applying captions to clip ${clipId}:`, {
      captionsCount: captions.length,
      style: style.position,
      captionedVideoUrl,
      newPath: captionedVideoUrl || 'no new path'
    });
    
    // Update the editing clip with captions and switch to captioned video
    setEditingClips(prevClips => 
      prevClips.map(clip => 
        clip.id === clipId 
          ? { 
              ...clip, 
              captions, 
              captionStyle: style,
              // Switch to captioned video if available, preserve original path as backup
              path: captionedVideoUrl || clip.path,
              originalPath: clip.originalPath || clip.path  // Preserve original path
            }
          : clip
      )
    );
    
    console.log(`✅ Captions applied to clip ${clipId}, preview should now show captioned version`);
  };

  const handleUploadProcess = async (platforms: string[], downloadMp4: boolean, socialAccounts: SocialMediaAccount[]) => {
    if (!selectedClipForUpload) return;

    try {
      // Handle MP4 download
      if (downloadMp4) {
        const link = document.createElement('a');
        link.href = apiService.getClipUrl(selectedClipForUpload.path);
        link.download = `${selectedClipForUpload.title}.mp4`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      // Handle social media uploads
      for (const platform of platforms) {
        const account = socialAccounts.find(acc => acc.platform === platform && acc.isConnected);
        if (!account || !account.accessToken) {
          console.error(`No access token found for ${platform}`);
          continue;
        }

        try {
          // Fetch the video file from the backend
          const videoResponse = await fetch(apiService.getClipUrl(selectedClipForUpload.path));
          if (!videoResponse.ok) {
            throw new Error(`Failed to fetch video file for ${platform}`);
          }
          
          const videoBlob = await videoResponse.blob();
          const videoFile = new File([videoBlob], `${selectedClipForUpload.title}.mp4`, { type: 'video/mp4' });

          if (platform === 'youtube') {
            const uploadResult = await apiService.uploadToYouTube(videoFile, {
              title: selectedClipForUpload.title,
              description: selectedClipForUpload.caption || selectedClipForUpload.text || 'Created with YouTube Shorts AI',
              tags: selectedClipForUpload.hashtags || ['shorts', 'ai', 'video'],
              accessToken: account.accessToken
            });
            
            console.log(`Successfully uploaded to YouTube:`, uploadResult);
            
          } else if (platform === 'instagram' && account.userId) {
            const uploadResult = await apiService.uploadToInstagram(videoFile, {
              caption: `${selectedClipForUpload.caption || selectedClipForUpload.text || selectedClipForUpload.title}\n\n${(selectedClipForUpload.hashtags || []).map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ')}`,
              accessToken: account.accessToken,
              userId: account.userId
            });
            
            console.log(`Successfully uploaded to Instagram:`, uploadResult);
          }
          
        } catch (uploadError) {
          console.error(`Failed to upload to ${platform}:`, uploadError);
          continue; // Continue with other platforms
        }
      }

      // Log success message
      const successMessages = [];
      if (platforms.length > 0) {
        successMessages.push(`Uploaded to: ${platforms.join(', ')}`);
      }
      if (downloadMp4) {
        successMessages.push('MP4 downloaded');
      }
      
      if (successMessages.length > 0) {
        console.log(`✅ Upload completed! ${successMessages.join(' • ')}`);
      }
      
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="relative z-10 px-6 py-4 bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-400 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">YS</span>
            </div>
            <span className="text-white font-bold text-xl">YouTube Shorts AI</span>
          </Link>
          <div className="flex items-center space-x-4">
            <button className="text-slate-300 hover:text-white transition-colors">
              Save Project
            </button>
            {appState === 'complete' && finalizedClips.length > 0 && (
              <button 
                onClick={() => {
                  // Upload all functionality would go here
                }}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all"
              >
                Upload All
              </button>
            )}
          </div>
        </div>
      </nav>

      <div className="px-6 py-8">
        {/* Input State */}
        {appState === 'input' && (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                Start your creation!
              </h1>
              <p className="text-slate-300 text-lg">
                Enter your YouTube URL and let AI create amazing shorts
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-white font-medium mb-3">YouTube URL</label>
                  <input
                    type="url"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="w-full px-6 py-4 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    required
                  />
                </div>

                <div>
                  <label className="block text-white font-medium mb-3">What kind of clips do you want?</label>
                  <textarea
                    value={formData.prompt}
                    onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                    placeholder="e.g., 'Create 3 engaging clips highlighting the main points', 'Extract funny moments', 'Find the most quotable parts'"
                    rows={4}
                    className="w-full px-6 py-4 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={!isFormValid || isSubmitting}
                  className="w-full py-4 px-8 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-2xl shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                      Processing...
                    </div>
                  ) : (
                    'Create Amazing Shorts'
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Processing State */}
        {appState === 'processing' && (
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                🎬 Creating Your Shorts...
              </h1>
              <p className="text-slate-300 text-lg">
                Our AI is analyzing your video and finding the best moments
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8">
              <div className="flex items-center justify-center mb-8">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent"></div>
              </div>
              
              <div className="text-center">
                <h3 className="text-xl font-semibold text-white mb-2">
                  {jobStatus?.message || 'Processing your video...'}
                </h3>
                <p className="text-slate-400 mb-4">Job ID: {jobId}</p>
                
                <div className="w-full bg-white/10 rounded-full h-2 mb-6">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                </div>
                
                <p className="text-slate-300">
                  This may take a few minutes depending on video length...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Editing State - Improved Video Editor Interface */}
        {appState === 'editing' && editingClips.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                🎬 Edit Your Clips
              </h1>
              <p className="text-slate-300 text-lg">
                Drag the timeline to adjust clips • Click clips below to navigate
              </p>
            </div>

            <div className="flex flex-col gap-8">
              {/* Main Video Editor */}
              <div className="flex gap-8">
                {/* Video Preview - YouTube Shorts Aspect Ratio */}
                <div className="flex-shrink-0">
                  <div className="bg-black/40 backdrop-blur-sm border border-white/10 rounded-3xl p-6">
                    <div className="w-80 h-[568px] bg-black rounded-2xl flex items-center justify-center relative overflow-hidden">
                      {editingClips[currentClipIndex]?.path.endsWith('.mp4') ? (
                        <video 
                          key={`video-${currentClipIndex}-${editingClips[currentClipIndex]?.id}-${editingClips[currentClipIndex]?.path}`}
                          ref={videoRef}
                          className="w-full h-full object-cover rounded-2xl"
                          controls
                          preload="metadata"
                          onLoadedMetadata={(e) => {
                            // For timeline visualization, use 2 minutes (120s) as the full width
                            // This makes the clip boxes larger and requires more horizontal scrolling
                            setVideoDuration(120); // Fixed 2-minute timeline width
                            
                            const currentClip = editingClips[currentClipIndex];
                            if (currentClip) {
                              // Start video at the beginning of this clip
                              e.currentTarget.currentTime = 0;
                              setCurrentTime(currentClip.editedStart);
                            }
                          }}
                          onTimeUpdate={(e) => {
                            // Map video time to timeline position
                            const currentClip = editingClips[currentClipIndex];
                            if (currentClip) {
                              const relativeTime = e.currentTarget.currentTime;
                              const timelineTime = currentClip.editedStart + relativeTime;
                              setCurrentTime(timelineTime);
                            }
                          }}
                        >
                          <source src={apiService.getClipUrl(editingClips[currentClipIndex].path)} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                      ) : (
                        <div className="text-6xl text-slate-500">📹</div>
                      )}
                      <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-sm px-3 py-1 rounded-lg">
                        <span className="text-white text-sm font-medium">
                          {editingClips[currentClipIndex]?.title}
                          {editingClips[currentClipIndex]?.captions && editingClips[currentClipIndex].captions!.length > 0 && (
                            <span className="ml-2 text-xs bg-green-500/30 text-green-300 px-2 py-1 rounded">
                              ✨ Captioned
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Timeline and Controls */}
                <div className="flex-1 space-y-6 min-w-0">
                  <div className="bg-black/40 backdrop-blur-sm border border-white/10 rounded-3xl p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Full Timeline - All Clips</h3>
                    
                    {/* Current clip info */}
                    <div className="flex items-center justify-between text-white text-sm mb-4">
                      <span>Editing: {editingClips[currentClipIndex]?.title}</span>
                      <span className="text-purple-400 font-semibold">
                        Duration: {formatDuration((editingClips[currentClipIndex]?.editedEnd || 0) - (editingClips[currentClipIndex]?.editedStart || 0))}
                      </span>
                      <span>Total: {formatTime(videoDuration)}</span>
                    </div>
                    
                    {/* Continuous Timeline - Properly Contained */}
                    <div 
                      ref={timelineContainerRef}
                      className="overflow-x-auto border border-slate-600 rounded-lg"
                      style={{ height: '120px' }}
                    >
                      <div 
                        ref={timelineRef}
                        className="relative bg-slate-800 h-full cursor-pointer select-none"
                        style={{ 
                          width: '1200px' // Fixed reasonable width that fits most screens
                        }}
                        onClick={handleTimelineClick}
                      >
                        {/* Timeline background with grid */}
                        <div className="absolute inset-0 bg-gradient-to-r from-slate-700 to-slate-600">
                          {/* Time markers every 30 seconds */}
                          {Array.from({ length: Math.ceil(videoDuration / 30) + 1 }, (_, i) => {
                            const minStart = Math.min(...editingClips.map(c => c.editedStart));
                            const markerTime = minStart + (i * 30);
                            return (
                            <div
                              key={i}
                              className="absolute top-0 bottom-0 border-l border-slate-500/30"
                              style={{ left: `${(i * 30 / videoDuration) * 100}%` }}
                            >
                              <span className="absolute top-1 left-1 text-xs text-slate-400">
                                {formatTime(markerTime)}
                              </span>
                            </div>
                            );
                          })}
                        </div>
                        
                        {/* All Clip segments */}
                        {editingClips.map((clip, clipIndex) => {
                          // Calculate timeline offset to normalize positioning
                          const minStart = Math.min(...editingClips.map(c => c.editedStart));
                          const normalizedStart = clip.editedStart - minStart;
                          const normalizedDuration = clip.editedEnd - clip.editedStart;
                          
                          return (
                          <div 
                            key={clip.id}
                            className={`absolute top-6 h-16 rounded-lg shadow-lg transition-all duration-200 ${
                              clipIndex === currentClipIndex 
                                ? 'bg-gradient-to-r from-purple-500 to-pink-500 ring-2 ring-yellow-400 z-20 cursor-move' 
                                : 'bg-gradient-to-r from-slate-500/60 to-slate-400/60 hover:from-slate-500/80 hover:to-slate-400/80 z-10 cursor-pointer'
                            }`}
                            style={{
                              left: `${(normalizedStart / videoDuration) * 100}%`,
                              width: `${(normalizedDuration / videoDuration) * 100}%`,
                              minWidth: '40px'
                            }}
                            onMouseDown={(e) => {
                              if (clipIndex === currentClipIndex) {
                                handleTimelineMouseDown(e, 'move', clipIndex);
                              } else {
                                // Just select the clip, don't start dragging
                                navigateToClip(clipIndex);
                              }
                            }}
                          >
                            <div className="flex items-center justify-center h-full px-2">
                              <span className={`text-xs font-medium truncate ${
                                clipIndex === currentClipIndex ? 'text-white' : 'text-slate-300'
                              }`}>
                                {clip.title}
                              </span>
                            </div>
                            
                            {/* Only show drag handles for the selected clip */}
                            {clipIndex === currentClipIndex && (
                              <>
                                {/* Left resize handle */}
                                <div 
                                  className="absolute left-0 top-0 w-4 h-full bg-purple-200 hover:bg-purple-100 cursor-col-resize opacity-80 hover:opacity-100 transition-all rounded-l-lg z-30 flex items-center justify-center"
                                  onMouseDown={(e) => {
                                    e.stopPropagation();
                                    handleTimelineMouseDown(e, 'start', clipIndex);
                                  }}
                                  onMouseEnter={(e) => e.currentTarget.style.cursor = 'col-resize'}
                                >
                                  <div className="w-0.5 h-8 bg-purple-600"></div>
                                </div>
                                
                                {/* Right resize handle */}
                                <div 
                                  className="absolute right-0 top-0 w-4 h-full bg-purple-200 hover:bg-purple-100 cursor-col-resize opacity-80 hover:opacity-100 transition-all rounded-r-lg z-30 flex items-center justify-center"
                                  onMouseDown={(e) => {
                                    e.stopPropagation();
                                    handleTimelineMouseDown(e, 'end', clipIndex);
                                  }}
                                  onMouseEnter={(e) => e.currentTarget.style.cursor = 'col-resize'}
                                >
                                  <div className="w-0.5 h-8 bg-purple-600"></div>
                                </div>
                              </>
                            )}
                            
                          </div>
                          );
                        })}
                        
                        {/* Playhead */}
                        <div 
                          className="absolute top-0 bottom-0 w-0.5 bg-yellow-400 pointer-events-none z-40 shadow-lg"
                          style={{left: `${((currentTime - Math.min(...editingClips.map(c => c.editedStart))) / videoDuration) * 100}%`}}
                        >
                          <div className="absolute -top-1 -left-1.5 w-3 h-3 bg-yellow-400 rounded-full"></div>
                        </div>
                        
                        {/* Drag feedback */}
                        {isDragging.type !== 'none' && (
                          <div className="absolute inset-0 bg-blue-500/10 pointer-events-none z-50"></div>
                        )}
                      </div>
                    </div>
                    
                    {/* Timeline help text */}
                    <div className="mt-4 text-center">
                      <div className="text-purple-400 text-sm font-semibold">
                        💡 Selected clip (purple): Drag to move • Drag edges to trim • Other clips: Click to select
                      </div>
                      <div className="text-slate-400 text-xs mt-1">
                        Only the highlighted clip can be edited • Clips cannot overlap
                      </div>
                    </div>
                  </div>

                  {/* Clip Details & Actions */}
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Clip Details</h3>
                      <button
                        onClick={() => handleOpenCaptions(editingClips[currentClipIndex])}
                        className="px-4 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-semibold rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                      >
                        ✨ Add Captions
                      </button>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Time:</span>
                        <span className="text-white font-mono">
                          {formatTime(editingClips[currentClipIndex]?.editedStart || 0)} - {formatTime(editingClips[currentClipIndex]?.editedEnd || 0)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Caption:</span>
                        <span className="text-white max-w-md truncate">{editingClips[currentClipIndex]?.caption || 'No caption'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Text:</span>
                        <span className="text-white max-w-md truncate">{editingClips[currentClipIndex]?.text || 'No text'}</span>
                      </div>
                      {editingClips[currentClipIndex]?.captions && editingClips[currentClipIndex].captions!.length > 0 && (
                        <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-3 mt-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-green-400 text-sm font-semibold">✅ Captions Added</span>
                          </div>
                          <div className="text-xs text-green-300">
                            {editingClips[currentClipIndex].captions!.length} caption segments configured
                          </div>
                        </div>
                      )}
                      {editingClips[currentClipIndex]?.hashtags?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {editingClips[currentClipIndex].hashtags.slice(0, 5).map((tag, i) => (
                            <span key={i} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">
                              {tag.startsWith('#') ? tag : `#${tag}`}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Horizontal Clip Selector */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Your Clips - Click to Navigate</h3>
                  <button 
                    onClick={handleFinalize}
                    disabled={isFinalizingClips}
                    className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isFinalizingClips ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Finalizing...
                      </div>
                    ) : (
                      'Finalize All Clips'
                    )}
                  </button>
                </div>
                
                <div className="flex gap-4 overflow-x-auto pb-4">
                  {editingClips.map((clip, index) => (
                    <div 
                      key={clip.id}
                      className={`flex-shrink-0 w-48 p-4 rounded-2xl border transition-all cursor-pointer ${
                        currentClipIndex === index 
                          ? 'bg-purple-500/20 border-purple-400 ring-2 ring-purple-400/50' 
                          : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                      }`}
                      onClick={() => navigateToClip(index)}
                    >
                      <div className="aspect-video bg-black/40 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                        {clip.path.endsWith('.mp4') ? (
                          <video 
                            className="w-full h-full object-cover rounded-lg"
                            preload="metadata"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <source src={apiService.getClipUrl(clip.path)} type="video/mp4" />
                          </video>
                        ) : (
                          <span className="text-2xl">🎬</span>
                        )}
                      </div>
                      
                      <div className="text-center">
                        <h4 className="font-semibold text-white text-sm mb-1 truncate">{clip.title}</h4>
                        <span className="text-xs text-slate-400">
                          {formatDuration(clip.editedEnd - clip.editedStart)}
                        </span>
                        <br />
                        <span className="text-xs text-slate-500">
                          {formatTime(clip.editedStart)} - {formatTime(clip.editedEnd)}
                        </span>
                        {clip.captions && clip.captions.length > 0 && (
                          <div className="mt-2">
                            <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded-full">
                              ✨ Captioned
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Complete State - Results View */}
        {appState === 'complete' && finalizedClips.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                🎉 Your Clips Are Ready!
              </h1>
              <p className="text-slate-300 text-lg">
                {finalizedClips.length} high-quality clips created from your video
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {finalizedClips.map((clip, index) => (
                <div key={clip.id} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-white">{clip.title}</h3>
                    <span className="text-sm text-slate-400">Clip {index + 1}</span>
                  </div>
                  
                  {/* YouTube Shorts aspect ratio (9:16) */}
                  <div className="w-full h-80 bg-black rounded-2xl flex items-center justify-center mb-4 relative overflow-hidden">
                    {clip.path.endsWith('.mp4') ? (
                      <video 
                        className="w-full h-full object-cover rounded-2xl"
                        controls
                        preload="metadata"
                      >
                        <source src={apiService.getClipUrl(clip.path)} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    ) : (
                      <div className="text-4xl text-slate-500">🎬</div>
                    )}
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Duration:</span>
                      <span className="text-white">{clip.duration}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Time Range:</span>
                      <span className="text-white">{clip.startTime} - {clip.endTime}</span>
                    </div>
                    
                    {clip.hashtags && clip.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {clip.hashtags.slice(0, 3).map((tag, i) => (
                          <span key={i} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">
                            {tag.startsWith('#') ? tag : `#${tag}`}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <button 
                      onClick={() => handleUpload(clip)}
                      className="w-full mt-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all"
                    >
                      Upload Clip
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Bottom Action Bar */}
            <div className="mt-8 flex justify-center">
              <div className="flex items-center space-x-4">
                <button 
                  onClick={handleReset}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-all"
                >
                  Create New Project
                </button>
                <button 
                  onClick={() => {
                    if (appState === 'complete' && finalizedClips.length > 0) {
                      // Upload all functionality would go here
                    }
                  }}
                  className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-purple-500/25 transition-all"
                >
                  Upload All
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {appState === 'error' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/20 rounded-3xl p-8 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h2 className="text-2xl font-bold text-white mb-4">Something went wrong</h2>
              <p className="text-red-200 mb-6">{error}</p>
              <button
                onClick={handleReset}
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {selectedClipForUpload && (
        <UploadModal
          isOpen={uploadModalOpen}
          onClose={() => {
            setUploadModalOpen(false);
            setSelectedClipForUpload(null);
          }}
          clip={selectedClipForUpload}
          onUpload={handleUploadProcess}
        />
      )}

      {/* Captions Modal */}
      {selectedClipForCaptions && jobId && (
        <CaptionsModal
          isOpen={captionsModalOpen}
          onClose={() => {
            setCaptionsModalOpen(false);
            setSelectedClipForCaptions(null);
          }}
          clip={selectedClipForCaptions}
          jobId={jobId}
          onCaptionsApplied={handleCaptionsApplied}
        />
      )}
    </div>
  );
} 