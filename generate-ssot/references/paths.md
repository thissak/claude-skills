# 경로 레퍼런스

## 엑셀 SSOT (Teams → Downloads → 로컬)

| 단계 | 경로 |
|------|------|
| Teams 원본 | Teams 공유 폴더 (브라우저에서 다운로드) |
| Downloads | `$HOME\Downloads\250520_FA50M-계층구조_버튼식별_v3.0*.xlsx` |
| 로컬 SSOT | `E:\UECsvDataTableConverter\250520_FA50M-계층구조_버튼식별_v3.0.xlsx` |

## SSOT 소스 (UECsvDataTableConverter)

| 파일 | 경로 |
|------|------|
| 엑셀 SSOT | `E:\UECsvDataTableConverter\250520_FA50M-계층구조_버튼식별_v3.0.xlsx` |
| DataTable 스크립트 | `E:\UECsvDataTableConverter\ue_create_datatable_gameplaytag.py` |
| Mapping 스크립트 | `E:\UECsvDataTableConverter\EquipmentMapping\generate_equipment_mapping.py` |

## 생성 파일 (Generated)

| 파일 | 경로 |
|------|------|
| DT_ControlData.csv | `E:\UECsvDataTableConverter\Generated\DT_ControlData.csv` |
| FA50M_GameplayTags.ini | `E:\UECsvDataTableConverter\Generated\FA50M_GameplayTags.ini` |
| equipment_mapping.h | `E:\UECsvDataTableConverter\Generated\equipment_mapping.h` |

## 언리얼 프로젝트 대상 경로

| 파일 | 대상 경로 |
|------|----------|
| DT_ControlData.csv | `E:\KAI_VCBT\fa50visualdev_new\DT_ControlData.csv` |
| FA50M_GameplayTags.ini | `E:\KAI_VCBT\fa50visualdev_new\Config\Tags\FA50M_GameplayTags.ini` |
| equipment_mapping.h | `E:\KAI_VCBT\fa50visualdev_new\Source\FA50VisualDev\Public\HostConnector\ReceiverUdp100\Types\equipment_mapping.h` |

## Conda 환경

```bash
conda activate processtree
```

## 실행 방법 (PowerShell 사용)

```powershell
# 전체 실행 (Downloads 엑셀 복사 + 생성 + 언리얼 복사 + diff)
powershell.exe -ExecutionPolicy Bypass -File ".claude/skills/generate-ssot/scripts/generate-and-sync.ps1"

# 엑셀 복사 건너뛰기 (로컬 엑셀 그대로 사용)
powershell.exe -ExecutionPolicy Bypass -File ".claude/skills/generate-ssot/scripts/generate-and-sync.ps1" -SkipExcel

# 개별 실행 (PowerShell에서)
cd E:\UECsvDataTableConverter; conda activate processtree; python ue_create_datatable_gameplaytag.py
cd E:\UECsvDataTableConverter\EquipmentMapping; python generate_equipment_mapping.py
```
