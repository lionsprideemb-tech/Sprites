#!/usr/bin/env python3
"""Offline DS recovery preflight. Never installs, downloads, or modifies a ROM."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PINS = {
    'r30_registry_fixture.h': 'de6f646e80069e1bd1bdf14d84ff8ab031d8fb6c',
    'r30_transaction.c': '98ec13138ba305da213e760d1ae706915c2bb7f7',
    'r31_party_adapter.c': '15cea2efd5ee4325a5ed9b3f97f6f5290171d393',
}
REQUIRED = ['git', 'make', 'ninja', 'bison', 'flex', 'arm-none-eabi-gcc',
            'arm-none-eabi-as', 'pkg-config', 'python3', 'wget', 'xz', 'rsync', 'jq']
CANDIDATES = {
    'desmume_0.9.13-4_amd64.deb': (870292, '977146d8bb2907517ef934e149b0e14568f39d7c8d6ace87bfcc71caf83b611f'),
    'gcc-arm-none-eabi_14.2.rel1-1_amd64.deb': (58042936, '99252fdda02ad134e8c3c344d3c843f7aa5c0d006e92a5b3d53daf4bd935b5d3'),
}

def verify(path, size, digest):
    if path.is_symlink() or not path.is_file():
        return 'MISSING_OR_NONREGULAR'
    if path.stat().st_size != size:
        return 'SIZE_MISMATCH'
    with path.open('rb') as stream:
        return 'VERIFIED' if hashlib.file_digest(stream, 'sha256').hexdigest() == digest else 'HASH_MISMATCH'

def git_blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def run(args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=60, check=True).stdout.strip()

def smoke(sources):
    for name, pin in PINS.items():
        if git_blob(sources / name) != pin:
            raise ValueError('source blob mismatch: ' + name)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name in PINS:
            shutil.copyfile(sources / name, tmp / name)
        results = {}
        for name in ['r30_transaction', 'r31_party_adapter']:
            run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-fsanitize=undefined', '-o', name, name + '.c'], tmp)
            results[name] = run([str(tmp / name)], tmp)
        (tmp / 'probe.c').write_text('volatile unsigned result; void _start(void){result=0x4d455243u; for(;;){}}\n')
        run(['clang', '--target=arm-none-eabi', '-mcpu=arm946e-s', '-ffreestanding', '-fno-builtin', '-nostdlib', '-fuse-ld=lld', '-Wl,-Ttext=0x02000000', '-Wl,-e,_start', '-o', 'probe.elf', 'probe.c'], tmp)
        elf = (tmp / 'probe.elf').read_bytes()
        assert elf[:6] == b'\x7fELF\x01\x01' and int.from_bytes(elf[16:18], 'little') == 2 and int.from_bytes(elf[18:20], 'little') == 40
        results['arm_link'] = 'PASS: ELF32 little-endian ARM executable; not a DS ROM'
        return results

def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / 'sample'; d = hashlib.sha256(b'abc').hexdigest()
        assert verify(p, 3, d) == 'MISSING_OR_NONREGULAR'
        p.write_bytes(b'abc'); assert verify(p, 3, d) == 'VERIFIED'
        p.write_bytes(b'ab'); assert verify(p, 3, d) == 'SIZE_MISMATCH'
        p.write_bytes(b'abd'); assert verify(p, 3, d) == 'HASH_MISMATCH'
        q = p.with_name('link'); q.symlink_to(p); assert verify(q, 3, d) == 'MISSING_OR_NONREGULAR'
    return 5

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', type=Path, required=True)
    parser.add_argument('--sources', type=Path)
    args = parser.parse_args()
    tools = {x: bool(shutil.which(x)) for x in REQUIRED + ['skrew', 'clang', 'ld.lld', 'desmume']}
    data = {'platform': os.uname().machine, 'tools': tools,
            'py_desmume_present': importlib.util.find_spec('desmume') is not None,
            'package_checks': {n: verify(args.packages / n, *v) for n, v in CANDIDATES.items()},
            'integrity_selftests': selftest(), 'dependency_closure_verified': False,
            'native_build_verified': False, 'emulator_verified': False,
            'production_allowed': False}
    if args.sources:
        data['smoke'] = smoke(args.sources)
    print(json.dumps(data, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
