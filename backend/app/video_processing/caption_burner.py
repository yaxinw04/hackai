"""
Caption burning processor for YouTube Shorts style captions.
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..schemas import CaptionSegment, CaptionStyle


def create_subtitle_file(captions: List[CaptionSegment], output_path: str) -> str:
    """Create an ASS subtitle file with YouTube Shorts styling."""
    
    ass_content = f"""[Script Info]
Title: YouTube Shorts Captions
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsCaption,Arial Black,{{}},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for caption in captions:
        start_time = seconds_to_ass_time(caption.start)
        end_time = seconds_to_ass_time(caption.end)
        text = caption.text.replace('\n', '\\N')
        ass_content += f"Dialogue: 0,{start_time},{end_time},ShortsCaption,,0,0,0,,{text}\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    return output_path


def seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.CC)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def create_youtube_shorts_filter(captions: List[CaptionSegment], style: CaptionStyle) -> str:
    """Create FFmpeg filter for YouTube Shorts style captions."""
    
    # Convert colors from hex to BGR for FFmpeg
    def hex_to_bgr(hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
    
    # Position mapping
    position_map = {
        'top': 8,     # Top center
        'center': 2,  # Middle center  
        'bottom': 2   # Bottom center (will adjust with MarginV)
    }
    
    margin_v = 50 if style.position == 'bottom' else 10
    alignment = position_map[style.position]
    
    # Background color with opacity
    bg_color = hex_to_bgr(style.backgroundColor) if style.backgroundColor != 'transparent' else '&H00000000'
    bg_alpha = int((1 - style.backgroundOpacity) * 255)
    bg_color_alpha = f"&H{bg_alpha:02X}{style.backgroundColor[5:7] if len(style.backgroundColor) >= 7 else '00'}{style.backgroundColor[3:5] if len(style.backgroundColor) >= 5 else '00'}{style.backgroundColor[1:3] if len(style.backgroundColor) >= 3 else '00'}"
    
    outline_color = hex_to_bgr(style.outlineColor)
    font_color = hex_to_bgr(style.fontColor)
    
    # Create the subtitle filter
    drawtext_filters = []
    
    for i, caption in enumerate(captions):
        start_time = caption.start
        end_time = caption.end
        text = caption.text.replace("'", "\\'").replace(":", "\\:")
        
        # Animation effects
        if style.animation == 'pop':
            # Scale animation
            scale_filter = f"if(between(t,{start_time},{start_time+0.2}),1+0.5*sin(2*PI*(t-{start_time})/0.2),1)"
        elif style.animation == 'slide':
            # Slide in from side
            x_offset = f"if(between(t,{start_time},{start_time+0.3}),w*(1-(t-{start_time})/0.3),(w-text_w)/2)"
        elif style.animation == 'typewriter':
            # Typewriter effect (simplified)
            text_progress = f"if(between(t,{start_time},{end_time}),floor((t-{start_time})/({end_time-start_time})*{len(text)}),{len(text)})"
        else:
            scale_filter = "1"
            x_offset = "(w-text_w)/2"
        
        # Positioning
        if style.position == 'top':
            y_pos = f"{margin_v}+{style.fontSize}"
        elif style.position == 'center':
            y_pos = "(h-text_h)/2"
        else:  # bottom
            y_pos = f"h-text_h-{margin_v}"
        
        if style.animation != 'slide':
            x_offset = "(w-text_w)/2"
        
        # Build the drawtext filter
        filter_parts = [
            f"drawtext=enable='between(t,{start_time},{end_time})'",
            f"text='{text}'",
            f"fontfile=/System/Library/Fonts/Arial\\ Black.ttf",
            f"fontsize={style.fontSize}",
            f"fontcolor={font_color}",
            f"x={x_offset}",
            f"y={y_pos}",
            f"borderw={style.outlineWidth}",
            f"bordercolor={outline_color}",
            f"box=1",
            f"boxcolor={bg_color_alpha}",
            f"boxborderw=5"
        ]
        
        if style.animation == 'pop':
            filter_parts.append(f"fontsize={style.fontSize}*{scale_filter}")
        
        drawtext_filters.append(":".join(filter_parts))
    
    # Combine all drawtext filters
    return ",".join(drawtext_filters)


def create_word_by_word_captions(captions: List[CaptionSegment]) -> List[CaptionSegment]:
    """Break captions into word-by-word segments for typewriter effect."""
    word_captions = []
    
    for caption in captions:
        words = caption.text.split()
        if not words:
            continue
            
        caption_duration = caption.end - caption.start
        words_per_second = len(words) / caption_duration if caption_duration > 0 else 2
        word_duration = min(0.5, max(0.2, 1 / words_per_second))  # Between 0.2 and 0.5 seconds per word
        
        current_time = caption.start
        accumulated_text = ""
        
        for i, word in enumerate(words):
            accumulated_text += word
            if i < len(words) - 1:
                accumulated_text += " "
            
            # Calculate end time for this word segment
            next_time = min(current_time + word_duration, caption.end)
            
            word_captions.append(CaptionSegment(
                start=current_time,
                end=next_time,
                text=accumulated_text,
                confidence=caption.confidence
            ))
            
            current_time = next_time
            
            # If we've reached the end time, break
            if current_time >= caption.end:
                break
    
    return word_captions


def burn_captions_ffmpeg(
    input_video: str, 
    output_video: str, 
    captions: List[CaptionSegment], 
    style: CaptionStyle
) -> bool:
    """Burn captions into video using FFmpeg with YouTube Shorts styling."""
    
    try:
        # Convert to word-by-word captions if typewriter animation is selected
        if style.animation == 'typewriter':
            captions = create_word_by_word_captions(captions)
        
        # Create a temporary subtitle file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
            subtitle_file = f.name
            
            # Write SRT format subtitles
            for i, caption in enumerate(captions, 1):
                start_time = format_srt_time(caption.start)
                end_time = format_srt_time(caption.end)
                f.write(f"{i}\n{start_time} --> {end_time}\n{caption.text}\n\n")
        
        # Position mapping for subtitle filter - optimized for YouTube Shorts
        position_map = {
            'top': 'Alignment=8,MarginV=60',  # Top with good margin
            'center': 'Alignment=2,MarginV=0',  # Center
            'bottom': 'Alignment=2,MarginV=200'  # Much lower bottom position
        }
        
        # Convert hex colors to decimal for subtitles filter
        def hex_to_decimal(hex_color: str) -> int:
            return int(hex_color.lstrip('#'), 16)
        
        font_color = hex_to_decimal(style.fontColor)
        outline_color = hex_to_decimal(style.outlineColor)
        bg_color = hex_to_decimal(style.backgroundColor) if style.backgroundColor != 'transparent' else 0
        
        # Build subtitle style optimized for mobile viewing
        subtitle_style = (
            f"FontName=Arial Black,"
            f"FontSize={style.fontSize},"
            f"PrimaryColour=&H{font_color:08X},"
            f"OutlineColour=&H{outline_color:08X},"
            f"BackColour=&H{bg_color:08X},"
            f"Bold=1,"
            f"Outline={style.outlineWidth},"
            f"Shadow=0,"  # No shadow for cleaner look
            f"BorderStyle=1,"  # Outline only
            f"Spacing=2,"  # Slight letter spacing for readability
            f"{position_map[style.position]}"
        )
        
        # FFmpeg command for burning subtitles
        cmd = [
            'ffmpeg', '-y',
            '-i', input_video,
            '-vf', f"subtitles={subtitle_file}:force_style='{subtitle_style}'",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            output_video
        ]
        
        print(f"🎬 Running FFmpeg caption burn with word-by-word animation")
        print(f"📍 Position: {style.position}, Font: {style.fontSize}px, Animation: {style.animation}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temporary file
        os.unlink(subtitle_file)
        
        if result.returncode == 0:
            print(f"✅ Successfully burned {len(captions)} caption segments into {output_video}")
            return True
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error burning captions: {e}")
        return False


def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def apply_captions_to_video(
    input_video_path: str,
    output_video_path: str,
    captions: List[Dict[str, Any]],
    style: Dict[str, Any]
) -> bool:
    """
    Apply captions to a video file with YouTube Shorts styling.
    
    Args:
        input_video_path: Path to input video
        output_video_path: Path for output video with captions
        captions: List of caption segments
        style: Caption styling options
        
    Returns:
        True if successful, False otherwise
    """
    
    try:
        # Convert dictionaries to Pydantic models
        caption_segments = [CaptionSegment(**cap) for cap in captions]
        caption_style = CaptionStyle(**style)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        # Burn captions using FFmpeg
        success = burn_captions_ffmpeg(
            input_video_path,
            output_video_path,
            caption_segments,
            caption_style
        )
        
        return success
        
    except Exception as e:
        print(f"❌ Failed to apply captions: {e}")
        return False 