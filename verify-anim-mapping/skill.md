---
name: verify-anim-mapping
description: 사용자가 "verify-anim-mapping", "애니메이션 매핑 검증", "시퀀스 매핑 검증", "anim mapping verify"라고 말하면 특정 Task 또는 전체의 엑셀·DB animation·UE 시퀀서 마커 정합성을 검증하고 결과를 절차 검증 SSOT에 등록한다.
---

# 애니메이션 매핑 검증

DB(tbl_step.animation) ↔ 시퀀서 마커 (UE Remote Execution) 정합성을 검증합니다.
선택적으로 엑셀(훈련절차 샷정리)과도 교차 검증합니다.

## 전체 절차 검증 SSOT 연결

실행 전에 `.claude/docs/qa-procedure-verification-ssot.md`를 읽는다. Task별 결과는 에이전트가 `record-supporting --method ANIMATION`으로 등록한다.

- PASS는 애니메이션 차원의 `CLEAN`이며 runtime Task 전체 clean을 단독으로 만들지 않는다.
- FAIL은 `ISSUE`로 등록하고 DB·시퀀서·엑셀 증거를 연결한다.
- 해소 확인은 기존 IssueKey를 `RESOLVED`로 연결한다.
- 사용자는 검증 결과만 확인하며 SSOT 형식을 작성하지 않는다.

## 핵심 검증

**DB animation 개수 vs 시퀀서 마커 개수**
- CSV(DT_AnimIdMarkerMapping)는 DB에서 자동 생성이므로 별도 검증 불필요
- uasset 바이너리 파싱은 오탐이 많아 사용하지 않음

## 데이터 소스

| 소스 | 위치 | 역할 |
|------|------|------|
| DB | `192.168.11.201:5432/FA_50_KAI` | animation 값 + ms_step_description (영문) |
| 시퀀서 마커 | UE Remote Execution으로 직접 조회 | 실제 마커 |
| 엑셀 (선택) | `references/excel-path.md` 참조 | shot code + Story (한글) |

## DB animation 값 구조

```
animation = AnimId × 10 + IsCockpit
예: 8010 → AnimId=801, IsCockpit=false
예: 8011 → AnimId=801, IsCockpit=true
```

## 검증 절차

### Step 1: DB에서 animation 데이터 수집

```bash
PGPASSWORD=kai_readonly psql -h 192.168.11.201 -p 5432 -U kai_readonly -d FA_50_KAI -c "
SELECT DISTINCT ON (s.step_no) s.step_no, s.animation, m.ms_step_description
FROM tbl_step s
LEFT JOIN tbl_main_step m ON m.ms_task_id = s.step_task_id AND m.ms_step_no = s.step_no AND m.ms_step_sub_no = 1
WHERE s.step_task_id = {TASK_ID}
ORDER BY s.step_no, s.step_sub_no;
"
```

### Step 2: UE Remote Execution으로 시퀀서 마커 조회

**전제조건**: 에디터 실행 + Python Remote Execution 활성화
(Edit → Project Settings → Plugins → Python → Enable Remote Execution)

```python
import sys, time, json
sys.path.insert(0, r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

cmd = '''
import unreal, json
seq = unreal.load_asset("{ASSET_PATH}")
if seq:
    markers = seq.get_marked_frames_from_sequence(unreal.MovieSceneTimeUnit.DISPLAY_RATE)
    print(json.dumps([m.label for m in markers]))
else:
    print("FAIL")
'''
result = re.run_command(cmd, unattended=True)
re.close_command_connection()
re.stop()
```

asset path는 vcbt_folder_mapping.json + task_tm_no로 구성:
```python
import json
d = json.load(open('E:/UECsvDataTableConverter/ANIMToSeq/vcbt_folder_mapping.json', encoding='utf-8'))
folder = d.get('mappings', d).get(task_tm_no)
# path = f'/Game/01_Visual/02_Animation/VCBT/{folder}/{folder.split("/")[-1]}_Master'
```

### Step 3: DB vs 시퀀서 비교

- DB: animation > 0인 DISTINCT step_no 수
- 시퀀서: 마커 수
- PASS = 동일, FAIL = 불일치

### Step 4: (선택) 엑셀 교차 검증

엑셀이 필요한 경우:
- shot code의 step_no 집합 vs DB animation step_no 집합
- Story(한글) vs ms_step_description(영문) 대조

## 결과 출력

```
=== Task {task_id} ({task_tm_no}) 검증 결과 ===

DB 애니메이션: {N}개 (AnimId: 301, 501, ...)
시퀀서 마커: {M}개 (A, B, C, ...)
결과: PASS / 마커 {X}개 부족
```

결과 출력 뒤 에이전트는 범위와 증거를 현재 절차 SSOT에 등록하고 생성 표의 해당 Task를 확인한다.

## 참고

- DB 접근 시 항상 `kai_readonly` 사용 (SELECT 전용)
- 엑셀 경로는 `references/excel-path.md`에서 관리
- UE Remote Execution 설정: 멀티캐스트 239.0.0.1:6766, Bind 127.0.0.1
- 에디터 미실행 시 마커 검증 건너뛰고 DB 매핑만 출력
