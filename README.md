# Marine Debris Detection — Cloud Notebook

Open `Marine_Debris_Cloud.ipynb` in Jupyter or Colab and choose **Run All**.
The first cell downloads and verifies the saved experiment package. The rest restores the tables,
figures and explanations. A live check rebuilds the main metric table from CSV records.

This is a **completed-results notebook**. It does not retrain models or run fresh predictions.
The original experiment code is shown in expandable blocks and included in the download.
The results are also embedded, so you can read them before running anything.

You need Python 3.10+ with a Jupyter kernel and internet on first use. No GPU, WSL or dataset setup
is needed for this edition. Set `DOWNLOAD_CHECKPOINTS = True` only if you also want to download
the five final checkpoints (about 3.9 GB). This does not trigger inference.

If the download fails, check the connection and public Release, then rerun the setup cell.
Verified downloads are cached. No login token should be added to the notebook.

For the project owner: follow [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md) before sharing.
The repository placeholder must be configured and the Release assets uploaded first.
`marine_debris_014/` remains the separate, original local project.

The figures use TrashCan imagery credited to the dataset authors and JAMSTEC. Models build on
Detectron2 and Hugging Face implementations with COCO pretraining. Upstream sources are credited
in the notebook; this repository does not grant new licenses to those materials.
