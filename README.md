# FA50 Claude Skills

FA-50 시뮬레이터 프로젝트용 Claude Skills 모음입니다.

## Skills 목록

| Skill | Description |
|-------|-------------|
| `/qa-log` | 언리얼 로그 파일 디버깅 |
| `/qa-host` | Host 로그 파일 디버깅 |
| `/sync-ac` | 빌드 + CP↔AC 프로젝트 동기화 |
| `/create-skill` | 새 스킬 생성 가이드 |

## 설치 방법

### Submodule로 추가
```bash
cd your-project/.claude
git submodule add https://github.com/thissak/claude-skills.git skills
```

### 직접 복사
```bash
git clone https://github.com/thissak/claude-skills.git
cp -r claude-skills/* your-project/.claude/skills/
```

## 폴더 구조

```
skills/
├── qa-log/
│   ├── SKILL.md
│   └── references/
├── qa-host/
│   ├── SKILL.md
│   └── references/
├── sync-ac/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
└── create-skill/
    ├── SKILL.md
    ├── references/
    └── assets/
```

## Skills 형식

Anthropic 공식 가이드 기반:
- 폴더 단위 패키지
- `SKILL.md` 필수 (YAML frontmatter + Markdown)
- `references/` - 참조 문서
- `scripts/` - 실행 스크립트
- `assets/` - 템플릿, 리소스

## 참고

- [Claude Skills 구축 완벽 가이드 (Anthropic 공식 PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
