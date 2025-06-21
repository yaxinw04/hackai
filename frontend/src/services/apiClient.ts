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
  results?: string[] | null;
}

// API service functions
export const apiService = {
  /**
   * Start processing a YouTube video
   */
  async startProcessing(url: string, prompt: string): Promise<ProcessResponse> {
    try {
      const response = await apiClient.post<ProcessResponse>('/process', {
        url,
        prompt,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to start processing');
      }
      throw new Error('Network error occurred');
    }
  },

  /**
   * Get the status of a processing job
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    try {
      const response = await apiClient.get<JobStatusResponse>(`/status/${jobId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to get job status');
      }
      throw new Error('Network error occurred');
    }
  },

  /**
   * Get the full URL for a clip
   */
  getClipUrl(clipPath: string): string {
    return `${API_BASE_URL}${clipPath}`;
  },
};

export default apiService; 