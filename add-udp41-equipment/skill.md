---
name: add-udp41-equipment
description: 지원장비 UDP41 파이프라인 전체 자동화 — Host 구조체/복사 로직 + 언리얼 동기화 + 엑셀 + SSOT + descriptor
user-invocable: false
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, AskUserQuestion
---

# 지원장비 UDP41 추가 스킬

지원장비 카테고리를 Host + 언리얼에 한번에 추가합니다.

## 입력

사용자가 다음 중 하나를 제공:
- **카테고리명** + **멤버 prefix** (예: `CAPACITANCE_TESTSET`, `Cts_`)
- **PDF 번호** (예: `#39`)

## 배경: 지원장비 통신 파이프라인

```
언리얼 AC (UDP41 Sender, PNLACT2HST 구조체)
  → Host 수신 (BUF_41)
  → 복사 (FA50MHOSTDlg.cpp): BUF_41.PNLACT2HST.XXX → BUF_51.PNLEQM2HST.Xxx
  → *UDP_51 = BUF_51
  → tc_update_input.cpp: PNLEQM2HST → 시뮬레이션 변수
```

**왜 이런 구조인가:**
- AC PC에서는 UDP41만 활성 (`bIsCockpit=false`). UDP51은 CP PC 전용.
- Host 기존 코드는 `PNLEQM2HST`(UDP51)에서 읽음.
- 해결: UDP41의 `PNLACT2HST`에 멤버 추가 → Host가 `PNLACT2HST → PNLEQM2HST` 복사 → 기존 코드 수정 불필요.

## 실행 절차

### Step 1: SSOT 파싱 — `panel_eqm_to_host_type.h`에서 멤버 읽기

```bash
grep "{prefix}" E:/KAI_HOST/fa50m-host/host/SimTypes/panel_eqm_to_host_type.h
```

이 파일이 **SSOT(단일 진실 원본)**. 여기서 타입과 멤버명을 파싱.

**중요: DT_ControlData에 등록된 멤버만 추가한다.** `panel_eqm_to_host_type.h`에 멤버가 20개 있어도 DT에 8개만 등록됐으면 8개만 추가. (TB_SIMULATOR: eqm 10개 중 5개만 추가한 선례)

```bash
# DT에 등록된 멤버 확인
grep "{CATEGORY}" E:/KAI_VCBT/fa50visualdev_new/DT_ControlData.csv
```

### Step 1.5: DT_ControlData 상태 확인 — 이미 등록되어 있는가?

```bash
grep "SUPPORT_EQUIPMENT.{CATEGORY}" E:/KAI_VCBT/fa50visualdev_new/DT_ControlData.csv
```

- **이미 등록 + PNLACT2HST 정상** → Step 5(엑셀), Step 6(generate-ssot) 스킵
- **미등록** → Step 5~6 수행 필요
- **등록됐지만 PNLACT2HST가 `SUPPORT_EQUIPMENT`** → 엑셀 수정 후 generate-ssot 재실행 필요

### Step 2: Host `panel_act_to_host_type.h` — 구조체 멤버 추가

**경로**: `E:\KAI_HOST\fa50m-host\host\SimTypes\panel_act_to_host_type.h`

- 마지막 블록 아래, `}PNLACT_TO_HST_TYPE;` 위에 추가
- 타입은 `panel_eqm_to_host_type.h`와 동일하게 유지
- `#pragma pack(push, 1)` 적용 중이므로 순서가 중요

**멤버명 변환 규칙:**
- camelCase인 경우 → UPPER_CASE로 변환
- **이미 UPPER_CASE인 경우 → 그대로 사용** (ECS, TEST_ADAPTER 등)

```
panel_eqm_to_host_type.h          panel_act_to_host_type.h
───────────────────────────        ───────────────────────────
int Cts_Ac_Cal_Sw;              → int CTS_AC_CAL_SW;          (camelCase → UPPER)
on_off_type ECS_POWER_ON_OFF_SW → on_off_type ECS_POWER_ON_OFF_SW  (이미 UPPER, 그대로)
```

### Step 3: Host `FA50MHOSTDlg.cpp` — 복사 로직 추가

**경로**: `E:\KAI_HOST\fa50m-host\FA50MHOSTDlg.cpp`
**위치**: 기존 복사 블록 아래, `*UDP_51 = BUF_51;` 위

```cpp
// {CATEGORY_NAME}
BUF_51.PNLEQM2HST.{eqm멤버명} = BUF_41.PNLACT2HST.{act멤버명};
```

좌변(PNLEQM2HST)은 `panel_eqm_to_host_type.h`의 원본 멤버명, 우변(PNLACT2HST)은 Step 2에서 추가한 멤버명. 이미 UPPER_CASE면 좌우 동일.

### Step 4: 언리얼 `panel_act_to_host_type.h` 동기화

```bash
cp "E:/KAI_HOST/fa50m-host/host/SimTypes/panel_act_to_host_type.h" \
   "E:/KAI_VCBT/fa50visualdev_new/Source/FA50VisualDev/Public/HostConnector/SenderUdp41/Types/"
```

Host와 언리얼의 구조체가 **완전 동일**해야 함 (패킷 오프셋).

**주의: 복사 후 include 복원 필수!** Host 원본에는 include가 없지만 언리얼에서는 필요:
```cpp
#pragma pack(push, 1)
#include "HostConnector/ReceiverUdp16/Types/udp_common.h"
#include "HostConnector/SenderUdp51/Types/cockpit_type.h"
```
이 2줄이 없으면 `BUTTON_TYPE`, `Circuit_Breaker_Type` 등 타입을 못 찾아 컴파일 실패.

### Step 5: 엑셀 SSOT 추가

**파일**: Downloads에서 최신 엑셀 (`250520_FA50M-계층구조_버튼식별_v3.0*.xlsx`)
**시트**: `FA50M_PNLACT`

**컬럼 값 규칙:**

| 컬럼 | 위치 | 값 |
|------|------|-----|
| SubPanel | F (6) | 카테고리명 (첫 행만) |
| EquipmentId_Name | I (9) | 컴포넌트명 (끝 `_` 포함) |
| EquipmentId | J (10) | Host GlobalTypes.h의 enum 값 |
| PNLACT2HST | L (12) | `PNLACT2HST.컴포넌트명` (끝 `_` 없이, dot-path) |
| NetworkType | O (15) | `Int32` |
| Type | P (16) | TYPE_MAP 참조 |
| StateValue | Q (17) | TYPE_MAP 참조 |
| DefaultValue | R (18) | TYPE_MAP 참조 |

**PNLACT2HST 컬럼 규칙:**
- Access Panel (`CONNECT_TYPE`): `SUPPORT_EQUIPMENT`
- 대화형 컨트롤: `PNLACT2HST.컴포넌트명` (dot-path, 끝 `_` 없이)

**EquipmentId 찾기:**
```bash
grep "{prefix}" E:/KAI_HOST/fa50m-host/host/GlobalTypes.h
```

**TYPE_MAP** (`cockpit_type.h` 기준):

| Host 타입 | Excel Type | StateValue | DefaultValue |
|----------|------------|------------|-------------|
| BUTTON_TYPE | Momentary Push Button | RELEASE, PRESS | RELEASE |
| on_off_type | Toggle Switch | OFF, ON | OFF |
| int | Variable Knob | 0, 1, 2, 3, 4, 5 | 0 |
| (커스텀 enum) | Rotary Switch | enum 값 나열 | 첫 번째 값 |

새로운 enum 타입은 `cockpit_type.h`에서 확인 후 StateValue 매핑.

### Step 6: `/generate-ssot` 실행

```bash
powershell.exe -ExecutionPolicy Bypass -File "E:\KAI_VCBT\fa50visualdev_new\.claude\skills\generate-ssot\scripts\generate-and-sync.ps1"
```

### Step 7: `generated_descriptors_41.inl` 재생성

```bash
cd E:/UECsvDataTableConverter/Total_processor
python scripts/smart_preprocessor.py
python scripts/generated_inl.py --udp 41
cp generated/generated_descriptors_41.inl \
   "E:/KAI_VCBT/fa50visualdev_new/Source/FA50VisualDev/Public/HostConnector/SenderUdp41/Types/"
```

### Step 8: 검수

모든 파일에서 멤버 개수가 일치하는지 확인:

```bash
# 모두 같은 숫자여야 함
grep "{PREFIX}" E:/KAI_HOST/fa50m-host/host/SimTypes/panel_act_to_host_type.h | wc -l
grep "{PREFIX}" E:/KAI_HOST/fa50m-host/FA50MHOSTDlg.cpp | wc -l
grep "{PREFIX}" E:/KAI_VCBT/fa50visualdev_new/Source/.../SenderUdp41/Types/panel_act_to_host_type.h | wc -l
grep "{CATEGORY}" E:/KAI_VCBT/fa50visualdev_new/DT_ControlData.csv | wc -l
grep "{PREFIX}" E:/KAI_VCBT/fa50visualdev_new/Source/.../SenderUdp41/Types/generated_descriptors_41.inl | wc -l
```

**주의: grep 패턴이 다른 카테고리를 같이 잡을 수 있음** (예: `ECS_` 검색 시 `CMP_ECS_*`도 잡힘). 실제 추가한 멤버만 카운트할 것.

의심스러운 항목만 사용자에게 질문:
- TYPE_MAP에 없는 새 enum 타입
- camelCase ↔ UPPER_CASE 변환 불확실 (이미 UPPER_CASE인 경우 변환 불필요)
- `panel_eqm_to_host_type.h`에 주석 처리된 멤버
- DT에 등록된 멤버와 `panel_eqm` 멤버의 이름이 미묘하게 다른 경우

### Step 9: 사용자에게 요약 보고

```
=== 지원장비 추가 완료: {CATEGORY_NAME} ===
멤버 수: {N}개
Host 구조체: 추가 완료
Host 복사 로직: 추가 완료
언리얼 헤더: 동기화 완료
DT_ControlData: {N}행 추가
UDP41 descriptor: {N}개 생성
DT_EquipmentBP: 등록됨/미등록

남은 작업:
- [ ] DB astd = 1 설정
- [ ] Host 빌드
- [ ] 언리얼 빌드 + DataTable Reimport
- [ ] /sync-ac
```

## 주의사항

- **Host 프로젝트 경로**: `E:\KAI_HOST` (D:\KAI 아님!)
- **끝 `_` 제거**: 엑셀 L열의 PNLACT2HST 값에서 끝 `_` 제거 필수
- **패킷 크기 동기화**: Host/언리얼 구조체 멤버 순서+타입+개수 완전 동일
- **equipment_mapping.h failed 항목**: enum 매핑 실패해도 EquipmentValue int 직접 매핑으로 동작 가능

## 관련 문서

- `.claude/docs/support-equipment-implementation.md` — 전체 절차 + 체크리스트 + 파이프라인 배경
- `.claude/docs/support-equipment-ssot.md` — SSOT 관리, 타입 매핑표, 등록 현황
- `.claude/docs/support-equipment-popup-design.md` — 팝업/Spawn 설계
