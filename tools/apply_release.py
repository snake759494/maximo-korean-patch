"""원본 BIN 의 해시를 확인하고 xdelta 를 적용한 뒤 결과 해시까지 검사한다.

사용:
  python tools/apply_release.py --xdelta <xdelta3.exe> --source "Maximo (Japan).bin" --patch Maximo_PS2_KO_v1.0.1.xdelta --output "Maximo (Japan) (Korean).bin"

기존 출력 파일은 덮어쓰지 않는다. 원본·패치·결과 중 하나라도 해시가 다르면 실패로 끝낸다.
성공하면 결과 BIN 옆에 같은 이름의 .cue 를 만든다.
"""
import argparse, hashlib, os, subprocess, sys

SOURCE_SIZE = 722884848
SOURCE_SHA256 = "0d5c2a6359dcaa8e0e0d6ad57902e18b6b51ca9ebfc9ff47629c814e1d5b2662"
PATCH_SHA256 = "a869941ef1fbf9eb27503037714ddafc9d21b0517d43479636ed42e8b7433cd3"
OUTPUT_SIZE = 722884848
OUTPUT_SHA256 = "89b711162976c097899c71de9dbd626e3613cec24838069064bcc49ec06f1d62"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def check(label, path, size, digest):
    n = os.path.getsize(path)
    if size is not None and n != size:
        print(f"{label}: 크기 {n:,} != {size:,}"); return False
    d = sha256(path)
    if d != digest:
        print(f"{label}: SHA-256 불일치\n  실제 {d}\n  기대 {digest}"); return False
    print(f"{label}: OK ({n:,} B)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xdelta", required=True, help="xdelta3 실행 파일")
    ap.add_argument("--source", required=True, help="수정되지 않은 일본판 BIN (MODE2/2352)")
    ap.add_argument("--patch", required=True, help="릴리즈 xdelta")
    ap.add_argument("--output", required=True, help="만들 한글판 BIN")
    a = ap.parse_args()
    if os.path.exists(a.output):
        sys.exit("출력 파일이 이미 있습니다: " + a.output)
    if not check("원본", a.source, SOURCE_SIZE, SOURCE_SHA256): sys.exit(1)
    if not check("패치", a.patch, None, PATCH_SHA256): sys.exit(1)
    r = subprocess.run([a.xdelta, "-d", "-s", a.source, a.patch, a.output])
    if r.returncode != 0:
        sys.exit("xdelta 적용 실패")
    if not check("결과", a.output, OUTPUT_SIZE, OUTPUT_SHA256): sys.exit(1)
    cue = os.path.splitext(a.output)[0] + ".cue"
    if not os.path.exists(cue):
        with open(cue, "w", newline="\r\n") as f:
            f.write('FILE "%s" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n' % os.path.basename(a.output))
        print("CUE 생성:", cue)
    print("완료")


if __name__ == "__main__":
    main()
