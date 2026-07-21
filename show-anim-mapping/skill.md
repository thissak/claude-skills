---
name: show-anim-mapping
description: Task ID별 애니메이션 매핑을 출력하고 DB, CSV, 시퀀서 마커를 교차 검증하거나 엑셀 리포트를 만들 때 사용합니다.
---

# show-anim-mapping

Task ID를 받아 해당 훈련절차의 애니메이션 매핑을 출력하고, DB animation 개수 vs 시퀀서 마커 개수를 검증합니다.

## Trigger

사용자가 "애니메이션 매핑 보여줘", "에니메이션 매핑 출력", "anim mapping" 등을 요청할 때.
인자: Task ID (예: 334001). 쉼표/공백으로 여러 개 지정 가능.

## 실행 절차

### 1. DB에서 Step별 애니메이션 조회

```bash
PGPASSWORD=kai_readonly psql -h 192.168.11.201 -p 5432 -U kai_readonly -d FA_50_KAI -c "
SELECT DISTINCT ON (s.step_no) s.step_no, s.animation, m.ms_step_description
FROM tbl_step s
LEFT JOIN tbl_main_step m ON m.ms_task_id = s.step_task_id AND m.ms_step_no = s.step_no AND m.ms_step_sub_no = 1
WHERE s.step_task_id = {TASK_ID}
ORDER BY s.step_no, s.step_sub_no;
"
```

### 2. task_tm_no 조회 + vcbt_folder_mapping.json에서 마스터 시퀀스 경로 조회

```bash
PGPASSWORD=kai_readonly psql -h 192.168.11.201 -p 5432 -U kai_readonly -d FA_50_KAI -t -A -c "
SELECT task_tm_no FROM tbl_task WHERE task_id = {TASK_ID};
"
```

```bash
python -c "
import json
d = json.load(open('E:/UECsvDataTableConverter/ANIMToSeq/vcbt_folder_mapping.json', encoding='utf-8'))
mappings = d.get('mappings', d)
proc = '{TASK_TM_NO}'  # 예: 34-20-01
folder = mappings.get(proc, 'NOT FOUND')
print(folder)
"
```

### 3. UE 에디터에서 시퀀서 마커 조회 (Remote Execution)

UE Python Remote Execution을 사용하여 에디터에서 직접 마커를 가져온다.
**전제조건**: 에디터가 실행 중이고, Python Remote Execution이 활성화되어 있어야 함.
(Edit → Project Settings → Plugins → Python → Enable Remote Execution 체크)

```python
import sys, os, json
ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote
import time

re = remote.RemoteExecution()
re.start()
time.sleep(2)

node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

# {ASSET_PATH}는 vcbt_folder_mapping에서 얻은 경로로 구성
# 예: /Game/01_Visual/02_Animation/VCBT/{folder}/{name}_Master
cmd = '''
import unreal, json
seq = unreal.load_asset("{ASSET_PATH}")
if seq:
    markers = seq.get_marked_frames_from_sequence(unreal.MovieSceneTimeUnit.DISPLAY_RATE)
    labels = [m.label for m in markers]
    print(json.dumps(labels))
else:
    print("LOAD_FAIL")
'''

result = re.run_command(cmd, unattended=True)
# result['output']에서 JSON 파싱하여 마커 목록 추출

re.close_command_connection()
re.stop()
```

여러 Task를 한 번에 검증할 때는 sequences dict에 모아서 한 번의 연결로 처리한다.

**에디터 미실행 시**: 마커 검증을 건너뛰고 DB 매핑만 출력. "에디터 미실행으로 마커 검증 생략" 메시지 표시.

### 4. DB vs 시퀀서 마커 검증

핵심 검증: **DB animation > 0인 DISTINCT step_no 수 == 시퀀서 마커 수**

- DB animation 값에서 AnimId 추출: `AnimId = animation // 10`
- 마커 순서: A, B, C, ... (알파벳순, 마커 = 구간의 끝 지점)
- 첫 애니메이션은 frame 0에서 시작

검증 결과:
- **PASS**: DB 개수 = 시퀀서 마커 수
- **FAIL**: 불일치 시 부족/초과 개수 표시

### 5. 출력 형식

#### 마스터 시퀀스 경로
```
폴더: 04_Navigation_System/EADI_EHSI_Checkout
```

#### Step별 애니메이션 매핑 테이블
| Step | Animation | AnimId | Marker | 절차 내용 |
|------|-----------|--------|--------|----------|
| 1 | -1 (입력) | - | - | ... |
| 3 | **3010** | 301 | A | ... |

- `animation = -1`: 사용자 입력 (콕핏 직접 조작) step
- `animation = -2`: 확인만 하는 step
- `animation > 0`: 시퀀서 애니메이션 ID
- animation 마지막 자리: 0=외부뷰, 1=콕핏뷰 (IsCockpit)

#### DB vs 시퀀서 검증 결과

| 항목 | DB | 시퀀서 | 결과 |
|------|-----|--------|------|
| 애니메이션/마커 수 | N개 | M개 | PASS/FAIL |

#### 요약
- 전체 step 수
- 애니메이션 있는 step 수 + ID 목록

### 6. db_input_tool 웹페이지 열기

매핑 출력 후 해당 Task의 db_input_tool 검수 페이지를 브라우저로 연다.

```bash
start http://192.168.11.201:6003/inspection?task_id={TASK_ID}
```

## 참고

- CSV(DT_AnimIdMarkerMapping)는 DB에서 자동 생성되므로 별도 검증 불필요
- UE Remote Execution 설정: 멀티캐스트 239.0.0.1:6766, Bind 127.0.0.1
- UE Python 모듈 경로: `E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python`
