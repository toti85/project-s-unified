import subprocess
import sys
import os

# Transfer ZIP to DL380 via LAN WinRM
ps_script = r"""
$secPass = ConvertTo-SecureString 'Qwe123' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('Administrator', $secPass)

Write-Output "=== Creating target directory on DL380 ==="
try {
    $s = New-PSSession -ComputerName 192.168.1.180 -Credential $cred -ErrorAction Stop
    Invoke-Command -Session $s -ScriptBlock {
        $target = 'C:\ProjectS-Snapshot-20260601'
        if (Test-Path $target) {
            Write-Output "Target directory already exists"
        } else {
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            Write-Output "Created: $target"
        }
    }
    Write-Output "Directory created successfully"
} catch {
    Write-Output ("Directory creation failed: " + $_.Exception.Message)
    exit 1
}

Write-Output "=== Copying ZIP file to DL380 ==="
$zipPath = 'C:\ProjectS-Unified\ProjectS-Snapshot-20260601.zip'
$zipSize = (Get-Item $zipPath).Length
Write-Output ("ZIP size: " + [math]::Round($zipSize/1MB, 2) + " MB")

try {
    Copy-Item -Path $zipPath -Destination "\\192.168.1.180\C$\ProjectS-Snapshot-20260601\ProjectS-Snapshot-20260601.zip" -Credential $cred -Force
    Write-Output "ZIP copied via SMB"
} catch {
    Write-Output ("SMB copy failed: " + $_.Exception.Message)
    Write-Output "Trying WinRM copy..."
    try {
        $fileBytes = [System.IO.File]::ReadAllBytes($zipPath)
        Invoke-Command -Session $s -ArgumentList $fileBytes -ScriptBlock {
            param($bytes)
            [System.IO.File]::WriteAllBytes('C:\ProjectS-Snapshot-20260601\ProjectS-Snapshot-20260601.zip', $bytes)
            Write-Output "ZIP written via WinRM"
        }
    } catch {
        Write-Output ("WinRM copy also failed: " + $_.Exception.Message)
    }
}

Write-Output "=== Verifying ZIP on DL380 ==="
try {
    $result = Invoke-Command -Session $s -ScriptBlock {
        $zip = 'C:\ProjectS-Snapshot-20260601\ProjectS-Snapshot-20260601.zip'
        if (Test-Path $zip) {
            $size = (Get-Item $zip).Length
            @{exists=$true; size=$size}
        } else {
            @{exists=$false; size=0}
        }
    }
    Write-Output ("ZIP exists on DL380: " + $result.exists)
    Write-Output ("ZIP size on DL380: " + [math]::Round($result.size/1MB, 2) + " MB")
} catch {
    Write-Output ("Verification failed: " + $_.Exception.Message)
}

Write-Output "=== Extracting ZIP on DL380 ==="
try {
    Invoke-Command -Session $s -ScriptBlock {
        $zip = 'C:\ProjectS-Snapshot-20260601\ProjectS-Snapshot-20260601.zip'
        $dest = 'C:\ProjectS-Snapshot-20260601'
        Expand-Archive -Path $zip -DestinationPath $dest -Force
        Write-Output "ZIP extracted"
        
        # List top-level contents
        $items = Get-ChildItem $dest -Directory | Select-Object -ExpandProperty Name
        Write-Output ("Top-level directories: " + ($items -join ', '))
        
        # Count files
        $fileCount = (Get-ChildItem $dest -Recurse -File).Count
        Write-Output ("Total files extracted: " + $fileCount)
        
        # Check for .env.local (should NOT exist)
        $envLocal = Get-ChildItem $dest -Recurse -Include '.env.local', '.env' -ErrorAction SilentlyContinue
        if ($envLocal) {
            Write-Output ("WARNING: Credential files found: " + ($envLocal | ForEach-Object { $_.FullName }))
        } else {
            Write-Output "No credential files found (OK)"
        }
        
        # Check self_state.json
        $ss = Join-Path $dest 'self_state.json'
        if (Test-Path $ss) {
            try {
                $content = Get-Content $ss -Raw
                $jsonObj = ConvertFrom-Json $content
                Write-Output "self_state.json: valid JSON"
            } catch {
                Write-Output "self_state.json: INVALID JSON"
            }
        } else {
            Write-Output "self_state.json: NOT FOUND"
        }
    }
} catch {
    Write-Output ("Extraction failed: " + $_.Exception.Message)
}

Remove-PSSession $s
Write-Output "=== Transfer complete ==="
"""

result = subprocess.run(
    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
    capture_output=True, text=True, timeout=600, cwd=r'C:\ProjectS-Unified'
)

output = result.stdout + result.stderr
print(output)

with open(r'C:\ProjectS-Unified\dl380_transfer_result.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Results saved to dl380_transfer_result.txt")