# 上传教程：只操作这个新文件夹

原项目 `marine_debris_014` 的 Notebook、HTML 和训练结果没有修改。
这个新文件夹 `marine_debris_cloud_submission` 是独立提交版。

## 1. 先理解文件怎么放

- GitHub 仓库：新版 Notebook、下载代码、说明和校验清单。
- GitHub Release：`release_assets` 里的结果 ZIP 和五个 checkpoint ZIP。
- 老师：只需要新版 Notebook。第一次 Run All 会下载结果包并恢复现有输出。
- 默认不下载 checkpoint，因为恢复表格和图不需要加载模型。要同时下载五个模型，在首个代码单元把 `DOWNLOAD_CHECKPOINTS` 改为 `True`。它会增加约 3.9 GB 下载，不会重新推理。

结果版会明确显示它读取的是已完成实验。它不是现场重新评估版。权重包包括模型状态，部分还包括优化器状态；推理仍需要原框架环境。中间每次保存的 checkpoint 不必全部上传，最终五个 checkpoint 足够保留本轮最终模型。

## 2. 安装工具并登录（只需一次）

在 PowerShell 运行，已安装的工具可跳过：

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

安装后重新打开 PowerShell，再运行：

```powershell
gh auth login
```

选择 GitHub.com、HTTPS，并在浏览器完成登录。不要把密码或 token 写进 Notebook。
若 Git 第一次提交要求身份，填写你自己的信息：

```powershell
git config --global user.name "Your Name"
git config --global user.email "Your GitHub email or GitHub noreply address"
```

## 3. 一次配置并上传

把下面的 `YOUR_USERNAME` 换成你的 GitHub 用户名。建议使用一个新的空仓库名。
脚本会创建 **public 仓库**，让老师无需登录即可下载；只发布这个新文件夹中明确列出的文件和结果包，不会上传整个课程目录。

```powershell
cd 'H:\unsw\2026 T3\COMP9444\marine_debris_cloud_submission'
powershell -ExecutionPolicy Bypass -File .\Upload_GitHub.ps1 -Repository 'YOUR_USERNAME/marine-debris-014' -Python 'H:\unsw\2026 T3\COMP9444\marine_debris_014\.venv313\Scripts\python.exe'
```

脚本会先把真实仓库地址写进**新版** Notebook，检查上传包的 SHA-256，再提交代码、创建 `results-v1` Release 和上传六个 ZIP。模型文件总共约 3.9 GB，上传需要时间。
如果中断，可重新运行同一条命令；已经上传的同名资源不会覆盖。不要替换已发布版本中的文件。需要改结果时使用新 tag，并重新配置 Notebook。

注意：GitHub 普通 Git 文件上限为 100 MiB，Release 单个资源必须小于 2 GiB；这里五个 checkpoint 已分别打包，均低于该限制。不要 `git add` 原项目，也不要把 ZIP 加进普通 Git 提交。

官方说明：[大文件](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)、[Release](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。

## 4. 上传后必须做一次真实云端检查

1. 用浏览器无痕窗口打开 `https://github.com/YOUR_USERNAME/marine-debris-014/releases/tag/results-v1`，确认能看到六个 ZIP，结果包可以直接下载。
2. 把**配置过地址之后的** `Marine_Debris_Detection.ipynb` 单独复制到另一文件夹，或上传到一个新的 Google Colab 会话。
3. 选择 Python 内核，点 Run All。默认不需要 GPU、不需要本地项目、不需要训练数据。
4. 确认首个代码单元完成下载、SHA-256 校验，并显示五个 AP：40.46、43.92、43.77、43.96、45.75。继续检查所有图片和分析都显示，所有单元无报错。
5. 保存这份执行后的新版 Notebook，再提交给老师。原来的 Notebook 和 HTML 可以继续留作备份。

如果下载失败：确认仓库公开、Release 已发布、资源文件名没有改动，且运行环境可以访问 GitHub。不要只凭打开 Notebook 看得到旧输出就认为云端运行成功。

本地测试会用临时 HTTP 地址验证同样的下载流程；这不能替代上传后的 GitHub 实测。
Notebook 中不要设置 `MARINE_DEBRIS_ASSET_BASE_URL`，它仅用于内部测试。

## 5. 可选：不用上传脚本，手动分步执行

只在这个新目录运行：

```powershell
python configure_repository.py YOUR_USERNAME/marine-debris-014
git init -b main
git add .gitignore README.md GITHUB_UPLOAD_GUIDE.md Marine_Debris_Detection.ipynb cloud_runtime.py configure_repository.py release_manifest.json repository.json Upload_GitHub.ps1 build_package.py validate_cloud.py presentation_cleanup.py
git commit -m "Add cloud results notebook"
gh repo create YOUR_USERNAME/marine-debris-014 --public --source . --remote origin --push
gh release create results-v1 --repo YOUR_USERNAME/marine-debris-014 --target main --title "Completed experiments" --notes "Frozen results and final checkpoints."
Get-ChildItem -LiteralPath .\release_assets -Filter *.zip | ForEach-Object { gh release upload results-v1 $_.FullName --repo YOUR_USERNAME/marine-debris-014 }
```

`python` 不可用时，可换成上面给出的 `.venv313\Scripts\python.exe` 完整路径。
`build_package.py` 是打包来源脚本，依赖你电脑上旁边的原项目；老师运行 Notebook 不需要执行它。
