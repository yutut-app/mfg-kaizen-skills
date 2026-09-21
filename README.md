# mfg-kaizen-skills

**製造業の業務改善・品質管理ドメイン専用**の Claude Agent Skills リポジトリ。

このリポジトリを唯一の編集元（単一ソース）とし、チャット／Claude Code／Cowork の各系統へはここからリパッケージして配布する。

---

## 収録スキル

| スキル | 版 | 概要 | 状態 |
|---|---|---|---|
| [`mfg-improvement-frameworks`](skills/mfg-improvement-frameworks/) | 1.8.1 | 製造現場の問題解決をQCストーリー・4M・QC7つ道具・新QC7つ道具で体系的に支援 | 運用中（育成期） |

**主戦場は Cowork。** スキルを育てている間は Cowork のみで使い、安定してからチャットにも配布する。
理由は [設計書 v0.2](docs/design/mfg-improvement-frameworks-v0.2.md) を参照。

---

## リポジトリ分割の方針

**ドメイン単位で1リポジトリ**とする。1スキル1リポジトリでも、全部を1リポジトリでもない。

```
mfg-kaizen-skills/     ← このリポジトリ（製造業改善）
kaggle-skills/         ← 別リポジトリ（データ分析）※必要になったら作る
document-skills/       ← 別リポジトリ（資料作成）  ※必要になったら作る
        ↓ 将来まとめる場合
claude-marketplace/    ← カタログ専用リポジトリ
└── .claude-plugin/marketplace.json
        （source: url で上記各リポジトリを参照する）
```

### この方針の根拠

1. **誤発火とトークン消費を防ぐ。** スキルが増えると description マッチングで無関係なスキルまで発火し、使わないスキルの description がコンテキストを占有し続ける。オプトインしたい単位＝ドメイン。
2. **リポジトリはアクセス制御の単位。** 自社の管理基準値や工程名を含みうる製造業系と、公開しても困らない分析系を同居させると、片方だけ private にできない。
3. **ライフサイクルが違う。** 更新頻度もタグ戦略もドメインごとに別。

分割してもカタログは1つに束ねられる（`marketplace.json` の `source` で外部リポジトリを参照可能）ため、分割によるデメリットはない。

---

## ディレクトリ構成

```
mfg-kaizen-skills/
├── README.md
├── CHANGELOG.md
├── .gitignore
├── .claude-plugin/
│   └── plugin.json        # プラグインマニフェスト（Phase 3への布石）
│
├── docs/                  # ★ スキルとしては読み込まれない資料
│   ├── design/            #   設計書（版ごとに残す）
│   ├── decisions/         #   意思決定の記録
│   ├── ops/               #   導入・配布・運用手順
│   └── feedback.md        #   改善ログ（Claudeが自動追記する）
│
├── skills/                # ★ ここだけが配布対象
│   └── mfg-improvement-frameworks/
│       ├── SKILL.md       #   必須。ルーター本体
│       ├── references/    #   必要時のみ読み込む詳細
│       └── assets/        #   出力に使うテンプレート
│
└── dist/                  # パッケージ生成物（gitignore対象）
```

### なぜ `docs/` を `skills/` の外に置くのか

1. **配布物に混入しない。** パッケージング／コピーの単位はスキルフォルダそのもの。外に出しておけば `.skill` にも `~/.claude/skills/` にも設計書が入らない。
2. **誤読を確実に防ぐ。** Claude は SKILL.md から参照されないファイルを原則読まないが、Claude Code でリポジトリを開いて作業する際は別。物理的に外に出すのが確実。
3. **資料を版ごとに残せる。** スキル本体は常に最新1本、設計書は v0.1, v0.2 と履歴を積むもの。混ぜると両方が汚れる。

---

## 段階的な拡張計画

| Phase | やること | 移行の目安 |
|---|---|---|
| **1（現在）** | このリポジトリを運用。`skills/` 配下にスキルを追加していく | — |
| **2** | 別ドメインのリポジトリを新規作成 | 製造業以外のスキルが必要になった時 |
| **3** | カタログリポジトリを立て、`source` で各ドメインを参照 | チーム配布を始める時 |

`plugin.json` を先に置いてあるため、Phase 3 への移行時に構造変更は不要。

---

## 改善サイクル

スキルは自動更新されない。仕組みで担保する。

```
Coworkで使う
  → 期待どおり動かなければ Claude が docs/feedback.md に自動追記
  → 月1回 or 未対応5件で棚卸し（人が判断）
  → 修正案を Claude が提案 → 承認 → 書き換え
  → version を上げる
```

**記録は自動、書き換えは承認制**とする。1回の失敗が永久ルールになる事故を防ぐため。
定型ルールは [`docs/design/skill-md-improvement-protocol.md`](docs/design/skill-md-improvement-protocol.md)。

---

## 配布フロー

```
skills/<name>/ を編集
   │
   ├─→ ~/.claude/skills/ へコピー → Cowork / Claude Code  ★育成期はここだけ
   ├─→ ZIP化           → チャット：Settings → カスタマイズ → スキル → 追加（安定期）
   └─→ git tag + push  → チーム共有
```

Cowork / Code はスキルのフォルダを監視しているため、SKILL.md の編集はセッション中に反映される
（反映されない場合は `/reload-skills`）。チャットは再アップロードと再起動が必要。

手順の詳細は [`docs/ops/deployment.md`](docs/ops/deployment.md)。

### 運用ルール

- **3系統は同期しない。** 更新したら使っている系統すべてを入れ直す。
- 入れ直したら**セッションを再起動**する。しないと反映されない。
- `SKILL.md` の `metadata.version` / `plugin.json` の `version` / git tag / CHANGELOG の4つを揃える。
- 認証情報・社内固有の数値はスキルに含めない。

> **注意**：チャットではプラグイン／マーケットプレイスの仕組みは使えない（ZIPアップロードのみ）。
> `plugin.json` が効くのは Claude Code / Cowork 側。

---

## 開発の進め方

1. `docs/design/` に設計書を書き、合意を取る
2. `skills/<name>/SKILL.md` と `references/` を実装
3. 発動テスト・動作テストを実施（観点は設計書の検証設計を参照）
4. パッケージ化して導入し、**読み取り専用の依頼**で動作確認
5. CHANGELOG を更新し、tag を切る

---

## 参考

- [Agent Skills - Claude Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [anthropics/skills](https://github.com/anthropics/skills)
