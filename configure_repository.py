"""Set the repository before uploading. Only edits the cloud copy."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def configure(repository, tag='results-v1'):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Use OWNER/REPOSITORY, not a URL.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', tag):
        raise ValueError('Use a simple release tag.')
    path = ROOT / 'Marine_Debris_Detection.ipynb'
    nb = json.loads(path.read_text(encoding='utf-8'))
    cell = next(c for c in nb['cells'] if c['id'] == 'cloud-setup')
    source = ''.join(cell['source'])
    source = re.sub(r'^REPOSITORY = .*$', 'REPOSITORY = ' + repr(repository), source, flags=re.M)
    source = re.sub(r'^RELEASE_TAG = .*$', 'RELEASE_TAG = ' + repr(tag), source, flags=re.M)
    cell['source'] = source
    # Keep archived figures visible before running; setup has no old machine output.
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    (ROOT / 'repository.json').write_text(json.dumps(dict(repository=repository, tag=tag),indent=2),encoding='utf-8')
    print('Configured:', repository, tag)
    print('The submitted notebook now contains the public Release address; readers need not edit it.')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('repository');p.add_argument('--tag',default='results-v1')
    args=p.parse_args();configure(args.repository,args.tag)
