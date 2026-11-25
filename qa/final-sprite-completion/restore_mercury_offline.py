#!/usr/bin/env python3
"""Restore the recovered Mercury DS QA tools from verified local package files."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
PINS = {
    'gcc-arm-none-eabi_14.2.rel1-1_amd64.deb': (58042936, '99252fdda02ad134e8c3c344d3c843f7aa5c0d006e92a5b3d53daf4bd935b5d3'),
    'py_desmume-0.0.9-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl': (3447469, '4fcb17e824dd5ab2f1baa3fdd930dd9af6f7176b8c9d7dc9bd329d45df1ac5bd'),
}
SCRIPTS = {
    'emulator_intake.py': '4e1f8f0e191df4cb4dc8a60641f45295f616b6e3',
    'emulator_execution_probe.py': '095ca08eaed6dbf1bb24e006d9651a4b0f3bb24b',
    'gcc_execution_probe.py': '53e24d0596ee0f41183064080144395c09a759c4',
    'offline_preflight.py': '8827b2791e69bad7786b480a115d2b21abc435b3',
}

def run(args, env, cwd):
    p = subprocess.run([str(x) for x in args], env=env, cwd=cwd, check=True, capture_output=True, text=True, timeout=120)
    print(p.stdout, end='', flush=True)
    return p.stdout

def main():
    for name, (size, digest) in PINS.items():
        p = ROOT / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size != size:
            raise ValueError('missing or incorrect file: ' + name)
        with p.open('rb') as f:
            if hashlib.file_digest(f, 'sha256').hexdigest() != digest:
                raise ValueError('package digest mismatch: ' + name)
    for name, digest in SCRIPTS.items():
        p = ROOT / name
        if p.is_symlink() or not p.is_file():
            raise ValueError('missing script: ' + name)
        b = p.read_bytes()
        if hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() != digest:
            raise ValueError('script digest mismatch: ' + name)
    print('PASS: 2 package SHA-256 hashes and 4 Git script hashes verified', flush=True)
    with tempfile.TemporaryDirectory(prefix='mercury-restore-') as td:
        work = Path(td)
        env = dict(os.environ, HOME=td, XDG_CONFIG_HOME=td, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYTHONNOUSERSITE='1')
        env.pop('PYTHONPATH', None)
        target = work / 'python'
        wheel = ROOT / next(n for n in PINS if n.endswith('.whl'))
        run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check', '--target', target, wheel], env, work)
        env['PYTHONPATH'] = str(target)
        run([sys.executable, ROOT / 'emulator_execution_probe.py'], env, work)
        run([sys.executable, ROOT / 'gcc_execution_probe.py', ROOT / next(n for n in PINS if n.endswith('.deb'))], env, work)
    print(json.dumps({'restoration':'PASS','packages':2,'scripts':4,'synthetic_frames':240,'native_platinum_build':False,'production_allowed':False}))

if __name__ == '__main__':
    main()
