$resp = Invoke-WebRequest -Uri 'http://46.253.140.72:8000/health' -TimeoutSec 10
Write-Host "Status: $($resp.StatusCode)"
Write-Host "Content: $($resp.Content)"