# Skills 제약사항

## YAML Frontmatter 규칙

| 필드 | 필수 | 규칙 |
|------|------|------|
| `name` | O | kebab-case만 (대문자, 공백 불가) |
| `description` | O | 1024자 이내, 사용자 관점 언어 |
| `triggers` | 권장 | 트리거 키워드 배열 |
| `args` | 선택 | 인자 정의 배열 |

## 금지 사항

- 스킬 폴더 내 `README.md` 포함 금지
- name 필드에 대문자, 공백 사용 금지
- frontmatter에 XML 태그 사용 금지
- "claude", "anthropic" 같은 예약어 사용 금지

## 설계 원칙

### Progressive Disclosure (3단계 정보 로딩)

| 단계 | 로드 시점 | 내용 |
|------|----------|------|
| 1 | 항상 | Frontmatter만 (트리거 판단용) |
| 2 | 스킬 활성화 시 | SKILL.md 본문 |
| 3 | 필요 시 | references/, scripts/, assets/ |

토큰 효율성을 위해 필요한 정보만 단계적으로 로드합니다.

### Composability

여러 스킬을 동시에 활성화할 수 있습니다.

### Portability

Claude.ai, API, Code 환경에서 동일하게 동작해야 합니다.
