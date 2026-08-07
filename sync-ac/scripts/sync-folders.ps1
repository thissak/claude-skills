param(
    [Parameter(Mandatory=$true)]
    [string]$Direction  # "cp2ac" or "ac2cp"
)

$CP = "E:\KAI_VCBT\fa50visualdev_new"
$AC = "E:\KAI_VCBT\fa50visualdev_new_AC"
$Folders = @("Binaries", "Source", "Plugins", "Content", "Intermediate", "Config\Tags")

if ($Direction -eq "cp2ac") {
    $Src = $CP
    $Dst = $AC
    Write-Host "=== CP -> AC ===" -ForegroundColor Cyan
} elseif ($Direction -eq "ac2cp") {
    $Src = $AC
    $Dst = $CP
    Write-Host "=== AC -> CP ===" -ForegroundColor Cyan
} else {
    Write-Host "Invalid direction: $Direction" -ForegroundColor Red
    exit 1
}

foreach ($f in $Folders) {
    Write-Host "  $f..." -NoNewline
    $result = robocopy "$Src\$f" "$Dst\$f" /MIR /NJH /NJS /NDL /NFL /NC /NS 2>&1
    if ($LASTEXITCODE -le 1) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " WARN ($LASTEXITCODE)" -ForegroundColor Yellow
    }
}

Write-Host "Done!" -ForegroundColor Cyan
