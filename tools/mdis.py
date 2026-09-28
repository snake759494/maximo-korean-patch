import sys, capstone
d = open('extract/SLPM_621.27', 'rb').read()
BASE = 0x100000 - 0x80
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS3 + capstone.CS_MODE_LITTLE_ENDIAN); md.skipdata = True
def dis(fo, n):
    for i in md.disasm(d[fo:fo + n * 4], fo + BASE):
        print('%06x %08x  %s %s' % (i.address - BASE, i.address, i.mnemonic, i.op_str))
if __name__ == '__main__':
    dis(int(sys.argv[1], 16), int(sys.argv[2]))
