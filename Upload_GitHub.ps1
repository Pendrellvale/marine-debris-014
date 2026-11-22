param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [string]$Python = 'python',
    [string]$Tag = 'results-v1'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') { throw 'Use OWNER/REPOSITORY.' }
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE). Stop and read the message above." } }
Get-Command git, gh, $Python -ErrorAction Stop | Out-Null
gh auth status
Check-Exit
& $Python configure_repository.py $Repository --tag $Tag
Check-Exit
$releaseManifest = Get-Content -LiteralPath release_manifest.json -Raw | ConvertFrom-Json
$assets = @($releaseManifest.results) + @($releaseManifest.checkpoints)
foreach ($asset in $assets) {
    $assetPath = Join-Path $PSScriptRoot ('release_assets/' + $asset.name)
    if (-not (Test-Path -LiteralPath $assetPath)) { throw "Missing asset: $assetPath" }
    $actualHash = (Get-FileHash -LiteralPath $assetPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $asset.sha256) { throw "Checksum failed: $assetPath" }
}
if (-not (Test-Path -LiteralPath '.git')) {
    git init -b main
    Check-Exit
}
$repoRoot = (git rev-parse --show-toplevel).Trim()
Check-Exit
if ([IO.Path]::GetFullPath($repoRoot) -ne [IO.Path]::GetFullPath($PSScriptRoot)) {
    throw 'This must be a separate Git repository in the cloud-submission folder.'
}
git add -- .gitignore README.md GITHUB_UPLOAD_GUIDE.md Marine_Debris_Detection.ipynb cloud_runtime.py configure_repository.py release_manifest.json repository.json Upload_GitHub.ps1 build_package.py validate_cloud.py presentation_cleanup.py
Check-Exit
git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    git commit -m 'Add cloud results notebook and verified release manifest'
    Check-Exit
} elseif ($LASTEXITCODE -ne 0) { throw 'Cannot inspect staged changes.' }
gh repo view $Repository --json nameWithOwner 2>$null
if ($LASTEXITCODE -ne 0) {
    gh repo create $Repository --public --source . --remote origin --push
    Check-Exit
} else {
    $remote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        git remote add origin "https://github.com/$Repository.git"
        Check-Exit
    } elseif ($remote -notin @("https://github.com/$Repository.git", "https://github.com/$Repository", "git@github.com:$Repository.git")) {
        throw 'Origin points to a different repository. No push was attempted.'
    }
    git push -u origin main
    Check-Exit
}
gh release view $Tag --repo $Repository 2>$null
if ($LASTEXITCODE -ne 0) {
    gh release create $Tag --repo $Repository --target main --title 'Completed marine debris experiments' --notes 'Saved results and five final checkpoints for the cloud notebook. This reading edition restores completed experiments; it does not retrain or rerun inference.'
    Check-Exit
}
$existing = gh release view $Tag --repo $Repository --json assets --jq '.assets[].name'
Check-Exit
foreach ($asset in $assets) {
    if ($existing -contains $asset.name) {
        Write-Host "Already present, not overwritten: $($asset.name). Verify the public download before submission."
        continue
    }
    $assetPath = Join-Path $PSScriptRoot ('release_assets/' + $asset.name)
    gh release upload $Tag $assetPath --repo $Repository
    Check-Exit
}
Write-Host "Release: https://github.com/$Repository/releases/tag/$Tag"
Write-Host 'Now test the submitted notebook on a fresh kernel without MARINE_DEBRIS_ASSET_BASE_URL.'
