param(
    [ValidateSet("coder", "planner", "stop", "status")]
    [string]$ProfileName = "status",
    [int]$ReadyTimeoutSec = 180
)

$ErrorActionPreference = "Stop"

$root = "F:\ModelVault"
$llamaServer = Join-Path $root "llama-cpp\vulkan-bin\llama-server.exe"
$python = "C:\Program Files\Python312\python.exe"
$proxyScript = Join-Path $root "scripts\model_cline_proxy.py"
$logDir = Join-Path $root "logs"
$statePath = Join-Path $root "runtime\active_profile.json"

$profiles = @{
    coder = @{
        model = Join-Path $root "gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf"
        model_id = "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf"
        port = 8098
        context = 8192
        extra = "-ngl 99"
        endpoint = "http://127.0.0.1:8098/v1"
    }
    planner = @{
        model = Join-Path $root "gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\Qwen3.6-35B-A3B-Q4_K_M.gguf"
        model_id = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
        port = 8096
        context = 16384
        extra = ""
        endpoint = "http://127.0.0.1:8097/v1"
    }
}

function Get-ManagedProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -eq "llama-server.exe" -and $_.CommandLine -match "ModelVault") -or
        ($_.Name -match "python" -and $_.CommandLine -match "cline_proxy|uvicorn")
    }
}

function Stop-ManagedProcesses {
    foreach ($process in @(Get-ManagedProcesses)) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Start-PersistentProcess {
    param([Parameter(Mandatory = $true)][string]$CommandLine)

    $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $CommandLine
    }
    if ($result.ReturnValue -ne 0) {
        throw "Win32_Process.Create failed with return value $($result.ReturnValue)"
    }
    return $result.ProcessId
}

function Wait-Endpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][int]$TimeoutSec
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    do {
        try {
            return Invoke-RestMethod -Uri $Url -TimeoutSec 4
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Endpoint did not become ready: $Url"
}

function Write-State {
    param([string]$Name, [hashtable]$Config, [int]$ModelPid, [Nullable[int]]$ProxyPid)

    $stateDir = Split-Path $statePath -Parent
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    [ordered]@{
        profile = $Name
        model = $Config.model_id
        endpoint = $Config.endpoint
        model_pid = $ModelPid
        proxy_pid = $ProxyPid
        started_utc = [DateTime]::UtcNow.ToString("o")
        bind = "127.0.0.1"
    } | ConvertTo-Json | Set-Content -Path $statePath -Encoding UTF8
}

function Show-Status {
    $processes = @(Get-ManagedProcesses | Select-Object ProcessId, Name, CommandLine)
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object LocalPort -in 8096, 8097, 8098, 8099 |
        Select-Object LocalAddress, LocalPort, OwningProcess)
    $state = if (Test-Path $statePath) {
        Get-Content $statePath -Raw | ConvertFrom-Json
    } else {
        $null
    }
    [pscustomobject]@{
        state = $state
        processes = $processes
        listeners = $listeners
    }
}

if ($ProfileName -eq "status") {
    Show-Status
    exit 0
}

Stop-ManagedProcesses
if (Test-Path $statePath) {
    Remove-Item $statePath -Force
}

if ($ProfileName -eq "stop") {
    Show-Status
    exit 0
}

$config = $profiles[$ProfileName]
if (-not (Test-Path $llamaServer)) {
    throw "llama-server not found: $llamaServer"
}
if (-not (Test-Path $config.model)) {
    throw "Model not found: $($config.model)"
}
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$modelCommand = '"{0}" -m "{1}" --port {2} --host 127.0.0.1 --ctx-size {3} {4}' -f `
    $llamaServer, $config.model, $config.port, $config.context, $config.extra
$null = Start-PersistentProcess -CommandLine $modelCommand
$null = Wait-Endpoint -Url "http://127.0.0.1:$($config.port)/v1/models" -TimeoutSec $ReadyTimeoutSec
$modelPid = (Get-NetTCPConnection -LocalPort $config.port -State Listen).OwningProcess

$proxyPid = $null
if ($ProfileName -eq "planner") {
    if (-not (Test-Path $python)) {
        throw "Python not found: $python"
    }
    if (-not (Test-Path $proxyScript)) {
        throw "Proxy not found: $proxyScript"
    }
    $proxyCommand = '"{0}" "{1}" --port 8097 --upstream http://127.0.0.1:8096' -f $python, $proxyScript
    $null = Start-PersistentProcess -CommandLine $proxyCommand
    $null = Wait-Endpoint -Url "http://127.0.0.1:8097/v1/models" -TimeoutSec 30
    $proxyPid = (Get-NetTCPConnection -LocalPort 8097 -State Listen).OwningProcess
}

Write-State -Name $ProfileName -Config $config -ModelPid $modelPid -ProxyPid $proxyPid
Show-Status
