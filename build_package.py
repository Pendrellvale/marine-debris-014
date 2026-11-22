"""Build a separate cloud-reading copy; never write into marine_debris_014."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'marine_debris_014'
STUDY = SOURCE / 'notebook_study'
SUITE = STUDY / 'outputs/overnight_v1'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def build():
    assets=HERE/'release_assets';assets.mkdir(exist_ok=True)
    originals={str(p.relative_to(SOURCE)):sha(p) for p in
               [SOURCE/'Marine_Debris_Research.ipynb',SOURCE/'Marine_Debris_Research.html',SOURCE/'README.md']}
    nb=json.loads((SOURCE/'Marine_Debris_Research.ipynb').read_text(encoding='utf-8'))
    snapshot={c['id']:dict(source=''.join(c['source']),outputs=c['outputs'])
              for c in nb['cells'] if c['cell_type']=='code'}
    assert not any(o['output_type']=='error' for c in snapshot.values() for o in c['outputs'])
    manifest={}
    archive=assets/'marine_debris_results_v1.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def add_bytes(name,body):
            z.writestr(name,body);manifest[name]=hashlib.sha256(body).hexdigest()
        def add_file(p,name):add_bytes(name,p.read_bytes())
        add_bytes('saved_outputs.json',json.dumps(snapshot,ensure_ascii=False).encode('utf-8'))
        for group in ['comparison','analysis']:
            for p in (SUITE/group).iterdir():
                if p.is_file() and p.suffix in {'.json','.csv','.md','.txt'}:
                    add_file(p,'records/'+group+'/'+p.name)
        for p in (SUITE/'robustness').glob('*.csv'):add_file(p,'records/robustness/'+p.name)
        for p in STUDY.glob('*.py'):add_file(p,'source/notebook_study/'+p.name)
        add_file(STUDY/'config.json','source/notebook_study/config.json')
        for p in (SUITE/'source').glob('*'):
            if p.is_file():add_file(p,'original_training_source/'+p.name)
        for name in ['environment.txt','experiment_identity.json']:
            add_file(SUITE/name,'records/'+name)
        for p in (STUDY/'outputs/data_analysis').glob('*'):
            if p.suffix in {'.csv','.json'}:add_file(p,'records/data_analysis/'+p.name)
        for folder in sorted(SUITE.glob('0*')):
            if not folder.is_dir():continue
            for p in folder.glob('*'):
                if p.suffix in {'.json','.yaml','.yml'}:add_file(p,'records/runs/'+folder.name+'/'+p.name)
            done=json.loads((folder/'complete.json').read_text())
            for p in (folder/done['final_evaluation']).iterdir():
                if p.suffix in {'.json','.npz'} and p.name!='segm_predictions.json':
                    add_file(p,'records/runs/'+folder.name+'/final_evaluation/'+p.name)
        # Historical raw evidence remains separate from the official split.
        hist=STUDY/'historical/track_a'
        for p in [hist/'comparison/three_model_metric_comparison.csv',hist/'comparison/balance_comparison.csv',
                  hist/'experiments/06_gradcam_robustness/records/model_robustness_summary.csv',hist/'IMPORT_MANIFEST.json']:
            add_file(p,'records/historical/'+p.name)
        add_bytes('DATA_SOURCE.txt',b'Figures contain TrashCan imagery credited to its authors and JAMSTEC.\n'
            b'Original data: https://conservancy.umn.edu/items/6dd6a960-c44a-4510-a679-efb8c82ebfb7\n'
            b'No license to the upstream data or frameworks is granted by this package.\n')
        z.writestr('FILE_MANIFEST.json',json.dumps(manifest,indent=2))
    release=dict(schema=1,suite='overnight_v1',source_notebook_sha256=originals['Marine_Debris_Research.ipynb'],
        results=dict(name=archive.name,sha256=sha(archive),bytes=archive.stat().st_size),checkpoints=[])
    for folder in sorted(SUITE.glob('0*')):
        if not folder.is_dir():continue
        checkpoint=folder/('last.pt' if folder.name=='05_rtdetr' else 'model_final.pth')
        package=assets/(folder.name+'_checkpoint.zip')
        if not package.exists():
            print('Packaging',folder.name,flush=True)
            with zipfile.ZipFile(package,'w',zipfile.ZIP_STORED) as z:
                z.write(checkpoint,checkpoint.name)
                for p in folder.rglob('*'):
                    if p.is_file() and (p.parent==folder and p.name in {'complete.json','provenance.json','config.yaml','weight_loading.json'}
                            or p.parent.name in {'processor','model_config'}):
                        z.write(p,str(p.relative_to(folder)).replace('\\','/'))
                z.writestr('CHECKPOINT_SHA256.txt',sha(checkpoint)+'  '+checkpoint.name+'\n')
        assert package.stat().st_size<2*1024**3
        release['checkpoints'].append(dict(run=folder.name,name=package.name,sha256=sha(package),bytes=package.stat().st_size,
            original_checkpoint_sha256=sha(checkpoint)))
    (HERE/'release_manifest.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
    config=json.loads((HERE/'repository.json').read_text()) if (HERE/'repository.json').exists() else dict(repository='YOUR_GITHUB_USERNAME/marine-debris-014',tag='results-v1')
    settings=f'''# The owner sets these before submission. Readers can run all cells unchanged.
REPOSITORY = {config['repository']!r}
RELEASE_TAG = {config['tag']!r}
DOWNLOAD_CHECKPOINTS = False  # True downloads all five final checkpoints (~3.9 GB); never needed to read results.
CACHE_DIRECTORY = Path(os.environ.get('MARINE_DEBRIS_CACHE_DIR', str(Path.home() / '.cache' / 'marine_debris_cloud')))
RELEASE_MANIFEST = {release!r}
BASE_URL = os.environ.get('MARINE_DEBRIS_ASSET_BASE_URL',
    f'https://github.com/{{REPOSITORY}}/releases/download/{{RELEASE_TAG}}')
if 'YOUR_GITHUB_USERNAME' in BASE_URL:
    raise RuntimeError('Owner setup is incomplete. Configure the GitHub repository and upload Release assets before submission.')
RESULTS_DIRECTORY = start(BASE_URL, RELEASE_MANIFEST, CACHE_DIRECTORY, DOWNLOAD_CHECKPOINTS)
print('Downloaded records:', RESULTS_DIRECTORY)
verify_results()
'''
    setup=dict(cell_type='code',id='cloud-setup',metadata={},execution_count=None,outputs=[],
        source=(HERE/'cloud_runtime.py').read_text(encoding='utf-8')+'\n'+settings)
    intro=dict(cell_type='markdown',id='cloud-intro',metadata={},source='''# Marine Debris Detection — Cloud Results Edition

**Choose Run All.** This copy downloads a versioned results package and restores the completed
experiment's tables, figures and analysis. No GPU, WSL, training dataset or local project folder is
needed. Use a Python 3.10+ Jupyter kernel (including Colab). Internet is needed for the first download.

**What runs here:** file downloads, SHA-256 verification, a live CSV consistency check and rendering
of archived experiment outputs. **What does not run:** training or fresh model inference. The original
experiment code is available in each expandable block and in the downloaded source folder. This
distinction matters: these are genuine saved measurements, not measurements produced by this session.

The five final checkpoints can also be downloaded by setting `DOWNLOAD_CHECKPOINTS = True` in the
setup cell. This adds about 3.9 GB of downloads but does not change the reported results. Checkpoints
are never loaded as executable Python objects here. Full inference still needs the documented model
environment and data; this notebook does not claim to be a one-click fresh evaluation.

Saved outputs are also embedded for reading before execution. First download time depends on the
connection. On later runs, the local cache is verified and reused. The original local notebook is
unchanged. Training-era environment paths shown inside archived records are historical metadata.
''')
    newcells=[intro,setup]
    for c in nb['cells']:
        c=dict(c)
        if c['cell_type']=='code':
            cid=c['id'];c['source']=f"show_original_code({cid!r})\nshow_saved_cell({cid!r})"
            c['execution_count']=None
            if cid=='cell-003':
                c['source']="print('Cloud reading mode: using verified results from overnight_v1.')\nshow_original_code('cell-003')"
                c['outputs']=[]
            if cid=='cell-024':c['source']="show_original_code('cell-024')"
        else:
            s=''.join(c['source'])
            if s.startswith('# Automated Marine'):
                begin=s.index('**Read this first:**');end=s.index('### Contents')
                s=s[:begin]+'**Cloud copy:** Run All restores saved outputs. Read the opening section for download and checkpoint options.\n\n'+s[end:]
            if s.startswith('# 2. Environment and Execution'):
                s='''# 2. Environment and Execution

The experiments below originally ran in the project Linux/WSL GPU environment. This cloud copy
only reads their completed outputs and runs the CSV check. It needs a Python 3.10+ Jupyter kernel
and internet access on first use. It does not import Detectron2, PyTorch or Transformers.

The expandable code blocks document the original experiments. They are displayed as reference,
not executed. Their local paths and training instructions belong to the original project.
'''
            if s.startswith('# 6. Execute the Experiment Queue'):
                s='''# 6. Completed Experiment Queue

All five runs are complete. The following output is restored from the frozen experiment package.
The original queue code is shown for reference and is not executed in this cloud edition.
'''
            s=s.replace('**Before submission:** complete the measured-result interpretation, verify the course AI-assistance\npolicy and acknowledgements, add names/zIDs and actual contributions, and review every output.',
                '**Before submission:** add names/zIDs and actual contributions, review the outputs and follow the course acknowledgement requirements.')
            s=s.replace('Use `Run_Overnight_Notebook.ps1 -Mode analysis` to rebuild this report without training.',
                'In the original project, `Run_Overnight_Notebook.ps1 -Mode analysis` rebuilds the report. This cloud copy uses its setup cell instead.')
            c['source']=s
        newcells.append(c)
    nb['cells']=newcells
    nb['metadata']['kernelspec']=dict(display_name='Python 3',language='python',name='python3')
    nb['metadata']['cloud_edition']=dict(mode='saved_result_restoration',release=release['results']['sha256'])
    from presentation_cleanup import clean_notebook
    nb=clean_notebook(nb)
    (HERE/'Marine_Debris_Detection.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
    assert all(sha(SOURCE/name)==value for name,value in originals.items())
    (HERE/'original_files_unchanged.json').write_text(json.dumps(originals,indent=2),encoding='utf-8')
    print('Results package MB:',round(archive.stat().st_size/1024**2,2))
    print('Original notebook, HTML and README hashes unchanged.')


if __name__=='__main__':build()
