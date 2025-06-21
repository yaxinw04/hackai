# test_pipeline.py
from processors.transcribe import transcribe_video
from processors.segments import detect_segments, score_segments
from processors.captions import generate_captions

path = "zipline.mp4"
# 1) Transcribe
segments = transcribe_video(path)
print(f"Transcript segments: {len(segments)} entries")

# 2) Detect & score
chunks = detect_segments(path, segments)
top_chunks = score_segments(chunks)
print(f"Top {len(top_chunks)} chunks:")
for c in top_chunks:
    print(c)

# 3) Generate captions
results = generate_captions(top_chunks)
for r in results:
    print(r['title'], r['caption'], r['hashtags'])