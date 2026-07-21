---
name: generate-ssot
description: Downloads에서 최신 엑셀 SSOT를 가져와 SSOT 파일을 생성하고 언리얼 프로젝트에 복사합니다
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

Downloads 폴더에서 최신 엑셀 SSOT를 가져오고, 언리얼용 파일들을 생성한 뒤 프로젝트에 복사합니다.

## 실행 절차

**반드시 PowerShell 스크립트로 실행** (수동 Step 진행 금지):

```bash
powershell.exe -ExecutionPolicy Bypass -File "E:\KAI_VCBT\fa50visualdev_new\.claude\skills\generate-ssot\scripts\generate-and-sync.ps1"
```

스크립트가 자동으로 수행하는 단계 (변경분만 실행):
1. **Downloads에서 최신 엑셀 탐색** → `E:\UECsvDataTableConverter\` 에 복사
   - 패턴: `$HOME\Downloads\250520_FA50M-계층구조_버튼식별_v3.0*.xlsx`
   - 로컬보다 최신이면 교체, 아니면 건너뜀
2. **Pipeline 1-1**: `ue_create_datatable_gameplaytag.py` → DT_ControlData.csv + GameplayTags.ini
   - 트리거: 엑셀 mtime > 출력 mtime
3. **Pipeline 1-2**: `generate_equipment_mapping.py` → equipment_mapping.h
   - 트리거: 엑셀 mtime > 출력 mtime **OR** 스크립트 mtime > 출력 (MANUAL_ENTRIES 변경)
4. **Pipeline 1-3**: `ANIMToSeq/scripts/generate_animid_marker_mapping.py` → DT_AnimIdMarkerMapping.csv
   - 트리거: `vcbt_folder_mapping.json` mtime > 출력 mtime
   - **DB animation 변경은 자동 검출 불가** → `-Force` 사용
5. **파일 복사**: Generated/ → 언리얼 프로젝트
6. **Diff 검증**: 변경사항 출력
7. **UE Editor Reimport**: 에디터 실행 중이면 `DT_ControlData`, `DT_AnimIdMarkerMapping`을 Python Remote Execution으로 자동 reimport (CP/AC 양쪽). 미실행 시 건너뜀.

## 스크립트 옵션

```bash
# 기본 (변경분만 - 입력보다 출력이 오래된 파이프라인만 실행 + 에디터 자동 reimport)
powershell.exe -ExecutionPolicy Bypass -File "...generate-and-sync.ps1"

# 모든 파이프라인 강제 실행 (DB animation 변경 후 등)
powershell.exe -ExecutionPolicy Bypass -File "...generate-and-sync.ps1" -Force

# 생성만 하고 프로젝트 복사 안 함
powershell.exe -ExecutionPolicy Bypass -File "...generate-and-sync.ps1" -SkipCopy

# 자동 Reimport 끄기 (에디터 충돌 회피용)
powershell.exe -ExecutionPolicy Bypass -File "...generate-and-sync.ps1" -SkipReimport
```

**주의**: 엑셀 수정은 사용자가 직접 수행. Claude는 파이프라인 실행만 담당.

## 생성 파일

| 파일 | 설명 | 대상 경로 | 입력 |
|------|------|----------|------|
| `DT_ControlData.csv` | 데이터 테이블 | 프로젝트 루트 | 엑셀 SSOT |
| `FA50M_GameplayTags.ini` | GameplayTag 설정 | `Config/Tags/` | 엑셀 SSOT |
| `equipment_mapping.h` | Host↔Unreal 매핑 | `Source/.../ReceiverUdp100/Types/` | 엑셀 + MANUAL_ENTRIES |
| `DT_AnimIdMarkerMapping.csv` | AnimId↔마커 매핑 | 프로젝트 루트 | `vcbt_folder_mapping.json` + DB |

## 실행 후 확인

스크립트 완료 후 git diff로 변경사항 확인:

```bash
cd E:/KAI_VCBT/fa50visualdev_new && git diff --stat
```

## MANUAL_ENTRIES (CSV 미등록 EquipmentId 보충)

Host가 UDP100으로 전송하지만 엑셀 SSOT/DT_ControlData.csv에 미등록된 EquipmentId를 수동 보충하는 메커니즘.

**위치**: `generate_equipment_mapping.py` → `self.MANUAL_ENTRIES` (SPECIAL_MAPPINGS 아래)

**추가 형식**:
```python
self.MANUAL_ENTRIES = [
    {
        'EquipmentId': 1923,
        'ControlTag': 'EX.ACCESS.2426P3.ACCESS_2426P3_7_INVERTER_CONNECT',
        'Component': 'ACCESS_2426P3_7_INVERTER_CONNECT',
        'NetworkType': 'Int32',
        'Reason': 'Host EquipmentId 1923 (_2426P3_7_), CSV 미등록 ACCESS_PANEL'
    },
]
```

**사용 시나리오**: Host가 EquipmentId=X를 전송하지만 `ProcessEquipmentValues()`에서 매핑을 찾지 못할 때

## EquipmentId 누락 검수 절차

Host가 보내는 EquipmentId가 언리얼에서 처리되지 않을 때 확인 순서:

### 1단계: 존재 여부 확인 (4곳 검색)

| # | 파일 | 검색 | 역할 |
|---|------|------|------|
| 1 | `cockpit_type.h` | `grep {ID}` | Host enum 정의 |
| 2 | `equipment_mapping.h` | `grep {ID}` | 언리얼 매핑 테이블 |
| 3 | `DT_ControlData.csv` | `grep {ID}` | 컨트롤 DataTable |
| 4 | `SPECIAL_MAPPINGS` (generate_equipment_mapping.py) | `grep {ID}` | 특수 매핑 |

### 2단계: Host 측 확인

```bash
# Host GlobalTypes.h에서 enum 이름 확인
grep "= {ID}" E:/KAI_HOST/fa50m-host/host/GlobalTypes.h

# Host에서 어떤 UDP/패널로 매핑되는지 확인
grep "{enum_name}" E:/KAI_HOST/fa50m-host/host/TC/tc_lnk_ext_input.cpp
```

### 3단계: DB 확인

```sql
-- 변수 정의 확인
SELECT iv_id, iv_name, iv_description FROM tbl_input_variable WHERE iv_id = {ID};

-- 어떤 Task에서 사용하는지 확인
SELECT step_task_id, step_no, step_sub_no, step_i_id, step_i_value
FROM tbl_step WHERE step_i_id = {ID};
```

### 4단계: 수정

- **엑셀 SSOT에 추가 가능** → 엑셀 수정 후 `/generate-ssot` 실행
- **엑셀 수정 불가/임시** → `MANUAL_ENTRIES`에 추가 후 파이프라인 2 실행

```bash
# 파이프라인 2만 실행
cd E:/UECsvDataTableConverter/EquipmentMapping && python generate_equipment_mapping.py

# equipment_mapping.h 복사
cp E:/UECsvDataTableConverter/Generated/equipment_mapping.h \
   E:/KAI_VCBT/fa50visualdev_new/Source/FA50VisualDev/Public/HostConnector/ReceiverUdp100/Types/
```

### 5단계: 검증

```bash
# 생성된 파일에서 ID 확인
grep {ID} E:/UECsvDataTableConverter/EquipmentMapping/Output/equipment_mapping.h
```

## 관련 문서

- 지원장비 SSOT 관리: `.claude/docs/support-equipment-ssot.md`
- 엑셀 SSOT 원본: `E:\UECsvDataTableConverter\250520_FA50M-계층구조_버튼식별_v3.0.xlsx`
- 지원장비 추가 스크립트: `E:\UECsvDataTableConverter\add_support_equipment.py`
