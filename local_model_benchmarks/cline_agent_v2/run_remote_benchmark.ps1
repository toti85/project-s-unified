param(
    [Parameter(Mandatory = $true)]
    [System.Management.Automation.PSCredential]$Credential,
    [string]$ComputerName = "46.253.140.72",
    [int]$WinRMPort = 15985,
    [string]$Endpoint = "http://127.0.0.1:8098/v1/chat/completions",
    [string]$Model = "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$cases = Get-Content (Join-Path $root "cases.json") -Raw | ConvertFrom-Json
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultDir = Join-Path $root "results\$stamp"
New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
$summary = @()

foreach ($case in $cases) {
    $fixturePath = Join-Path $root $case.fixture
    $fixture = Get-Content $fixturePath -Raw
    $prompt = "$($case.instruction)`n`n--- FIXTURE START ---`n$fixture`n--- FIXTURE END ---"
    $started = Get-Date

    $response = Invoke-Command -ComputerName $ComputerName -Port $WinRMPort -Credential $Credential -ScriptBlock {
        param($Uri, $ModelId, $PromptText, $MaxTokens)
        $body = @{
            model = $ModelId
            messages = @(@{ role = "user"; content = $PromptText })
            temperature = 0.1
            max_tokens = $MaxTokens
            stream = $false
        } | ConvertTo-Json -Depth 6
        Invoke-RestMethod -Uri $Uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec 300
    } -ArgumentList $Endpoint, $Model, $prompt, ([int]$case.max_tokens)

    $content = [string]$response.choices[0].message.content
    $elapsed = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
    $responsePath = Join-Path $resultDir "$($case.id)_response.txt"
    [System.IO.File]::WriteAllText($responsePath, $content, [System.Text.UTF8Encoding]::new($false))

    $checks = @()
    foreach ($group in $case.required_groups) {
        $matched = @($group | Where-Object { $content.IndexOf([string]$_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
        $checks += [pscustomobject]@{ alternatives = @($group); passed = $matched.Count -gt 0; matched = @($matched) }
    }
    $forbiddenHits = @($case.forbidden | Where-Object { $content.IndexOf([string]$_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
    $passedChecks = @($checks | Where-Object passed).Count
    $casePassed = $passedChecks -eq $checks.Count -and $forbiddenHits.Count -eq 0

    $summary += [pscustomobject]@{
        id = $case.id
        passed = $casePassed
        required_passed = $passedChecks
        required_total = $checks.Count
        forbidden_hits = $forbiddenHits
        latency_seconds = $elapsed
        completion_tokens = $response.usage.completion_tokens
        checks = $checks
        response_file = (Split-Path $responsePath -Leaf)
    }
}

$summaryPath = Join-Path $resultDir "summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding UTF8
$summary | Select-Object id, passed, required_passed, required_total, forbidden_hits, latency_seconds, completion_tokens | Format-Table -AutoSize
Write-Host "Results: $summaryPath"
