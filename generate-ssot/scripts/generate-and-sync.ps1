# generate-and-sync.ps1
# SSOT 생성 + 언리얼 프로젝트 복사 + Diff 검증

param(
    [switch]$SkipCopy,      # 생성만 하고 복사하지 않음
    [switch]$SkipGenerate   # 생성 건너뛰고 복사만
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================
# 경로 설정
# ============================================
$SSOT_ROOT = "E:\UECsvDataTableConverter"
$UE_PROJECT = "E:\KAI_VCBT\fa50visualdev_new"

$FILES = @(
    @{
        Name = "DT_ControlData.csv"
        Source = "$SSOT_ROOT\Generated\DT_ControlData.csv"
        Target = "$UE_PROJECT\DT_ControlData.csv"
    },
    @{
        Name = "FA50M_GameplayTags.ini"
        Source = "$SSOT_ROOT\Generated\FA50M_GameplayTags.ini"
        Target = "$UE_PROJECT\Config\Tags\FA50M_GameplayTags.ini"
    },
    @{
        Name = "equipment_mapping.h"
        Source = "$SSOT_ROOT\Generated\equipment_mapping.h"
        Target = "$UE_PROJECT\Source\FA50VisualDev\Public\HostConnector\ReceiverUdp100\Types\equipment_mapping.h"
    }
)

# ============================================
# Step 1: SSOT 스크립트 실행
# ============================================
if (-not $SkipGenerate) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  [1/4] SSOT 스크립트 실행" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    # DataTable + GameplayTags 생성
    Write-Host ""
    Write-Host "  [1-1] DataTable 생성 중..." -ForegroundColor Yellow
    Push-Location $SSOT_ROOT
    try {
        # conda 환경에서 실행
        $result = & cmd /c "conda activate processtree && python ue_create_datatable_gameplaytag.py 2>&1"
        Write-Host $result
        if ($LASTEXITCODE -ne 0) { throw "DataTable 생성 실패" }
        Write-Host "       OK" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }

    # Equipment Mapping 생성
    Write-Host ""
    Write-Host "  [1-2] Equipment Mapping 생성 중..." -ForegroundColor Yellow
    Push-Location "$SSOT_ROOT\EquipmentMapping"
    try {
        $result = & cmd /c "conda activate processtree && python generate_equipment_mapping.py 2>&1"
        Write-Host $result
        if ($LASTEXITCODE -ne 0) { throw "Equipment Mapping 생성 실패" }
        Write-Host "       OK" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}

if ($SkipCopy) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  생성 완료 (복사 건너뜀)" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    exit 0
}

# ============================================
# Step 2: 기존 파일 백업
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  [2/4] 기존 파일 백업" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$BACKUP_DIR = "$env:TEMP\ssot_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null

foreach ($file in $FILES) {
    $backupPath = "$BACKUP_DIR\$($file.Name)"
    if (Test-Path $file.Target) {
        Copy-Item $file.Target $backupPath
        Write-Host "  $($file.Name) -> 백업 완료" -ForegroundColor Gray
    } else {
        Write-Host "  $($file.Name) -> 기존 파일 없음 (신규)" -ForegroundColor Yellow
        # 빈 파일 생성 (diff용)
        New-Item -ItemType File -Path $backupPath -Force | Out-Null
    }
}

# ============================================
# Step 3: 파일 복사
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  [3/4] 파일 복사" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

foreach ($file in $FILES) {
    if (Test-Path $file.Source) {
        # 대상 디렉토리 확인
        $targetDir = Split-Path $file.Target -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        Copy-Item $file.Source $file.Target -Force
        Write-Host "  $($file.Name) -> 복사 완료" -ForegroundColor Green
    } else {
        Write-Host "  $($file.Name) -> 소스 파일 없음!" -ForegroundColor Red
    }
}

# ============================================
# Step 4: Diff 검증
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  [4/4] 변경사항 검증 (Diff)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$totalChanges = 0

foreach ($file in $FILES) {
    $backupPath = "$BACKUP_DIR\$($file.Name)"
    $newPath = $file.Target

    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "  $($file.Name)" -ForegroundColor White
    Write-Host "----------------------------------------" -ForegroundColor DarkGray

    if ((Test-Path $backupPath) -and (Test-Path $newPath)) {
        # 파일 비교
        $oldContent = Get-Content $backupPath -ErrorAction SilentlyContinue
        $newContent = Get-Content $newPath -ErrorAction SilentlyContinue

        if ($null -eq $oldContent) { $oldContent = @() }
        if ($null -eq $newContent) { $newContent = @() }

        $diff = Compare-Object $oldContent $newContent -PassThru

        if ($diff) {
            $added = ($diff | Where-Object { $_.SideIndicator -eq "=>" }).Count
            $removed = ($diff | Where-Object { $_.SideIndicator -eq "<=" }).Count

            Write-Host "  +$added 추가 / -$removed 삭제" -ForegroundColor Yellow
            $totalChanges += ($added + $removed)

            # 상세 diff (최대 10줄)
            $diffLines = $diff | Select-Object -First 10
            foreach ($line in $diffLines) {
                if ($line.SideIndicator -eq "=>") {
                    Write-Host "    + $($line.ToString().Substring(0, [Math]::Min(80, $line.ToString().Length)))" -ForegroundColor Green
                } else {
                    Write-Host "    - $($line.ToString().Substring(0, [Math]::Min(80, $line.ToString().Length)))" -ForegroundColor Red
                }
            }
            if ($diff.Count -gt 10) {
                Write-Host "    ... 외 $($diff.Count - 10)개 변경" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  변경 없음" -ForegroundColor Green
        }
    } else {
        Write-Host "  신규 파일" -ForegroundColor Yellow
        $totalChanges += 1
    }
    Write-Host ""
}

# ============================================
# 결과 요약
# ============================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  완료!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  생성된 파일: $SSOT_ROOT\Generated\" -ForegroundColor Gray
Write-Host "  복사된 위치: $UE_PROJECT\" -ForegroundColor Gray
Write-Host "  총 변경사항: $totalChanges 건" -ForegroundColor $(if ($totalChanges -gt 0) { "Yellow" } else { "Green" })
Write-Host ""
Write-Host "  백업 위치: $BACKUP_DIR" -ForegroundColor DarkGray
Write-Host ""

# 변경사항이 있으면 종료 코드 1 반환 (CI/CD용)
if ($totalChanges -gt 0) {
    exit 1
} else {
    exit 0
}
