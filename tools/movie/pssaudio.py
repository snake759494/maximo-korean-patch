"""PSS 음성(BD 스트림, SShd type 1 = 16bit PCM, 48kHz 스테레오, 0x200 인터리브) -> WAV"""
import sys, os, struct, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pss

def extract(path, out):
    data = open(path, 'rb').read()
    buf = bytearray()
    for x in pss.parse(data):
        if x[0] == 'pes' and x[2] == 0xBD:
            buf += data[x[7] + 4:x[7] + x[8]]
    assert buf[:4] == b'SShd', buf[:4]
    typ, rate, ch, il = struct.unpack_from('<4I', buf, 8)
    body = buf[8 + 0x18 + 8:]
    size = struct.unpack_from('<I', buf, 8 + 0x18 + 4)[0]
    body = bytes(body[:size]); body = body[:len(body) // (il * ch) * il * ch]
    a = np.frombuffer(body, '<i2').reshape(-1, ch, il // 2)   # blocks
    pcm = a.transpose(0, 2, 1).reshape(-1, ch)
    with wave.open(out, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm.tobytes())
    return typ, rate, ch, il, len(pcm) / rate

if __name__ == '__main__':
    for p in sys.argv[1:]:
        o = os.path.join('work/movie/wav', os.path.basename(p)[:-4] + '.wav')
        os.makedirs(os.path.dirname(o), exist_ok=True)
        print(p, extract(p, o))
