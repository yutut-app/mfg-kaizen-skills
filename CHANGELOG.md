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

### [1.0.0] - 2026-09-01

#### 追加
- `references/` 全7ファイルを執筆
  - `00_mapping.md`（選定の対応表）
  - `10_qc-story.md`（進め方の型）
  - `20_factor-axes.md`（要因の分解軸）
  - `30_qc7.md`（QC7つ道具）
  - `40_n7.md`（新QC7つ道具）
  - `50_standardization.md`（標準化・定着）
  - `60_data-design.md`（データ取得設計）

- `SKILL.md`（ルーター本体＋改善プロトコル）
- `assets/qc-process-table.xlsx`（QC工程表テンプレ、工程図記号の凡例つき）
- `assets/check-sheet.xlsx`（記録用／点検用／層別設計メモ）
- `assets/a3-report.md`（A3改善報告書テンプレ）

これにより v1.0.0 の実装が完了。

### 設計 - 2026-09-01
- 設計書 v0.1 を確定（`docs/design/mfg-improvement-frameworks-v0.1.md`）
- v1.0 スコープを「T1コア＋データ取得設計＋入力4分岐」に決定

### 設計 - 2026-09-01（v0.2）
- 主戦場をチャットから **Cowork** に変更（改善ループがCoworkでのみ閉じるため）
- 改善プロトコルを追加（記録は自動、書き換えは承認制）
- `docs/feedback.md`（改善ログ）を追加
- 運用フェーズを「育成期／安定期」の2段階に定義

### [1.0.1] - 2026-09-01
#### 修正
- `SKILL.md` の description を325文字→186文字に短縮（200文字の上限に違反していた）
- description の記法をブロックスカラー `>` から二重引用符の1行に変更
  （`>` は改行を半角スペースに畳むため、日本語文中に不要な空白が混入していた）
