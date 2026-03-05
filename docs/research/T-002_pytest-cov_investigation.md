# T-002: pytest-cov + CI Coverage Gate — 調査レポート

**調査日**: 2026-03-05  
**プロジェクト**: Helix v1.0.0a1  
**スコープ**: テストカバレッジ計測とCI ゲート設定の実装準備

---

## 1. pyproject.toml 現状

### 1.1 現在の dev 依存 (optional-dependencies.dev)

```toml
[project.optional-dependencies]
zstd = ["zstandard>=0.23"]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

**状態**:
- `pytest-cov` 未導入
- 現在は基本的な pytest のみ
- ruff (linter) と pytest が dev の主要依存

### 1.2 pytest 設定 ([tool.pytest.ini_options])

```toml
[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
```

**状態**:
- `-q` オプション: テスト結果を簡潔に出力
- `testpaths`: tests/ ディレクトリのみをスキャン
- カバレッジ設定なし

### 1.3 setuptools 設定

```toml
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.dynamic]
version = {attr = "helix.__version__"}
```

**重要**: src/ レイアウトを使用しており、`PYTHONPATH=src` による動的なパス解決が必須。

### 1.4 uv.lock の現状

- pytest 9.0.2 がロック済み
- pytest-cov は未ロック
- `uv sync --extra dev` 実行後に pytest-cov がインストールされる予定

---

## 2. CI ワークフロー現状 (.github/workflows/ci.yml)

### 2.1 全体構造

4つのジョブが並行実行:

| ジョブ | 目的 | テスト対象 |
|-------|------|----------|
| **lint** | コード品質チェック | ruff check . |
| **test** | ユニット/統合テスト | 61個の pytest テスト |
| **compat** | 互換性チェック | test_compat_fixtures.py のみ |
| **bench-gate** | パフォーマンス閾値 | scripts/bench_gate.py |

### 2.2 test ジョブの詳細

**現在のコマンド**:
```bash
PYTHONPATH=src uv run --no-sync --no-editable python -m pytest
```

**フロー**:
```yaml
- name: Checkout
  uses: actions/checkout@v4
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: Setup uv
  uses: astral-sh/setup-uv@v5
- name: Install dependencies
  run: uv sync --no-editable --extra dev
- name: Pytest
  run: PYTHONPATH=src uv run --no-sync --no-editable python -m pytest
```

**重要ポイント**:
- `uv sync --no-editable --extra dev`: editable install なし
- `PYTHONPATH=src`: src/ レイアウトの動的パス解決
- `--no-sync`: 既にインストール済みなのでスキップ
- `--no-editable`: setup.py 実行しない

### 2.3 他のジョブとの関係

- **compat**: test ジョブとは独立実行（別途 pytest 呼び出し）
- **bench-gate**: Python スクリプト実行 (pytest 非使用)
- **lint**: test とは無関係

---

## 3. テスト構成

### 3.1 テストファイル一覧

**合計**: 22個のテストファイル, 61個のテスト関数, 1,768 LOC

| ファイル | LOC | テスト数 | 対象モジュール |
|---------|-----|---------|--------------|
| test_remote_pinning.py | 171 | 5 | pinning.py, ipfs.py |
| test_oci_oras_bridge.py | 170 | 9 | oci.py, mlhooks.py |
| test_ml_hooks.py | 164 | 6 | mlhooks.py |
| test_dvc_bridge.py | 155 | 6 | mlhooks.py |
| test_ipfs_reliability.py | 151 | 4 | ipfs.py |
| test_container.py | 97 | 2 | container.py |
| test_genome_snapshot.py | 91 | 2 | storage.py, codec.py |
| test_doctor.py | 90 | 4 | diagnostics.py |
| test_signature.py | 79 | 2 | container.py |
| test_encryption.py | 69 | 2 | codec.py, container.py |
| test_perf_gates.py | 62 | 2 | perf.py |
| test_ipfs_fetch_validation.py | 60 | 2 | ipfs.py |
| test_compat_fixtures.py | 58 | 2 | codec.py, container.py |
| test_keygen_cli.py | 56 | 4 | cli.py |
| test_verify_strict.py | 49 | 1 | codec.py |
| test_ipfs_optional.py | 46 | 1 | ipfs.py, codec.py |
| test_manifest_private.py | 40 | 1 | container.py |
| test_genes_pack.py | 39 | 1 | storage.py |
| test_prime_verify.py | 34 | 1 | codec.py |
| test_publish_warning.py | 33 | 2 | ipfs.py |
| test_roundtrip.py | 31 | 1 | codec.py, chunking.py |
| test_chunking.py | 23 | 2 | chunking.py |

### 3.2 conftest.py

**状態**: 存在しない

現在はグローバルな pytest fixture がない。各テストが必要なフィクスチャを局所定義。

**例**: test_ipfs_optional.py では `pytest.MonkeyPatch` を引数で受け取る。

### 3.3 テスト実行方法

**ローカル開発**:
```bash
PYTHONPATH=src UV_CACHE_DIR=.uv-cache uv run --no-editable python -m pytest
```

**CI**:
```bash
PYTHONPATH=src uv run --no-sync --no-editable python -m pytest
```

**単一テスト実行**:
```bash
PYTHONPATH=src uv run --no-editable python -m pytest tests/test_roundtrip.py
```

**テスト収集確認**:
```bash
PYTHONPATH=src uv run --no-editable python -m pytest --collect-only
```
→ 61個のテストが正常に収集される ✓

### 3.4 スキップマーカーの使用

2つのファイルで条件付きスキップ:
- **test_ipfs_optional.py**: IPFS CLI が未インストール時にスキップ
- **test_publish_warning.py**: 同様

実装例:
```python
def test_publish_fetch_if_ipfs_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("ipfs") is None:
        pytest.skip("ipfs CLI not installed")
```

---

## 4. カバレッジ推定

### 4.1 ソースコード構成

**合計**: 3,333 LOC (src/helix/ 配下の全 *.py)

| モジュール | LOC | 備考 |
|-----------|-----|------|
| cli.py | 591 | CLI コマンド実装 |
| codec.py | 550 | encode/decode ロジック |
| container.py | 529 | HLX1 シード形式パーシング |
| mlhooks.py | 352 | ML インテグレーション (DVC/MLflow/HF) |
| ipfs.py | 277 | IPFS publish/fetch |
| pinning.py | 231 | リモートピニング (Pinata など) |
| diagnostics.py | 183 | doctor コマンド実装 |
| perf.py | 173 | パフォーマンス評価 |
| oci.py | 144 | OCI/ORAS ブリッジ |
| chunking.py | 140 | CDC チャンキング (buzhash/rabin) |
| storage.py | 85 | SQLite genome 管理 |
| errors.py | 71 | エラーコード定義 |
| __main__.py | 4 | CLI エントリポイント |
| __init__.py | 3 | version のみ |

### 4.2 テスト-モジュール マッピング

#### A. よくカバーされているモジュール (推定 >80%)

1. **container.py** (529 LOC)
   - test_container.py (97 LOC, 2テスト): parse/serialize
   - test_signature.py (79 LOC, 2テスト): signature
   - test_manifest_private.py (40 LOC, 1テスト): manifest privacy
   - → カバレッジ: **高い** (3ファイル, 5テスト)

2. **diagnostics.py** (183 LOC)
   - test_doctor.py (90 LOC, 4テスト): doctor CLI 完全
   - → カバレッジ: **高い** (1ファイル, 4テスト)

3. **perf.py** (173 LOC)
   - test_perf_gates.py (62 LOC, 2テスト): benchmark 評価
   - → カバレッジ: **高い** (1ファイル, 2テスト)

4. **ipfs.py** (277 LOC)
   - test_ipfs_optional.py (46 LOC, 1テスト)
   - test_ipfs_fetch_validation.py (60 LOC, 2テスト)
   - test_ipfs_reliability.py (151 LOC, 4テスト)
   - test_remote_pinning.py (171 LOC, 5テスト): pinning 側
   - test_publish_warning.py (33 LOC, 2テスト): publish warning
   - → カバレッジ: **高い** (5ファイル, 14テスト)

5. **oci.py** (144 LOC)
   - test_oci_oras_bridge.py (170 LOC, 9テスト): 完全カバー
   - → カバレッジ: **非常に高い** (1ファイル, 9テスト)

#### B. 中程度のカバレッジ (推定 50-80%)

1. **codec.py** (550 LOC) — 最大級のモジュール
   - test_roundtrip.py (31 LOC, 1テスト): encode_file/decode_file の主流
   - test_compat_fixtures.py (58 LOC, 2テスト): 互換性チェック
   - test_genome_snapshot.py (91 LOC, 2テスト): restore
   - test_encryption.py (69 LOC, 2テスト): 暗号化
   - test_verify_strict.py (49 LOC, 1テスト): verify strict
   - test_prime_verify.py (34 LOC, 1テスト): prime/verify
   - → テスト計 9個だが LOC は少ない
   - → 推定カバレッジ: **60-70%** (エラーパス、エッジケース未カバー)

2. **cli.py** (591 LOC) — 最大級の実装
   - test_keygen_cli.py (56 LOC, 4テスト): keygen のみ
   - その他: doctor/publish/fetch/verify/prime コマンドは散発的
   - → 推定カバレッジ: **30-40%** (CLI コマンドの大半が未テスト)

3. **mlhooks.py** (352 LOC)
   - test_ml_hooks.py (164 LOC, 6テスト): DVC/MLflow/HF
   - test_dvc_bridge.py (155 LOC, 6テスト): DVC 統合
   - → 推定カバレッジ: **70-80%** (統合テスト中心)

#### C. カバレッジ不足 (推定 <50%)

1. **pinning.py** (231 LOC)
   - test_remote_pinning.py (171 LOC, 5テスト)
   - → 複雑なロジック (retry, auth mapping)
   - → 推定カバレッジ: **65%** (うち一部エッジケース未カバー)

2. **chunking.py** (140 LOC)
   - test_chunking.py (23 LOC, 2テスト): determinism のみ
   - roundtrip テストで間接的にカバー
   - → 推定カバレッジ: **60%** (エラーパス未カバー)

3. **storage.py** (85 LOC)
   - test_genome_snapshot.py (91 LOC, 2テスト): restore のみ
   - → 推定カバレッジ: **40-50%** (ほぼ統合テストのみ)

4. **errors.py** (71 LOC)
   - 専用テストファイルなし
   - エラー処理は各モジュールのテストに散在
   - → 推定カバレッジ: **30%** (定義のみ、エラーケース未テスト)

#### D. 非機能的

- **__init__.py** (3 LOC): version 属性のみ
- **__main__.py** (4 LOC): CLI dispatch

### 4.3 推定総カバレッジ

```
加重計算:
- 高カバレッジ (>80%): 1,600+ LOC
- 中カバレッジ (50-80%): 1,300+ LOC
- 低カバレッジ (<50%): 400+ LOC

推定: 65-75%
```

**結論**:
- 80% の達成には **8-10% の追加カバレッジが必要**
- 必要な改善:
  1. CLI コマンドテスト (doctor, publish, fetch, verify, prime)
  2. storage.py ユニットテスト
  3. codec.py のエッジケーステスト
  4. errors.py の例外ケーステスト

---

## 5. リスク と注意点

### 5.1 パス解決リスク (PYTHONPATH=src)

**状態**: SAFE ✓

理由:
- setuptools の `package-dir = {"" = "src"}` により src/ が明示的に指定済み
- PYTHONPATH=src は現在のテスト実行で既に使用中
- pytest-cov は sys.path を参照するため、PYTHONPATH=src が効く
- `--cov=helix` は package name なので、src/helix/ に自動解決

**確認**:
```bash
PYTHONPATH=src uv run --no-editable python -c "import sys; print(sys.path); from helix import __version__; print(__version__)"
```

### 5.2 CI 環境での実行可能性

**状態**: SAFE ✓

確認内容:
1. 全 61 テスト現在実行中: ✓
2. PYTHONPATH=src 設定済み: ✓
3. `uv run --no-editable` でも imports 成功: ✓
4. IPFS テストは gracefully skip: ✓

実行結果:
```
61 tests collected in 0.03s
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . [100%]
```

### 5.3 初期閾値 80% の妥当性

**状況**: AMBITIOUS だが ACHIEVABLE

```
現在推定: 65-75%
目標: 80%

ギャップ: 5-15%

実現方法:
- cli.py テスト追加: +5-10% (doctor, publish, fetch など)
- storage.py ユニットテスト: +2-3%
- codec.py エッジケース: +2-3%
```

**推奨**:
- 初期実装時は 80% に設定
- 目標に達しない場合は 75% に下げて段階的引き上げ
- または T-002 実装と同時に追加テスト (T-005 以降) を組む

### 5.4 依存関係と uv.lock

**確認**:
```
uv.lock に pytest 9.0.2 ロック済み
pytest-cov 追加時:
- pyproject.toml に "pytest-cov>=5.0" を dev に追加
- uv sync --extra dev で自動ロック
- pytest-cov が coverage パッケージも依存でインストール
```

**リスク**: なし (uv が自動管理)

### 5.5 既存ワークフロー互換性

**compat ジョブへの影響**: NONE
- compat ジョブは独立実行: `pytest tests/test_compat_fixtures.py`
- coverage 非使用なので影響なし

**bench-gate ジョブへの影響**: NONE
- Python スクリプト実行なので無関係

**lint ジョブへの影響**: NONE
- pytest-cov は ruff チェック対象外 (dev 依存)

---

## 6. 実装推奨事項

### 6.1 チケット スコープ実装手順

#### Step 1: pyproject.toml 修正

```toml
[project.optional-dependencies]
zstd = ["zstandard>=0.23"]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",  # ← 追加
  "ruff>=0.6",
]
```

#### Step 2: pytest 設定追加

```toml
[tool.pytest.ini_options]
addopts = "-q --cov=helix --cov-report=term-missing"
testpaths = ["tests"]
```

理由:
- `--cov=helix`: src/helix/ 全モジュール計測
- `--cov-report=term-missing`: ターミナルに出力 + 未カバー行表示
- デフォルト で pyproject.toml に設定しておくと、ローカル開発でも自動実行

#### Step 3: CI ワークフロー修正

`.github/workflows/ci.yml` の test ジョブの pytest コマンドに追加:

```yaml
- name: Pytest with coverage gate
  run: PYTHONPATH=src uv run --no-sync --no-editable python -m pytest --cov-fail-under=80
```

**または** addopts に含めずに CI でのみ指定する場合:

```yaml
- name: Pytest
  run: PYTHONPATH=src uv run --no-sync --no-editable python -m pytest --cov-fail-under=80
```

推奨: pyproject.toml に `--cov` は含める、`--cov-fail-under` は CI で指定

#### Step 4: uv.lock 再生成

```bash
uv lock
```

### 6.2 実装の注意点

**注意 1: --cov-fail-under=80 の初期値**
- 初回実行で 80% に達しない可能性あり
- 推定現在値: 65-75%
- オプション A: チケット実装時に +テストコミットも含める
- オプション B: 初回は 70% で設定し、段階的に引き上げ

**注意 2: カバレッジレポート出力場所**
- `--cov-report=term-missing`: コンソール出力のみ
- HTML レポート不要ならこれで OK
- 必要な場合は `--cov-report=html` 追加（gitignored な .htmlcov/ に生成）

**注意 3: IPFS テストのスキップと計測**
- IPFS CLI 未インストール時、テストは pytest.skip で実行をスキップ
- カバレッジは実行されたテストのみ計測
- スキップされたテストのコードはカバレッジに含まれない（これは正常）
- 計測にはハンバーグセ機能をリセットするので影響なし

### 6.3 段階的な追加テスト計画

カバレッジ向上のための優先順位 (T-002 後):

1. **T-006 (P1)**: cli.py テスト拡張
   - doctor, publish, fetch, verify, prime コマンド
   - 期待: +10% (591 LOC → 50 LOC のテスト追加)

2. **T-007 (P1)**: storage.py ユニットテスト
   - genome 操作、hash lookup
   - 期待: +3% (85 LOC → 独立テスト)

3. **T-008 (P2)**: codec.py エッジケース
   - エラーパス、小さいファイル、大きいファイル
   - 期待: +5%

### 6.4 ローカル開発への影響

T-002 実装後、ローカルでのテスト実行:

```bash
# 従来通り（覆蔽率表示が追加）
PYTHONPATH=src UV_CACHE_DIR=.uv-cache uv run --no-editable python -m pytest

# Expected output:
# ========================= test session starts ==========================
# ...
# ========================= coverage report ==========================
# Name                    Stmts   Miss  Cover   Missing
# -------------------------------------------------
# helix/__init__.py           3      0   100%
# helix/__main__.py           4      1    75%   3
# helix/chunking.py         140     45    68%   20-30, 50-60, ...
# ...
# TOTAL                    3333    900    73%
# ========================= 61 passed in 2.45s ==========================
```

カバレッジに問題があれば即座に見える ✓

---

## 7. 検収チェックリスト

T-002 実装完了時の確認項目:

- [ ] pyproject.toml に `pytest-cov>=5.0` を dev に追加
- [ ] pyproject.toml の `[tool.pytest.ini_options]` に `addopts = "--cov=helix --cov-report=term-missing"` を追加
- [ ] .github/workflows/ci.yml の test ジョブの pytest コマンドに `--cov-fail-under=80` を追加
- [ ] uv.lock 再生成 (uv lock コマンド)
- [ ] ローカルで `PYTHONPATH=src uv run --no-editable python -m pytest` 実行して coverage が表示される
- [ ] CI で test ジョブが失敗しないこと (80% 達成、または段階的に下げた値を設定)
- [ ] lint/compat/bench-gate ジョブに影響がないこと
- [ ] CONTRIBUTING.md に coverage 実行方法を追記（オプション）

---

## 8. 関連チケットとの連携

- **T-001** (Version Single Source of Truth): 既完了 ✓
- **T-004** (decrypt_seed_bytes Double scrypt Fix): 既完了 ✓
- **T-002** (pytest-cov + CI Coverage Gate): このチケット ← NOW
- **T-005** (scrypt uplift): T-004 依存解消済み、独立実行可能
- **T-015**, **T-016** (pytest integration): T-002 が基盤提供
- **T-006** (CLI テスト拡張): T-002 後の推奨フォロー

---

## 9. 参考資料

### 文書
- `CONTRIBUTING.md`: 開発ワークフロー
- `CLAUDE.md`: プロジェクト概要
- `docs/FORMAT.md`: バイナリフォーマット仕様
- `docs/DESIGN.md`: アーキテクチャ設計
- `docs/THREAT_MODEL.md`: セキュリティ考慮

### テストファイル
- `tests/test_roundtrip.py`: 基本的なエンコード/デコード
- `tests/test_container.py`: コンテナパーシング
- `tests/test_ipfs_optional.py`: IPFS スキップ実装例

### 外部リソース
- [pytest-cov ドキュメント](https://pytest-cov.readthedocs.io/)
- [coverage.py ドキュメント](https://coverage.readthedocs.io/)

---

**レポート作成**: Claude Code (claude-haiku-4-5-20251001)  
**最終更新**: 2026-03-05
