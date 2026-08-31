# 変更履歴

`mfg-kaizen-skills` リポジトリに収録する全スキルの変更履歴。
形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠する。

バージョンは以下4つを常に一致させる。
`SKILL.md` の `metadata.version` / `.claude-plugin/plugin.json` の `version` / git tag / この履歴

---

## リポジトリ

### [0.1.0] - 2026-09-01
- リポジトリを初期化
- ドメイン単位でのリポジトリ分割方針を決定（製造業改善ドメイン専用とする）
- `.claude-plugin/plugin.json` を追加（将来のカタログ化への布石）
- `docs/` を `skills/` の外に配置し、設計資料が配布物に混入しない構成とした

---

## mfg-improvement-frameworks

### [Unreleased]

#### 追加予定
- `SKILL.md`（ルーター本体）
- `references/` 全7ファイル
- `assets/` テンプレート3点

### 設計 - 2026-09-01
- 設計書 v0.1 を確定（`docs/design/mfg-improvement-frameworks-v0.1.md`）
- v1.0 スコープを「T1コア＋データ取得設計＋入力4分岐」に決定
