"""원본 디스크에서 동영상 PSS 추출(work/movie/orig) + 음성 WAV(work/movie/wav). movenc.py/asr.py 전에 실행."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdimg import CD
import pssaudio
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(ROOT)
os.makedirs('work/movie/orig', exist_ok=True)
cd = CD('Maximo (Japan).bin')
for n, l, s, _, _ in cd.walk():
    if n.endswith('.PSS'):
        p = 'work/movie/orig/' + os.path.basename(n)
        open(p, 'wb').write(cd.read(l, s))
        if '--wav' in sys.argv:
            os.makedirs('work/movie/wav', exist_ok=True)
            pssaudio.extract(p, 'work/movie/wav/' + os.path.basename(n)[:-4] + '.wav')
        print(p)
