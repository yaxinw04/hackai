'use client';

import { useEffect } from 'react';

export default function YouTubeCallbackPage() {
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const error = urlParams.get('error');
      
      if (error) {
        // Send error to parent window
        window.opener?.postMessage({
          type: 'YOUTUBE_AUTH_ERROR',
          error: error
        }, window.location.origin);
        window.close();
        return;
      }
      
      if (code) {
        try {
          // Exchange authorization code for access token
          const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
          const clientSecret = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET; // Note: In production, this should be handled server-side
          const redirectUri = `${window.location.origin}/auth/youtube/callback`;
          
          const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              client_id: clientId || '',
              client_secret: clientSecret || '',
              code: code,
              grant_type: 'authorization_code',
              redirect_uri: redirectUri,
            }),
          });
          
          const tokenData = await tokenResponse.json();
          
          if (tokenData.access_token) {
            // Send success to parent window
            window.opener?.postMessage({
              type: 'YOUTUBE_AUTH_SUCCESS',
              tokens: {
                accessToken: tokenData.access_token,
                refreshToken: tokenData.refresh_token,
              }
            }, window.location.origin);
          } else {
            throw new Error('No access token received');
          }
          
        } catch (error) {
          // Send error to parent window
          window.opener?.postMessage({
            type: 'YOUTUBE_AUTH_ERROR',
            error: error instanceof Error ? error.message : 'Unknown error'
          }, window.location.origin);
        }
      }
      
      window.close();
    };
    
    handleCallback();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
        <p className="text-white">Processing YouTube authentication...</p>
      </div>
    </div>
  );
} 