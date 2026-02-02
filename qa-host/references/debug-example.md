# 디버깅 예시

## IUFC 스위치 OFF 전환 시 절차 안 넘어감

### 문제 상황

스위치를 OFF로 전환했지만 Host에서 절차가 진행되지 않음

### 언리얼 로그 (`/qa-log`)

```
[UDP61] IOEX2HST.Avionics_Power_Panel.IUFC_On -> OFF (int: 0)
[UDP61 Sender] Changed: [IOEX2HST.Avionics_Power_Panel.IUFC_On=false]
```

### Host 로그 (`/qa-host`)

```
[HOST][JUDGE] step=72 i_id=264 cur=1 tgt=0 result=WRONG
```

### 분석

- 언리얼: 0 전송
- Host: cur=1로 인식
- 결론: UDP 전송 또는 수신 문제

### 해결 방향

1. UDP 패킷 실제 전송 여부 확인
2. Host 수신 버퍼 확인
3. 필드 경로 매핑 확인
