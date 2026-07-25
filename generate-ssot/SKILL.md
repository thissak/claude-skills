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
   - 트리거: 엑셀 mtime > 출력 mtime **OR** 스크립트 mtime > 출력 (`SPECIAL_MAPPINGS`/`MANUAL_ENTRIES` 변경)
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
| `equipment_mapping.h` | Host↔Unreal 매핑 | `Source/.../ReceiverUdp100/Types/` | 엑셀 + `SPECIAL_MAPPINGS` + `MANUAL_ENTRIES` |
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

## enum 순서 불일치 검수

`equipment_mapping.h`의 enum 타입과 값 순서는 상태 이름 유사도만으로 확정하지 않습니다. 생성기 `_find_enum_type()`은 `StateValue` 이름 점수를 실제 Host 구조체 필드 타입보다 먼저 사용할 수 있으므로, 이름은 비슷하지만 정수 순서가 다른 enum을 선택할 수 있습니다.

다음 증상이면 `UNREAL_EQUIPMENT_MAPPING_ENUM_DRIFT`로 조사합니다.

- UDP100 초기화 뒤 Unreal 물리 위치가 DB 초기값의 실제 의미와 다름
- AutomationDriver `CAPS target_index`가 Host enum 의미와 다름
- 현재 상태와 목표가 같다는 `NO_PHYSICAL_EDGE`가 실제 패널 의미와 맞지 않음

검수 순서는 다음과 같습니다.

1. DB `tbl_input_variable.iv_data_type`과 공통·Task별 초기값을 확인합니다.
2. Host `cockpit_to_host_type.h`의 실제 필드 선언과 `cockpit_type.h` enum 정수값을 확인합니다.
3. Host UDP 수신 대입과 `tc_lnk_ext_input.cpp`의 `EX_IN` 링크를 확인합니다.
4. `DT_ControlData.csv`의 `StateValue` 인덱스 순서와 생성된 Host→State index 표를 대조합니다.
5. 타입 또는 순서가 다르면 생성된 `equipment_mapping.h`를 직접 편집하지 않고 `generate_equipment_mapping.py`의 `SPECIAL_MAPPINGS`에 EquipmentId·Component별 명시 매핑을 추가합니다.
6. 정식 `generate-and-sync.ps1` 파이프라인으로 재생성하고 diff와 실제 UDP100/CAPS를 회귀합니다.

### StateValue 순서 변경 금지 게이트

`CAPS target_index`가 틀렸다는 이유만으로 Excel `StateValue`를 재배치하지 않습니다. `StateValue`는 Unreal 상태 인덱스이고 Host 숫자 의미는 방향별 명시 맵이 결정하므로, 다음 자료를 모두 확인하기 전에는 Excel 수정 프롬프트를 작성하지 않습니다.

1. DB Step의 `I_VAL`, `IoDataType`, 현재 STD의 SIGNAL과 초기값
2. Unreal→Host 송신 descriptor와 `udp51_send_map.h`의 `StateToHostMapping`
3. Host UDP 필드→`EX_IN` 링크와 `Cur/Exp` 직접 판정 로그
4. Host→Unreal `equipment_mapping.h`의 `HostToStateMapping`
5. 명시 수신맵에 없는 raw 값이 `StateValue[raw]`로 떨어지는 fallback 여부

송신과 Host 판정이 정상이고 수신맵에만 상태가 빠졌다면 Excel 순서를 바꾸지 않고 `SPECIAL_MAPPINGS.direct_mapping`에 누락된 Host→State index를 추가합니다.

2026-07-25 기준 사례:

```text
ID 214 DN_LOCK_REL
StateValue=("HOLD","ON","OFF")
DB/UDP51/Host: OFF=0, ON=1, HOLD=2
기존 수신맵: {0:2, 1:1}          # raw 2가 index fallback으로 OFF가 됨
정정 수신맵: {0:2, 1:1, 2:0}     # raw 2→HOLD
```

이 사례에서 Excel을 `("OFF","ON","HOLD")`로 재배치하자는 초기 제안은 송신 이름맵을 확인하지 않은 오진이었다. 같은 증상에서는 위 대조 순서를 먼저 수행합니다.

2026-07-22 확인 사례:

```text
ID 259 SEL_IFF:     실제 ANTENNA_TYPE -> {0:0, 1:1, 2:2}
ID 260 SEL_UHF_VHF: 실제 ANTENNA_TYPE -> {0:2, 1:1, 2:0}
```

매핑 수정 뒤에도 DB 초기 상태와 첫 요구 목표가 같으면 그것은 생성 결함이 아니라 별도의 절차 edge 문제입니다. 합성 re-arm으로 통과시키지 않습니다.

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
