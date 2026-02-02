param(
    [Parameter(Mandatory=$true)]
    [string]$Direction,  # "cp2ac" or "ac2cp"
    [switch]$LaunchEditor  # 에디터 실행 여부
)

$CP = "E:\KAI_VCBT\fa50visualdev_new"
$AC = "E:\KAI_VCBT\fa50visualdev_new_AC"
$UE_Editor = "E:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe"
$Folders = @("Binaries", "Source", "Plugins", "Content", "Intermediate")

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

# 에디터 실행
if ($LaunchEditor) {
    Write-Host "=== Launching Editors ===" -ForegroundColor Cyan
    Write-Host "  CP Editor..." -NoNewline
    Start-Process -FilePath $UE_Editor -ArgumentList "`"$CP\FA50VisualDev.uproject`""
    Write-Host " OK" -ForegroundColor Green

    Write-Host "  AC Editor..." -NoNewline
    Start-Process -FilePath $UE_Editor -ArgumentList "`"$AC\FA50VisualDev.uproject`""
    Write-Host " OK" -ForegroundColor Green
}
