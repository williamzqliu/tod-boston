"""Write 2026-rebuild.ipynb from build_2026.py, then execute it in place.

    python tools/build_notebook.py               # convert and execute
    python tools/build_notebook.py --no-execute  # convert only

Run from the repository root. build_2026.py is in the percent format: `# %%`
opens a code cell, and `# %% [markdown]` opens a markdown cell whose lines are
commented out. This is the split the committed notebook was made with (the
converter reproduces its 48 cells exactly at e18a184); it lives here so that
regenerating the notebook does not depend on a tool requirements.txt does not
list. Executing it writes figures/ and outputs/, exactly as running the script
does.
"""
import re
import sys

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

SRC, DST = 'build_2026.py', '2026-rebuild.ipynb'


def cells(text):
    parts = re.split(r'^# %%(.*)$', text, flags=re.M)
    for tag, body in zip(parts[1::2], parts[2::2]):
        body = body.strip('\n')
        if '[markdown]' in tag:
            lines = [l[2:] if l.startswith('# ') else l[1:] if l.startswith('#') else l
                     for l in body.splitlines()]
            yield nbformat.v4.new_markdown_cell('\n'.join(lines))
        else:
            yield nbformat.v4.new_code_cell(body)


def main():
    with open(SRC, encoding='utf-8') as fh:
        nb = nbformat.v4.new_notebook(cells=list(cells(fh.read())))
    # Keep the existing cell ids where the cell count has not changed, so a
    # regenerated notebook diffs by content rather than by fresh random ids.
    try:
        old = nbformat.read(DST, as_version=4)
        if len(old.cells) == len(nb.cells):
            for new, prev in zip(nb.cells, old.cells):
                if 'id' in prev:
                    new['id'] = prev['id']
    except FileNotFoundError:
        pass
    nb.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python',
                                 'name': 'python3'}
    if '--no-execute' not in sys.argv:
        ExecutePreprocessor(timeout=900, kernel_name='python3').preprocess(
            nb, {'metadata': {'path': '.'}})
    with open(DST, 'w', encoding='utf-8', newline='\n') as fh:
        nbformat.write(nb, fh)
    print(f'{DST}: {len(nb.cells)} cells')


if __name__ == '__main__':
    main()
