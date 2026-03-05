---
allowed-tools: Agent, Read, Glob, Grep, Write, Edit, AskUserQuestion
description: "Create a new refactoring ticket with Claude Code workflow recommendations"
---

# /create-ticket

チケットの説明: $ARGUMENTS

## Instructions

与えられたチケット説明から、構造化されたリファクタリングチケットを生成する。

### Phase 1: 調査（researcher agent）

researcher agent を使って以下を調査:

1. チケット説明に関連するソースコード (`src/helix/`, `tests/`)
2. 影響を受けるファイルと行範囲
3. 既存のテストカバレッジ
4. 関連するドキュメント (`docs/`)
5. 依存関係（他チケットとの関連）

### Phase 2: 計画（planner agent）

planner agent を使って以下を設計:

1. チケットの構造（背景・Scope・Acceptance Criteria・Implementation Notes）
2. 適切なカテゴリ（Security / CodeQuality / Doc / DevOps / Community）とサイズ（S/M/L/XL）の判定
3. `.docs/templates/workflow-patterns.md` を参照し、カテゴリ×サイズに基づくワークフロー推奨を生成

### Phase 3: チケット出力

以下のフォーマットでチケットを生成し、ユーザーに提示する:

```markdown
## T-NNN: [タイトル]

| 項目 | 値 |
|------|-----|
| Priority | **P?** |
| Category | [カテゴリ] |
| Size | [S/M/L/XL] |
| Dependencies | [依存チケット or —] |

### 背景

[問題の説明と根拠]

### Scope

| ファイル | 行 | 変更内容 |
|----------|-----|---------|
| ... | ... | ... |

### Acceptance Criteria

1. ...
2. ...

### Implementation Notes

- ...

### Claude Code Workflow

| Phase | Command / Agent | 目的 |
|-------|----------------|------|
| 1. ... | ... | ... |

**実行例**:
```
[コマンドフロー]
```
```

### ワークフロー選択ガイド

利用可能なコマンド・エージェントを `.claude/commands/` と `.claude/agents/` から読み取り、
`.docs/templates/workflow-patterns.md` のパターンを参照してワークフローを設計すること。

**カテゴリ別の基本方針**:
- **Security**: `/security-scan` を前後に挟む。spec-first でドキュメント先行。
- **CodeQuality**: `/refactor` コマンドを活用。振る舞い変更なしを保証。
- **Doc**: doc-writer agent を活用。
- **DevOps**: CI/CD設定はテスト困難なため `/plan` で慎重に設計。
- **Community**: 業界標準テンプレートを参照。

**サイズ別の方針**:
- **S**: `/plan` 省略可。直接実装。
- **M**: `/plan` 推奨。
- **L/XL**: `/plan` 必須。段階実装を推奨。
