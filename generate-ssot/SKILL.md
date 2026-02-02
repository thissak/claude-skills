---
name: generate-ssot
description: SSOT 스크립트 실행 후 언리얼 프로젝트에 복사하고 변경사항을 diff로 검증합니다
triggers:
  - generate-ssot
  - ssot 생성
  - datatable 생성
  - mapping 생성
args:
  - name: skip-copy
    description: 생성만 하고 복사하지 않음
    required: false
    default: "false"
---

# Generate SSOT (Single Source of Truth)

엑셀 SSOT에서 언리얼용 파일들을 생성하고, 프로젝트에 복사한 뒤 변경사항을 검증합니다.

## 생성 파일

| 파일 | 설명 | 대상 경로 |
|------|------|----------|
| `DT_ControlData.csv` | 데이터 테이블 | 프로젝트 루트 |
| `FA50M_GameplayTags.ini` | GameplayTag 설정 | `Config/Tags/` |
| `equipment_mapping.h` | Host↔Unreal 매핑 | `Source/.../Types/` |

## 실행 단계

### Step 1: SSOT 스크립트 실행

```bash
cd "E:/UECsvDataTableConverter"
conda activate processtree && python ue_create_datatable_gameplaytag.py
```

```bash
cd "E:/UECsvDataTableConverter/EquipmentMapping"
python generate_equipment_mapping.py
```

### Step 2: 기존 파일 백업 및 Diff 준비

복사 전 기존 파일들을 임시 저장하여 비교 준비

### Step 3: 파일 복사

```powershell
# DT_ControlData.csv
Copy-Item "E:\UECsvDataTableConverter\Generated\DT_ControlData.csv" "E:\KAI_VCBT\fa50visualdev_new\DT_ControlData.csv"

# FA50M_GameplayTags.ini
Copy-Item "E:\UECsvDataTableConverter\Generated\FA50M_GameplayTags.ini" "E:\KAI_VCBT\fa50visualdev_new\Config\Tags\FA50M_GameplayTags.ini"

# equipment_mapping.h
Copy-Item "E:\UECsvDataTableConverter\Generated\equipment_mapping.h" "E:\KAI_VCBT\fa50visualdev_new\Source\FA50VisualDev\Public\HostConnector\ReceiverUdp100\Types\equipment_mapping.h"
```

### Step 4: Diff 검증

각 파일의 변경사항을 diff로 확인하여 사용자에게 보고

## 참고

- 상세 경로: `references/paths.md`
- 스크립트: `scripts/generate-and-sync.ps1`
