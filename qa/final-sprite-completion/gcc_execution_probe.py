#!/usr/bin/env python3
"""Verified GNU ARM compiler plus LLVM assembler/linker and DeSmuME smoke; no game ROM."""
import hashlib, json, os, struct, subprocess, tempfile, sys
from pathlib import Path
from emulator_execution_probe import crc16
from desmume.emulator import DeSmuME

EXPECTED='99252fdda02ad134e8c3c344d3c843f7aa5c0d006e92a5b3d53daf4bd935b5d3'

def run(args):
    return subprocess.run(list(map(str,args)),check=True,capture_output=True,text=True,timeout=90).stdout

def main():
    package=Path(sys.argv[1]); assert hashlib.file_digest(package.open('rb'),'sha256').hexdigest()==EXPECTED
    with tempfile.TemporaryDirectory() as d:
        t=Path(d); root=t/'root'; root.mkdir()
        run(['dpkg-deb','-x',package,root]); gcc=root/'usr/bin/arm-none-eabi-gcc'
        version=run([gcc,'--version']).splitlines()[0]
        c=t/'probe.c'; s=t/'probe.s'; o=t/'probe.o'; elf=t/'probe.elf'
        c.write_text('void _start(void) { *(volatile unsigned *)0x02010000u=0x4d455243u; for (;;) {} }\n')
        run([gcc,'-mcpu=arm946e-s','-marm','-O2','-ffreestanding','-fno-builtin','-S',c,'-o',s])
        run(['clang','--target=arm-none-eabi','-mcpu=arm946e-s','-c',s,'-o',o])
        run(['ld.lld','-m','armelf','-Ttext=0x02000000','-e','_start',o,'-o',elf])
        data=elf.read_bytes(); assert data[:6]==b'\x7fELF\x01\x01'
        assert struct.unpack_from('<HHI',data,16)==(2,40,1)
        entry,phoff=struct.unpack_from('<II',data,24); entsize,num=struct.unpack_from('<HH',data,42)
        assert entry==0x02000000 and entsize==32
        segments=[struct.unpack_from('<8I',data,phoff+i*entsize) for i in range(num)]
        load=[x for x in segments if x[0]==1 and x[2]==entry and x[6]&1]
        assert len(load)==1; _,off,_,_,sz,memsz,_,_=load[0]; assert sz==memsz and 0<sz<0x4000
        arm9=data[off:off+sz]; arm7=struct.pack('<I',0xeafffffe)
        b=bytearray(131072); b[:12]=b'MERCURY TEST'; b[12:16]=b'QAAA'; b[16:18]=b'00'
        struct.pack_into('<4I',b,0x20,0x4000,entry,entry,len(arm9)); struct.pack_into('<4I',b,0x30,0x8000,0x03800000,0x03800000,len(arm7)); struct.pack_into('<II',b,0x80,len(b),0x4000)
        b[0x4000:0x4000+len(arm9)]=arm9; b[0x8000:0x8000+len(arm7)]=arm7
        struct.pack_into('<H',b,0x15c,crc16(b[0xc0:0x15c])); struct.pack_into('<H',b,0x15e,crc16(b[:0x15e])); rom=t/'probe.nds'; rom.write_bytes(b)
        emu=DeSmuME()
        try:
            emu.open(str(rom)); assert emu.is_running(); before=emu.memory.unsigned.read_long(0x02010000); assert before==0
            for _ in range(120):
                emu.cycle(False); assert emu.is_running()
            after=emu.memory.unsigned.read_long(0x02010000); assert after==0x4d455243
            assert emu.screenshot().size==(256,384)
            print(json.dumps({'result':'PASS','gcc':version,'assembly':'GNU GCC','assembler':'LLVM clang','linker':'LLVM lld','arm9_bytes':sz,'frames':120,'before':hex(before),'after':hex(after),'screenshot':[256,384],'native_platinum_build':False,'gameplay_verified':False}))
        finally: emu.destroy()

if __name__=='__main__': main()
