$oldKey = "[REDACTED - EXPOSED KEY REMOVED]"
$redacted = "[REDACTED - EXPOSED KEY REMOVED]"

$locations = @(
    @{ Name = "DEV workspace"; Path = "C:\ProjectS-Unified" },
    @{ Name = "Server staging"; Path = "C:\ProjectS\project-s-code" }
)

$results = @{
    ServerOccurrences = 0
    DevOccurrences = 0
    FilesRedacted = @()
    ScriptsHardened = @()
    RemainingSecrets = @()
}

foreach ($loc in $locations) {
    $count = 0
    $files = Get-ChildItem -Path $loc.Path -Recurse -Include "*.md","*.txt","*.json","*.ps1","*.py","*.env","*.yml","*.yaml","*.cfg","*.ini","*.toml" -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw -ErrorAction Stop
            if ($content -match [regex]::Escape($oldKey)) {
                $count++
                if ($loc.Name -eq "Server staging") {
                    $results.ServerOccurrences++
                } else {
                    $results.DevOccurrences++
                }
                $results.FilesRedacted += $file.FullName
                
                # Redact
                $newContent = $content -replace [regex]::Escape($oldKey), $redacted
                Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8 -ErrorAction Stop
                
                # Track if it's a script
                if ($file.Extension -match '\.(ps1|py)$') {
                    $results.ScriptsHardened += $file.FullName
                }
            }
        } catch {
            # Skip files we can't read
        }
    }
}

# Check for any remaining raw key occurrences
foreach ($loc in $locations) {
    $files = Get-ChildItem -Path $loc.Path -Recurse -Include "*.md","*.txt","*.json","*.ps1","*.py","*.env","*.yml","*.yaml","*.cfg","*.ini","*.toml" -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw -ErrorAction Stop
            if ($content -match 'sk-or-v1-[a-f0-9]{70}') {
                $results.RemainingSecrets += $file.FullName
            }
        } catch {}
    }
}

# Save results
$results | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.redaction_results.json" -Encoding UTF8

# Output summary
Write-Host "=== SECRET REDACTION RESULTS ===" -ForegroundColor Cyan
Write-Host ("Server occurrences: " + $results.ServerOccurrences) -ForegroundColor Yellow
Write-Host ("Dev occurrences: " + $results.DevOccurrences) -ForegroundColor Yellow
Write-Host ("Files redacted: " + $results.FilesRedacted.Count) -ForegroundColor Yellow
Write-Host ("Scripts hardened: " + $results.ScriptsHardened.Count) -ForegroundColor Yellow
Write-Host ("Remaining secrets: " + ($results.RemainingSecrets.Count -gt 0)) -ForegroundColor $(if($results.RemainingSecrets.Count -eq 0){"Green"}else{"Red"})
