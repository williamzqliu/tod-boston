"""Reproduce the 2026 baseline exactly as it stood at commit e18a184.

    python revision/reproduce_baseline.py

Run from the repository root. Extracts the whole tree at that commit with
`git archive` into a temporary directory, runs its build_2026.py there
unchanged, and copies what it wrote into revision/baseline_e18a184/:

    outputs/*.csv, outputs/map.json   the baseline tables, tracked
    figures/*.png                     the baseline charts, not tracked
    run_stdout.txt                    everything the script printed
    manifest.json                     commit, checksums, environment

Nothing in the working tree's own figures/ or outputs/ is read or written, so
the frozen copy cannot pick up edits made after the commit.
"""
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

COMMIT = 'e18a184'
DEST = os.path.join('revision', 'baseline_e18a184')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def versions():
    out = {'python': platform.python_version(), 'platform': platform.platform()}
    for mod in ('numpy', 'pandas', 'matplotlib', 'sklearn', 'pyarrow'):
        try:
            out[mod] = __import__(mod).__version__
        except ImportError:
            out[mod] = None
    return out


def main():
    full = subprocess.run(['git', 'rev-parse', COMMIT], capture_output=True,
                          text=True, check=True).stdout.strip()
    tar = subprocess.run(['git', 'archive', '--format=tar', full],
                         capture_output=True, check=True).stdout

    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            tf.extractall(tmp, filter='data')
        env = dict(os.environ, MPLBACKEND='Agg', PYTHONIOENCODING='utf-8')
        run = subprocess.run([sys.executable, 'build_2026.py'], cwd=tmp, env=env,
                             capture_output=True, text=True, encoding='utf-8')
        if run.returncode:
            sys.stderr.write(run.stderr)
            sys.exit(f'build_2026.py at {COMMIT} exited with {run.returncode}')

        for sub in ('outputs', 'figures'):
            dst = os.path.join(DEST, sub)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(os.path.join(tmp, sub), dst)
        with open(os.path.join(DEST, 'run_stdout.txt'), 'w', encoding='utf-8',
                  newline='\n') as fh:
            fh.write(run.stdout)

        data = {f: sha256(os.path.join(tmp, 'data', f))
                for f in sorted(os.listdir(os.path.join(tmp, 'data')))}
        script = sha256(os.path.join(tmp, 'build_2026.py'))

    manifest = {
        'commit': full,
        'script': 'build_2026.py',
        'script_sha256': script,
        'command': 'python build_2026.py  (MPLBACKEND=Agg, in a clean git archive of the commit)',
        'seeds': {'dirichlet': 7, 'kmeans_random_state': 7},
        'environment': versions(),
        'data_sha256': data,
        'outputs_sha256': {f: sha256(os.path.join(DEST, 'outputs', f))
                           for f in sorted(os.listdir(os.path.join(DEST, 'outputs')))},
        'figures_sha256': {f: sha256(os.path.join(DEST, 'figures', f))
                           for f in sorted(os.listdir(os.path.join(DEST, 'figures')))},
    }
    with open(os.path.join(DEST, 'manifest.json'), 'w', encoding='utf-8',
              newline='\n') as fh:
        json.dump(manifest, fh, indent=2)
        fh.write('\n')
    print(f'baseline {full[:7]} reproduced into {DEST}/')
    for f, h in manifest['outputs_sha256'].items():
        print(f'  {f:<34} {h[:16]}')


if __name__ == '__main__':
    main()
