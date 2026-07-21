---
name: qa-signal
description: 언리얼 ↔ 호스트 신호 검증 통합 QA. "신호 검증", "왜 판정 안돼?", "UDP 확인" 등의 요청에 사용
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Task
---

# 언리얼 ↔ 호스트 신호 검증 QA

3개의 전문 에이전트를 활용하여 언리얼-호스트 간 신호 흐름을 검증합니다.

## 에이전트 구성

| 에이전트 | 역할 | 프로젝트 |
|----------|------|----------|
| `unreal-agent` | UDP 송수신 로그 분석 | `E:\KAI_VCBT\fa50visualdev_new` |
| `host-agent` | 판정 로직 + 디버그 로그 분석 | `E:\KAI_HOST\fa50m-host` |
| `db-agent` | Step/변수/초기값 조회 | PostgreSQL DB |

## 신호 검증 흐름

```
[언리얼 조종석 입력]
     │
     ├─ UDP61 ─→ [Host UDP 수신]
     │                 │
     │           [판정 로직]
     │                 │
     │           [DB Step 데이터]
     │                 │
     └─ UDP100 ←─ [Host UDP 송신]
           │
    [언리얼 상태 반영]
```

## 검증 시나리오

### 1. 언리얼 → Host 송신 검증
- 언리얼에서 조작한 컨트롤이 Host에 도달하는가?
- IO2HOST 필드 매핑이 올바른가?

### 2. Host 판정 검증
- 입력값이 정답(step_i_value)과 일치하는가?
- 비교 조건(TERM)과 오차(MARGIN)가 적절한가?

### 3. Host → 언리얼 송신 검증
- EquipmentValue가 올바르게 전송되는가?
- 언리얼에서 상태가 정확히 반영되는가?

## 사용 방법

### 기본 사용
```
/qa-signal
```
→ 사용자에게 Task ID, Step 번호, 증상을 질문 후 분석 시작

### 인자 지정
```
/qa-signal 333005 26
```
→ Task 333005의 Step 26 검증

## 검증 절차

### Phase 0: SIGNAL 플래그 사전 검증 (필수!)
1. Step의 i_id를 확인한 뒤, 해당 변수의 `astd` 값을 **반드시** 조회:
```sql
SELECT iv_id, iv_name, astd, fstd FROM tbl_input_variable WHERE iv_id = {I_ID};
```
2. **`astd=0`이면 Host가 이 변수의 변화를 완전히 무시한다** (RECV/JUDGE 로그 없음, 절차 진행 불가)
3. `astd=0`이 원인이면 다른 에이전트 분석 없이 즉시 해결 가능:
```sql
UPDATE tbl_input_variable SET astd = 1 WHERE iv_id = {I_ID};
-- Host 재시작 필수
```
4. 배경: Host는 `_ASTD` 빌드. DB의 `astd` 컬럼이 `PRE_EX_IN[].SIGNAL`로 로드됨. 상세: [db-host-judgment-reference.md §10](../docs/db-host-judgment-reference.md)

### Phase 1: 정보 수집
1. Task ID, Step 번호, 문제 증상 확인
2. DB에서 Step 정보 조회 (i_id, i_value, term)

### Phase 2: 병렬 분석 (3개 에이전트)
```
┌─────────────┬─────────────┬─────────────┐
│ unreal-agent│ host-agent  │ db-agent    │
│             │             │             │
│ UDP 송신    │ UDP 수신    │ Step 정보   │
│ 로그 확인   │ 판정 로직   │ 초기값 확인 │
│             │ 디버그 로그 │             │
└─────────────┴─────────────┴─────────────┘
```

### Phase 3: 결과 종합
1. 각 에이전트 분석 결과 수집
2. 불일치 지점 식별
3. 원인 분석 및 해결책 제시

## 출력 형식

```
## 신호 검증 결과

### 검증 대상
- Task: {task_id} ({task_name})
- Step: {step_no}
- i_id: {i_id} ({변수명})
- 정답: {i_value}

### 언리얼 분석 (unreal-agent)
- UDP 송신: {정상/오류}
- 송신 값: {value}
- 로그: {관련 로그}

### 호스트 분석 (host-agent)
- UDP 수신: {정상/오류}
- 판정 로직: {정상/오류}
- 디버그 로그: {관련 로그}

### DB 분석 (db-agent)
- Step 정보: i_id={id}, i_value={value}, term={term}
- 초기값: {init_value}
- 절차: {ms_action}

### 불일치 지점
- {위치}: {상세 설명}

### 원인
- {원인 분석}

### 해결책
1. {해결 방법 1}
2. {해결 방법 2}
```

## 일반적인 문제 유형

### 1. 언리얼 송신 오류
- IO2HOST 매핑 누락
- generated_descriptors_*.inl 미갱신
- NEnum 타입 처리 오류
- **타입 불일치 (Int32 vs Int32_as_Bool)** ← 아래 상세 설명

### 2. Host 수신 오류
- dt_cpt_recv_data.cpp 변환 로직 누락
- tc_lnk_ext_input.cpp EX_IN 연결 누락

### 3. 판정 오류
- PREV_DATA 미업데이트 (DISCRETE_TYPE 버그)
- Term/Margin 불일치
- Step 데이터 오류

### 4. 초기값 오류
- tbl_input_variable_initialize 누락
- 초기값 덮어쓰기 순서 문제

### 5. SIGNAL 플래그 누락 (astd=0)
- **증상**: UDP 전송 정상, Host RECV/JUDGE 로그 0건, EX_IN 값 불변
- **원인**: `tbl_input_variable.astd=0` → Host가 변수 변화를 완전히 무시
- **빈발**: 새 지원장비 변수 추가 시 `fstd=1`만 넣고 `astd=1` 누락
- **진단**: `SELECT astd FROM tbl_input_variable WHERE iv_id = {I_ID};`
- **수정**: `UPDATE tbl_input_variable SET astd = 1 WHERE iv_id = {I_ID};` + Host 재시작

---

## 타입 불일치 문제 (Int32 vs Int32_as_Bool)

### 증상
- 언리얼 로그: `ON state, sending int: 0` (ON인데 0을 보냄)
- Host: 버튼 상태(DEPRESS=1/RELEASE=0) 기대, 수신값 역전

### 원인
`generated_descriptors_*.inl`에서 타입이 `Int32`로 지정되면:
- `GetValueAsInt32()` 호출 → StateValue 배열 인덱스 반환
- StateValue: ("ON", "OFF") → ON=0, OFF=1 (역전!)

`Int32_as_Bool`로 지정하면:
- `GetValueAsBool()` 호출 → "ON"/"UP" 이름이면 true(1) 반환
- ON=1, OFF=0 (정상)

### 확인 방법
```bash
# UDP61 로그에서 값 확인
grep "Mode_Button" FA50VisualDev.log | tail -10
# "int: 0" 이면서 ON 상태면 타입 문제
```

### 해결 방법
`E:\UECsvDataTableConverter\Total_processor\scripts\generated_inl.py`의 `TYPE_OVERRIDES`에 추가:

```python
TYPE_OVERRIDES = {
    # 버튼 타입인데 ON/OFF StateValue 사용하는 경우
    "SI2HST.toEfi.EMASI.Mode_Button": "EUnifiedMemberType::Int32_as_Bool",
    "SI2HST.toEfi.EAI.Mode_Button": "EUnifiedMemberType::Int32_as_Bool",
    # ... 추가 필드
}
```

재생성 및 적용:
```bash
E:\UECsvDataTableConverter\Total_processor\bin\generate_inl.bat
# 복사
copy generated_descriptors_61.inl → Source/.../SenderUdp61/Types/
/sync-ac  # 빌드 + 동기화
```

### 판별 기준
| 컨트롤 타입 | StateValue | 권장 타입 |
|-------------|------------|-----------|
| MOMENTARY_PUSH_BUTTON | ON/OFF | Int32_as_Bool |
| MOMENTARY_OPTION_BUTTON | 다중 상태 | Int32 |
| TOGGLE_SWITCH | ON/OFF | Int32_as_Bool |
| ROTARY_SWITCH | 다중 상태 | Int32 |

---

## DB 변수 조회 방법

### I_ID vs O_ID

| 구분 | 설명 | 테이블 | 방향 |
|------|------|--------|------|
| **I_ID** (Input) | 언리얼 → Host 입력 변수 | `tbl_input_variable` | 조종석 조작 |
| **O_ID** (Output) | Host → 언리얼 출력 변수 | `tbl_output_variable` | 시뮬레이션 결과 |

### Step에서 I_ID / O_ID 조회

```bash
# Step의 입력(I_ID)과 출력(O_ID) 조회
PGPASSWORD=kai psql -h 192.168.11.201 -p 5432 -U kai -d FA_50_KAI -c \
"SELECT step_no, step_sub_no, step_i_id, step_i_value, step_o_id, step_o_value
 FROM tbl_step
 WHERE step_task_id = {TASK_ID} AND step_no = {STEP_NO}
 ORDER BY step_sub_no;"
```

### 변수명으로 ID 찾기

```bash
# 입력 변수 (I_ID) 검색
PGPASSWORD=kai psql -h 192.168.11.201 -p 5432 -U kai -d FA_50_KAI -c \
"SELECT iv_id, iv_name, iv_type FROM tbl_input_variable WHERE iv_name ILIKE '%키워드%';"

# 출력 변수 (O_ID) 검색
PGPASSWORD=kai psql -h 192.168.11.201 -p 5432 -U kai -d FA_50_KAI -c \
"SELECT ov_id, ov_name FROM tbl_output_variable WHERE ov_name ILIKE '%키워드%';"
```

### O_ID 사용하는 Step 찾기

```bash
# 특정 O_ID를 사용하는 모든 Step 조회
PGPASSWORD=kai psql -h 192.168.11.201 -p 5432 -U kai -d FA_50_KAI -c \
"SELECT step_no, step_sub_no, step_i_id, step_i_value, step_o_id, step_o_value
 FROM tbl_step
 WHERE step_task_id = {TASK_ID} AND step_o_id = {O_ID}
 ORDER BY step_no, step_sub_no;"
```

---

## Host 내부 타이머 제한

### 사례: EGI_Select_Mode (O_ID 133)

**증상**: `EGI_Select_Mode`가 5가 되어야 하는데 1~4까지만 가능

**원인**: Host 내부 타이머 기반 제한 (`iufc_draw_egi_page.cpp`)

```cpp
if (iufcL_mtd.EGI_Page_Mode == 1)
{
    if (iufcL_mtd.EGI_Timer_Cnt < 1962)
    {
        // 타이머 1962 미만: EGI_Select_Mode 1~4만 가능
        if (iufcL_mtd.EGI_Select_Mode >= 5)
            iufcL_mtd.EGI_Select_Mode = 1;  // 5가 되면 1로 리셋
    }
    else
    {
        // 타이머 1962 이상: EGI_Select_Mode 1~5 가능
        if (iufcL_mtd.EGI_Select_Mode >= 6)
            iufcL_mtd.EGI_Select_Mode = 1;
    }
}
```

| 조건 | EGI_Select_Mode 범위 |
|------|---------------------|
| `EGI_Timer_Cnt < 1962` | 1~4만 가능 |
| `EGI_Timer_Cnt >= 1962` | 1~5 가능 |

**1962 ≈ 196.2초 (약 3분 16초)**

**해결**: EGI 페이지에서 타이머가 충분히 경과할 때까지 대기 후 Step 진행

### Host 출력 변수 로직 위치

출력 변수(O_ID)의 값은 Host 내부 로직에서 계산됨:

| 파일 | 역할 |
|------|------|
| `tc_update_ex_out.cpp` | EX_OUT[] 배열에 출력 변수 매핑 |
| `Sim/avionics/IUFC/*.cpp` | IUFC 관련 출력 변수 계산 |
| `Sim/avionics/EFI/*.cpp` | EFI 관련 출력 변수 계산 |

```bash
# 출력 변수명으로 Host 로직 찾기
grep -r -n "변수명" "E:\KAI_HOST\fa50m-host" --include="*.cpp" --include="*.h"
```

---

## 참고 문서

- `docs/udp-descriptor-guide.md`: UDP Descriptor 가이드
- `HOST_LOGGING_SSOT.md`: **Host 상시 로깅 SSOT** (로그 삽입 위치/포맷 정의)
- `E:\KAI_HOST\iostestapp\docs\QA_Host_Debug_Log_Guide.md`: 호스트 디버그 로그 가이드 (수동 디버깅용)

## Host 로그 기반 분석

Host의 DebugLog 시스템이 `E:\KAI_HOST\fa50m-host\log\host_debug_*.log`에 기록:

```
[HOST][RECV]    → 언리얼에서 Host로 수신된 값 (입력 변화 감지)
[HOST][JUDGE]   → 판정 결과 (PASS/WRONG)
[HOST][UDP100]  → Host에서 언리얼로 송신 (EquipmentId, answer, TaskID)
[HOST][STEP]    → Step 전환 (STEP_IDX 변화)
[HOST][AUTORUN] → AutoRun 상태 변화
[HOST][SYNC]    → 동기화 상태
```

### DebugLog 코드 위치
| 파일 | 역할 |
|------|------|
| `E:\KAI_HOST\fa50m-host\host\DebugLog.h` | 함수 선언 |
| `E:\KAI_HOST\fa50m-host\host\DebugLog.cpp` | 함수 구현 (파일+TRACE 출력) |

### 주요 패턴
```
# 정상 흐름
[HOST][RECV]    ID=264: 0 -> 1 (DISCRETE)
[HOST][JUDGE]   STEP=3, I_ID=264: Cur=1, Exp=1, Term=0, PASS
[HOST][STEP]    STEP_IDX=72->73, STEP_NO=3
[HOST][UDP100]  EquipmentId=265, answer=0, TaskID=329006, MTD_MODE=RUN

# AutoRun SKIP (문제!)
[HOST][JUDGE]   STEP=7, I_ID=1136: Cur=0, Exp=0, Term=0, PASS  ← SKIP으로 자동 PASS
                                                                  ← [RECV] 로그 없음
```
