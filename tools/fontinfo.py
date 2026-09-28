"""Maximo JP font: atlas in FONT.PRT (last 512x512 8bpp, stored bottom-up),
glyph table in ELF: 430 x 48B records starting at 0xD8CD0:
  [x0,y0,0,1, x1,y1,0,1, u0,v0,u1,v1] (floats; v = 1 - row/512; x/y = quad offsets)
  table() returns them reordered as [u0,v0,u1,v1, x0,y0,0,1, x1,y1,0,1]
Text code c>=0x80 -> glyph c-0x80. 0x20 space."""
import struct, numpy as np
ELF = 'extract/SLPM_621.27'
PRT = 'extract/PSXDATA/GAME/FONT.PRT'
TAB = 0xD8CF0
N = 430
BASE = 0x100000 - 0x80  # vaddr - BASE = file offset

def atlas(prt=None):
    d = open(prt or PRT, 'rb').read()
    return np.frombuffer(d[-262144:], np.uint8).reshape(512, 512)[::-1].copy()

def table(elf=None):
    d = open(elf or ELF, 'rb').read()
    return [struct.unpack_from('<4f', d, TAB + i * 48) + struct.unpack_from('<8f', d, TAB - 0x20 + i * 48) for i in range(N)]

def rect(r):
    x0 = round(r[0] * 512); x1 = round(r[2] * 512)
    y0 = round(512 - r[1] * 512); y1 = round(512 - r[3] * 512)
    return x0, y0, x1, y1
