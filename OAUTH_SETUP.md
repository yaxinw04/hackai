# OAuth Setup Guide for YouTube Shorts AI

This guide explains how to set up OAuth credentials for YouTube and Instagram API integration.

## Required Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# OAuth Client IDs for Social Media Integration
# YouTube Data API v3
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
NEXT_PUBLIC_GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Instagram Basic Display API  
NEXT_PUBLIC_INSTAGRAM_CLIENT_ID=your_instagram_client_id_here
NEXT_PUBLIC_INSTAGRAM_CLIENT_SECRET=your_instagram_client_secret_here

# API Base URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## YouTube API Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the **YouTube Data API v3**

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Configure OAuth consent screen:
   - Application type: **Web application**
   - Name: `YouTube Shorts AI`
   - Authorized redirect URIs: `http://localhost:3000/auth/youtube/callback`

### 3. Required Scopes

- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

## Instagram API Setup

### 1. Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add **Instagram Basic Display** product

### 2. Configure Instagram Basic Display

1. Go to **Instagram Basic Display** → **Basic Display**
2. Create New App
3. Add OAuth Redirect URI: `http://localhost:3000/auth/instagram/callback`

### 3. Required Permissions

- `user_profile`
- `user_media`

## Backend Video Processing

### File Organization

The backend now organizes clips in a structured way:

```
backend/app/output_clips/{job_id}/
├── original_clips/          # Original extracted clips
│   ├── clip1.mp4
│   └── clip2.mp4
└── finalized_clips/         # Trimmed clips with edits
    ├── Highlight_1_final.mp4
    └── Highlight_2_final.mp4
```

### API Endpoints

- `POST /finalize/{job_id}` - Re-process clips with edited timings
- Video files are properly trimmed using FFmpeg
- Organized directory structure for better file management

## Features Implemented

### ✅ Video Processing
- **Actual video trimming** with edited start/end times
- **Organized output structure** (original_clips + finalized_clips)
- **FFmpeg integration** for fast, lossless trimming

### ✅ Social Media Integration
- **Real YouTube Data API v3** integration
- **Real Instagram Basic Display API** integration
- **OAuth 2.0 authentication** flows
- **Automatic video upload** to both platforms

### ✅ UI Improvements
- **Real YouTube/Instagram logos** (SVG icons)
- **Professional upload modal** with platform selection
- **Progress indicators** and error handling
- **Success/failure notifications**

## Usage Flow

1. **Edit clips** on the timeline (drag edges to trim)
2. **Click "Finalize All Clips"** → Backend re-processes videos with exact timings
3. **In results page**, click "Upload Clip"
4. **Connect social accounts** (YouTube/Instagram OAuth)
5. **Select platforms** + download option
6. **Click "Upload"** → Videos automatically posted

## Security Notes

⚠️ **Important**: In production, OAuth client secrets should be handled server-side, not in the frontend. The current implementation is for development/demo purposes.

For production:
- Move token exchange to backend API
- Store secrets securely (environment variables, secret managers)
- Implement proper token refresh mechanisms
- Add rate limiting and error handling

## Testing

1. Start the backend: `cd backend && python -m uvicorn app.main:main --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Create clips and test the full flow
4. Check the organized file structure in `backend/app/output_clips/`

The system now provides a complete end-to-end solution for creating, editing, and publishing YouTube Shorts with real API integrations! 🎬 