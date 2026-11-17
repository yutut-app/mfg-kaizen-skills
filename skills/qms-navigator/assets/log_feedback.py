#!/usr/bin/env python3
"""改善ログに1行追記する。記録先を自分で探し、どこに書いたかを報告する。

**なぜ機械でやるか。** 記録先を本文の規則で書くと、環境ごとに判断が要り、
**書けないときに沈黙する。** 実績が2回ある。

  - 別セッションで改善プロトコルが動かず、記録が残らなかった（2026-09-22 の報告）
  - スキルをコピーした環境では、リポジトリの `docs/` が無く、記録が1件も残らなかった
    （2026-11-17 のレビュー。ログの最終記録が1か月古いまま見えていた）

**配布はスキルフォルダ単位**なので、`docs/` が無い環境が必ずある。
探す順と、書いた場所の報告を機械に持たせれば沈黙しない。

**このファイルは、同じリポジトリの複数のスキルに同じものを置く。**
配布がスキルフォルダ単位なので、別のスキルから参照すると、そのスキルだけをコピーした環境で壊れる。
**直すときは、置いてあるすべてのスキルで直す**（`check_edit.sh` に旧文字列を渡して確かめる）。

**スキル名は置き場所から決まる**（このファイルの2つ上のディレクトリ名）。
記録先のファイル名もそこから決まるので、スキルごとに書き換える必要はない。

使い方
    python3 log_feedback.py --date 2026-11-17 --req "<依頼の要約>" \\
        --expected "<期待した挙動>" --actual "<実際の挙動>" \\
        --cause "<推定原因。規約名と場面を名指しする>" [--id "<原因ID>"]

    python3 log_feedback.py --where     記録先だけ表示する
    python3 log_feedback.py --show      ホーム配下の記録を表示する（取り込み用）

記録先を探す順（`<skill>` はこのファイルの2つ上のディレクトリ名）
    1. 環境変数 FEEDBACK_LOG（または MFG_FEEDBACK）が指すファイル
       **別PCではここで指定する**
    2. スキルの実体から2つ上の docs/feedback-<skill>.md、無ければ docs/feedback.md
       （リンク環境＝リポジトリの中に実体がある）
    3. ~/.claude/<skill>-feedback-local.md（**どのPCでも書ける**。無ければ作る）

3番に書いたときは「このPCの記録はリポジトリに入っていない」と添える。
**追記した行は標準出力にも出す。** 会話に残れば、リポジトリを持つセッションが本ログへ移せる。
"""

import argparse
import os
import sys
from pathlib import Path

SKILL_NAME = Path(__file__).resolve().parent.parent.name   # .../skills/<skill>/assets/ の <skill>
LOCAL = Path.home() / ".claude" / f"{SKILL_NAME}-feedback-local.md"
LOCAL_HEADER = f"""# 改善ログ（このPCの控え） — {SKILL_NAME}

**リポジトリの `docs/feedback.md` に入っていない。** スキルをコピーした環境で書かれたもの。
リポジトリを持つセッションに渡して、本ログへ移す。

| 日付 | 依頼の要約 | 期待した挙動 | 実際の挙動 | 推定原因 | 対応 |
|---|---|---|---|---|---|
"""


def resolve():
    """記録先を順に探す。(パス, 何番で見つかったか, リポジトリ内か, 注意) を返す。

    **使えない指定を黙って飛ばさない。** 黙って次へ落ちると、
    指定したつもりの場所に書かれていないことに気づけない。
    """
    notes = []
    for var in ("FEEDBACK_LOG", "MFG_FEEDBACK"):
        env = os.environ.get(var)
        if not env:
            continue
        p = Path(env).expanduser()
        if p.parent.is_dir():
            return p, f"1 環境変数 {var}", True, notes
        notes.append(f"環境変数 {var}=`{env}` は使えない"
                     f"（親ディレクトリ {p.parent} が無い）。次の候補に落ちた")

    # 2: スキルの実体から2つ上。シンボリックリンクは解決してから辿る
    skill_dir = Path(__file__).resolve().parent.parent      # .../skills/<name>/
    docs = skill_dir.parent.parent / "docs"
    for name in (f"feedback-{SKILL_NAME}.md", "feedback.md"):
        cand = docs / name
        if cand.exists():
            return cand, f"2 実体から2つ上の docs/{name}", True, notes
    notes.append(f"{docs}/feedback-{SKILL_NAME}.md と {docs}/feedback.md が無い"
                 "（コピー環境。リポジトリの docs/ は配布されない）")

    return LOCAL, "3 ホーム配下の控え", False, notes


def append(path, in_repo, row):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(LOCAL_HEADER, encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(row + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--date")
    ap.add_argument("--req")
    ap.add_argument("--expected")
    ap.add_argument("--actual")
    ap.add_argument("--cause")
    ap.add_argument("--id", default="")
    ap.add_argument("--where", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args(argv)

    if a.help:
        print(__doc__)
        return 0

    path, how, in_repo, notes = resolve()
    for n in notes:
        print(f"[注意] {n}")

    if a.where:
        print(f"記録先: {path}（{how}）")
        print("リポジトリの中" if in_repo else "**リポジトリの外。このPCの控え**")
        return 0

    if a.show:
        if LOCAL.exists():
            print(LOCAL.read_text(encoding="utf-8"))
        else:
            print(f"{LOCAL} は無い（このPCの控えは空）")
        return 0

    missing = [n for n, v in (("--date", a.date), ("--req", a.req),
                              ("--expected", a.expected), ("--actual", a.actual),
                              ("--cause", a.cause)) if not v]
    if missing:
        print(f"[エラー] 足りない引数: {missing}\n", file=sys.stderr)
        print(__doc__)
        return 2

    cause = f"{a.cause}（{a.id}）" if a.id else a.cause
    row = f"| {a.date} | {a.req} | {a.expected} | {a.actual} | {cause} | 未対応 |"

    append(path, in_repo, row)

    print(f"記録先: {path}（{how}）")
    print(row)
    if not in_repo:
        print("\n**このPCの記録はリポジトリに入っていない。**")
        print("上の行を、リポジトリを持つセッションに渡して docs/feedback.md へ移す。")
        print("別PCで毎回ここに落ちるなら、環境変数 FEEDBACK_LOG で記録先を指定する。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
