"""
Caption and hashtag generation processor.
"""

import os
import random
from typing import List, Dict, Any

# Try to import OpenAI, fallback gracefully
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def generate_captions_with_ai(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate captions using OpenAI API."""
    if not OPENAI_AVAILABLE:
        raise Exception("openai package required. Install with: pip install openai")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception("OPENAI_API_KEY environment variable required")
    
    client = openai.OpenAI(api_key=api_key)
    
    enhanced_chunks = []
    
    for i, chunk in enumerate(chunks):
        try:
            # Create prompt for caption generation
            prompt = f"""
            Create an engaging social media caption for this video clip content:
            
            Content: "{chunk['text']}"
            Duration: {chunk.get('duration', 30):.1f} seconds
            
            Generate:
            1. A catchy title (max 8 words)
            2. An engaging caption (max 150 characters) 
            3. 5-8 relevant hashtags
            4. A hook line to grab attention
            
            Format as JSON:
            {{
                "title": "...",
                "caption": "...",
                "hashtags": ["#tag1", "#tag2", ...],
                "hook": "..."
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            # Parse the response
            import json
            ai_content = json.loads(response.choices[0].message.content)
            
            # Add AI-generated content to chunk
            chunk['title'] = ai_content.get('title', chunk.get('title', f'Clip {i+1}'))
            chunk['caption'] = ai_content.get('caption', '')
            chunk['hashtags'] = ai_content.get('hashtags', [])
            chunk['hook'] = ai_content.get('hook', '')
            
        except Exception as e:
            print(f"AI caption generation failed for chunk {i+1}: {e}")
            # Fallback to mock generation for this chunk
            chunk = generate_mock_caption(chunk, i)
        
        enhanced_chunks.append(chunk)
    
    return enhanced_chunks


def generate_mock_captions(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mock captions for demo purposes."""
    
    caption_templates = [
        "This will blow your mind! 🤯",
        "You need to see this! 👀",
        "Game changer right here! 🔥",
        "This is incredible! ✨",
        "Mind = blown! 💫",
        "Wait for it... 🎯",
        "This changes everything! 🚀",
        "You won't believe this! 😱"
    ]
    
    hashtag_sets = [
        ["#viral", "#mindblown", "#mustsee", "#incredible", "#wow"],
        ["#gamechange", "#amazing", "#viral", "#trending", "#fire"],
        ["#shocking", "#unbelievable", "#epic", "#viral", "#omg"],
        ["#mindblowing", "#insane", "#viral", "#mustwatch", "#crazy"],
        ["#incredible", "#amazing", "#viral", "#trending", "#wow"],
        ["#epic", "#gamechange", "#viral", "#fire", "#insane"],
        ["#shocking", "#mindblown", "#viral", "#amazing", "#wtf"],
        ["#unreal", "#incredible", "#viral", "#epic", "#mindblowing"]
    ]
    
    hook_templates = [
        "Wait until you see this...",
        "This is about to get crazy!",
        "You're not ready for this!",
        "Plot twist incoming...",
        "This will change your perspective!",
        "Brace yourself for this one!",
        "You'll never guess what happens!",
        "This is pure gold!"
    ]
    
    enhanced_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Keep existing title or generate one
        if 'title' not in chunk:
            chunk['title'] = f"Viral Moment #{i+1}"
        
        # Generate caption
        caption_template = random.choice(caption_templates)
        chunk['caption'] = caption_template
        
        # Generate hashtags
        hashtag_set = random.choice(hashtag_sets)
        chunk['hashtags'] = hashtag_set
        
        # Generate hook
        hook = random.choice(hook_templates)
        chunk['hook'] = hook
        
        enhanced_chunks.append(chunk)
    
    return enhanced_chunks


def generate_mock_caption(chunk: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Generate a single mock caption for a chunk."""
    return generate_mock_captions([chunk])[0]


def generate_platform_optimized_captions(chunks: List[Dict[str, Any]], platform: str = "tiktok") -> List[Dict[str, Any]]:
    """Generate platform-specific optimized captions."""
    
    platform_configs = {
        "tiktok": {
            "max_caption_length": 150,
            "hashtag_count": 3-5,
            "style": "trendy",
            "hashtags": ["#fyp", "#viral", "#trending", "#foryou"]
        },
        "instagram": {
            "max_caption_length": 125,
            "hashtag_count": 5-10,
            "style": "aesthetic",
            "hashtags": ["#reels", "#viral", "#trending", "#explore"]
        },
        "youtube": {
            "max_caption_length": 100,
            "hashtag_count": 2-4,
            "style": "searchable",
            "hashtags": ["#shorts", "#viral", "#trending"]
        }
    }
    
    config = platform_configs.get(platform, platform_configs["tiktok"])
    
    optimized_chunks = []
    for chunk in chunks:
        # Adjust caption length
        caption = chunk.get('caption', '')
        if len(caption) > config['max_caption_length']:
            caption = caption[:config['max_caption_length']-3] + "..."
        
        # Add platform-specific hashtags
        hashtags = chunk.get('hashtags', [])
        platform_hashtags = config['hashtags']
        
        # Combine and limit hashtags
        all_hashtags = list(set(hashtags + platform_hashtags))
        chunk['hashtags'] = all_hashtags[:config['hashtag_count']]
        chunk['caption'] = caption
        chunk['platform'] = platform
        
        optimized_chunks.append(chunk)
    
    return optimized_chunks


def generate_captions(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate engaging captions and hashtags for video chunks.
    
    Args:
        chunks: List of video chunks with text content
        
    Returns:
        List of chunks enhanced with captions, hashtags, and hooks
    """
    try:
        # Try AI-powered caption generation first
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            print("🤖 Using AI for caption generation...")
            return generate_captions_with_ai(chunks)
        else:
            print("🎭 Using mock caption generation...")
            return generate_mock_captions(chunks)
            
    except Exception as e:
        print(f"Caption generation failed, using mock data: {e}")
        return generate_mock_captions(chunks) 