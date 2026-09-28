# 재빌드 방법

필요한 것: Python 3.10+ (numpy, Pillow), 동영상까지 다시 만들 때는 PyAV, imageio-ffmpeg, faster-whisper. xdelta3 3.1.0.

## 준비

저장소 루트에 다음 파일을 둡니다(저장소에는 포함되지 않음).

- `Maximo (Japan).bin` — 해시가 README 표와 일치하는 원본
- `NanumSquareNeo-dEb.ttf` — 네이버 나눔스퀘어 네오 ExtraBold
- `extract/SLPM_621.27`, `extract/PSXDATA/GAME/FONT.PRT` — 분석용 도구(`dump_jp.py`, `fontinfo.py`, `qa_width.py`)가 읽는 원본 파일. `tools/cdimg.py` 로 BIN 에서 꺼낼 수 있습니다.

## 게임 텍스트·글꼴

```
python tools/qa_width.py          # 줄 폭 검사 (flagged 0 이어야 함)
python tools/build.py --check     # 글리프 수·문자열 풀 용량 검사
python tools/build.py             # -> Maximo (Japan) (Korean).bin / .cue
python tools/verify.py            # 결과를 다시 읽어 223개 문자열 포인터·내용 확인
```

`build.py --no-movie` 는 동영상을 원본 그대로 둡니다.

## 동영상 자막

```
python tools/movie/extract.py --wav              # work/movie/orig/*.PSS, work/movie/wav/*.wav
python tools/movie/asr.py INSERTA ...            # (번역을 새로 할 때만) 받아쓰기 -> work/movie/asr/
python tools/movie/movenc.py INSERTA INSERTB INSERTC INSERTD OPENING ENDING
                                                 # translation/movie/*.tsv -> work/patched/*.PSS
python tools/build.py                            # work/patched/*.PSS 가 있으면 같은 LBA 에 덮어씀
```

movenc 는 편당 1~4분(q 후보 14벌 인코딩)이 걸립니다. faster-whisper large-v3 는 메모리를 약 3GB 씁니다.

## 배포 파일

```
xdelta3 -e -9 -S none -A -f -s "Maximo (Japan).bin" "Maximo (Japan) (Korean).bin" Maximo_PS2_KO_v1.0.xdelta
xdelta3 -d -f -s "Maximo (Japan).bin" Maximo_PS2_KO_v1.0.xdelta roundtrip.bin   # 결과 SHA-1 비교
```
