# Install payments-ops-squad without the plugin system: copies agents, skills, commands and the
# documentation fetcher into ~/.claude (user scope) or ./.claude (project scope).
#
# Usage: install/install.ps1 [-Scope user|project] [-Force]
#
# Without -Force nothing is overwritten: if any target already exists the script lists the
# conflicts, writes nothing and exits 2.
[CmdletBinding()]
param(
    [ValidateSet("user", "project")]
    [string]$Scope = "user",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Scope -eq "user") {
    $Dest = Join-Path $HOME ".claude"
} else {
    $Dest = Join-Path (Get-Location).Path ".claude"
}

$Src = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Pkg = Join-Path $Dest "payments-ops-squad"

# Units to install: kind, source, target.
$Units = New-Object System.Collections.Generic.List[object]
function Add-Unit([string]$Kind, [string]$Source, [string]$Target) {
    $Units.Add([pscustomobject]@{ Kind = $Kind; Source = $Source; Target = $Target })
}

Get-ChildItem -Path (Join-Path $Src "agents") -Filter "*.md" -File | Sort-Object Name | ForEach-Object {
    Add-Unit "agent" $_.FullName (Join-Path (Join-Path $Dest "agents") $_.Name)
}
$SkillDirs = @()
$SkillDirs += Get-ChildItem -Path (Join-Path $Src "skills") -Directory | Where-Object { $_.Name -ne "stripe" }
$SkillDirs += Get-ChildItem -Path (Join-Path (Join-Path $Src "skills") "stripe") -Directory
foreach ($d in ($SkillDirs | Sort-Object Name)) {
    if (Test-Path (Join-Path $d.FullName "SKILL.md")) {
        Add-Unit "skill" $d.FullName (Join-Path (Join-Path $Dest "skills") $d.Name)
    }
}
Get-ChildItem -Path (Join-Path $Src "commands") -Filter "*.md" -File | Sort-Object Name | ForEach-Object {
    Add-Unit "command" $_.FullName (Join-Path (Join-Path $Dest "commands") $_.Name)
}
Add-Unit "support" (Join-Path (Join-Path $Src "tools") "fetch_doc.py") (Join-Path (Join-Path $Pkg "tools") "fetch_doc.py")
Add-Unit "support" (Join-Path (Join-Path $Src "knowledge") "INDEX.md") (Join-Path $Pkg "INDEX.md")
Add-Unit "support" (Join-Path (Join-Path $Src "knowledge") "sources.json") (Join-Path $Pkg "sources.json")

$Conflicts = @($Units | Where-Object { Test-Path -LiteralPath $_.Target } | ForEach-Object { $_.Target })

if ($Conflicts.Count -gt 0 -and -not $Force) {
    [Console]::Error.WriteLine("install: $($Conflicts.Count) target(s) already exist; nothing was written:")
    foreach ($c in $Conflicts) { [Console]::Error.WriteLine("  $c") }
    [Console]::Error.WriteLine("install: run again with -Force to overwrite them.")
    exit 2
}

$Counts = @{ agent = 0; skill = 0; command = 0; support = 0 }
foreach ($u in $Units) {
    $parent = Split-Path -Parent $u.Target
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    if (Test-Path -LiteralPath $u.Source -PathType Container) {
        if (Test-Path -LiteralPath $u.Target) { Remove-Item -LiteralPath $u.Target -Recurse -Force }
        Copy-Item -LiteralPath $u.Source -Destination $u.Target -Recurse
    } else {
        Copy-Item -LiteralPath $u.Source -Destination $u.Target -Force
    }
    $Counts[$u.Kind]++
}

# Knowledge cache for documentation fetched on demand. The marker lets fetch_doc.py find it.
$Knowledge = Join-Path $Pkg "knowledge"
New-Item -ItemType Directory -Force -Path $Knowledge | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $Knowledge ".payments-ops-cache") | Out-Null

Write-Output "payments-ops-squad installed ($Scope scope) into $Dest"
Write-Output "  agents:   $($Counts['agent'])"
Write-Output "  skills:   $($Counts['skill'])"
Write-Output "  commands: $($Counts['command'])"
Write-Output "  tools:    $(Join-Path (Join-Path $Pkg 'tools') 'fetch_doc.py')"
Write-Output "  cache:    $Knowledge"
if ($Conflicts.Count -gt 0) {
    Write-Output "  overwritten (-Force): $($Conflicts.Count)"
}
Write-Output "Restart Claude Code to load the new agents, skills and commands."
