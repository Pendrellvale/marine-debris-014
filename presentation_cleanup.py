"""Keep the submission focused on the project, with a short execution note."""
AUTHORS = '''Tianyu Tang (z5708585)  
Sarang Rawat (z5630151)  
Shunhao Xu (z5697334)  
Roshni Roy (z5516075)  
Haorui Kang (z5464761)'''


def clean_notebook(nb):
    setup = next(c for c in nb['cells'] if c['id']=='cloud-setup')
    cells=[]
    for cell in nb['cells']:
        if cell['id'] in {'cloud-intro','cloud-setup'}:continue
        text=''.join(cell['source'])
        if cell['id']=='cell-000':
            text='''# Automated Marine Debris Detection

**COMP9444 · Project 014**

'''+AUTHORS+'''

We study object detection in underwater images using the TrashCan dataset. We compare longer
training, learning-rate decay, class-aware sampling, mask supervision and RT-DETR. Each section
explains the model or change, shows the results, and discusses what we learned.

### Contents
1. Research questions
2. Experimental setup
3. Dataset and evaluation
4. Models and fine-tuning
5. Paper reproduction and earlier experiments
6. Experiment overview
7. Training duration and learning rate
8. Class-aware sampling
9. Mask supervision
10. RT-DETR
11. Results and error analysis
12. Discussion and future work
'''
        elif cell['id']=='cell-001':
            text=text.replace('# 1. Research Questions and Assessment Alignment','# 1. Research Questions')
            a=text.find('The rubric gives');b=text.find('**Ownership:**')
            if a>=0 and b>=0:text=text[:a]+text[b:]
        elif cell['id']=='cell-002':
            text='''# 2. Experimental Setup

The experiments used a Linux GPU environment, COCO-pretrained models and the official TrashCan
Instance split. The following table gives the training budgets and changes tested.

*Run All downloads the saved experiment records and displays their results; it does not repeat
training or inference. The experiment code is included for reference.*
'''
        elif cell['id']=='cell-003':
            text="show_original_code('cell-003')"
            cell['outputs']=[]
        elif cell['id']=='cell-022':
            text='''# 6. Experiment Overview

We completed five training runs. The table below summarizes their final and validation-selected
checkpoints. The following sections examine each change separately.
'''
        elif cell['id']=='cell-051':
            a=text.find('## 12.4');b=text.find('## References')
            text=text[:a]+'''## 12.4 Experimental Summary

Longer training and learning-rate decay gave the clearest improvements in our matched CNN
experiments. Repeat sampling changed class-level performance, while mask supervision added
segmentation output. RT-DETR achieved the highest overall AP in the new study, although its
training recipe and exposure differed. These comparisons show why model choice depends on the
metric and the intended use, rather than one score alone.

'''+text[b:]
            text=text.split('**Before submission:**')[0].rstrip()+'\n'
        if cell['cell_type']=='markdown':
            text=text.replace('The audit cells recompute these counts.','The dataset audit reports these counts.')
        cell['source']=text
        cells.append(cell)
        if cell['id']=='cell-002':cells.append(setup)
    nb['cells']=cells
    return nb
