---
name: qa-log
description: 사용자가 "qa-log", "로그 확인", "언리얼 로그", "unreal log"라고 말하면 Unreal 로그의 UDP 통신과 상태 변경을 분석하고, Task 문맥이 있으면 절차 검증 SSOT에 진단 증거로 연결한다. 기본 최근 100줄 또는 사용자가 지정한 줄 수를 읽는다.
---

# QA Log Debug

언리얼 로그 파일을 실시간으로 읽어서 디버깅합니다.

## 전체 절차 검증 SSOT 연결

Task 문맥이 있는 로그 분석은 `.claude/docs/qa-procedure-verification-ssot.md`를 따른다. 로그는 원인 증거이므로 단독 Task clean 판정에 사용하지 않는다.

- 실제 문제를 확인하면 에이전트가 `record-supporting --method LOG --verdict ISSUE`로 등록한다.
- 정상 흐름이나 기존 IssueKey를 뒷받침하는 로그는 `OBSERVATION`으로 연결한다.
- 사용자는 로그 경로나 관찰만 전달하며 SSOT 형식을 작성하지 않는다.

## 로그 파일 경로

`E:\KAI_VCBT\fa50visualdev_new\Saved\Logs\FA50VisualDev.log`

## 실행 단계

### Step 1: 최근 로그 읽기

```bash
tail -$ARGUMENTS "E:/KAI_VCBT/fa50visualdev_new/Saved/Logs/FA50VisualDev.log"
```

인자가 없으면 기본 100줄을 읽습니다.

### Step 2: 주요 패턴 필터링 (필요시)

```bash
tail -500 "E:/KAI_VCBT/fa50visualdev_new/Saved/Logs/FA50VisualDev.log" | grep -E "(UDP61|UDP51|UDP41|Error|Warning|JUDGE)"
```

### Step 3: 컨트롤 골드셋 재생성 (요청 시)

기존 CP/AP 일반 Unreal 로그와 성공한 physical 절차 보고서를 합쳐 골드셋을 재생성합니다.

```powershell
Set-Location E:\KAI_HOST\iostestapp
python -m qa.unreal_control.goldset
```

생성물:

- `qa/goldsets/unreal_control_goldset.json`: 로그 또는 실절차로 확인된 컨트롤
- `qa/goldsets/unresolved_controls.csv`: 로그만으로 확인하지 못해 추가 조작이 필요한 컨트롤

`PROCEDURE_VERIFIED`는 실제 Unreal `ACT` 조작과 절차 판정이 확인된 컨트롤이고, `LOG_OBSERVED`는 `DT_ControlData` 출력 경로와 일반 Unreal 로그의 후속 UDP 전환이 일대일로 연결된 컨트롤입니다. 첫 `Changed` 프레임은 초기 스냅샷으로만 사용합니다. 일반 로그 채굴에서는 `AutomationDriver` 세션을 제외하고, 명시적인 physical JSON 보고서만 자동화 증거로 사용합니다.

## 참고

주요 로그 패턴은 `references/log-patterns.md`를 참조하세요.
