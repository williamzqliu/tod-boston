"""Bundle the research revision for an external reviewer.

    python tools/make_review_package.py

Run from the repository root after `python revision_2026.py`. Writes
dist/tod-boston-revision-review.zip (dist/ is not tracked). The bundle holds
the report, the code that produced every number in it, the result tables and
figures, the frozen e18a184 baseline records and a checksum for every file. It
does not copy data/ (22 MB): the reviewer gets it from the repository at the
recorded commit, and the SHA-256 of each data file is listed so a copy can be
checked before use.
"""
import hashlib
import json
import os
import zipfile

NAME = 'tod-boston-revision-review'
FILES = [
    'RESEARCH_REVISION_REPORT.md', 'README.md', 'requirements.txt',
    'revision_2026.py', 'revision/methods.py', 'revision/geometry.py', 'revision/checks.py',
    'revision/reproduce_baseline.py', 'revision/manifest.json',
    'build_2026.py', 'tools/build_notebook.py', 'tools/make_review_package.py',
    'revision/baseline_e18a184/manifest.json', 'revision/baseline_e18a184/run_stdout.txt',
    'revision/VERSIONS.md', 'revision/archive_round1/NOTE.md',
    'revision/archive_round2/RESEARCH_REVISION_REPORT_round2.md',
]
DIRS = ['revision/outputs', 'revision/figures', 'revision/baseline_e18a184/outputs']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    files = list(FILES)
    for d in DIRS:
        files += sorted(os.path.join(d, f).replace('\\', '/') for f in os.listdir(d))
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        raise SystemExit(f'missing: {missing}; run revision_2026.py first')
    man = json.load(open('revision/manifest.json', encoding='utf-8'))
    readme = f"""# External review bundle: TOD Boston research revision

Start with `RESEARCH_REVISION_REPORT.md`. Every number in it is produced by
`revision_2026.py` into `revision/outputs/` and `revision/figures/`.

## What is not in this bundle, and where to get it

- **Input data** (`data/`, 14 files, about 22 MB). Clone
  https://github.com/williamzqliu/tod-boston and check out the commit below, or
  any later one whose `data/` matches these checksums (the revision did not
  change any input file):

      baseline commit   {man['baseline_commit']}
      working tree HEAD {man['working_tree_head']} (uncommitted changes: {man['working_tree_dirty']})

{chr(10).join(f'      {h}  data/{f}' for f, h in man['data_sha256'].items())}

- **The historical baseline** is `build_2026.py` exactly as at that commit.
  `revision/reproduce_baseline.py` re-runs it from a clean `git archive` and
  writes `revision/baseline_e18a184/`; the tables, printed output and
  checksums from that run are included here.
- **The 2024 notebook** and the generated 2026 notebook are in the repository,
  not here.

## Re-running

If the revision is not yet committed at the checked-out commit, copy this bundle's
files over the checkout first (same relative paths). Then, from the repository
root, Python {man['environment']['python']}:

    pip install -r requirements.txt
    python revision/reproduce_baseline.py   # the frozen baseline (needs git)
    python revision/checks.py               # 21 checks on the scoring rules
    python revision_2026.py                 # all tables and figures, ~3-4 min
    python build_2026.py                    # the baseline notebook's own outputs

Seeds, draw counts and tolerances are in `revision/manifest.json`. Which
setting is the main comparison, which are historical and which exploratory is
in `revision/VERSIONS.md` and `revision/outputs/settings.csv`.
`SHA256SUMS.txt` (`sha256sum -c` format) and `PACKAGE_MANIFEST.json` list the
SHA-256 of every file in this bundle.
"""
    os.makedirs('dist', exist_ok=True)
    out = f'dist/{NAME}.zip'
    listing = {f: sha256(f) for f in files}
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f'{NAME}/{f}')
        z.writestr(f'{NAME}/REVIEW_README.md', readme)
        z.writestr(f'{NAME}/PACKAGE_MANIFEST.json', json.dumps(
            {'files_sha256': listing, 'data_not_included_sha256': man['data_sha256'],
             'baseline_commit': man['baseline_commit']}, indent=2))
        sums = ''.join(f'{h}  {f}\n' for f, h in listing.items())
        z.writestr(f'{NAME}/SHA256SUMS.txt', sums)
    with open('dist/SHA256SUMS.txt', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(sums)
    zsum = sha256(out)
    with open(out + '.sha256', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f'{zsum}  {os.path.basename(out)}\n')
    print(f'{out}: {len(files) + 3} files, {os.path.getsize(out) / 1e6:.1f} MB, sha256 {zsum}')


if __name__ == '__main__':
    main()
