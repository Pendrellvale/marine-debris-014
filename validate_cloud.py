"""Owner-only clean-directory HTTP test, using an installed Jupyter environment."""
import contextlib
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import threading
import time
import zipfile
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from jupyter_client import KernelManager
import sys

ROOT=Path(__file__).resolve().parent


def main():
    work=ROOT/'_validation';work.mkdir(exist_ok=True)
    clean=work/('clean_'+str(time.time_ns()));clean.mkdir()
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),
        functools.partial(QuietHandler,directory=str(ROOT/'release_assets')))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    address=f'http://127.0.0.1:{server.server_port}'
    os.environ['MARINE_DEBRIS_ASSET_BASE_URL']=address
    os.environ['MARINE_DEBRIS_CACHE_DIR']=str(clean/'cache')
    original=ROOT/'Marine_Debris_Cloud.ipynb'
    nb=nbformat.read(original,as_version=4);nbformat.validate(nb)
    # The kernel sees only this clean directory, not the old project's Python package.
    for c in nb.cells:
        if c.cell_type=='code': c.outputs=[];c.execution_count=None
    manager=KernelManager(kernel_name='python3')
    manager.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    started=time.monotonic()
    client=NotebookClient(nb,timeout=300,km=manager,resources={'metadata':{'path':str(clean)}},
        on_cell_start=lambda cell_index=None,**kw:print(f'Cloud cell {cell_index+1}/{len(nb.cells)}',flush=True))
    try:
        client.execute()
    finally:
        if manager.has_kernel:manager.shutdown_kernel(now=True)
        server.shutdown();server.server_close()
    nbformat.validate(nb)
    errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
    assert not errors
    count=sum('image/png' in o.get('data',{}) for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    source=nbformat.read(ROOT.parent/'marine_debris_014/Marine_Debris_Research.ipynb',as_version=4)
    expected=sum('image/png' in o.get('data',{}) for c in source.cells if c.cell_type=='code' for o in c.outputs)
    assert count==expected,(count,expected)
    nbformat.write(nb,work/'cloud_executed.ipynb')
    # Export deliverable preview from configured-independent template, not localhost execution logs.
    preview,_=HTMLExporter().from_notebook_node(nbformat.read(original,as_version=4))
    (ROOT/'Marine_Debris_Cloud.html').write_text(preview,encoding='utf-8')
    hashes=json.loads((ROOT/'original_files_unchanged.json').read_text())
    from cloud_runtime import digest,download,extract_verified
    for name,value in hashes.items():assert digest(ROOT.parent/'marine_debris_014'/name)==value
    # Reuse verified cache with an unreachable URL: no network access should be attempted.
    manifest=json.loads((ROOT/'release_manifest.json').read_text())
    result=manifest['results'];cached=clean/'cache'/result['name']
    download('http://127.0.0.1:1/not-used',cached,result['sha256'])
    bad=work/'unsafe.zip'
    with zipfile.ZipFile(bad,'w') as z:z.writestr('../outside.txt','not allowed')
    try:extract_verified(bad,work/'safe_extract')
    except ValueError:pass
    else:raise AssertionError('Unsafe archive was accepted')
    report=dict(test='fresh directory, HTTP download, no project imports or GPU',
        cells=len(nb.cells),executed_code_cells=sum(c.cell_type=='code' for c in nb.cells),
        images=count,errors=0,seconds=round(time.monotonic()-started,2),
        verified_cache_reused=True,unsafe_archive_rejected=True,original_files_unchanged=True,
        public_github_test='Pending owner repository configuration and upload')
    (ROOT/'VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
