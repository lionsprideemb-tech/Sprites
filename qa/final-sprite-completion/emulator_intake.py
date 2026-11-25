#!/usr/bin/env python3
"""Verify official emulator wheel and initialize offline in a disposable target."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

NAME = 'py_desmume-0.0.9-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl'
SHA256 = '4fcb17e824dd5ab2f1baa3fdd930dd9af6f7176b8c9d7dc9bd329d45df1ac5bd'
MAX_BYTES = 8 * 1024 * 1024


def intake(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('not a regular file')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('oversize input')
    if path.name == NAME:
        data = path.read_bytes()
    elif path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as z:
            entries = [i for i in z.infolist() if not i.is_dir()]
            matches = [i for i in entries if i.filename == NAME]
            if len(entries) != 1 or len(matches) != 1 or matches[0].file_size > MAX_BYTES:
                raise ValueError('ZIP must contain only the exact wheel at its root')
            data = z.read(matches[0])
    else:
        raise ValueError('wrong filename or envelope')
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('wheel SHA-256 mismatch')
    return data


def smoke(path):
    data = intake(path)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wheel = root / NAME
        wheel.write_bytes(data)
        target = root / 'python'
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check', '--target', str(target), str(wheel)], check=True, timeout=90)
        env = dict(os.environ, PYTHONPATH=str(target), SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', HOME=str(root), XDG_CONFIG_HOME=str(root))
        code = 'from desmume.emulator import DeSmuME; emu=DeSmuME(); emu.destroy(); print("PASS: emulator initialized and destroyed; no ROM loaded")'
        result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env, check=True, capture_output=True, text=True, timeout=45)
        return {'sha256': SHA256, 'bytes': len(data), 'emulator_init': result.stdout.strip(), 'gameplay_verified': False}


def selftest():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        bad = p / NAME
        bad.write_bytes(b'not the wheel')
        wrapped = p / 'upload.zip'
        with zipfile.ZipFile(wrapped, 'w') as z:
            z.writestr(NAME, b'not the wheel')
        traversal = p / 'traversal.zip'
        with zipfile.ZipFile(traversal, 'w') as z:
            z.writestr('../' + NAME, b'not the wheel')
        extra = p / 'extra.zip'
        with zipfile.ZipFile(extra, 'w') as z:
            z.writestr(NAME, b'not the wheel')
            z.writestr('other', b'x')
        wrong = p / 'unknown.whl'
        wrong.write_bytes(b'x')
        link = p / 'link.zip'
        link.symlink_to(wrapped)
        for f in [bad, wrapped, traversal, extra, wrong, link, p / 'missing.zip']:
            try:
                intake(f)
            except ValueError:
                continue
            raise AssertionError(f'accepted invalid input: {f.name}')
    return {'negative_intake_checks': 7, 'actual_wheel_available': False, 'emulator_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wheel', nargs='?', type=Path)
    args = parser.parse_args()
    print(json.dumps(smoke(args.wheel) if args.wheel else selftest(), indent=2))
