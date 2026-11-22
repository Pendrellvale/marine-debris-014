"""Download and display the frozen experiment; no local project or GPU required."""
import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path
import urllib.request
import zipfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def download(url, target, expected):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and digest(target) == expected:
        print('Using verified cache:', target.name)
        return target
    temp = target.with_suffix(target.suffix + '.part')
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'MarineDebrisCourseNotebook/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response, temp.open('wb') as stream:
            total = int(response.headers.get('Content-Length', 0))
            received = 0
            next_report = 25 * 1024**2
            while True:
                block = response.read(1024**2)
                if not block:
                    break
                stream.write(block); received += len(block)
                if received >= next_report:
                    print(f'{target.name}: {received / 1024**2:.0f} MB' +
                          (f' / {total / 1024**2:.0f} MB' if total else ''))
                    next_report += 25 * 1024**2
        if digest(temp) != expected:
            raise ValueError('Checksum mismatch for ' + target.name + '. Do not use this download.')
        temp.replace(target)
    except Exception as exc:
        temp.unlink(missing_ok=True)
        raise RuntimeError('Cannot retrieve ' + url +
            '. Check internet access, the public Release, and the configured repository. Rerun this cell.') from exc
    return target


def extract_verified(archive, target):
    target = Path(target).resolve()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            path = (target / item.filename).resolve()
            if not path.is_relative_to(target) or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe archive entry: ' + item.filename)
        z.extractall(target)


def start(base_url, manifest, cache_dir, download_checkpoints=False):
    global RESULT_ROOT, SNAPSHOT
    from IPython.display import display, Markdown
    cache = Path(cache_dir).expanduser().resolve()
    result = manifest['results']
    archive = download(base_url + '/' + result['name'], cache / result['name'], result['sha256'])
    RESULT_ROOT = cache / ('results_' + result['sha256'][:12])
    extract_verified(archive, RESULT_ROOT)
    SNAPSHOT = json.loads((RESULT_ROOT / 'saved_outputs.json').read_text(encoding='utf-8'))
    records = json.loads((RESULT_ROOT / 'FILE_MANIFEST.json').read_text(encoding='utf-8'))
    for name, expected in records.items():
        if digest(RESULT_ROOT / name) != expected:
            raise ValueError('Extracted result file failed verification: ' + name)
    display(Markdown('**Completed experiment loaded.** The following sections restore the saved '
        'outputs of `overnight_v1`. No training or model inference is performed in this reading mode. '
        'Tables and figures retain their original measured values. The live check below reads the CSV records.'))
    if download_checkpoints:
        for item in manifest['checkpoints']:
            path = download(base_url + '/' + item['name'], cache / item['name'], item['sha256'])
            extract_verified(path, cache / 'checkpoints' / item['run'])
        print('Checkpoints downloaded and verified. They were not deserialized or executed.')
    return RESULT_ROOT


def show_saved_cell(cell_id):
    from IPython.display import display
    cell = SNAPSHOT[cell_id]
    for output in cell['outputs']:
        kind = output['output_type']
        if kind == 'stream':
            value = output.get('text', '')
            print(''.join(value) if isinstance(value, list) else value, end='')
        elif kind in ('display_data', 'execute_result'):
            data = {k: ''.join(v) if isinstance(v, list) else v for k, v in output['data'].items()}
            display(data, raw=True, metadata=output.get('metadata', {}))
        elif kind == 'error':
            raise RuntimeError('The archived cell contains an error: ' + cell_id)


def show_original_code(cell_id):
    from IPython.display import HTML, display
    source = SNAPSHOT[cell_id]['source']
    display(HTML('<details><summary>Original experiment code (reference, not executed here)</summary>'
                 '<pre>' + html.escape(source) + '</pre></details>'))


def verify_results():
    """Rebuild a summary from CSV and cross-check the independently recomputed AP audit."""
    from IPython.display import HTML, display
    path = RESULT_ROOT / 'records/comparison/final_comparison.csv'
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    audits = json.loads((RESULT_ROOT / 'records/analysis/evaluation_audit.json').read_text())
    assert len(rows) == len(audits) == 5
    for r in rows:
        audit = next(a for a in audits if a['run'] == r['run'])
        assert abs(float(r['AP']) - audit['recomputed_AP']) < 1e-9
    body = ''.join('<tr><td>' + html.escape(r['model']) + '</td>' +
        ''.join(f'<td>{float(r[k]):.2f}</td>' for k in ['AP', 'AP50', 'AP75']) + '</tr>' for r in rows)
    display(HTML('<h3>Live check of downloaded records</h3><table><tr><th>Model</th><th>AP</th>'
        '<th>AP50</th><th>AP75</th></tr>' + body + '</table>'))
    print('All five CSV results agree with the saved independent COCO AP audit.')
    print('This checks records, not a new model evaluation. AP is not classification accuracy.')


def export_outputs():
    """Return a portable index without changing the source project."""
    return str(RESULT_ROOT)
