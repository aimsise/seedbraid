# T-002: pytest-cov + CI Coverage Gate — 実装計画

## 概要

テストカバレッジ計測ツール `pytest-cov` を導入し、ローカル開発ではカバレッジレポートを自動表示、CI ではカバレッジ閾値ゲートを設置して品質低下を防止する。変更対象は pyproject.toml、ci.yml、uv.lock の 3 ファイル。

## 前提条件

調査レポート (`docs/research/T-002_pytest-cov_investigation.md`) からの重要な前提:

1. **推定現在カバレッジ**: 65-75% (加重計算に基づく)
2. **テスト構成**: 22 テストファイル、61 テスト関数、1,768 LOC
3. **ソース構成**: src/helix/ 配下 14 モジュール、3,333 LOC
4. **パス解決**: `PYTHONPATH=src` + `--cov=helix` の組み合わせで src/helix/ に正しく解決 (SAFE)
5. **CI 環境**: `uv run --no-sync --no-editable python -m pytest` で実行中、互換性問題なし
6. **他ジョブへの影響**: compat / bench-gate / lint ジョブへの影響なし
7. **conftest.py**: 存在しない (グローバル fixture なし)
8. **IPFS テスト**: 2 ファイルで条件付き pytest.skip 使用 (スキップ分はカバレッジ計測外、正常動作)

## 影響ファイル

| ファイル | 変更種別 | 影響度 |
|----------|---------|--------|
| `pyproject.toml` L17-20 | 修正 (dev 依存追加) | 低 |
| `pyproject.toml` L34-36 | 修正 (pytest addopts) | 低 |
| `.github/workflows/ci.yml` L45-46 | 修正 (test ジョブ) | 中 |
| `uv.lock` | 自動再生成 | 低 |

## 実装ステップ

### Step 1: pyproject.toml — dev 依存追加

**ファイル**: `pyproject.toml` L17-20

**変更前**:
```toml
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

**変更後**:
```toml
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
  "ruff>=0.6",
]
```

**理由**:
- pytest-cov 5.0+ は coverage.py 7.x を依存に含む
- pytest 8.x/9.x との互換性確認済み
- アルファベット順で `pytest` と `ruff` の間に配置

### Step 2: pyproject.toml — pytest addopts 設定

**ファイル**: `pyproject.toml` L34-36

**変更前**:
```toml
[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
```

**変更後**:
```toml
[tool.pytest.ini_options]
addopts = "-q --cov=helix --cov-report=term-missing"
testpaths = ["tests"]
```

**設計判断**:
- `--cov=helix`: src/helix/ パッケージ全体を計測対象に指定
- `--cov-report=term-missing`: ターミナルにカバレッジ + 未カバー行番号を出力
- `--cov-fail-under`: addopts に含めない（ローカル開発を妨げないため、CI でのみ指定）
- `-q` は維持: カバレッジレポートのみ詳細表示し、テスト出力は簡潔に

### Step 3: .github/workflows/ci.yml — カバレッジゲート追加

**ファイル**: `.github/workflows/ci.yml` L45-46

**変更前**:
```yaml
      - name: Pytest
        run: PYTHONPATH=src uv run --no-sync --no-editable python -m pytest
```

**変更後**:
```yaml
      - name: Pytest with coverage gate
        run: PYTHONPATH=src uv run --no-sync --no-editable python -m pytest --cov-fail-under=80
```

**設計判断**:
- `--cov-fail-under=80`: CI でのみ閾値チェックを適用
- pyproject.toml の addopts で `--cov=helix --cov-report=term-missing` が既に有効なため、ここでは閾値のみ追加
- ステップ名を変更して意図を明確化

**初期閾値の段階的戦略**:

| 実測カバレッジ | 対応 |
|---------------|------|
| >= 80% | そのまま `--cov-fail-under=80` を維持 |
| 75-79% | `--cov-fail-under=75` に設定し、後続チケットで段階的引き上げ |
| 70-74% | `--cov-fail-under=70` に設定し、後続チケットで段階的引き上げ |
| < 70% | `--cov-fail-under=65` に設定し、テスト追加チケットを優先 |

### Step 4: uv.lock 再生成

```bash
uv lock
```

確認:
```bash
grep -A 2 'name = "pytest-cov"' uv.lock
grep -A 2 'name = "coverage"' uv.lock
```

### Step 5: ローカル検証

**5a. 依存インストール**:
```bash
uv sync --no-editable --extra dev
```

**5b. カバレッジレポート生成確認**:
```bash
PYTHONPATH=src uv run --no-editable python -m pytest
```
- カバレッジレポートがターミナルに表示されること (AC #1)
- `--cov-fail-under` がないためローカルでは閾値チェックなし (AC #3)

**5c. CI 相当のカバレッジゲート確認**:
```bash
PYTHONPATH=src uv run --no-editable python -m pytest --cov-fail-under=80
```
- 80% 以上: OK → 閾値 80 のまま維持
- 80% 未満: → Step 3 の段階的戦略に従い閾値調整

**5d. 他テスト実行への影響なし確認**:
```bash
PYTHONPATH=src uv run --no-editable python -m pytest tests/test_roundtrip.py
```

### Step 6: 閾値調整 (条件付き)

Step 5c の結果に基づき、必要に応じて ci.yml の `--cov-fail-under` 値を調整。

### Step 7: lint + テスト最終確認

```bash
UV_CACHE_DIR=.uv-cache uv run --no-editable ruff check .
PYTHONPATH=src uv run --no-editable python -m pytest
```

### Step 8: コミット

```bash
git add pyproject.toml uv.lock .github/workflows/ci.yml
git commit -m "feat: add pytest-cov and CI coverage gate (T-002)"
```

## リスクと対策

| リスク | 確率 | 対策 |
|--------|------|------|
| 実測カバレッジが 80% 未満 | 高 | Step 5c で事前確認、段階的戦略で閾値調整 |
| パス解決エラー | 極低 | 調査で SAFE 判定済み。問題時は `--cov=src/helix` に変更 |
| CI 実行時間増加 | 低 | オーバーヘッド 5-15%、現在 ~2.5 秒なので影響 <0.5 秒 |
| compat ジョブ干渉 | なし | addopts のレポート表示のみ。閾値は test ジョブのみ |
| uv.lock 競合 | 低 | `uv lock` で再生成すれば解決 |

## Acceptance Criteria チェックリスト

| # | 基準 | 対応ステップ | 確認方法 |
|---|------|-------------|---------|
| AC1 | カバレッジレポートが生成される | Step 2, 5b | ローカル pytest 実行でテーブル表示 |
| AC2 | CI が 80% 未満で失敗する | Step 3 | ci.yml の `--cov-fail-under` 指定 |
| AC3 | ローカルでは閾値なし | Step 2 | addopts に閾値を含めない設計 |
| AC4 | uv.lock 更新済み | Step 4 | `grep "pytest-cov" uv.lock` |

## ロールバック手順

### 完全ロールバック
```bash
git revert HEAD
uv lock && uv sync --no-editable --extra dev
```

### 部分ロールバック (CI ゲートのみ無効化)
ci.yml の `--cov-fail-under=80` を削除するだけで即座に回復可能。

## 後続チケットとの関係

| チケット | 関連 |
|---------|------|
| T-008 (CI Python Matrix) | T-002 に依存。カバレッジが各バージョンで生成される |
| T-006 (next_action) | カバレッジ向上に寄与 |
| T-003 (GenomeStorage CM) | 独立。カバレッジ計測で効果が可視化される |
