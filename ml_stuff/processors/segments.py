from pydub import AudioSegment, silence
import numpy as np
from typing import List, Dict
from transformers import pipeline
from datetime import timedelta

# Setup sentiment and keyword extractors
_sentiment = pipeline('sentiment-analysis')
_keyphrase = pipeline('feature-extraction', model='distilbert-base-uncased')

TRENDING_KEYWORDS = set(["trending", "viral", "breaking", "tips", "how to", "life hack"])


def detect_segments(video_path: str, transcript: List[Dict]) -> List[Dict]:
    """
    Split transcript into candidate video clips based on pauses in audio.

    Returns:
        List of chunks: [{ 'start': float, 'end': float, 'text': str }]
    """
    audio = AudioSegment.from_file(video_path)
    silent_ranges = silence.detect_silence(audio, min_silence_len=800, silence_thresh=-40)
    # Convert to seconds
    silent_spans = [(start/1000, stop/1000) for start, stop in silent_ranges]

    chunks = []
    last = 0.0
    for start, end in silent_spans:
        # include segment from last to start
        text_segment = _concat_transcript(transcript, last, start)
        if text_segment:
            chunks.append({'start': last, 'end': start, 'text': text_segment})
        last = end
    # final segment
    final_text = _concat_transcript(transcript, last, transcript[-1]['end'])
    if final_text:
        chunks.append({'start': last, 'end': transcript[-1]['end'], 'text': final_text})
    return chunks


def _concat_transcript(transcript, start, end):
    parts = [seg['text'] for seg in transcript if seg['start'] >= start and seg['end'] <= end]
    return " ".join(parts).strip()


def score_segments(chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Score each chunk by sentiment intensity and keyword matches.

    Returns:
        Top-K chunks sorted by score.
    """
    scored = []
    for chunk in chunks:
        sentiment_score = _sentiment(chunk['text'])[0]
        polarity = sentiment_score['score'] if sentiment_score['label']=='POSITIVE' else -sentiment_score['score']

        # Keyword match count
        words = set(chunk['text'].lower().split())
        keyword_score = len(words.intersection(TRENDING_KEYWORDS))

        # combined score
        score = polarity * 0.6 + keyword_score * 0.4
        scored.append({**chunk, 'score': score})

    # sort and return top_k
    scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)
    return scored_sorted[:top_k]