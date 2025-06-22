import axios from 'axios';

// API Base URL - adjust this based on your backend configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// TypeScript interfaces for API request/response types
export interface ProcessRequest {
  url: string;
  prompt: string;
}

export interface ProcessResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  status: string;
  message: string;
  results?: any[];
  is_demo?: boolean;
  metadata?: any;
}

export interface FinalizeResponse {
  status: string;
  message: string;
  finalized_clips: any[];
  organization: {
    original_clips: string;
    finalized_clips: string;
  };
}

export interface CaptionSegment {
  start: number;
  end: number;
  text: string;
  confidence?: number;
}

export interface CaptionStyle {
  fontSize: number;
  fontColor: string;
  backgroundColor: string;
  backgroundOpacity: number;
  outlineColor: string;
  outlineWidth: number;
  position: 'top' | 'center' | 'bottom';
  animation: 'none' | 'pop' | 'slide' | 'typewriter';
}

export interface GenerateCaptionsRequest {
  jobId: string;
  clipId: string;
  style?: CaptionStyle;
}

export interface GenerateCaptionsResponse {
  status: string;
  message: string;
  captions: CaptionSegment[];
  previewUrl?: string;
}

// API service functions
export const apiService = {
  /**
   * Start processing a YouTube video
   */
  async startProcessing(url: string, prompt: string): Promise<ProcessResponse> {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, prompt }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get the status of a processing job
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/status/${jobId}`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Finalize clips
   */
  async finalizeClips(jobId: string, editedClips: any[]): Promise<FinalizeResponse> {
    const response = await fetch(`${API_BASE_URL}/finalize/${jobId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ edited_clips: editedClips }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Upload video to YouTube
   */
  async uploadToYouTube(videoFile: File, metadata: {
    title: string;
    description: string;
    tags: string[];
    accessToken: string;
  }): Promise<any> {
    // YouTube Data API v3 multipart upload
    const videoMetadata = {
      snippet: {
        title: metadata.title,
        description: metadata.description,
        tags: metadata.tags,
        categoryId: '22', // People & Blogs
        defaultLanguage: 'en',
        defaultAudioLanguage: 'en'
      },
      status: {
        privacyStatus: 'public',
        madeForKids: false,
        selfDeclaredMadeForKids: false
      }
    };

    // Create multipart boundary
    const boundary = `upload_boundary_${Date.now()}`;
    
    // Create multipart body
    const delimiter = `\r\n--${boundary}\r\n`;
    const closeDelimiter = `\r\n--${boundary}--`;

    // Convert video file to ArrayBuffer
    const videoBuffer = await videoFile.arrayBuffer();

    // Build multipart body
    let body = delimiter;
    body += 'Content-Type: application/json\r\n\r\n';
    body += JSON.stringify(videoMetadata);
    body += delimiter;
    body += `Content-Type: ${videoFile.type || 'video/mp4'}\r\n\r\n`;

    // Convert body string to Uint8Array
    const bodyStart = new TextEncoder().encode(body);
    const bodyEnd = new TextEncoder().encode(closeDelimiter);

    // Combine all parts
    const fullBody = new Uint8Array(bodyStart.length + videoBuffer.byteLength + bodyEnd.length);
    fullBody.set(bodyStart, 0);
    fullBody.set(new Uint8Array(videoBuffer), bodyStart.length);
    fullBody.set(bodyEnd, bodyStart.length + videoBuffer.byteLength);

    const response = await fetch('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${metadata.accessToken}`,
        'Content-Type': `multipart/related; boundary="${boundary}"`,
      },
      body: fullBody
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`YouTube upload failed: ${response.status} ${response.statusText}. ${errorText}`);
    }

    return response.json();
  },

  /**
   * Upload video to Instagram
   */
  async uploadToInstagram(videoFile: File, metadata: {
    caption: string;
    accessToken: string;
    userId: string;
  }): Promise<any> {
    // Instagram Basic Display API integration
    // Step 1: Upload video to Instagram
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('caption', metadata.caption);
    formData.append('access_token', metadata.accessToken);

    const response = await fetch(`https://graph.instagram.com/${metadata.userId}/media`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Instagram upload failed: ${response.status} ${response.statusText}`);
    }

    const uploadResult = await response.json();

    // Step 2: Publish the media
    const publishResponse = await fetch(`https://graph.instagram.com/${metadata.userId}/media_publish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        creation_id: uploadResult.id,
        access_token: metadata.accessToken
      })
    });

    if (!publishResponse.ok) {
      throw new Error(`Instagram publish failed: ${publishResponse.status} ${publishResponse.statusText}`);
    }

    return publishResponse.json();
  },

  /**
   * Authenticate YouTube
   */
  async authenticateYouTube(): Promise<{ accessToken: string; refreshToken: string }> {
    // Google OAuth 2.0 flow for YouTube
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/youtube/callback`;
    
    const scope = 'https://www.googleapis.com/auth/youtube.upload';
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${clientId}&` +
      `redirect_uri=${redirectUri}&` +
      `scope=${scope}&` +
      `response_type=code&` +
      `access_type=offline&` +
      `prompt=consent`;

    // Open OAuth window
    const authWindow = window.open(authUrl, 'youtube_auth', 'width=500,height=600');
    
    return new Promise((resolve, reject) => {
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed);
          reject(new Error('Authentication cancelled'));
        }
      }, 1000);

      // Listen for message from popup
      const messageListener = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'YOUTUBE_AUTH_SUCCESS') {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          authWindow?.close();
          resolve(event.data.tokens);
        } else if (event.data.type === 'YOUTUBE_AUTH_ERROR') {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          authWindow?.close();
          reject(new Error(event.data.error));
        }
      };

      window.addEventListener('message', messageListener);
    });
  },

  /**
   * Authenticate Instagram
   */
  async authenticateInstagram(): Promise<{ accessToken: string; userId: string }> {
    // Instagram Basic Display API OAuth flow
    const clientId = process.env.NEXT_PUBLIC_INSTAGRAM_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/instagram/callback`;
    
    const scope = 'user_profile,user_media';
    const authUrl = `https://api.instagram.com/oauth/authorize?` +
      `client_id=${clientId}&` +
      `redirect_uri=${redirectUri}&` +
      `scope=${scope}&` +
      `response_type=code`;

    // Open OAuth window
    const authWindow = window.open(authUrl, 'instagram_auth', 'width=500,height=600');
    
    return new Promise((resolve, reject) => {
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed);
          reject(new Error('Authentication cancelled'));
        }
      }, 1000);

      // Listen for message from popup
      const messageListener = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'INSTAGRAM_AUTH_SUCCESS') {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          authWindow?.close();
          resolve(event.data.tokens);
        } else if (event.data.type === 'INSTAGRAM_AUTH_ERROR') {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          authWindow?.close();
          reject(new Error(event.data.error));
        }
      };

      window.addEventListener('message', messageListener);
    });
  },

  /**
   * Generate captions for a specific clip
   */
  async generateCaptions(jobId: string, clipId: string, style?: CaptionStyle): Promise<GenerateCaptionsResponse> {
    const response = await fetch(`${API_BASE_URL}/captions/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ jobId, clipId, style }),
    });

    if (!response.ok) {
      throw new Error(`Caption generation failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Apply captions to a video clip
   */
  async applyCaptions(jobId: string, clipId: string, captions: CaptionSegment[], style: CaptionStyle): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/captions/apply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ jobId, clipId, captions, style }),
    });

    if (!response.ok) {
      throw new Error(`Caption application failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get the full URL for a clip
   */
  getClipUrl(path: string): string {
    if (path.startsWith('http')) {
      return path;
    }
    return `${API_BASE_URL}${path}`;
  },
};

export default apiService; 