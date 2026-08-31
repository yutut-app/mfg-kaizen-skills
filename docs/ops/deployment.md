# 導入・配布・運用手順

対象: `claude-skills` リポジトリ内の全スキル
最終更新: 2026-09-01

---

## 0. 前提：3系統は別物

| 系統 | 保存場所 | 設定画面 |
|---|---|---|
| チャット | Anthropic サーバー | Settings → カスタマイズ → スキル |
| Claude Code | `~/.claude/skills/` または `~/.claude/plugins/` | Settings → Claude Code |
| Cowork | ローカルフォルダ | Settings → Cowork |

同じ SKILL.md でも置き場所が違えば別物として扱われる。片方に入れても、もう片方の一覧には出ない。これは仕様。

---

## 1. リポジトリの初期化

```bash
cd <任意の作業ディレクトリ>
git init mfg-kaizen-skills
cd mfg-kaizen-skills
# 本リポジトリの中身を配置してから
git add .
git commit -m "chore: リポジトリ初期化"
git branch -M main
git remote add origin <ホスティング先のURL>
git push -u origin main
```

---

## 2. チャットへの導入

1. スキルフォルダを ZIP 化する

```bash
cd skills
zip -r ../dist/mfg-improvement-frameworks.zip mfg-improvement-frameworks
```

2. Settings → カスタマイズ → スキル → 追加 でアップロード
3. Settings → 機能 で「コード実行とファイル作成」が ON になっていることを確認

> **ZIP の階層について**
> 手元の実績では「ZIP のルートにスキルフォルダが来る（SKILL.md が1階層下）」で通っている。
> 一方、SKILL.md をアーカイブ直下に置く流儀を書いている情報源もある。
> 実装は上記の実績側を採用しているが、**アップロードでエラーが出たらもう一方の階層を試す**こと。

---

## 3. Claude Code / Cowork への導入

```bash
# 個人用（全プロジェクトで有効）
mkdir -p ~/.claude/skills
cp -r skills/mfg-improvement-frameworks ~/.claude/skills/

# 確認：SKILL.md が直下にあること（二重ネストになっていないか）
ls ~/.claude/skills/mfg-improvement-frameworks/SKILL.md
```

プロジェクト限定にしたい場合は `<project>/.claude/skills/` に配置する。

---

## 4. 更新時の手順

1. `skills/<name>/` を編集
2. `metadata.version` を更新
3. `CHANGELOG.md` に追記
4. commit → `git tag v1.x.x` → push
5. **使っている系統すべてに入れ直す**（ZIP再アップロード / 再コピー）
6. **セッションを再起動**する

手順5〜6を飛ばすと古い版が動き続ける。原因不明の挙動の大半はこれ。

---

## 5. 動作確認

導入後は必ず、**読み取り専用の依頼**から始める。

```
「不良率が悪化している。原因を整理する進め方を教えて」
```

期待動作:
- スキルが発動する
- QCストーリーの型を選定するための質問が返る
- いきなり結論や図を出してこない

発動しない場合のチェック:
- Settings でスキルが有効になっているか
- セッションを再起動したか
- description に該当する語が含まれているか

---

## 6. やらないこと

- スキルに認証情報・社内固有の数値を含めない
- 同じ案件を複数の系統で並行して進めない（履歴が同期しないため追跡不能になる）
- 権限モードの Bypass は使わない

---

## 7. リポジトリを増やすとき（Phase 2 以降）

製造業改善以外のドメインが必要になったら、このリポジトリに足さず**新しいリポジトリを作る**。

判断基準は次の3つのいずれかに当てはまるか。

- 別ドメインで、同時にオプトインしたくない（誤発火・トークン消費を避けたい）
- 公開範囲が違う（private にしたい／しなくてよい）
- 更新頻度やタグ戦略が明確に違う

複数リポジトリを1つのカタログに束ねる場合は、カタログ専用リポジトリを作り、
`marketplace.json` の `plugins` 配列に `source` で各リポジトリを参照させる。
`url` / `github` / `git-subdir` のいずれのソース指定も使える。
