$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Fixing SMB Share Permissions ===" -ForegroundColor Cyan

# Fix share permissions and NTFS permissions
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $shareName = "ProjectSStage"
    $sharePath = "C:\ProjectS\project-s-code"
    
    Write-Host "[1] Checking share exists..." -ForegroundColor Gray
    $existingShare = Get-WmiObject -Class Win32_Share -Filter "Name='$shareName'" -ErrorAction SilentlyContinue
    if ($existingShare) {
        Write-Host "  Share found: $($existingShare.Path)" -ForegroundColor Green
    } else {
        Write-Host "  Share NOT found. Recreating..." -ForegroundColor Yellow
        $share = [WMICLASS]"\\.\ROOT\CIMV2:Win32_Share"
        $result = $share.Create($sharePath, $shareName, 0, [int32]::MaxValue, "ProjectS staging")
        Write-Host "  Share created with return code: $($result.ReturnValue)" -ForegroundColor $(if($result.ReturnValue -eq 0){"Green"}else{"Red"})
    }
    
    Write-Host "[2] Setting share permissions (Everyone Full Control)..." -ForegroundColor Gray
    # Remove existing share permissions and re-add
    $shares = Get-WmiObject -Class Win32_Share -Filter "Name='$shareName'"
    foreach ($s in $shares) {
        $acl = $s.GetSecurityDescriptor()
        if ($acl.ReturnValue -eq 0) {
            # Add Everyone with full control
            $newAce = [WMICLASS]"\\.\ROOT\CIMV2:Win32_ACE"
            $newTrustee = [WMICLASS]"\\.\ROOT\CIMV2:Win32_Trustee"
            $newTrustee.Name = "Everyone"
            $newTrustee.Domain = $null
            
            # ACCESS_ALLOWED_ACE = 0, FULL = 255
            $newAce.AceType = 0
            $newAce.AccessMask = 2032127  # STANDARD_RIGHTS_ALL + SPECIFIC_RIGHTS_ALL for full control
            $newAce.AceFlags = 0
            $newAce.Trustee = $newTrustee
            
            $acl.Object.Ace = @($acl.Object.Ace) + @($newAce.Ace)
            $s.SetSecurityDescriptor($acl.Object) | Out-Null
            Write-Host "  Share permissions updated" -ForegroundColor Green
        }
    }
    
    Write-Host "[3] Setting NTFS permissions (Everyone Full Control)..." -ForegroundColor Gray
    $acl = Get-Acl $sharePath
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl -Path $sharePath -AclObject $acl
    Write-Host "  NTFS permissions updated" -ForegroundColor Green
    
    Write-Host "[4] Verifying permissions..." -ForegroundColor Gray
    $currentAcl = Get-Acl $sharePath
    $currentAcl.Access | ForEach-Object {
        Write-Host "    $($_.IdentityReference) - $($_.FileSystemRights)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Permissions fixed. Retrying UNC test..." -ForegroundColor Cyan

# Test UNC again
$destUNC = "\\192.168.1.180\ProjectSStage"
net use $destUNC Qwe123 /user:192.168.1.180\Administrator 2>$null
Start-Sleep -Seconds 2

$uncTest = Test-Path $destUNC
Write-Host "  UNC path reachable: $uncTest" -ForegroundColor $(if($uncTest){"Green"}else{"Red"})

if ($uncTest) {
    Write-Host "  Testing write access..." -ForegroundColor Gray
    $testFile = Join-Path $destUNC ".write_test"
    try {
        Set-Content -Path $testFile -Value "test" -ErrorAction Stop
        Write-Host "  Write access: OK" -ForegroundColor Green
        Remove-Item $testFile -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Write access: FAIL - $_" -ForegroundColor Red
    }
}

# Cleanup
net use $destUNC /delete /y 2>$null