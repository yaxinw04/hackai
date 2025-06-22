#!/bin/bash

# FFmpeg Fix for Shopify Santa / Corporate Environments
# Run this script if you're getting Santa security warnings

echo "🔧 FFmpeg Fix for Shopify/Corporate Environments"
echo "================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're in a Shopify environment
if [[ "$USER" == *shopify* ]] || [[ "$HOME" == *shopify* ]] || command -v santa >/dev/null 2>&1; then
    echo -e "${YELLOW}🏢 Shopify environment detected${NC}"
    SHOPIFY_ENV=true
else
    SHOPIFY_ENV=false
fi

echo ""
echo -e "${BLUE}1. Checking current FFmpeg status...${NC}"

if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg_path=$(which ffmpeg)
    echo -e "${GREEN}   ✅ FFmpeg found at: $ffmpeg_path${NC}"
    
    # Test if it's accessible
    if ffmpeg -version >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ FFmpeg is working properly${NC}"
        FFMPEG_WORKING=true
    else
        echo -e "${RED}   ❌ FFmpeg found but not accessible (Santa blocked?)${NC}"
        FFMPEG_WORKING=false
    fi
else
    echo -e "${YELLOW}   ⚠️  FFmpeg not found${NC}"
    FFMPEG_WORKING=false
fi

echo ""
echo -e "${BLUE}2. Setting up environment variables...${NC}"

# Set environment variables to force system FFmpeg usage
export USE_SYSTEM_FFMPEG=1
export IMAGEIO_FFMPEG_EXE=$(which ffmpeg 2>/dev/null || echo "")

echo -e "${GREEN}   ✅ USE_SYSTEM_FFMPEG=1${NC}"
if [ -n "$IMAGEIO_FFMPEG_EXE" ]; then
    echo -e "${GREEN}   ✅ IMAGEIO_FFMPEG_EXE=$IMAGEIO_FFMPEG_EXE${NC}"
fi

# Add to shell profile for persistence
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "USE_SYSTEM_FFMPEG" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Force MoviePy to use system FFmpeg (avoid Santa restrictions)" >> "$SHELL_RC"
        echo "export USE_SYSTEM_FFMPEG=1" >> "$SHELL_RC"
        if [ -n "$IMAGEIO_FFMPEG_EXE" ]; then
            echo "export IMAGEIO_FFMPEG_EXE=$IMAGEIO_FFMPEG_EXE" >> "$SHELL_RC"
        fi
        echo -e "${GREEN}   ✅ Added to $SHELL_RC for persistence${NC}"
    fi
fi

echo ""
echo -e "${BLUE}3. Installing/updating FFmpeg...${NC}"

if [ "$SHOPIFY_ENV" = true ]; then
    echo -e "${YELLOW}   📋 Shopify environment detected. Checking approved installation methods...${NC}"
    
    # Check if Homebrew is available and approved
    if command -v brew >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Homebrew found${NC}"
        if ! $FFMPEG_WORKING; then
            echo -e "${BLUE}   Installing FFmpeg via Homebrew...${NC}"
            if brew install ffmpeg; then
                echo -e "${GREEN}   ✅ FFmpeg installed successfully${NC}"
            else
                echo -e "${RED}   ❌ FFmpeg installation failed${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}   ⚠️  Homebrew not found${NC}"
        echo -e "${YELLOW}   Contact IT about installing FFmpeg through approved channels${NC}"
    fi
else
    # Non-Shopify environment
    if command -v brew >/dev/null 2>&1; then
        echo -e "${BLUE}   Installing FFmpeg via Homebrew...${NC}"
        brew install ffmpeg
    elif command -v apt-get >/dev/null 2>&1; then
        echo -e "${BLUE}   Installing FFmpeg via apt...${NC}"
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo -e "${YELLOW}   ⚠️  Please install FFmpeg manually for your system${NC}"
    fi
fi

echo ""
echo -e "${BLUE}4. Testing the fix...${NC}"

# Test if MoviePy can now work
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    
    # Test MoviePy import
    if python3 -c "
import os
os.environ['USE_SYSTEM_FFMPEG'] = '1'
try:
    from moviepy.editor import VideoFileClip
    print('✅ MoviePy import successful')
except Exception as e:
    print(f'❌ MoviePy import failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}   ✅ MoviePy can now use system FFmpeg${NC}"
        TEST_PASSED=true
    else
        echo -e "${RED}   ❌ MoviePy still having issues${NC}"
        TEST_PASSED=false
    fi
else
    echo -e "${YELLOW}   ⚠️  Virtual environment not found, skipping test${NC}"
    TEST_PASSED=false
fi

cd ..

echo ""
echo -e "${GREEN}🎉 Fix Complete!${NC}"
echo "=================="

if [ "$TEST_PASSED" = true ]; then
    echo -e "${GREEN}✅ FFmpeg is now working with MoviePy${NC}"
    echo -e "${GREEN}✅ Santa restrictions bypassed${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "   1. Restart your terminal or run: ${GREEN}source ~/.zshrc${NC}"
    echo -e "   2. Run your application: ${GREEN}./start.sh${NC}"
else
    echo -e "${YELLOW}⚠️  Additional steps may be needed${NC}"
    echo ""
    echo -e "${BLUE}Manual solutions:${NC}"
    echo -e "   1. Restart terminal and try again"
    echo -e "   2. Contact IT about FFmpeg binary approval"
    echo -e "   3. Use demo mode (no real video processing)"
fi

echo ""
echo -e "${YELLOW}💡 Environment variables set:${NC}"
echo -e "   USE_SYSTEM_FFMPEG=1"
echo -e "   IMAGEIO_FFMPEG_EXE=$(which ffmpeg 2>/dev/null || echo 'not found')"
echo ""
echo -e "${YELLOW}📚 For more help:${NC}"
echo -e "   • Shopify Kepler: Search for 'ffmpeg approval'"
echo -e "   • Or run in demo mode without real video processing" 