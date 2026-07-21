# 신호 검증 로깅 SSOT

Host/언리얼 코드가 변경될 때마다 이 문서를 참조하여 로깅 코드를 적용합니다.

---

# Part 1: 언리얼 로깅

## 로그 제어 (Console Variable)

25Hz UDP로 인한 로그 폭발 방지를 위해 **특정 EquipmentId만** 로그 출력:

```
// 언리얼 콘솔에서 실행
QA.WatchEquipId 35      // EquipmentId 35만 로그 출력
QA.WatchEquipId -1      // 모든 QA 로그 끔 (기본값)
```

| CVar 값 | 동작 |
|---------|------|
| `-1` (기본) | 모든 QA 로그 끔 |
| `0` 이상 | 해당 EquipmentId의 `[RECV]` 로그만 출력, `[SEND]`/`[STATE]`는 끔 |

## 로그 카테고리

언리얼은 `UE_LOG(LogTemp, Log, ...)` 사용. Output Log에서 확인.

## 로그 삽입 위치 (3곳)

### 1. 수신 로그 [RECV] - Host → 언리얼

**파일:** `UDP100MediatorSubsystem.cpp`

**위치:** `ProcessSingleEquipment` 함수 - NewState 변환 후 (ParseRawValueToControlState 호출 후)

```cpp
// 4. 헬퍼 함수로 변환
FControlStateValue NewState = ParseRawValueToControlState(...);

// QA 상시 로깅 - Host 값과 언리얼 해석값 비교 (변경 시에만)
{
    static TMap<int32, int32> PrevHostValues;
    const int32* PrevValue = PrevHostValues.Find(EquipmentId);
    if (!PrevValue || *PrevValue != HostValue)
    {
        UE_LOG(LogTemp, Log, TEXT("[RECV] EquipId=%d, HostValue=%d -> State=%s, Tag=%s"),
            EquipmentId, HostValue, *NewState.ToString(), *Mapping.ControlTag.ToString());
        PrevHostValues.Add(EquipmentId, HostValue);
    }
}
```

**핵심:** `HostValue=%d -> State=%s` 형식으로 매핑 결과를 함께 로그하여 매핑 오류 감지

### 2. 송신 로그 [SEND] - 언리얼 → Host

**파일:** `UDPSenderMediatorSubsystemBase.cpp`

**위치:** `OnControlStateChangedHandler` 함수 (약 84행)

```cpp
void UUDPSenderMediatorSubsystemBase::OnControlStateChangedHandler(
    const FGameplayTag& ControlTag,
    const FControlStateValue& OldState,
    const FControlStateValue& NewState)
{
    const FControlData* ControlData = DataManager->GetCachedControlData(ControlTag);

    if (ControlData)
    {
        // QA 상시 로깅 - Host로 송신
        UE_LOG(LogTemp, Log, TEXT("[SEND] Tag=%s, IO2HOST=%s, State=%s"),
            *ControlTag.ToString(),
            *ControlData->IO2HOST.ToString(),
            *NewState.ToString());

        ProcessControlStateChange(ControlTag, *ControlData, NewState);
    }
}
```

### 3. 상태 변경 로그 [STATE]

**파일:** `ControlRegisterSubsystem.cpp`

**위치:** `BroadcastControlStateChange` 함수 (약 437행) - 이미 로그 있음, 포맷만 통일

```cpp
void UControlRegisterSubsystem::BroadcastControlStateChange(
    const FGameplayTag& ControlTag,
    const FControlStateValue& OldState,
    const FControlStateValue& NewState)
{
    // QA 상시 로깅 - 상태 변경
    UE_LOG(LogTemp, Log, TEXT("[STATE] %s: %s -> %s"),
        *ControlTag.ToString(),
        *OldState.ToString(),
        *NewState.ToString());

    OnControlStateChanged.Broadcast(ControlTag, OldState, NewState);
}
```

## 언리얼 로그 포맷

| 태그 | 의미 | 주요 필드 |
|------|------|----------|
| `[RECV]` | Host→언리얼 수신 | EquipId, HostValue |
| `[SEND]` | 언리얼→Host 송신 | Tag, IO2HOST, State |
| `[STATE]` | 상태 변경 | Tag, OldState→NewState |

## 예상 로그 흐름 (언리얼)

```
[STATE] FORWARD_COCKPIT.LEFT_CONSOLE.EXT_LIGHTS.LANDING_TAXI: OFF -> TAXI
[SEND] Tag=FORWARD_COCKPIT.LEFT_CONSOLE.EXT_LIGHTS.LANDING_TAXI, IO2HOST=Landing_Taxi_Light_Switch, State=TAXI
...
[RECV] EquipId=35, HostValue=2
[STATE] FORWARD_COCKPIT.LEFT_CONSOLE.EXT_LIGHTS.LANDING_TAXI: TAXI -> LANDING
```

---

# Part 2: Host 로깅

## 목적

- 신호 흐름 전체를 `debug_qa.log` 한 파일에 기록
- 값이 **변경될 때만** 출력하여 성능 영향 최소화
- host-agent가 로그만 분석하면 즉시 디버깅 가능

## 로그 파일 위치

```
E:\KAI_HOST\debug_qa.log
```

## 로그 함수 (GlobalData.h)

이미 존재하는 `DebugLogQA` 함수 사용:

```cpp
// host/GlobalData.h 끝부분
inline void DebugLogQA(const char* format, ...) {
    static FILE* fp = nullptr;
    static bool firstCall = true;
    if (firstCall) {
        fp = fopen("E:\\KAI_HOST\\debug_qa.log", "w");
        firstCall = false;
        if (fp) {
            SYSTEMTIME st;
            GetLocalTime(&st);
            fprintf(fp, "=== Debug Log Started: %04d-%02d-%02d %02d:%02d:%02d ===\n",
                st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
            fflush(fp);
        }
    }
    if (fp) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(fp, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
        va_list args;
        va_start(args, format);
        vfprintf(fp, format, args);
        va_end(args);
        fflush(fp);
    }
}
```

---

## 로그 삽입 위치 (3곳)

### 1. 수신 로그 [RECV]

**파일:** `host/TC/tc_find_trainee_input.cpp`

**위치:** `INPUT_CHANGE == TRUE` 블록 내부 (약 94-101행)

```cpp
/* IF any external input is changed THEN */
if (INPUT_CHANGE == TRUE)
{
    /* SET the Changed Input to the external input. (ID, Previous Value, New Value) */
    CHNG_INPUT.ID        = i - 1;
    CHNG_INPUT.PREV_DATA = EX_IN[i - 1].PREV_DATA;
    CHNG_INPUT.NEW_DATA  = NEW_DATA;

    // ===== QA 상시 로깅 =====
    DebugLogQA("[RECV] STEP=%d, I_ID=%d: %d -> %d (TYPE=%d)\n",
        CURNT_STEP_NO, CHNG_INPUT.ID, CHNG_INPUT.PREV_DATA, CHNG_INPUT.NEW_DATA, EX_IN[i-1].TYPE);

} /* END IF */
```

**출력 예시:**
```
[09:15:32.123] [RECV] STEP=26, I_ID=264: 0 -> 1 (TYPE=1)
```

---

### 2. 판정 로그 [JUDGE]

**파일:** `host/TC/tc_chk_trainee_input.cpp`

**위치:** 판정 결과가 결정되는 시점 (CHK_RESULT 설정 후)

```cpp
// 판정 완료 후 로그 (값 변경 시에만 출력)
{
    static int prevStepNo = -1;
    static int prevResult = -1;
    if (CURNT_STEP_NO != prevStepNo || CHK_RESULT != prevResult) {
        DebugLogQA("[JUDGE] STEP=%d, I_ID=%d: Cur=%d, Exp=%d, Term=%d, %s\n",
            CURNT_STEP_NO,
            STEP_DATA[STEP_IDX].I_ID,
            *EX_IN[STEP_DATA[STEP_IDX].I_ID].DATA,
            STEP_DATA[STEP_IDX].I_VAL,
            STEP_DATA[STEP_IDX].TERM,
            CHK_RESULT ? "PASS" : "FAIL");
        prevStepNo = CURNT_STEP_NO;
        prevResult = CHK_RESULT;
    }
}
```

**출력 예시:**
```
[09:15:32.125] [JUDGE] STEP=26, I_ID=264: Cur=1, Exp=1, Term=1, PASS
```

---

### 3. 송신 로그 [SEND]

**파일:** `host/DT/dt_udp100_send_data.cpp`

**위치:** 함수 끝부분 (UDP_100 데이터 설정 후)

```cpp
// ===== QA 상시 로깅 (변경 시에만) =====
{
    static int prevStepNo = -1;
    static int prevEquipId = -1;
    static int prevEquipSet = -1;

    if (CURNT_STEP_NO != prevStepNo ||
        UDP_100->EquipmentId != prevEquipId ||
        (int)UDP_100->EquipmentSet != prevEquipSet) {

        DebugLogQA("[SEND] STEP=%d, EquipId=%d, EquipSet=%d, ErrCnt=%d\n",
            CURNT_STEP_NO,
            UDP_100->EquipmentId,
            (int)UDP_100->EquipmentSet,
            UDP_100->errCount);

        prevStepNo = CURNT_STEP_NO;
        prevEquipId = UDP_100->EquipmentId;
        prevEquipSet = (int)UDP_100->EquipmentSet;
    }
}
```

**출력 예시:**
```
[09:15:32.127] [SEND] STEP=26, EquipId=264, EquipSet=0, ErrCnt=0
```

---

## Step 전환 로그 [STEP] (선택)

**파일:** `host/TC/tc_cntl_norm_step.cpp`

**위치:** Step 완료 및 전환 시점

```cpp
// Step 전환 로그
DebugLogQA("[STEP] === STEP %d COMPLETED === Next: STEP %d, I_ID=%d\n",
    CURNT_STEP_NO,
    CURNT_STEP_NO + 1,
    STEP_DATA[STEP_IDX + 1].I_ID);
```

---

## 로그 포맷 표준

| 태그 | 의미 | 주요 필드 |
|------|------|----------|
| `[RECV]` | 언리얼→Host 수신 | STEP, I_ID, 이전값→새값, TYPE |
| `[JUDGE]` | 판정 결과 | STEP, I_ID, 현재값, 기대값, Term, PASS/FAIL |
| `[SEND]` | Host→언리얼 송신 | STEP, EquipId, EquipSet, ErrCnt |
| `[STEP]` | Step 전환 | 완료 Step, 다음 Step, 다음 I_ID |

---

## 예상 로그 흐름

```
=== Debug Log Started: 2025-01-15 09:15:30 ===
[09:15:32.123] [RECV] STEP=26, I_ID=264: 0 -> 1 (TYPE=1)
[09:15:32.125] [JUDGE] STEP=26, I_ID=264: Cur=1, Exp=1, Term=1, PASS
[09:15:32.127] [SEND] STEP=26, EquipId=264, EquipSet=0, ErrCnt=0
[09:15:32.130] [STEP] === STEP 26 COMPLETED === Next: STEP 27, I_ID=265
[09:15:35.456] [RECV] STEP=27, I_ID=265: 0 -> 2 (TYPE=0)
[09:15:35.458] [JUDGE] STEP=27, I_ID=265: Cur=2, Exp=1, Term=1, FAIL
```

---

## 문제 유형별 로그 패턴

### 1. 수신은 되는데 판정 실패
```
[RECV] STEP=26, I_ID=264: 0 -> 1    ← 수신 OK
[JUDGE] STEP=26, I_ID=264: Cur=1, Exp=2, FAIL   ← 기대값 불일치
```
→ DB의 i_value 확인 필요

### 2. 수신 자체가 안됨
```
[JUDGE] STEP=26, I_ID=264: Cur=0, Exp=1, FAIL   ← RECV 로그 없음
```
→ 언리얼 UDP 송신 확인 필요

### 3. Step이 넘어가지 않음
```
[RECV] STEP=26, I_ID=264: 0 -> 1
[JUDGE] STEP=26, I_ID=264: Cur=1, Exp=1, PASS   ← 판정 OK
                                                 ← [STEP] 로그 없음
```
→ tc_cntl_norm_step.cpp 로직 확인 필요

### 4. SIGNAL=0으로 입력 변화 무시 (RECV/JUDGE 모두 없음)
```
[SEND] STEP=20, EquipId=-1, EquipSet=0, ErrCnt=0
[SEND] STEP=20, EquipId=224, EquipSet=0, ErrCnt=0   ← RUN_MODE 진입, 판정 대상 설정
                                                      ← [RECV] 없음, [JUDGE] 없음
```
→ `[SEND]`만 있고 `[RECV]`/`[JUDGE]`가 전혀 없으면 **SIGNAL=0** 의심

**실제 사례 (Task 321003 Step 20, i_id=224 DFOG_Lever_Angle_):**

디버그 로그 추가로 확인:
```
[DEBUG] EX_IN[224]: SIGNAL=0, SKIP=0, TYPE=1, PREV_DATA=0, CUR_DATA=0, DATA_PTR=valid
[DEBUG] EX_IN[224]: SIGNAL=0, SKIP=0, TYPE=1, PREV_DATA=0, CUR_DATA=100, DATA_PTR=valid
```
- DATA_PTR=valid, CUR_DATA=0→100 (레버 조작 정상 도착)
- **SIGNAL=0** → `PRE_EX_IN[i].SIGNAL == FALSE` → 변화 감지 로직 자체를 건너뜀

**원인:** DB `tbl_input_variable`의 `astd` 컬럼이 0
- Host가 `_ASTD` 빌드 → `PRE_EX_IN[ID].SIGNAL = db_get_table_data(K_ASTD_SIGNAL)` → 0

**STD 타입별 SIGNAL 컬럼:**

| 빌드 플래그 | DB 컬럼 | 시뮬레이터 타입 |
|------------|---------|----------------|
| `_ASTD` | `astd` | Avionics System Training Device |
| `_PHSTD` | `phstd` | Procedure Hands-on TD |
| `_FSTD` | `fstd` | Full-Scope TD |
| `_EESTD` | `eestd` | EE System TD |
| `_COSTD` | `cstd` | Cockpit System TD |

**해결:** `UPDATE tbl_input_variable SET astd = 1 WHERE iv_id = 224;` → Host 재시작

**디버깅 방법:** `tc_find_trainee_input.cpp`에 아래 디버그 로그 추가:
```cpp
if (i == {TARGET_I_ID}) {
    static int prev = -9999;
    static bool first = true;
    int cur = (EX_IN[i].DATA != NULL) ? *EX_IN[i].DATA : -9999;
    if (first || cur != prev) {
        DebugLogQA("[DEBUG] EX_IN[%d]: SIGNAL=%d, SKIP=%d, TYPE=%d, PREV_DATA=%d, CUR_DATA=%d, DATA_PTR=%s\n",
            i, PRE_EX_IN[i].SIGNAL, EX_IN[i].SKIP, EX_IN[i].TYPE,
            EX_IN[i].PREV_DATA, cur, (EX_IN[i].DATA != NULL) ? "valid" : "NULL");
        prev = cur;
        first = false;
    }
}
```

---

## 적용 체크리스트

Host 코드 변경 후 아래 체크:

- [ ] `GlobalData.h`에 `DebugLogQA` 함수 존재 확인
- [ ] `tc_find_trainee_input.cpp`에 `[RECV]` 로그 추가
- [ ] `tc_chk_trainee_input.cpp`에 `[JUDGE]` 로그 추가
- [ ] `dt_udp100_send_data.cpp`에 `[SEND]` 로그 추가
- [ ] (선택) `tc_cntl_norm_step.cpp`에 `[STEP]` 로그 추가
- [ ] Host 빌드 후 `debug_qa.log` 생성 확인

---

## host-agent 연동

host-agent는 이 로그를 분석할 때:

1. `E:\KAI_HOST\debug_qa.log` 파일 읽기
2. `[RECV]`, `[JUDGE]`, `[SEND]`, `[STEP]` 태그로 필터링
3. 특정 Step, I_ID 기준으로 흐름 추적
4. 불일치 지점 식별

```bash
# 특정 Step 로그만 추출
grep "STEP=26" E:\KAI_HOST\debug_qa.log

# 특정 I_ID 로그만 추출
grep "I_ID=264" E:\KAI_HOST\debug_qa.log
```

---

# Part 3: 양쪽 로그 비교

## 신호 흐름 전체 추적

### 정상 케이스: 언리얼 조작 → Host 판정 → 언리얼 반영

```
=== 언리얼 로그 (Output Log) ===
[STATE] FORWARD_COCKPIT...LANDING_TAXI: OFF -> TAXI
[SEND] Tag=...LANDING_TAXI, IO2HOST=Landing_Taxi_Light_Switch, State=TAXI

=== Host 로그 (debug_qa.log) ===
[09:15:32.123] [RECV] STEP=26, I_ID=35: 0 -> 1 (TYPE=1)
[09:15:32.125] [JUDGE] STEP=26, I_ID=35: Cur=1, Exp=1, Term=1, PASS
[09:15:32.127] [SEND] STEP=26, EquipId=35, EquipSet=0, ErrCnt=0
[09:15:32.130] [STEP] === STEP 26 COMPLETED === Next: STEP 27, I_ID=36

=== 언리얼 로그 (UDP100 수신) ===
[RECV] EquipId=35, HostValue=1, Tag=...LANDING_TAXI
```

## 문제 유형별 디버깅

### 1. 언리얼 송신 OK, Host 수신 실패
```
언리얼: [SEND] Tag=...LANDING_TAXI, IO2HOST=Landing_Taxi_Light_Switch, State=TAXI
Host:   (RECV 로그 없음)
```
→ **원인**: UDP61 네트워크 문제 또는 Host가 실행 중이 아님

### 2. Host 수신 OK, 판정 실패
```
Host: [RECV] STEP=26, I_ID=35: 0 -> 1
Host: [JUDGE] STEP=26, I_ID=35: Cur=1, Exp=2, FAIL  ← 기대값 불일치
```
→ **원인**: DB의 i_value가 잘못됨

### 3. Host 송신 OK, 언리얼 수신 실패
```
Host:   [SEND] STEP=26, EquipId=35, EquipSet=1
언리얼: (RECV 로그 없음)
```
→ **원인**: UDP100 네트워크 문제

### 4. 언리얼 수신 OK, 상태 반영 실패
```
언리얼: [RECV] EquipId=35, HostValue=2
언리얼: (STATE 로그 없음)
```
→ **원인**: EquipmentMapping 누락 또는 ControlTag 매칭 실패

---

## 적용 체크리스트 (전체)

### Host
- [ ] `GlobalData.h`에 `DebugLogQA` 함수 존재
- [ ] `tc_find_trainee_input.cpp`에 `[RECV]` 로그
- [ ] `tc_chk_trainee_input.cpp`에 `[JUDGE]` 로그
- [ ] `dt_udp100_send_data.cpp`에 `[SEND]` 로그
- [ ] `tc_cntl_norm_step.cpp`에 `[STEP]` 로그
- [ ] Host 빌드 후 `debug_qa.log` 생성 확인

### 언리얼
- [ ] `UDP100MediatorSubsystem.cpp`에 `[RECV]` 로그
- [ ] `UDPSenderMediatorSubsystemBase.cpp`에 `[SEND]` 로그
- [ ] `ControlRegisterSubsystem.cpp`에 `[STATE]` 로그
- [ ] 언리얼 빌드 후 Output Log에서 태그 확인

---

# Part 4: Host 로깅 복원 가이드

> **목적:** Host 코드가 git pull 등으로 초기화될 때마다 이 가이드를 따라 로깅을 복원합니다.
> 로깅 코드는 Host git에 커밋되지 않으므로 pull 시 유실됩니다.

## 배경

- Host 프로젝트: `E:\KAI_HOST\fa50m-host\`
- 로깅 코드는 **로컬 전용** (Host git에 커밋하지 않음)
- git pull 후 소스가 초기화되면 이 가이드로 복원

## 수정 대상 파일 (5개)

| # | 파일 경로 | 수정 내용 |
|---|----------|----------|
| 1 | `host/GlobalData.h` | `DebugLogQA` 함수 정의 |
| 2 | `host/TC/tc_find_trainee_input.cpp` | `[RECV]` 로그 |
| 3 | `host/TC/tc_chk_trainee_input.cpp` | `[JUDGE]` 로그 |
| 4 | `host/DT/dt_udp100_send_data.cpp` | `[SEND]` 로그 |
| 5 | `host/TC/tc_cntl_norm_step.cpp` | `[STEP]` 로그 |

## 수정 1: GlobalData.h - DebugLogQA 함수

**위치:** `#endif` 직전 (파일 끝부분)

**삽입할 코드:**

```cpp
/* ===== QA Debug Logging ===== */
#include <stdio.h>
#include <stdarg.h>

inline void DebugLogQA(const char* format, ...) {
    static FILE* fp = nullptr;
    static bool firstCall = true;
    if (firstCall) {
        fp = fopen("E:\\KAI_HOST\\debug_qa.log", "w");
        firstCall = false;
        if (fp) {
            SYSTEMTIME st;
            GetLocalTime(&st);
            fprintf(fp, "=== Debug Log Started: %04d-%02d-%02d %02d:%02d:%02d ===\n",
                st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
            fflush(fp);
        }
    }
    if (fp) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(fp, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
        va_list args;
        va_start(args, format);
        vfprintf(fp, format, args);
        va_end(args);
        fflush(fp);
    }
}
```

**찾는 방법:** 파일 끝에서 `#endif` 검색 → 그 바로 위에 삽입

## 수정 2: tc_find_trainee_input.cpp - [RECV] 로그

**위치:** `INPUT_CHANGE == TRUE` 블록 내부, `CHNG_INPUT.NEW_DATA = NEW_DATA;` 직후

**원본 코드:**
```cpp
if (INPUT_CHANGE == TRUE)
{
    CHNG_INPUT.ID        = i - 1;
    CHNG_INPUT.PREV_DATA = EX_IN[i - 1].PREV_DATA;
    CHNG_INPUT.NEW_DATA  = NEW_DATA;

} /* END IF */
```

**수정 후:**
```cpp
if (INPUT_CHANGE == TRUE)
{
    CHNG_INPUT.ID        = i - 1;
    CHNG_INPUT.PREV_DATA = EX_IN[i - 1].PREV_DATA;
    CHNG_INPUT.NEW_DATA  = NEW_DATA;

    // ===== QA 상시 로깅 =====
    DebugLogQA("[RECV] STEP=%d, I_ID=%d: %d -> %d (TYPE=%d)\n",
        CURNT_STEP_NO, CHNG_INPUT.ID, CHNG_INPUT.PREV_DATA, CHNG_INPUT.NEW_DATA, EX_IN[i-1].TYPE);

} /* END IF */
```

## 수정 3: tc_chk_trainee_input.cpp - [JUDGE] 로그

**위치:** `} /* END IF */` 와 `return CHK_RESULT;` 사이

**원본 코드:**
```cpp
    } /* END IF */

    /* RETURN the Trainee action check result. */
    return CHK_RESULT;
```

**수정 후:**
```cpp
    } /* END IF */

    // ===== QA 상시 로깅 (변경 시에만) =====
    {
        static int prevStepNo = -1;
        static int prevResult = -1;
        if (CURNT_STEP_NO != prevStepNo || CHK_RESULT != prevResult) {
            DebugLogQA("[JUDGE] STEP=%d, I_ID=%d: Cur=%d, Exp=%d, Term=%d, %s\n",
                CURNT_STEP_NO,
                STEP_DATA[STEP_IDX].I_ID,
                *EX_IN[STEP_DATA[STEP_IDX].I_ID].DATA,
                STEP_DATA[STEP_IDX].I_VAL,
                STEP_DATA[STEP_IDX].I_TERM,
                CHK_RESULT ? "PASS" : "FAIL");
            prevStepNo = CURNT_STEP_NO;
            prevResult = CHK_RESULT;
        }
    }

    /* RETURN the Trainee action check result. */
    return CHK_RESULT;
```

**주의:** 구조체 필드는 `I_TERM` (SSOT 문서의 `TERM`은 오류)

## 수정 4: dt_udp100_send_data.cpp - [SEND] 로그

**위치:** 함수 끝 `}` 직전

**원본 코드:**
```cpp
    }

}
```

**수정 후:**
```cpp
    }

    // ===== QA 상시 로깅 (변경 시에만) =====
    {
        static int prevStepNo = -1;
        static int prevEquipId = -1;
        static int prevEquipSet = -1;

        if (CURNT_STEP_NO != prevStepNo ||
            UDP_100->EquipmentId != prevEquipId ||
            (int)UDP_100->EquipmentSet != prevEquipSet) {

            DebugLogQA("[SEND] STEP=%d, EquipId=%d, EquipSet=%d, ErrCnt=%d\n",
                CURNT_STEP_NO,
                UDP_100->EquipmentId,
                (int)UDP_100->EquipmentSet,
                UDP_100->errCount);

            prevStepNo = CURNT_STEP_NO;
            prevEquipId = UDP_100->EquipmentId;
            prevEquipSet = (int)UDP_100->EquipmentSet;
        }
    }

}
```

**주의:** `EquipmentSet`은 `bool`이므로 `(int)` 캐스팅 필요

## 수정 5: tc_cntl_norm_step.cpp - [STEP] 로그

**위치:** `STEP_IDX = STEP_IDX + SUBSTEP_COUNTER;` 직후

**원본 코드:**
```cpp
            STEP_IDX = STEP_IDX + SUBSTEP_COUNTER;

            /* RESET the Substep_Counter to 1. */
            SUBSTEP_COUNTER = 1;
```

**수정 후:**
```cpp
            STEP_IDX = STEP_IDX + SUBSTEP_COUNTER;

            // ===== QA 상시 로깅 =====
            DebugLogQA("[STEP] === STEP %d COMPLETED === Next: STEP %d, I_ID=%d\n",
                CURNT_STEP_NO,
                STEP_DATA[STEP_IDX].STEP_NO,
                STEP_DATA[STEP_IDX].I_ID);

            /* RESET the Substep_Counter to 1. */
            SUBSTEP_COUNTER = 1;
```

## SSOT vs 실제 코드 차이점

| SSOT 문서 표기 | 실제 코드 | 비고 |
|---------------|----------|------|
| `STEP_DATA[].TERM` | `STEP_DATA[].I_TERM` | 구조체에 TERM 필드 없음 |
| `CURNT_STEP_NO + 1` (STEP 로그) | `STEP_DATA[STEP_IDX].STEP_NO` | STEP_IDX 이미 증가 후이므로 직접 참조 |
| `SetEquipment` | `EquipmentSet` (bool) | 멤버명 다름 + `(int)` 캐스팅 필요 |
| `Wait` | 존재하지 않음 | UDP_100_TYPE에 Wait 필드 없음 → 로그에서 제거 |

## 검증 방법

1. Host 빌드 후 실행
2. 훈련 시작 (RUN_MODE 진입)
3. `E:\KAI_HOST\debug_qa.log` 파일 확인
4. 정상 흐름: `[RECV]` → `[JUDGE]` → `[SEND]` → `[STEP]` 순서로 기록
5. `/qa-host` 스킬로 로그 분석 테스트

## 예상 정상 출력

```
=== Debug Log Started: 2026-02-05 10:00:00 ===
[10:00:01.123] [SEND] STEP=1, EquipId=-1, EquipSet=0, ErrCnt=0
[10:00:05.456] [RECV] STEP=9, I_ID=264: 0 -> 1 (TYPE=0)
[10:00:05.458] [JUDGE] STEP=9, I_ID=264: Cur=1, Exp=1, Term=0, PASS
[10:00:05.460] [STEP] === STEP 9 COMPLETED === Next: STEP 10, I_ID=283
[10:00:05.462] [SEND] STEP=10, EquipId=283, EquipSet=0, ErrCnt=0
```
