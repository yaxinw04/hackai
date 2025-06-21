import whisper

# Load Whisper model once
_model = whisper.load_model('base')

def transcribe_video(path: str):
    """
    Transcribe video to timestamped text segments.

    Returns:
        List of segments: [{ 'start': float, 'end': float, 'text': str }]
    """
    result = _model.transcribe(path, word_timestamps=True)
    return result['segments']