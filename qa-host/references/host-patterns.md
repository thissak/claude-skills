# Host 로그 패턴 레퍼런스

## 주요 로그 패턴

| 패턴 | 의미 |
|------|------|
| `[HOST][JUDGE] step=N i_id=ID cur=X tgt=Y result=WRONG` | 판정 실패 |
| `[HOST][JUDGE] step=N ... result=CORRECT` | 판정 성공 |
| `[IOS][RECV] step=N err_count=N mode=RUN_MODE` | IOS 수신 상태 |
| `[UDP61][RECV]` | UDP61 수신 |

## 문제 유형별 해결

### cur != tgt (값 불일치)

- 언리얼에서 보낸 값과 Host에서 인식한 값이 다름
- Bool 반전 문제 확인 (ON/OFF 매핑)
- UDP 필드 경로 확인
- `equipment_mapping.h` 매핑 확인

### UDP 수신 안 됨

- 네트워크 연결 확인
- UDP 포트 확인 (UDP61: 61000)
- 방화벽 설정 확인
