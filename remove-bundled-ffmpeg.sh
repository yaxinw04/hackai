#!/bin/bash

# Remove Bundled FFmpeg Binary to Prevent Santa Restrictions
# This script removes the bundled FFmpeg that triggers Shopify Santa

echo "🗑️  Removing Bundled FFmpeg Binary"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd backend

if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run ./setup.sh first.${NC}"
    exit 1
fi

# Find the bundled FFmpeg binary
BUNDLED_FFMPEG=$(find venv -name "ffmpeg-*" -type f 2>/dev/null | head -1)

if [ -n "$BUNDLED_FFMPEG" ]; then
    echo -e "${BLUE}Found bundled FFmpeg: $BUNDLED_FFMPEG${NC}"
    
    # Create backup
    BACKUP_PATH="${BUNDLED_FFMPEG}.santa-backup"
    if [ ! -f "$BACKUP_PATH" ]; then
        echo -e "${YELLOW}Creating backup: $BACKUP_PATH${NC}"
        cp "$BUNDLED_FFMPEG" "$BACKUP_PATH"
    fi
    
    # Remove the bundled binary
    echo -e "${BLUE}Removing bundled FFmpeg binary...${NC}"
    rm -f "$BUNDLED_FFMPEG"
    
    # Create a symbolic link to system FFmpeg
    SYSTEM_FFMPEG=$(which ffmpeg)
    if [ -n "$SYSTEM_FFMPEG" ]; then
        echo -e "${GREEN}Creating symlink to system FFmpeg: $SYSTEM_FFMPEG${NC}"
        ln -sf "$SYSTEM_FFMPEG" "$BUNDLED_FFMPEG"
    else
        echo -e "${YELLOW}System FFmpeg not found. Creating a dummy script.${NC}"
        cat > "$BUNDLED_FFMPEG" << 'EOF'
#!/bin/bash
# Dummy FFmpeg script - redirects to system FFmpeg
if command -v ffmpeg >/dev/null 2>&1; then
    exec ffmpeg "$@"
else
    echo "Error: System FFmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi
EOF
        chmod +x "$BUNDLED_FFMPEG"
    fi
    
    echo -e "${GREEN}✅ Bundled FFmpeg replaced successfully${NC}"
else
    echo -e "${YELLOW}⚠️  No bundled FFmpeg found${NC}"
fi

# Also check imageio_ffmpeg binaries directory
IMAGEIO_DIR=$(find venv -path "*/imageio_ffmpeg/binaries" -type d 2>/dev/null | head -1)
if [ -n "$IMAGEIO_DIR" ]; then
    echo -e "${BLUE}Found imageio_ffmpeg binaries directory: $IMAGEIO_DIR${NC}"
    
    for binary in "$IMAGEIO_DIR"/ffmpeg-*; do
        if [ -f "$binary" ]; then
            echo -e "${BLUE}Processing: $(basename "$binary")${NC}"
            
            # Create backup
            BACKUP_PATH="${binary}.santa-backup"
            if [ ! -f "$BACKUP_PATH" ]; then
                cp "$binary" "$BACKUP_PATH"
            fi
            
            # Replace with symlink to system FFmpeg
            rm -f "$binary"
            SYSTEM_FFMPEG=$(which ffmpeg)
            if [ -n "$SYSTEM_FFMPEG" ]; then
                ln -sf "$SYSTEM_FFMPEG" "$binary"
                echo -e "${GREEN}   ✅ Replaced with symlink to $SYSTEM_FFMPEG${NC}"
            fi
        fi
    done
fi

cd ..

echo ""
echo -e "${GREEN}🎉 Bundled FFmpeg Removal Complete!${NC}"
echo "===================================="
echo ""
echo -e "${YELLOW}What was done:${NC}"
echo -e "• Backed up original bundled FFmpeg binaries"
echo -e "• Replaced them with symlinks to system FFmpeg"
echo -e "• This should prevent Santa from blocking the binaries"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Restart the application: ${GREEN}./start.sh${NC}"
echo -e "2. Test video processing functionality"
echo ""
echo -e "${YELLOW}To restore original binaries (if needed):${NC}"
echo -e "Find .santa-backup files in venv/ and rename them back" 