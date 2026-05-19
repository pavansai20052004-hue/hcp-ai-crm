param(
    [string]$RepoName = "hcp-ai-crm-assignment",
    [string]$Visibility = "public"
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI is not installed. Install it, run 'gh auth login', then rerun this script."
    exit 1
}

gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Error "GitHub CLI is not authenticated. Run 'gh auth login' first."
    exit 1
}

git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    git init
    git add .
    git commit -m "Build AI-first HCP CRM assignment"
}

git status -sb
git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    if ($Visibility -eq "private") {
        gh repo create $RepoName --source . --remote origin --push --private
    } else {
        gh repo create $RepoName --source . --remote origin --push --public
    }
} else {
    git push -u origin (git branch --show-current)
}

Write-Host "Published repository:"
gh repo view --web
