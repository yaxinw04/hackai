import os
import openai

oai_key = os.getenv('OPENAI_API_KEY')
openai.api_key = oai_key


def generate_captions(chunks: List[Dict]) -> List[Dict]:
    """
    For each top chunk, generate title, caption, and hashtags using OpenAI.
    Adds 'title', 'caption', 'hashtags', and 'thumbnail_ts'.
    """
    results = []
    for idx, chunk in enumerate(chunks):
        prompt = (
            f"""Given this video transcript excerpt: '{chunk['text']}', 
write:
- A catchy short title (max 5 words)
- A 1-sentence engaging caption
- 3 relevant hashtags"""
        )
        resp = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[{'role':'user','content':prompt}],
            temperature=0.8,
            max_tokens=100
        )
        content = resp.choices[0].message.content.strip().split('')
        title = content[0].strip('- ').strip()
        caption = content[1].strip('- ').strip()
        hashtags = [h.strip() for h in content[2].split(',')]

        results.append({
            **chunk,
            'title': title,
            'caption': caption,
            'hashtags': hashtags,
            'thumbnail_ts': (chunk['start'] + chunk['end'])/2
        })

    return results