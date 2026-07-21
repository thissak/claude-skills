# FA50 Claude Skills

FA-50 시뮬레이터 프로젝트용 Claude Skills 모음입니다.

## Skills 목록

| Skill | Description |
|-------|-------------|
| `/add-udp41-equipment` | UDP41 지원장비 추가 |
| `/anim-fresh` | 애니메이션 fresh 작업 |
| `/create-skill` | 새 스킬 생성 가이드 |
| `/generate-ssot` | 엑셀 SSOT 생성·동기화·검증 |
| `/qa-host` | Host 로그 파일 디버깅 |
| `/qa-log` | 언리얼 로그 파일 디버깅 |
| `/qa-signal` | Unreal↔Host 신호 사슬 검증 |
| `/qa-static` | QA 정적 사전검증 |
| `/qa-workflow` | QA 워크플로우 오케스트레이터 |
| `/screenshot` | 프로젝트 스크린샷 캡처 |
| `/show-anim-mapping` | 애니메이션 매핑 조사 |
| `/sync-ac` | 빌드 + CP↔AC 프로젝트 동기화 |
| `/verify-anim-mapping` | 애니메이션 매핑 검증 |

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
skills/<skill-name>/
├── SKILL.md
├── references/   # 선택
├── scripts/      # 선택
└── assets/       # 선택
```

프로젝트의 `.agents/skills/<skill-name>/SKILL.md`는 이 저장소의 Claude 원본을 읽게 하는 Codex용 얇은 어댑터다. 원칙과 절차를 어댑터에 복제하지 않고 Claude `SKILL.md`를 SSOT로 유지한다.

## Skills 형식

Anthropic 공식 가이드 기반:
- 폴더 단위 패키지
- `SKILL.md` 필수 (YAML frontmatter + Markdown)
- `references/` - 참조 문서
- `scripts/` - 실행 스크립트
- `assets/` - 템플릿, 리소스

## 참고

- [Claude Skills 구축 완벽 가이드 (Anthropic 공식 PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
