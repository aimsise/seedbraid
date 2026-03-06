# T-006: Add next_action to Error Raises

| 項目 | 値 |
|------|-----|
| Priority | **P1** |
| Category | CodeQuality |
| Size | M |
| Dependencies | なし |
| 作成日 | 2026-03-07 |

---

## 目的

`container.py` と `codec.py` の全ての `raise` 文に `next_action` パラメータを追加し、ユーザーがエラー発生時に次に取るべきアクションを明確に伝える。CLI の `_print_error()` 関数は既に `next_action` を stderr に出力する仕組みを持っており、エラークラスも `next_action` パラメータを既にサポートしているため、raise 文への引数追加のみが必要。

## 現状分析

### エラーインフラ (既に整備済み)

- `src/helix/errors.py`: 全エラークラス (`HelixError`, `SeedFormatError`, `DecodeError`, `ExternalToolError`) に `next_action: str | None = None` パラメータあり
- `src/helix/cli.py` L651-656: `_print_error()` が `next_action` を `error[CODE]: message` の後に `next_action: <hint>` として表示
- `docs/ERROR_CODES.md`: `next_action: <hint>` の出力フォーマットを規約化済み

### next_action 実装状況

| モジュール | raise 箇所数 | next_action 付与済み | 未付与 |
|-----------|:----------:|:------------------:|:-----:|
| `container.py` | 45 | 0 | **45** |
| `codec.py` | 16 | 0 | **16** |
| `cli.py` | 5 | 5 | 0 |
| `ipfs.py` | 12 | 12 | 0 |
| `pinning.py` | 13 | 13 | 0 |
| `mlhooks.py` | 13 | 13 | 0 |
| `oci.py` | 5 | 5 | 0 |
| `diagnostics.py` | 1 | 1 | 0 |
| **合計** | **110** | **49** | **61** |

**実装対象**: container.py (45 箇所) + codec.py (16 箇所) = **61 箇所**

---

## 変更対象ファイル一覧

### 1. `src/helix/errors.py` -- 定型メッセージ定数の追加

新規追加する定型 next_action 定数:

```python
# -- next_action templates ------------------------------------------
ACTION_VERIFY_SEED = (
    "Verify seed file integrity or regenerate with `helix encode`."
)
ACTION_REGENERATE_SEED = (
    "Regenerate the seed file with `helix encode`."
)
ACTION_REFETCH_SEED = (
    "Re-download or re-transfer the seed file."
)
ACTION_UPGRADE_HELIX = (
    "Upgrade Helix to the latest version."
)
ACTION_VERIFY_ENCRYPTION = (
    "Verify encryption key/password is correct."
)
ACTION_PROVIDE_ENCRYPTION_KEY = (
    "Provide --encryption-key or set HELIX_ENCRYPTION_KEY."
)
ACTION_INSTALL_ZSTD = (
    "Run `uv sync --extra zstd` to install zstandard."
)
ACTION_CHECK_OPTIONS = (
    "Check command-line options and retry."
)
ACTION_REPORT_BUG = (
    "This is likely a bug. Please report it."
)
ACTION_CHECK_GENOME = (
    "Check genome database, or run `helix prime` to rebuild."
)
ACTION_VERIFY_SNAPSHOT = (
    "Verify the snapshot file or regenerate with `helix genome-snapshot`."
)
ACTION_VERIFY_GENES_PACK = (
    "Verify the genes pack file or regenerate with `helix export-genes`."
)
ACTION_CHECK_DISK = (
    "Check directory permissions and available disk space."
)
ACTION_ENABLE_LEARN_OR_PORTABLE = (
    "Enable --learn or --portable for unknown chunks."
)
```

### 2. `src/helix/container.py` -- 45 箇所の raise 文に next_action 追加

カテゴリ別の next_action マッピング:

| カテゴリ | 対象行 | next_action 定数 |
|---------|--------|-----------------|
| zstd 未インストール | L73, L89 | `ACTION_INSTALL_ZSTD` |
| 未サポート圧縮形式 | L77, L93, L521 | `ACTION_REGENERATE_SEED` |
| レシピエンコード不正 (内部) | L101 | `ACTION_REPORT_BUG` |
| レシピデコード破損 | L113, L119, L126, L136 | `ACTION_VERIFY_SEED` |
| 不明オペコード/インデックス超過 | L130, L132 | `ACTION_REGENERATE_SEED` |
| RAW セクション破損 | L151, L157, L161, L165 | `ACTION_VERIFY_SEED` |
| 暗号化エンベロープ破損 | L221, L226, L233 | `ACTION_REFETCH_SEED` |
| 暗号化バージョン未サポート | L228 | `ACTION_UPGRADE_HELIX` |
| 復号認証失敗 | L292 | `ACTION_VERIFY_ENCRYPTION` |
| 暗号鍵未提供 | L565 | `ACTION_PROVIDE_ENCRYPTION_KEY` |
| シリアライズ圧縮不正 | L308 | `ACTION_CHECK_OPTIONS` |
| シード短すぎ/破損 | L375, L394, L398, L417 | `ACTION_REFETCH_SEED` |
| マジック不一致 | L379 | `ACTION_VERIFY_SEED` |
| バージョン未サポート | L381 | `ACTION_UPGRADE_HELIX` |
| 必須セクション欠落 | L424 | `ACTION_REGENERATE_SEED` |
| 整合性 JSON 不正 | L429 | `ACTION_REGENERATE_SEED` |
| 整合性セクション位置不明 | L432 | `ACTION_REGENERATE_SEED` |
| 署名セクション順序不正 | L437 | `ACTION_REGENERATE_SEED` |
| CRC32/SHA-256 不一致 (8 箇所) | L454-514 | `ACTION_REFETCH_SEED` |
| マニフェスト空 | L517 | `ACTION_REGENERATE_SEED` |
| マニフェスト JSON 不正 | L530 | `ACTION_REGENERATE_SEED` |
| 署名セクション JSON 不正 | L544 | `ACTION_REGENERATE_SEED` |
| 署名セクション位置不明 | L548 | `ACTION_REGENERATE_SEED` |

### 3. `src/helix/codec.py` -- 16 箇所の raise 文に next_action 追加

| 対象行 | エラークラス | next_action 定数 |
|--------|------------|-----------------|
| L124 | `HelixError` | `ACTION_ENABLE_LEARN_OR_PORTABLE` |
| L195 | `DecodeError` | `ACTION_REGENERATE_SEED` |
| L205 | `DecodeError` | `ACTION_CHECK_GENOME` |
| L213 | `DecodeError` | `ACTION_CHECK_GENOME` |
| L244 | `DecodeError` | `ACTION_REFETCH_SEED` |
| L471 | `HelixError` | `ACTION_CHECK_DISK` |
| L495 | `HelixError` | `ACTION_VERIFY_SNAPSHOT` |
| L501 | `HelixError` | `ACTION_VERIFY_SNAPSHOT` |
| L506 | `HelixError` | `ACTION_UPGRADE_HELIX` |
| L517 | `HelixError` | `ACTION_VERIFY_SNAPSHOT` |
| L525 | `HelixError` | `ACTION_VERIFY_SNAPSHOT` |
| L537 | `HelixError` | `ACTION_VERIFY_SNAPSHOT` |
| L542 | `HelixError` | `ACTION_CHECK_DISK` |
| L599 | `HelixError` | `ACTION_VERIFY_GENES_PACK` |
| L604 | `HelixError` | `ACTION_VERIFY_GENES_PACK` |
| L608 | `HelixError` | `ACTION_VERIFY_GENES_PACK` |

### 4. テストファイル -- next_action 検証テスト追加

| ファイル | 変更内容 |
|---------|---------|
| `tests/test_container.py` | 代表的な SeedFormatError の `next_action` 属性をアサート (3-5 件) |
| `tests/test_codec.py` (既存拡張) | 代表的な DecodeError/HelixError の `next_action` 属性をアサート (2-3 件) |

---

## 実装ステップ

### Step 1: errors.py に定型メッセージ定数を追加

`src/helix/errors.py` の末尾に `ACTION_*` 定数を追加する。

- 変更量: ~40 行追加
- リスク: なし (新規定数のみ)

### Step 2: container.py の全 raise 文に next_action を追加

45 箇所の `raise SeedFormatError(...)` に `next_action=ACTION_*` を付与する。

- 変更パターン例 (単行 raise):
  ```python
  # Before
  raise SeedFormatError("Recipe section too short.")
  # After
  raise SeedFormatError(
      "Recipe section too short.",
      next_action=ACTION_VERIFY_SEED,
  )
  ```

- 変更パターン例 (複数行 raise):
  ```python
  # Before
  raise SeedFormatError(
      "Manifest CRC32 mismatch;"
      " seed may be corrupted or tampered."
  )
  # After
  raise SeedFormatError(
      "Manifest CRC32 mismatch;"
      " seed may be corrupted or tampered.",
      next_action=ACTION_REFETCH_SEED,
  )
  ```

- `from .errors import SeedFormatError` を拡張して定数をインポート:
  ```python
  from .errors import (
      SeedFormatError,
      ACTION_VERIFY_SEED,
      ACTION_REGENERATE_SEED,
      ACTION_REFETCH_SEED,
      ACTION_UPGRADE_HELIX,
      ACTION_VERIFY_ENCRYPTION,
      ACTION_PROVIDE_ENCRYPTION_KEY,
      ACTION_INSTALL_ZSTD,
      ACTION_CHECK_OPTIONS,
      ACTION_REPORT_BUG,
  )
  ```

- 変更量: ~90 行変更 (import + 45 raise 文)
- リスク: 低 (メッセージ文字列は変更しない)

### Step 3: codec.py の全 raise 文に next_action を追加

16 箇所の `raise DecodeError(...)` / `raise HelixError(...)` に `next_action=ACTION_*` を付与する。

- `from .errors import DecodeError, HelixError` を拡張して定数をインポート:
  ```python
  from .errors import (
      DecodeError,
      HelixError,
      ACTION_CHECK_DISK,
      ACTION_CHECK_GENOME,
      ACTION_ENABLE_LEARN_OR_PORTABLE,
      ACTION_REFETCH_SEED,
      ACTION_REGENERATE_SEED,
      ACTION_UPGRADE_HELIX,
      ACTION_VERIFY_GENES_PACK,
      ACTION_VERIFY_SNAPSHOT,
  )
  ```

- 変更量: ~35 行変更 (import + 16 raise 文)
- リスク: 低 (メッセージ文字列は変更しない)

### Step 4: テスト実行 + lint 確認

```bash
# テスト実行
PYTHONPATH=src uv run --no-editable python -m pytest

# リント確認
UV_CACHE_DIR=.uv-cache uv run --no-editable ruff check .
```

- 既存テストは `match=` パターンでメッセージの部分一致をチェックしており、`next_action` は別属性なので影響なし

### Step 5: next_action 検証テストの追加

代表的なエラーパスで `next_action` 属性が正しく設定されていることをアサートするテストを追加。

`tests/test_container.py` に追加するテスト例:

```python
def test_seed_format_error_has_next_action():
    """SeedFormatError includes next_action for truncated seed."""
    with pytest.raises(SeedFormatError) as exc_info:
        parse_seed(b"short")
    assert exc_info.value.next_action is not None
    assert "seed" in exc_info.value.next_action.lower()
```

`tests/test_codec.py` (または既存テストファイル) に追加するテスト例:

```python
def test_decode_error_has_next_action_for_missing_chunk():
    """DecodeError includes next_action for missing chunk."""
    # ... setup ...
    with pytest.raises(DecodeError) as exc_info:
        _resolve_chunk(op, hash_table, {}, mock_genome)
    assert exc_info.value.next_action is not None
```

- 変更量: ~30 行追加
- 追加テスト数: 5-8 件

### Step 6: 最終テスト + lint 実行

```bash
PYTHONPATH=src uv run --no-editable python -m pytest
UV_CACHE_DIR=.uv-cache uv run --no-editable ruff check .
```

---

## テスト戦略

### 既存テストへの影響

- **影響なし**: `next_action` はメッセージ本体 (`str(exception)`) とは別の属性。`pytest.raises(match=...)` は `str(exception)` のみをチェックするため、既存テストは全てそのまま通過する。

### 新規テストの方針

1. **代表パターン検証**: 各カテゴリ (フォーマット破損 / 暗号化 / バージョン未サポート / 圧縮 / ゲノム) から 1-2 件ずつ代表的なエラーパスを選択し、`next_action` が `None` ではないことを確認
2. **定数一致検証**: 特定のエラーパスで期待する `ACTION_*` 定数が使われていることを確認
3. **CLI 出力検証**: 既存の `test_cli_commands.py` で `next_action:` が stderr に含まれることを確認 (既存テスト `test_error_output_includes_code_and_next_action` が存在するが、container/codec 起源のエラーパスも追加)

### テスト対象の選定

| テスト | 対象エラー | 検証内容 |
|--------|----------|---------|
| container: 短すぎるシード | `parse_seed(b"short")` | `next_action == ACTION_REFETCH_SEED` |
| container: マジック不一致 | `parse_seed(b"XXXX" + ...)` | `next_action == ACTION_VERIFY_SEED` |
| container: 暗号化認証失敗 | `decrypt_seed_bytes(blob, "wrong")` | `next_action == ACTION_VERIFY_ENCRYPTION` |
| container: zstd 未インストール | mock で ImportError を発生 | `next_action == ACTION_INSTALL_ZSTD` |
| codec: 不明チャンクエラー | `--no-learn --no-portable` 時 | `next_action == ACTION_ENABLE_LEARN_OR_PORTABLE` |
| codec: 遺伝子パック不正 | `import_genes(bad_pack, ...)` | `next_action == ACTION_VERIFY_GENES_PACK` |

---

## リスクと注意点

### リスク低

1. **メッセージ文字列は変更しない**: `str(exception)` は変更されないため、既存テストの `match=` パターンに影響なし
2. **後方互換性**: `next_action` はオプショナルパラメータ (デフォルト `None`) であり、エラークラスのインタフェースに変更なし
3. **振る舞い変更なし**: raise されるエラーの種類やタイミングは変わらない

### 注意点

1. **ruff line-length=79**: `next_action=ACTION_*` を追加すると行が長くなる場合がある。既に複数行の raise 文は問題ないが、単行 raise 文は複数行に展開が必要
2. **import 文の肥大化**: `container.py` では最大 10 個程度の定数をインポートする。読みやすさを維持するため括弧付きインポートで整理する
3. **英語メッセージ**: `next_action` のメッセージは全て英語で統一する (CLI 出力向けであるため)
4. **T-012 との連携**: T-012 (Long Function Decomposition) は T-006 の完了を前提としている。関数分割時に `next_action` が既に付与されていることが重要

---

## 完了基準

1. `container.py` の全 45 箇所の `raise SeedFormatError(...)` に `next_action` 引数が付与されている
2. `codec.py` の全 16 箇所の `raise DecodeError(...)` / `raise HelixError(...)` に `next_action` 引数が付与されている
3. `errors.py` に `ACTION_*` 定型メッセージ定数が定義されている
4. `next_action` はカテゴリ別の定型メッセージを使用しており、一貫性がある
5. 全既存テストパス (振る舞い変更なし)
6. `next_action` 属性を検証する新規テストが 5 件以上追加されている
7. `ruff check` パス
8. `pytest` 全テストパス

---

## 変更量の見積もり

| ファイル | 追加行 | 変更行 | 削除行 |
|---------|:-----:|:-----:|:-----:|
| `src/helix/errors.py` | ~40 | 0 | 0 |
| `src/helix/container.py` | ~60 | ~45 | 0 |
| `src/helix/codec.py` | ~25 | ~16 | 0 |
| `tests/test_container.py` | ~25 | 0 | 0 |
| `tests/test_codec.py` | ~15 | 0 | 0 |
| **合計** | **~165** | **~61** | **0** |

---

### Claude Code Workflow

カテゴリ: **CodeQuality** / サイズ: **M**

パターン: `/investigate` -> `/plan` or `/refactor` -> `/test` -> `/review` -> `/commit`

| Phase | Command / Agent | 目的 |
|-------|----------------|------|
| 1. 調査 | `/investigate` | raise 文の現状把握 (完了: `docs/research/T-006_investigation.md`) |
| 2. 計画 | `/plan` | 実装計画の策定 (本ドキュメント) |
| 3. 実装 Phase A | 直接実装 | `errors.py` に ACTION_* 定数追加 |
| 4. 実装 Phase B | 直接実装 | `container.py` の 45 箇所に next_action 追加 |
| 5. 実装 Phase C | 直接実装 | `codec.py` の 16 箇所に next_action 追加 |
| 6. テスト | `/test` | 既存テスト確認 + next_action 検証テスト追加 |
| 7. レビュー | `/review` | メッセージの一貫性・全箇所カバー確認 |
| 8. コミット | `/commit` | `improve: add next_action to all error raises in container/codec (T-006)` |

**実行例**:
```
/investigate "error raises" (完了)
  -> /plan (本ドキュメント)
  -> /clear
  -> (errors.py 定数追加)
  -> (container.py 45箇所更新)
  -> (codec.py 16箇所更新)
  -> /test
  -> /review
  -> /commit
```
