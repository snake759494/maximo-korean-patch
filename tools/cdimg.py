"""MODE2/2352 raw CD image access (ISO9660 over Form1 sectors)."""
import struct, sys, os

RAW = 2352
HDR = 24  # sync(12)+header(4)+subheader(8)

class CD:
    def __init__(self, path, mode='rb'):
        self.path = path
        self.f = open(path, mode)

    def read_sector(self, lba):
        self.f.seek(lba * RAW + HDR)
        return self.f.read(2048)

    def read(self, lba, size):
        out = bytearray()
        n = (size + 2047) // 2048
        for i in range(n):
            out += self.read_sector(lba + i)
        return bytes(out[:size])

    def walk(self):
        pvd = self.read_sector(16)
        root = pvd[156:156 + 34]
        res = []
        self._walk(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '', res)
        return res

    def _walk(self, lba, size, prefix, res):
        data = self.read(lba, size)
        off = 0
        while off < len(data):
            ln = data[off]
            if ln == 0:
                off = (off // 2048 + 1) * 2048
                continue
            rec = data[off:off + ln]
            elba = struct.unpack_from('<I', rec, 2)[0]
            esz = struct.unpack_from('<I', rec, 10)[0]
            flags = rec[25]
            nl = rec[32]
            name = rec[33:33 + nl]
            if name not in (b'\x00', b'\x01'):
                nm = name.decode('ascii', 'replace').split(';')[0]
                if flags & 2:
                    self._walk(elba, esz, prefix + nm + '/', res)
                else:
                    # record position: dir lba + off
                    res.append((prefix + nm, elba, esz, lba, off))
            off += ln

if __name__ == '__main__':
    cd = CD(sys.argv[1])
    for n, l, s, dl, do in cd.walk():
        print(f'{l:8d} {s:10d} {n}')
