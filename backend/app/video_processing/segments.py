"""
Video segment detection and scoring processor.
"""

import os
import math
from typing import List, Dict, Any


def detect_segments(video_path: str, transcript_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect potential video segments based on transcript and video analysis.
    
    Args:
        video_path: Path to the video file
        transcript_segments: List of transcript segments from transcription
        
    Returns:
        List of video chunks with metadata
    """
    chunks = []
    
    # Group transcript segments into larger chunks (15-60 second clips)
    min_duration = 10  # minimum clip duration in seconds
    max_duration = 60  # maximum clip duration in seconds
    target_duration = 30  # target clip duration in seconds
    
    current_chunk = {
        'start': 0,
        'end': 0,
        'text': '',
        'segments': []
    }
    
    for i, segment in enumerate(transcript_segments):
        # If this is the first segment, start a new chunk
        if not current_chunk['segments']:
            current_chunk['start'] = segment['start']
            current_chunk['text'] = segment['text']
            current_chunk['segments'].append(segment)
        else:
            # Calculate current chunk duration
            potential_end = segment['end']
            current_duration = potential_end - current_chunk['start']
            
            # If adding this segment would make the chunk too long, finalize current chunk
            if current_duration > max_duration:
                current_chunk['end'] = current_chunk['segments'][-1]['end']
                current_chunk['duration'] = current_chunk['end'] - current_chunk['start']
                chunks.append(current_chunk.copy())
                
                # Start new chunk
                current_chunk = {
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'segments': [segment]
                }
            else:
                # Add segment to current chunk
                current_chunk['text'] += ' ' + segment['text']
                current_chunk['segments'].append(segment)
                current_chunk['end'] = segment['end']
    
    # Don't forget the last chunk
    if current_chunk['segments']:
        current_chunk['end'] = current_chunk['segments'][-1]['end']
        current_chunk['duration'] = current_chunk['end'] - current_chunk['start']
        chunks.append(current_chunk)
    
    # Filter chunks by minimum duration
    valid_chunks = [chunk for chunk in chunks if chunk.get('duration', 0) >= min_duration]
    
    print(f"📝 Created {len(valid_chunks)} video chunks from {len(transcript_segments)} transcript segments")
    
    return valid_chunks


def score_segments(chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Score video chunks based on various factors and return the top K.
    
    Args:
        chunks: List of video chunks
        top_k: Number of top chunks to return
        
    Returns:
        List of top-scored chunks
    """
    
    def calculate_engagement_score(chunk: Dict[str, Any]) -> float:
        """Calculate engagement score based on text content."""
        text = chunk['text'].lower()
        score = 0.0
        
        # Positive engagement indicators
        positive_words = [
            'amazing', 'incredible', 'wow', 'awesome', 'fantastic', 
            'perfect', 'love', 'best', 'great', 'excellent',
            'mind-blowing', 'unbelievable', 'insane', 'crazy',
            'secret', 'hack', 'tip', 'trick', 'method',
            'result', 'proven', 'works', 'success', 'winner'
        ]
        
        excitement_words = [
            'excited', 'pumped', 'thrilled', 'stoked',
            '!', 'really', 'super', 'so', 'very'
        ]
        
        hook_phrases = [
            'you won\'t believe', 'this is crazy', 'check this out',
            'wait for it', 'here\'s the thing', 'plot twist',
            'but here\'s what happened', 'this changed everything'
        ]
        
        # Score based on positive words
        for word in positive_words:
            if word in text:
                score += 0.3
        
        # Score based on excitement
        for word in excitement_words:
            if word in text:
                score += 0.2
        
        # Score based on hook phrases
        for phrase in hook_phrases:
            if phrase in text:
                score += 0.5
        
        # Length penalty/bonus (prefer 20-45 second clips)
        duration = chunk.get('duration', 30)
        if 20 <= duration <= 45:
            score += 0.4
        elif duration < 15 or duration > 60:
            score -= 0.3
        
        # Confidence score from transcription
        avg_confidence = sum(seg.get('confidence', 0.8) for seg in chunk.get('segments', [])) / max(len(chunk.get('segments', [])), 1)
        score += avg_confidence * 0.2
        
        return score
    
    def calculate_timing_score(chunk: Dict[str, Any], position: int, total: int) -> float:
        """Calculate score based on position in video."""
        # Slightly prefer content from the beginning and middle
        relative_position = position / max(total - 1, 1)
        
        if relative_position < 0.2:  # Beginning
            return 0.2
        elif relative_position < 0.8:  # Middle
            return 0.3
        else:  # End
            return 0.1
    
    # Score all chunks
    for i, chunk in enumerate(chunks):
        engagement_score = calculate_engagement_score(chunk)
        timing_score = calculate_timing_score(chunk, i, len(chunks))
        
        # Combine scores
        chunk['engagement_score'] = engagement_score
        chunk['timing_score'] = timing_score
        chunk['total_score'] = engagement_score + timing_score
        
        # Add some metadata for the UI
        chunk['title'] = generate_chunk_title(chunk, i + 1)
    
    # Sort by total score and return top K
    sorted_chunks = sorted(chunks, key=lambda x: x['total_score'], reverse=True)
    top_chunks = sorted_chunks[:top_k]
    
    # Sort the top chunks by start time for a natural order
    top_chunks.sort(key=lambda x: x['start'])
    
    print(f"🏆 Selected top {len(top_chunks)} chunks based on engagement and timing scores")
    
    return top_chunks


def generate_chunk_title(chunk: Dict[str, Any], index: int) -> str:
    """Generate a title for a video chunk based on its content."""
    text = chunk['text'].lower()
    
    # Define title patterns based on content
    if any(word in text for word in ['welcome', 'intro', 'start', 'begin']):
        return f"Opening Hook"
    elif any(word in text for word in ['secret', 'hack', 'tip', 'trick']):
        return f"Pro Tip"
    elif any(word in text for word in ['result', 'outcome', 'what happened']):
        return f"Big Reveal"
    elif any(word in text for word in ['crazy', 'insane', 'unbelievable', 'incredible']):
        return f"Viral Moment"
    elif any(word in text for word in ['important', 'key', 'main', 'crucial']):
        return f"Key Insight"
    elif any(word in text for word in ['final', 'last', 'conclusion', 'wrap']):
        return f"Perfect Ending"
    elif any(word in text for word in ['funny', 'hilarious', 'laugh']):
        return f"Comedy Gold"
    elif any(word in text for word in ['emotional', 'touching', 'heart']):
        return f"Emotional Peak"
    else:
        return f"Highlight #{index}" 