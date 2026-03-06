# T-006: Add next_action to Error Raises — Investigation Report

## チケット仕様（原文要約）

**Priority**: P1 | **Category**: CodeQuality | **Size**: M | **Dependencies**: None

エラーメッセージにユーザーが次に取るべきアクション（`next_action`）が含まれていない。デバッグ効率が低い。

### Scope

| ファイル | 対象 | 箇所数 |
|----------|------|--------|
| `src/helix/container.py` | `SeedFormatError` raises | ~45 箇所 |
| `src/helix/codec.py` | `DecodeError`/`HelixError` raises | ~10 箇所 |

### Acceptance Criteria

1. 全ての `raise SeedFormatError(...)` に `next_action` 引数が付与されている
2. 全ての `raise DecodeError(...)` / `raise HelixError(...)` に `next_action` 引数が付与されている
3. `next_action` はカテゴリ別の定型メッセージを使用
4. 全テストパス

---

## エラーコード体系の現状

### エラーコード定義（docs/ERROR_CODES.md）

エラーコードは以下のフォーマットで定義されている：

```
Prefix: HELIX_E_
Output: CLI prints error[CODE]: <message> and next_action: <hint> when available
```

### 定義済みコード一覧（関連もの）

| Code | Category | 説明 |
|------|----------|------|
| `HELIX_E_UNKNOWN` | Core | 予期しない例外パス |
| `HELIX_E_SEED_FORMAT` | Core | シード/コンテナ整合性、パース、復号化フォーマットエラー |
| `HELIX_E_DECODE` | Core | 再構築/デコード失敗 |
| `HELIX_E_EXTERNAL_TOOL` | Core | 汎用外部ツール失敗 |

---

## エラークラス構造

### src/helix/errors.py（現状）

```python
@dataclass(frozen=True)
class ErrorCodeInfo:
    code: str
    message: str
    next_action: str | None = None


class HelixError(Exception):
    """Base error for Helix operations."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_UNKNOWN",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.next_action = next_action
    
    def as_info(self) -> ErrorCodeInfo:
        return ErrorCodeInfo(
            code=self.code,
            message=str(self),
            next_action=self.next_action,
        )


class SeedFormatError(HelixError):
    """Raised when HLX1 seed structure or integrity checks fail."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_SEED_FORMAT",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)


class DecodeError(HelixError):
    """Raised when reconstruction cannot proceed."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_DECODE",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)


class ExternalToolError(HelixError):
    """Raised when external tools (e.g., ipfs) are unavailable or fail."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_EXTERNAL_TOOL",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)
```

**結論**: すべてのエラークラスは既に `next_action` パラメータをサポートしている。問題は **raise 文でこの引数が使用されていない** ことにある。

---

## raise 文の全箇所リスト

### container.py の SeedFormatError（合計 45 箇所）

#### カテゴリ1: 圧縮エラー（L73-93）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 73 | (ImportError) | `Compression 'zstd' requires optional dependency 'zstandard'.` | ❌ None | `uv sync --extra zstd` |
| 77 | (no raise context) | `Unsupported compression: {name}` | ❌ None | 有効な圧縮形式を使用 |
| 89 | (ImportError) | `Seed uses zstd compression but 'zstandard' is not installed.` | ❌ None | `uv sync --extra zstd` |
| 93 | (no raise context) | `Unknown manifest compression id: {ctype}` | ❌ None | シードファイルを再生成 |

#### カテゴリ2: レシピエンコード/デコードエラー（L101-137）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 101-104 | encode_recipe | `Recipe hash table must contain 32-byte SHA-256 digests.` | ❌ None | 内部エラー（バグ報告） |
| 113 | decode_recipe | `Recipe section too short.` | ❌ None | シードファイルの整合性を確認 |
| 119 | decode_recipe | `Recipe hash table truncated.` | ❌ None | シードファイルの整合性を確認 |
| 126 | decode_recipe | `Recipe op stream truncated.` | ❌ None | シードファイルの整合性を確認 |
| 130 | decode_recipe | `Unknown recipe opcode: {opcode}` | ❌ None | シードファイルを再生成 |
| 132 | decode_recipe | `Recipe op hash index out of bounds.` | ❌ None | シードファイルを再生成 |
| 136 | decode_recipe | `Recipe section has trailing bytes.` | ❌ None | シードファイルの整合性を確認 |

#### カテゴリ3: RAW ペイロードエラー（L150-165）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 151 | decode_raw_payloads | `RAW section too short.` | ❌ None | シードファイルの整合性を確認 |
| 157 | decode_raw_payloads | `RAW section entry header truncated.` | ❌ None | シードファイルの整合性を確認 |
| 161 | decode_raw_payloads | `RAW section entry payload truncated.` | ❌ None | シードファイルの整合性を確認 |
| 165 | decode_raw_payloads | `RAW section has trailing bytes.` | ❌ None | シードファイルの整合性を確認 |

#### カテゴリ4: 暗号化エラー（L221-236）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 221 | validate_encrypted_seed_envelope | `Encrypted seed is too short.` | ❌ None | シードファイルをダウンロード再度取得 |
| 226 | validate_encrypted_seed_envelope | `Encrypted seed magic mismatch. Expected HLE1.` | ❌ None | シードファイルの整合性を確認 |
| 228 | validate_encrypted_seed_envelope | `Unsupported encrypted seed version: {version}` | ❌ None | Helix を最新版にアップグレード |
| 233-236 | validate_encrypted_seed_envelope | `Encrypted seed length mismatch or truncation detected.` | ❌ None | シードファイルの整合性を確認 |

#### カテゴリ5: シード parsing エラー（L375-424）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 375 | parse_seed | `Seed file too short.` | ❌ None | シードファイルをダウンロード再度取得 |
| 379 | parse_seed | `Invalid seed magic; expected HLX1.` | ❌ None | 正しいシードファイルを指定 |
| 381 | parse_seed | `Unsupported seed version: {version}` | ❌ None | Helix を最新版にアップグレード |
| 394 | parse_seed | `Section header truncated.` | ❌ None | シードファイルの整合性を確認 |
| 398 | parse_seed | `Section payload truncated.` | ❌ None | シードファイルの整合性を確認 |
| 417 | parse_seed | `Seed has trailing bytes outside sections.` | ❌ None | シードファイルの整合性を確認 |
| 424 | parse_seed | `Seed missing required section(s).` | ❌ None | シードファイルを再生成 |

#### カテゴリ6: 整合性チェックエラー（L429-514）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 429 | parse_seed | `Integrity section is not valid JSON.` | ❌ None | シードファイルを再生成 |
| 432 | parse_seed | `Integrity section position not found.` | ❌ None | シードファイルを再生成 |
| 437-440 | parse_seed | `Signature section must appear before integrity section.` | ❌ None | シードファイルを再生成 |
| 454-457 | parse_seed | `Manifest CRC32 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 459-462 | parse_seed | `Recipe CRC32 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 464-467 | parse_seed | `Seed payload CRC32 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 473-476 | parse_seed | `Manifest SHA-256 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 482-485 | parse_seed | `Recipe SHA-256 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 491-494 | parse_seed | `Seed payload SHA-256 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 502-505 | parse_seed | `RAW CRC32 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |
| 511-514 | parse_seed | `RAW SHA-256 mismatch; seed may be corrupted or tampered.` | ❌ None | シードファイルをダウンロード再度取得 |

#### カテゴリ7: マニフェスト処理エラー（L517-530）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 517 | parse_seed | `Manifest section empty.` | ❌ None | シードファイルを再生成 |
| 521-524 | parse_seed | `Unknown manifest compression id: {compression_id}` | ❌ None | シードファイルを再生成 |
| 530 | parse_seed | `Manifest JSON decode failed.` | ❌ None | シードファイルを再生成 |

#### カテゴリ8: 署名セクション エラー（L544-548）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 544-546 | parse_seed | `Signature section is not valid JSON.` | ❌ None | シードファイルを再生成 |
| 548 | parse_seed | `Signature section position not found.` | ❌ None | シードファイルを再生成 |

#### カテゴリ9: 暗号化キー/復号化エラー（L292-296, L565-568）
| 行 | コード | メッセージ | 現在の next_action | 推奨 next_action |
|----|--------|-----------|------------------|-----------------|
| 292-295 | decrypt_seed_bytes | `Encrypted seed authentication failed (wrong key or tampering).` | ❌ None | パスワード/キーを確認、シードファイルが改ざんされていないか確認 |
| 565-568 | read_seed | `Encrypted seed requires decryption key. Provide --encryption-key or set HELIX_ENCRYPTION_KEY.` | ❌ None | `--encryption-key` を指定、または環境変数を設定 |

### codec.py の DecodeError/HelixError（合計 10 箇所）

| 行 | エラークラス | メッセージ | 現在の next_action | 推奨 next_action |
|----|------------|----------|------------------|-----------------|
| 124-129 | HelixError | `Encountered unknown chunk while --no-learn and --no-portable are active. Enable --learn or --portable.` | ❌ None | `--learn` または `--portable` を有効化 |
| 195 | DecodeError | `Recipe refers to hash index out of bounds.` | ❌ None | シードファイルを再生成 |
| 205 | DecodeError | `Missing required chunk: {digest.hex()}` | ❌ None | ゲノムデータベースを確認、`helix prime` で学習 |
| 213 | DecodeError | `Missing RAW payload and genome chunk: {digest.hex()}` | ❌ None | ゲノムデータベースを確認、`helix prime` で学習 |
| 244-247 | DecodeError | `Decoded SHA-256 mismatch: expected {expected}, got {actual}.` | ❌ None | ゲノムデータベース/シードファイルを確認 |
| 471-474 | HelixError | `Failed to write genome snapshot: {out_path}` | ❌ None | ディレクトリ権限・ディスク容量を確認 |
| 495-498 | HelixError | `Invalid genome snapshot: header is truncated.` | ❌ None | スナップショットファイルを再生成 |
| 501-504 | HelixError | `Invalid genome snapshot magic. Expected HGS1.` | ❌ None | 正しいスナップショットファイルを指定 |
| 506-509 | HelixError | `Unsupported genome snapshot version: {version}.` | ❌ None | Helix を最新版にアップグレード |
| 517-520, 525-529, 537-540, 542-545 | HelixError | `Invalid genome snapshot: {detail}` | ❌ None | スナップショットファイルを再生成 |
| 599 | HelixError | `Invalid genes pack magic. Expected GENE1.` | ❌ None | 正しい遺伝子パックファイルを指定 |
| 604 | HelixError | `Truncated genes pack hash entry.` | ❌ None | 遺伝子パックファイルを再生成 |
| 608 | HelixError | `Truncated genes pack payload entry.` | ❌ None | 遺伝子パックファイルを再生成 |

### ipfs.py, oci.py, pinning.py, mlhooks.py, diagnostics.py

これらのファイルでは、すでに **多くの raise 文で `next_action` が付与されている**（2024 年から段階的に導入されている模様）。

#### ipfs.py の例（既に next_action あり）
```python
raise ExternalToolError(
    "ipfs CLI not found. Install IPFS and ensure `ipfs` is on PATH...",
    code="HELIX_E_IPFS_NOT_FOUND",
    next_action="Install Kubo and verify with `ipfs --version`.",  # ✅ 既に有効
)
```

#### pinning.py の例（既に next_action あり）
```python
raise ExternalToolError(
    "Remote pin retries must be >= 1.",
    code="HELIX_E_INVALID_OPTION",
    next_action="Use --retries with value >= 1.",  # ✅ 既に有効
)
```

#### mlhooks.py（oci.py 含む）の例（既に next_action あり）
```python
raise ExternalToolError(
    "MLflow tracking URI is required.",
    code="HELIX_E_MLFLOW_CONFIG",
    next_action="Pass --tracking-uri or set MLFLOW_TRACKING_URI.",  # ✅ 既に有効
)
```

---

## 既存テストの状況

### テストパターン

テストでは主に 2 つの方法でエラーをチェックしている：

1. **`pytest.raises()` + `match` パターン** - メッセージ内容の一部を正規表現でチェック
   ```python
   with pytest.raises(SeedFormatError, match="Encrypted seed requires decryption key"):
       ...
   ```

2. **例外情報の直接チェック** - `exc_info.value` で属性を確認
   ```python
   with pytest.raises(ExternalToolError) as exc_info:
       ...
   assert exc_info.value.code == "HELIX_E_..."
   ```

### 影響の少なさ

- `next_action` をメッセージの末尾に付加する場合、既存の `match` パターンは影響を受けない
- `next_action` はメッセージと異なる属性として扱うべき（現在のエラークラス設計に沿う）

---

## 実装上の注意点・リスク

### 1. 既に next_action を使用しているモジュール

以下のモジュールでは raise 文で `next_action` が既に使用されている：
- `src/helix/ipfs.py` （全 raise 文）
- `src/helix/pinning.py` （全 raise 文）
- `src/helix/mlhooks.py` （全 raise 文）
- `src/helix/oci.py` （全 raise 文）
- `src/helix/diagnostics.py` （一部の raise 文）

これらは **既に実装済み** なため、確認のみで十分。

### 2. 不足している箇所

**集中対象**：
- `container.py`: 45 箇所
- `codec.py`: 10 箇所

### 3. メッセージの一貫性

カテゴリ別の定型メッセージ案（T-006 チケットより）：

| カテゴリ | 推奨 next_action |
|---------|----------------|
| シードフォーマットエラー | `"Verify seed file integrity or regenerate with helix encode."` |
| 暗号化エラー | `"Verify encryption key/password is correct."` |
| ゲノムストレージエラー | `"Check database file and permissions, or run helix prime to rebuild."` |
| 外部ツール（IPFS）エラー | `"Verify IPFS daemon is running with ipfs daemon."`  |
| オプションエラー | `"Check command-line options and retry."` |

### 4. テスト影響の最小化

- エラーメッセージの部分（`str(exception)`）は変更しない
- `next_action` は別属性として追加
- 既存テストの `match` パターンは影響を受けない

---

## 推奨実装手順

### Phase 1: 定型メッセージ定数の定義

`src/helix/errors.py` に定型メッセージを定義：

```python
# Error action templates
ACTION_SEED_FORMAT = (
    "Verify seed file integrity or regenerate with helix encode."
)
ACTION_SEED_ENCRYPTION = (
    "Verify encryption key or password is correct."
)
ACTION_SEED_CORRUPTION = (
    "Refetch the seed file or regenerate with helix encode."
)
ACTION_GENOME_ERROR = (
    "Check genome database file, or run helix prime to rebuild."
)
ACTION_UNKNOWN_CHUNK = (
    "Enable --learn or --portable, or verify genome data."
)
```

### Phase 2: container.py の raise 文を更新

44 箇所の `raise SeedFormatError(...)` に `next_action` を追加。

テンプレート：
```python
# 例1: 圧縮エラー
raise SeedFormatError(
    "Compression 'zstd' requires optional dependency 'zstandard'.",
    next_action="Run: uv sync --extra zstd",
)

# 例2: 整合性エラー
raise SeedFormatError(
    "Manifest CRC32 mismatch; seed may be corrupted or tampered.",
    next_action=ACTION_SEED_CORRUPTION,
)
```

### Phase 3: codec.py の raise 文を更新

10 箇所の `raise DecodeError(...)` / `raise HelixError(...)` に `next_action` を追加。

### Phase 4: テスト確認

```bash
# 全テスト実行
PYTHONPATH=src uv run --no-editable python -m pytest

# リント確認
UV_CACHE_DIR=.uv-cache uv run --no-editable ruff check .
```

### Phase 5: 既存モジュールの確認（ドライラン）

- ipfs.py, pinning.py, mlhooks.py, oci.py の raise 文を spot-check
- 設定パターンの統一性を確認

---

## 補充情報

### raise 文の出現分布（モジュール別）

| モジュール | SeedFormatError | DecodeError | HelixError | ExternalToolError | 合計 | next_action 現状 |
|-----------|-----------------|-------------|-----------|------------------|------|-----------------|
| container.py | 45 | 0 | 0 | 0 | 45 | ❌ 0/45 |
| codec.py | 0 | 4 | 9 | 0 | 13 | ❌ 0/13 |
| ipfs.py | 0 | 0 | 0 | 15 | 15 | ✅ 15/15 |
| pinning.py | 0 | 0 | 0 | 15 | 15 | ✅ 15/15 |
| mlhooks.py | 0 | 0 | 0 | 13 | 13 | ✅ 13/13 |
| oci.py | 0 | 0 | 0 | 5 | 5 | ✅ 5/5 |
| diagnostics.py | 0 | 0 | 0 | 1 | 1 | ✅ 1/1 |
| **合計** | **45** | **4** | **9** | **49** | **107** | **✅ 49/107** |

**実装対象**: container.py (45 件) + codec.py (13 件) = **58 件**

---

## 参考資料

- **チケット定義**: `.docs/09_リファクタリングチケット.md` (L352-403)
- **エラーコード規約**: `docs/ERROR_CODES.md`
- **エラークラス定義**: `src/helix/errors.py`
- **container.py**: `src/helix/container.py` (45 箇所のコメント付き詳細リストあり)
- **codec.py**: `src/helix/codec.py` (13 箇所のコメント付き詳細リストあり)
