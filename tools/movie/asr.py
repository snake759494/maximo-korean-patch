"""faster-whisper large-v3 로 동영상 음성 받아쓰기 -> work/movie/asr/<이름>.json"""
import sys, os, json
from faster_whisper import WhisperModel
m = WhisperModel(os.environ.get('WM', 'large-v3'), device='cpu', compute_type='int8', cpu_threads=4)
os.makedirs(os.environ.get('OUT','work/movie/asr'), exist_ok=True)
for name in sys.argv[1:]:
    segs, info = m.transcribe('work/movie/wav/%s.wav' % name, language='ja', beam_size=5,
                              vad_filter=os.environ.get('VAD','1')=='1', word_timestamps=True, condition_on_previous_text=False)
    out = [dict(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip(),
                words=[(round(w.start, 2), round(w.end, 2), w.word) for w in s.words]) for s in segs]
    json.dump(out, open(os.environ.get('OUT','work/movie/asr') + '/%s.json' % name, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(name, len(out), flush=True)
