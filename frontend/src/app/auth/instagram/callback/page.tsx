'use client';

import { useEffect } from 'react';

export default function InstagramCallbackPage() {
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const error = urlParams.get('error');
      
      if (error) {
        // Send error to parent window
        window.opener?.postMessage({
          type: 'INSTAGRAM_AUTH_ERROR',
          error: error
        }, window.location.origin);
        window.close();
        return;
      }
      
      if (code) {
        try {
          // Exchange authorization code for access token
          const clientId = process.env.NEXT_PUBLIC_INSTAGRAM_CLIENT_ID;
          const clientSecret = process.env.NEXT_PUBLIC_INSTAGRAM_CLIENT_SECRET; // Note: In production, this should be handled server-side
          const redirectUri = `${window.location.origin}/auth/instagram/callback`;
          
          // Step 1: Exchange code for short-lived access token
          const tokenResponse = await fetch('https://api.instagram.com/oauth/access_token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              client_id: clientId || '',
              client_secret: clientSecret || '',
              grant_type: 'authorization_code',
              redirect_uri: redirectUri,
              code: code,
            }),
          });
          
          const tokenData = await tokenResponse.json();
          
          if (tokenData.access_token) {
            // Step 2: Exchange short-lived token for long-lived token
            const longLivedTokenResponse = await fetch(
              `https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=${clientSecret}&access_token=${tokenData.access_token}`,
              { method: 'GET' }
            );
            
            const longLivedTokenData = await longLivedTokenResponse.json();
            
            // Send success to parent window
            window.opener?.postMessage({
              type: 'INSTAGRAM_AUTH_SUCCESS',
              tokens: {
                accessToken: longLivedTokenData.access_token || tokenData.access_token,
                userId: tokenData.user_id,
              }
            }, window.location.origin);
          } else {
            throw new Error('No access token received');
          }
          
        } catch (error) {
          // Send error to parent window
          window.opener?.postMessage({
            type: 'INSTAGRAM_AUTH_ERROR',
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
        <p className="text-white">Processing Instagram authentication...</p>
      </div>
    </div>
  );
} 