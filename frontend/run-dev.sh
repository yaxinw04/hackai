#!/bin/bash

echo "🚀 Starting YouTube Shorts AI Frontend..."
echo "🎨 Beautiful UI loading..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🔥 Starting Next.js development server..."
npm run dev 