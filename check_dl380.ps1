# Check DL380 RAG workspace
try {
    $s = New-PSSession -ComputerName "46.253.140.72" -Port 15985 -UseSSL -SessionOption (New-PSSessionOption -SkipCACheck -SkipCNCheck) -ErrorAction Stop
    $result = Invoke-Command -Session $s -ScriptBlock {
        if (Test-Path "F:\ModelVault\rag\project_s_index_v1\") {
            Get-ChildItem "F:\ModelVault\rag\project_s_index_v1\" -Recurse
        } else {
            Write-Output "PATH_NOT_FOUND"
        }
    }
    $result
    Remove-PSSession $s
} catch {
    Write-Output "CONNECTION_FAILED: $_"
}