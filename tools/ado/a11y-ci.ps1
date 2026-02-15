<#
.SYNOPSIS
    Runs the a11y-ci gate, generates artifacts, and prepares a PR comment.
    Designed for Azure DevOps pipelines but can be run locally.

.DESCRIPTION
    Wrapper around a11y-ci CLI tools to standardize execution in CI environments.
    Handles:
    - Input validation
    - Directory setup (artifacts/a11y)
    - Running the gate (with or without baseline/allowlist)
    - Generating the PR comment markdown
    - Setting pipeline output variables (if in ADO)

.PARAMETER Current
    Path to the current scorecard JSON. Required.

.PARAMETER Baseline
    Path to the baseline scorecard JSON. Optional.

.PARAMETER Allowlist
    Path to the allowlist JSON. Optional.

.PARAMETER FailOn
    Minimum severity to fail the build. Default: serious.

.PARAMETER Top
    Limit blocking findings in output. Default: 10.

.PARAMETER Platform
    Markdown flavor for PR comments (github or ado). Default: ado.

.PARAMETER ArtifactDir
    Directory to output artifacts. Default: artifacts/a11y.

.PARAMETER PostComment
    Whether to generate the PR comment file. Default: true.

.EXAMPLE
    .\a11y-ci.ps1 -Current "scorecard.json" -FailOn "minor"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Current,

    [Parameter(Mandatory=$false)]
    [string]$Baseline,

    [Parameter(Mandatory=$false)]
    [string]$Allowlist,

    [Parameter(Mandatory=$false)]
    [string]$FailOn = "serious",

    [Parameter(Mandatory=$false)]
    [int]$Top = 10,

    [Parameter(Mandatory=$false)]
    [string]$Platform = "ado",

    [Parameter(Mandatory=$false)]
    [string]$ArtifactDir = "artifacts/a11y",

    [Parameter(Mandatory=$false)]
    [switch]$PostComment
)

$ErrorActionPreference = "Stop"

function Log-Section {
    param([string]$Message)
    Write-Host "##[section]$Message"
}

function Log-Error {
    param([string]$Message)
    Write-Host "##[error]$Message"
}

# 1. Validate Inputs
Log-Section "Validating Inputs"

if (-not (Test-Path $Current)) {
    Log-Error "Current scorecard not found: $Current"
    exit 2 # A11Y.CI.INPUT.MISSING.FILE
}

if ($Baseline -and (-not (Test-Path $Baseline))) {
    Log-Error "Baseline scorecard not found: $Baseline"
    exit 2
}

if ($Allowlist -and (-not (Test-Path $Allowlist))) {
    Log-Error "Allowlist file not found: $Allowlist"
    exit 2
}

# 2. Setup Artifacts
Log-Section "Setting up Artifacts"
if (-not (Test-Path $ArtifactDir)) {
    New-Item -ItemType Directory -Path $ArtifactDir -Force | Out-Null
}

$Global:ReportJson = Join-Path $ArtifactDir "report.json"
$Global:EvidenceJson = Join-Path $ArtifactDir "evidence.json"
$Global:CommentMd = Join-Path $ArtifactDir "comment.md"

# Copy input artifacts for traceability?
# Maybe later. For now just generate new ones.

# 3. Run Gate & Generate Evidence
Log-Section "Running Accessibility Gate"

$gateArgs = @(
    "gate",
    "--current", $Current,
    "--fail-on", $FailOn,
    "--top", $Top,
    "--emit-mcp",
    "--mcp-out", $Global:EvidenceJson
)

if ($Baseline) {
    $gateArgs += "--baseline", $Baseline
}

if ($Allowlist) {
    $gateArgs += "--allowlist", $Allowlist
}

Write-Host "Running: a11y-ci $gateArgs"

# Capture exit code carefully
$exitCode = 0
try {
    # We want stdout to go to console (text report), and json report to file?
    # CLI handles --mcp-out to file.
    # Text report goes to stdout.
    
    # Run the command. If it fails (exit 3), it might look like a script failure.
    # We use Invoke-Expression or Start-Process to capture exit code without throwing immediately.
    
    # Direct execution:
    & a11y-ci $gateArgs
    if ($LASTEXITCODE -gt 0) {
        $exitCode = $LASTEXITCODE
    }
}
catch {
    Log-Error "Execution failed: $_"
    exit 1 # Internal error
}

# 4. Generate PR Comment
if ($PostComment) {
    Log-Section "Generating PR Comment"
    
    if (Test-Path $Global:EvidenceJson) {
        try {
            # Use CLI to render
            $commentStart = Get-Content $Global:EvidenceJson | ConvertFrom-Json
            
            # Or simpler:
            a11y-ci comment --mcp $Global:EvidenceJson --platform $Platform --top $Top | Out-File -FilePath $Global:CommentMd -Encoding utf8
            Write-Host "Comment generated at $Global:CommentMd"
        }
        catch {
            Write-Warning "Failed to generate PR comment: $_"
        }
    }
    else {
        Write-Warning "Evidence file missing, cannot generate comment."
    }
}

Log-Section "Summary"
Write-Host "Gate Exit Code: $exitCode"
Write-Host "Artifacts location: $ArtifactDir"

# Set ADO output variables if supported
if ($env:TF_BUILD) {
    Write-Host "##vso[task.setvariable variable=A11yExitCode]$exitCode"
    Write-Host "##vso[task.setvariable variable=A11yReportPath]$Global:EvidenceJson"
    Write-Host "##vso[task.setvariable variable=A11yCommentPath]$Global:CommentMd"
}

exit $exitCode
