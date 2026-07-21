# 로그 패턴 레퍼런스

## UDP 전송 로그

| 패턴 | 의미 |
|------|------|
| `[UDP61] ... -> ON/OFF` | UDP61 값 전송 |
| `[UDP61 Sender] Changed:` | UDP61 패킷 변경 |
| `[UDP51] ...` | UDP51 (후방석) 전송 |
| `[UDP41 Sender]` | UDP41 (외부 패널) 전송 |

`[UDPxx Sender] Changed:`의 파일·채널별 첫 프레임은 초기 상태 스냅샷일 수 있으므로 조작 전환으로 판정하지 않습니다. 이후 프레임에서 동일 멤버의 값이 실제로 바뀐 경우만 과거 로그 기반 전환 증거로 사용합니다.

모멘터리 버튼은 `PRESS`에서 `1/ON`, `RELEASE`에서 `0/OFF`가 발생하며 두 명령 사이에는 별도 출력 변화가 없는 것이 정상입니다. 누르고 있는 시간 자체를 `HOLD` 출력으로 해석하지 않습니다.

## 상태 변경 로그

| 패턴 | 의미 |
|------|------|
| `[BroadcastControlStateChange]` | 컨트롤 상태 변경 |
| `[Interaction]` | 상호작용 이벤트 |
| `[SequenceSystem]` | 시퀀스 시스템 |

## QA 관련 로그

| 패턴 | 의미 |
|------|------|
| `[QA]` | QAExecute 실행 |
| `[AnimVM]` | 애니메이션 뷰모델 |

## 에러 패턴

| 패턴 | 의미 |
|------|------|
| `Error:` | 일반 에러 |
| `Warning:` | 경고 |
| `LogUDP` | UDP 관련 로그 |

## 디버깅 워크플로우

1. **문제 재현**: 에디터에서 절차 실행
2. **로그 읽기**: `/qa-log` 실행
3. **패턴 분석**: UDP 전송, 상태 변경, 에러 확인
4. **원인 파악**: 언리얼 vs Host 문제 구분

## 골드셋 판독

- 일반 Unreal 로그: `AutomationDriver` 문자열이 없는 세션만 과거 관측 자료로 사용
- 자동검증 결과: `physical_*.json`에서 `PASS` 또는 `PASS_WITH_FINDING`이고 모든 action이 `ACTION_SENT`인 컨트롤만 사용
- 출력 연결: `DT_ControlData.csv`의 `IO2HOST`, `PNLEQM2HST`, `PNLACT2HST`와 정확히 일치해야 함
- 연결 대상이 여러 컨트롤이면 자동 확정하지 않고 `AMBIGUOUS_OUTPUT_MAPPING`으로 남김
- `EquipmentId`가 음수이면 CLI로 지정할 수 없으므로 `NO_EQUIPMENT_ID`로 남김
- 전환 기록이 없으면 `NO_POST_BASELINE_TRANSITION`으로 남기고 필요한 컨트롤만 사용자 조작을 요청
