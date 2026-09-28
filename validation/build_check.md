# 빌드 검증 기록 (v1.0, 2026-09-28)

```
max jp width 417.0 flagged 0
glyphs: 45 kept symbols, 346 new (344 Hangul), 39 free slots left
atlas rows used: 385/512 px
pool 0ce650-0d0080 used 5298/6704 bytes
pool 1331c0-1331f8 used 38/56 bytes
strings 223 pointer mismatches 0
INSERTA: 994 프레임(자막 712), GOP 58 개 q 분포 1.6:44 1.8:4 2.0:7 2.2:1 2.4:1 2.7:1, 최대 지연 4, 강제 0, ES 19238276 → 14928537 (78%, 81s)
  -> work\patched\INSERTA.PSS OK (26083332 bytes)
INSERTB: 1355 프레임(자막 997), GOP 81 개 q 분포 1.6:27 1.8:1 2.0:1 2.2:2 2.4:4 2.7:15 3.0:3 3.4:5 3.9:12 4.5:7 5.3:1 6.5:3, 최대 지연 4, 강제 0, ES 26111877 → 23203228 (89%, 126s)
  -> work\patched\INSERTB.PSS OK (35258372 bytes)
INSERTC: 1020 프레임(자막 608), GOP 61 개 q 분포 1.6:51 2.0:2 2.2:1 2.7:6 3.4:1, 최대 지연 4, 강제 0, ES 19583876 → 14068885 (72%, 74s)
  -> work\patched\INSERTC.PSS OK (26591236 bytes)
INSERTD: 1949 프레임(자막 839), GOP 120 개 q 분포 1.6:100 1.8:2 2.0:4 2.2:1 2.4:4 2.7:4 3.0:5, 최대 지연 4, 강제 0, ES 37420679 → 23889798 (64%, 136s)
  -> work\patched\INSERTD.PSS OK (50511876 bytes)
OPENING: 3210 프레임(자막 2112), GOP 184 개 q 분포 1.6:147 1.8:10 2.0:10 2.2:7 2.4:4 2.7:4 3.4:1 3.9:1, 최대 지연 4, 강제 0, ES 61631877 → 44527600 (72%, 232s)
  -> work\patched\OPENING.PSS OK (82984964 bytes)
ENDING: 3019 프레임(자막 1479), GOP 175 개 q 분포 1.6:168 1.8:2 2.0:4 2.2:1, 최대 지연 4, 강제 0, ES 57964678 → 34951604 (60%, 264s)
  -> work\patched\ENDING.PSS OK (78086148 bytes)
완료. 실패: 없음
xdelta round-trip SHA-1: 0102ece522f331d40db93fcbd5a3c80530f7cb03 (= 결과 BIN)
동영상 6편: 결과 BIN 속 PSS == work/patched, 표본 섹터 EDC/ECC 정상
```
