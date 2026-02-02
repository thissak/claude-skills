---
name: create-skill
description: Anthropic 공식 가이드 기반으로 Claude Skills를 생성합니다
triggers:
  - create-skill
  - 스킬 생성
  - 스킬 만들기
  - new skill
args:
  - name: skill-name
    description: 생성할 스킬 이름 (kebab-case)
    required: true
---

# Claude Skills 생성 가이드

Anthropic 공식 33페이지 가이드 기반 스킬 생성 워크플로우입니다.

## Skills 개념

**Skills**는 반복되는 작업 흐름을 한 번 정의해 지속적으로 재사용하는 패키지입니다.

- 일회성 프롬프트가 아닌 조직의 표준 워크플로를 고정하는 자산
- Claude.ai, API, Code 환경에서 동일하게 동작 (Portability)
- 여러 스킬 동시 활성화 가능 (Composability)

## 폴더 구조 (필수)

```
.claude/skills/{skill-name}/
├── SKILL.md          # 필수 - 정확히 이 이름 사용
├── scripts/          # 선택 - 실행 스크립트
├── references/       # 선택 - 참조 문서
└── assets/           # 선택 - 템플릿, 리소스
```

## 실행 단계

### Step 1: 스킬 폴더 생성

```bash
mkdir -p ".claude/skills/$ARGUMENTS"
mkdir -p ".claude/skills/$ARGUMENTS/references"
```

### Step 2: SKILL.md 생성

`assets/skill-template.md` 템플릿을 참조하여 SKILL.md를 작성합니다.

### Step 3: 필요시 추가 파일 생성

- `scripts/`: 실행할 스크립트
- `references/`: 상세 문서
- `assets/`: 템플릿, 리소스

## 제약사항

상세 제약사항은 `references/constraints.md`를 참조하세요.
