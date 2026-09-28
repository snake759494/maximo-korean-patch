"""minimal MIPS (R5900 subset) disassembler for reading code"""
import struct, sys
R = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
BASE = 0x100000 - 0x80
def s16(x): return x - 0x10000 if x & 0x8000 else x
def dis(w, pc):
    op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; sa = (w >> 6) & 31; fn = w & 63; imm = w & 0xffff
    I = {8:'addi',9:'addiu',10:'slti',11:'sltiu',12:'andi',13:'ori',14:'xori',24:'daddi',25:'daddiu'}
    M = {32:'lb',33:'lh',35:'lw',36:'lbu',37:'lhu',40:'sb',41:'sh',43:'sw',55:'ld',63:'sd',49:'lwc1',57:'swc1',30:'lq',31:'sq'}
    if w == 0: return 'nop'
    if op == 0:
        SP = {0:'sll',2:'srl',3:'sra',8:'jr',9:'jalr',33:'addu',35:'subu',36:'and',37:'or',38:'xor',39:'nor',42:'slt',43:'sltu',45:'daddu',47:'dsubu',24:'mult',26:'div',18:'mflo',16:'mfhi',4:'sllv',6:'srlv',7:'srav',56:'dsll',58:'dsrl',59:'dsra',60:'dsll32',62:'dsrl32',63:'dsra32',10:'movz',11:'movn'}
        n = SP.get(fn, 'sp%d' % fn)
        if fn in (0,2,3,56,58,59,60,62,63): return '%s %s,%s,%d' % (n, R[rd], R[rt], sa)
        if fn == 8: return 'jr %s' % R[rs]
        return '%s %s,%s,%s' % (n, R[rd], R[rs], R[rt])
    if op in I: return '%s %s,%s,%s' % (I[op], R[rt], R[rs], hex(imm) if op in (12,13,14) else s16(imm))
    if op == 15: return 'lui %s,%s' % (R[rt], hex(imm))
    if op in M: return '%s %s,%d(%s)' % (M[op], ('f%d' % rt) if op in (49,57) else R[rt], s16(imm), R[rs])
    if op in (4,5,6,7,20,21): return '%s %s,%s,%x' % ({4:'beq',5:'bne',6:'blez',7:'bgtz',20:'beql',21:'bnel'}[op], R[rs], R[rt], pc + 4 + s16(imm) * 4)
    if op == 1: return 'regimm%d %s,%x' % (rt, R[rs], pc + 4 + s16(imm) * 4)
    if op in (2,3): return '%s %x' % ('j' if op == 2 else 'jal', ((pc + 4) & 0xf0000000) | ((w & 0x3ffffff) << 2))
    if op == 17:
        fmt = rs
        if fmt == 0: return 'mfc1 %s,f%d' % (R[rt], rd)
        if fmt == 4: return 'mtc1 %s,f%d' % (R[rt], rd)
        if fmt == 16:
            FN = {0:'add.s',1:'sub.s',2:'mul.s',3:'div.s',6:'mov.s',7:'neg.s',36:'cvt.w.s',50:'c.eq.s',52:'c.lt.s',54:'c.le.s',24:'adda.s',28:'madd.s'}
            return '%s f%d,f%d,f%d' % (FN.get(fn, 'fop%d' % fn), sa, rd, rt)
        if fmt == 20: return 'cvt.s.w f%d,f%d' % (sa, rd)
        if fmt == 8: return 'bc1 %x' % (pc + 4 + s16(imm) * 4)
        return 'cop1 %08x' % w
    return '.word %08x' % w
if __name__ == '__main__':
    d = open('extract/SLPM_621.27', 'rb').read()
    a = int(sys.argv[1], 16); n = int(sys.argv[2])
    for o in range(a, a + 4 * n, 4):
        w = struct.unpack_from('<I', d, o)[0]
        print('%06x %08x  %s' % (o, o + BASE, dis(w, o + BASE)))
