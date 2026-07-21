---
name: qa-log
description: 언리얼 로그 파일을 실시간으로 읽어서 UDP 통신 및 상태 변경을 디버깅합니다
triggers:
  - qa-log
  - 로그 확인
  - 언리얼 로그
  - unreal log
args:
  - name: lines
    description: 읽을 줄 수
    required: false
    default: "100"
---

# QA Log Debug

언리얼 로그 파일을 실시간으로 읽어서 디버깅합니다.

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
