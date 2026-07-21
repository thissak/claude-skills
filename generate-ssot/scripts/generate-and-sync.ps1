# generate-and-sync.ps1
# Downloads에서 최신 엑셀 복사 → SSOT 생성(변경분만) → 언리얼 프로젝트 복사 → Diff 검증

param(
    [switch]$SkipCopy,       # 생성만 하고 복사하지 않음
    [switch]$SkipGenerate,   # 생성 건너뛰고 복사만
    [switch]$SkipExcel,      # 엑셀 복사 건너뛰기
    [switch]$SkipReimport,   # UE Editor 자동 Reimport 건너뛰기
    [switch]$Force           # 변경 감지 무시하고 모든 파이프라인 강제 실행
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================
# 경로 설정
# ============================================
$SSOT_ROOT = "E:\UECsvDataTableConverter"
$UE_PROJECT = "E:\KAI_VCBT\fa50visualdev_new"
$EXCEL_PATTERN = "$HOME\Downloads\250520_FA50M-계층구조_버튼식별_v3.0*.xlsx"
$EXCEL_TARGET = "$SSOT_ROOT\250520_FA50M-계층구조_버튼식별_v3.0.xlsx"

# ANIMToSeq 경로
# 파이프라인:
#   vcbt_folder_mapping.json + DB(tbl_task)
#     → [1-3a] generate_task_vcbt_csv.py
#       → DT_TaskVcbtMapping.csv (중간 산출물, UE에 복사 안 함)
#         → [1-3b] generate_animid_marker_mapping.py
#           → DT_AnimIdMarkerMapping.csv (UE 복사 대상)
$ANIMTOSEQ_DIR = "$SSOT_ROOT\ANIMToSeq"
$ANIMTOSEQ_MAPPING = "$ANIMTOSEQ_DIR\vcbt_folder_mapping.json"

$TASKVCBT_SCRIPT = "$ANIMTOSEQ_DIR\scripts\generate_task_vcbt_csv.py"
$TASKVCBT_OUTPUT = "$ANIMTOSEQ_DIR\Generated\DT_TaskVcbtMapping.csv"

$ANIMTOSEQ_SCRIPT = "$ANIMTOSEQ_DIR\scripts\generate_animid_marker_mapping.py"
$ANIMTOSEQ_OUTPUT = "$ANIMTOSEQ_DIR\Generated\DT_AnimIdMarkerMapping.csv"

# Equipment Mapping 스크립트 경로 (MANUAL_ENTRIES 변경 감지용)
$EQUIPMAP_SCRIPT = "$SSOT_ROOT\EquipmentMapping\generate_equipment_mapping.py"

# Python 환경
# - processtree (conda): 엑셀 처리용 (openpyxl 등) → [1-1], [1-2]
# - base (miniconda):    psycopg2 보유          → [1-3] (DB 조회)
$BASE_PYTHON = "C:\ProgramData\miniconda3\python.exe"

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
    },
    @{
        Name = "DT_AnimIdMarkerMapping.csv"
        Source = $ANIMTOSEQ_OUTPUT
        Target = "$UE_PROJECT\DT_AnimIdMarkerMapping.csv"
    }
)

# ============================================
# Helper: 변경 감지 (입력 파일 SHA256 해시 사이드카 비교)
# - mtime 비교는 false negative 발생 가능 (partial run, 외부 touch 등)
# - 해시는 입력 내용 기반이라 false negative 없음
# - 사이드카: <output>.input-hash (해시 묶음 텍스트)
# ============================================
function Get-InputHash {
    param([string[]]$Sources)
    $sb = New-Object System.Text.StringBuilder
    foreach ($s in ($Sources | Sort-Object)) {
        if (Test-Path $s) {
            $h = (Get-FileHash $s -Algorithm SHA256).Hash
            [void]$sb.AppendLine("$s|$h")
        } else {
            [void]$sb.AppendLine("$s|MISSING")
        }
    }
    return $sb.ToString()
}

function Get-HashFilePath {
    param([string]$Target)
    return "$Target.input-hash"
}

function Test-NeedRun {
    param(
        [string[]]$Sources,   # 입력 파일들
        [string]$Target       # 출력 파일
    )
    if ($Force) { return $true }
    if (-not (Test-Path $Target)) { return $true }   # 출력 없으면 실행

    $hashFile = Get-HashFilePath $Target
    if (-not (Test-Path $hashFile)) { return $true }  # 사이드카 없으면 실행

    $current = Get-InputHash -Sources $Sources
    $stored = Get-Content $hashFile -Raw -ErrorAction SilentlyContinue
    return ($current -ne $stored)
}

function Save-InputHash {
    param(
        [string[]]$Sources,
        [string]$Target
    )
    if (-not (Test-Path $Target)) { return }
    $hashFile = Get-HashFilePath $Target
    $current = Get-InputHash -Sources $Sources
    Set-Content -Path $hashFile -Value $current -Encoding UTF8 -NoNewline
}

# ============================================
# Step 0: Downloads에서 최신 엑셀 복사
# ============================================
if (-not $SkipExcel -and -not $SkipGenerate) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  [0/5] Downloads에서 최신 엑셀 복사" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    $latestExcel = Get-ChildItem $EXCEL_PATTERN -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($latestExcel) {
        Write-Host "  찾은 파일: $($latestExcel.Name)" -ForegroundColor White
        Write-Host "  수정 시간: $($latestExcel.LastWriteTime)" -ForegroundColor Gray

        if (Test-Path $EXCEL_TARGET) {
            $currentExcel = Get-Item $EXCEL_TARGET
            if ($latestExcel.LastWriteTime -gt $currentExcel.LastWriteTime) {
                Copy-Item $latestExcel.FullName $EXCEL_TARGET -Force
                Write-Host "  -> 최신 엑셀로 교체 완료" -ForegroundColor Green
            } else {
                Write-Host "  -> 로컬이 이미 최신 (건너뜀)" -ForegroundColor Yellow
            }
        } else {
            Copy-Item $latestExcel.FullName $EXCEL_TARGET -Force
            Write-Host "  -> 엑셀 복사 완료" -ForegroundColor Green
        }
    } else {
        Write-Host "  Downloads에서 엑셀을 찾을 수 없음" -ForegroundColor Yellow
        Write-Host "  패턴: $EXCEL_PATTERN" -ForegroundColor Gray
        Write-Host "  -> 기존 로컬 엑셀 사용" -ForegroundColor Yellow
    }
}

# ============================================
# Step 1: SSOT 스크립트 실행 (변경분만)
# ============================================
if (-not $SkipGenerate) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  [1/5] SSOT 스크립트 실행 (변경분만)" -ForegroundColor Cyan
    if ($Force) { Write-Host "  *** -Force: 전체 강제 실행 ***" -ForegroundColor Magenta }
    Write-Host "============================================" -ForegroundColor Cyan

    # ----- [1-1] DataTable + GameplayTags -----
    Write-Host ""
    $dtSources = @($EXCEL_TARGET)
    $dtTarget = "$SSOT_ROOT\Generated\DT_ControlData.csv"
    if (Test-NeedRun -Sources $dtSources -Target $dtTarget) {
        Write-Host "  [1-1] DataTable 생성 중..." -ForegroundColor Yellow
        Push-Location $SSOT_ROOT
        try {
            conda activate processtree
            $env:PYTHONIOENCODING = "utf-8"
            python ue_create_datatable_gameplaytag.py
            if ($LASTEXITCODE -ne 0) { throw "DataTable 생성 실패" }
            Save-InputHash -Sources $dtSources -Target $dtTarget
            Write-Host "       OK" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "  [1-1] DataTable: 변경 없음 (건너뜀)" -ForegroundColor DarkGray
    }

    # ----- [1-2] Equipment Mapping -----
    Write-Host ""
    $emSources = @($EXCEL_TARGET, $EQUIPMAP_SCRIPT)
    $emTarget = "$SSOT_ROOT\Generated\equipment_mapping.h"
    if (Test-NeedRun -Sources $emSources -Target $emTarget) {
        Write-Host "  [1-2] Equipment Mapping 생성 중..." -ForegroundColor Yellow
        Push-Location "$SSOT_ROOT\EquipmentMapping"
        try {
            python generate_equipment_mapping.py
            if ($LASTEXITCODE -ne 0) { throw "Equipment Mapping 생성 실패" }
            Save-InputHash -Sources $emSources -Target $emTarget
            Write-Host "       OK" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "  [1-2] Equipment Mapping: 변경 없음 (건너뜀)" -ForegroundColor DarkGray
    }

    # ----- [1-3a] Task VCBT Mapping CSV (json → csv, DB 사용) -----
    # vcbt_folder_mapping.json 변경 시 → DT_TaskVcbtMapping.csv 재생성
    Write-Host ""
    $tvSources = @($ANIMTOSEQ_MAPPING, $TASKVCBT_SCRIPT)
    if (Test-NeedRun -Sources $tvSources -Target $TASKVCBT_OUTPUT) {
        Write-Host "  [1-3a] Task VCBT Mapping 생성 중..." -ForegroundColor Yellow
        if (-not (Test-Path $BASE_PYTHON)) {
            throw "Base Python not found: $BASE_PYTHON (psycopg2 보유 환경 필요)"
        }
        Push-Location $ANIMTOSEQ_DIR
        try {
            & $BASE_PYTHON scripts\generate_task_vcbt_csv.py
            if ($LASTEXITCODE -ne 0) { throw "Task VCBT Mapping 생성 실패" }
            Save-InputHash -Sources $tvSources -Target $TASKVCBT_OUTPUT
            Write-Host "       OK" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "  [1-3a] Task VCBT Mapping: 변경 없음 (건너뜀)" -ForegroundColor DarkGray
    }

    # ----- [1-3b] AnimId Marker Mapping (csv → csv, DB 사용) -----
    # DT_TaskVcbtMapping.csv 변경 시 → DT_AnimIdMarkerMapping.csv 재생성
    Write-Host ""
    $animSources = @($TASKVCBT_OUTPUT, $ANIMTOSEQ_SCRIPT)
    if (Test-NeedRun -Sources $animSources -Target $ANIMTOSEQ_OUTPUT) {
        Write-Host "  [1-3b] AnimId Marker Mapping 생성 중..." -ForegroundColor Yellow
        Write-Host "         (DB animation 변경은 자동 검출 불가 - 필요 시 -Force)" -ForegroundColor DarkGray
        if (-not (Test-Path $BASE_PYTHON)) {
            throw "Base Python not found: $BASE_PYTHON (psycopg2 보유 환경 필요)"
        }
        Push-Location $ANIMTOSEQ_DIR
        try {
            & $BASE_PYTHON scripts\generate_animid_marker_mapping.py
            if ($LASTEXITCODE -ne 0) { throw "AnimId Marker Mapping 생성 실패" }
            Save-InputHash -Sources $animSources -Target $ANIMTOSEQ_OUTPUT
            Write-Host "       OK" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "  [1-3b] AnimId Marker Mapping: 변경 없음 (건너뜀)" -ForegroundColor DarkGray
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
Write-Host "  [2/5] 기존 파일 백업" -ForegroundColor Cyan
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
        New-Item -ItemType File -Path $backupPath -Force | Out-Null
    }
}

# ============================================
# Step 3: 파일 복사
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  [3/5] 파일 복사" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

foreach ($file in $FILES) {
    if (Test-Path $file.Source) {
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
Write-Host "  [4/5] 변경사항 검증 (Diff)" -ForegroundColor Cyan
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
# Step 5: UE Editor Reimport (DataTables)
# ============================================
if (-not $SkipReimport -and -not $SkipCopy) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  [5/5] UE Editor Reimport (DataTables)" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    $reimportScript = "$PSScriptRoot\reimport_datatables.py"
    if (-not (Test-Path $reimportScript)) {
        Write-Host "  reimport_datatables.py 없음 (건너뜀): $reimportScript" -ForegroundColor Yellow
    } else {
        # 에디터 실행 여부 확인
        $editorProc = Get-Process -Name "UnrealEditor" -ErrorAction SilentlyContinue
        if (-not $editorProc) {
            Write-Host "  UE Editor 미실행 - Reimport 건너뜀" -ForegroundColor Yellow
            Write-Host "  (에디터 실행 후 수동: python $reimportScript)" -ForegroundColor DarkGray
        } else {
            Write-Host "  UE Editor $($editorProc.Count)개 실행 중 - Remote Execution으로 Reimport" -ForegroundColor Gray
            try {
                python $reimportScript
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  Reimport 완료" -ForegroundColor Green
                } else {
                    Write-Host "  Reimport 일부 실패 (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  Reimport 실행 오류: $_" -ForegroundColor Red
            }
        }
    }
}

# ============================================
# 결과 요약
# ============================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  완료!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  생성된 파일: $SSOT_ROOT\Generated\, $ANIMTOSEQ_DIR\Generated\" -ForegroundColor Gray
Write-Host "  복사된 위치: $UE_PROJECT\" -ForegroundColor Gray
Write-Host "  총 변경사항: $totalChanges 건" -ForegroundColor $(if ($totalChanges -gt 0) { "Yellow" } else { "Green" })
Write-Host ""
Write-Host "  백업 위치: $BACKUP_DIR" -ForegroundColor DarkGray
Write-Host ""

if ($totalChanges -gt 0) {
    exit 1
} else {
    exit 0
}
