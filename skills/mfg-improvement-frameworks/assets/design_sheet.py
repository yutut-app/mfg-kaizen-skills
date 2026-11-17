#!/usr/bin/env python3
"""設計シートの雛形を出し、埋めたものを検査する。

**なぜ機械でやるか。** 「出力必須」と本文に書いた表が、実際には出ないことが繰り返された。
文章（段1）→表（段2）→出力必須（段3）と強めても、**出さなかったことを検出できない**。
検出できるのは機械だけなので、ここに置く（`skill-builder` の `15_strength.md` の階段）。

使い方
    python3 design_sheet.py --new                  雛形を標準出力に出す
    python3 design_sheet.py --check <ファイル>      埋めたシートを検査する

検査は2区分（`skill-builder` の `40_test.md`）。
    落とす   … 外れたことが機械で確かめられるもの（表が無い、列が無い、空欄）
    要確認   … 外れて見えるが正しい可能性があるもの（主張が手段に見える、など）

**要確認では異常終了しない。** 落とすと、通すために中身を曲げることになる。

終了コード: 0 = 落とすが0件 / 1 = 落とすが1件以上 / 2 = ファイルや引数の誤り
"""

import re
import sys
from pathlib import Path

# 入口の点。判定の列が空のものを落とす（点ごとに決める。案件の種類で一括しない）
ENTRY_POINTS = ["題材", "用途", "データ", "型", "安全", "読者", "主張"]

# 判定に使える値。「効かない」には理由が要る
VERDICTS = ["効く", "部分的に効く", "効かない"]

# 「言い換えていない」と読める書き方。これらに確認は要らない
# （誤検出で見つけた。「足した語なし」を言い換え扱いして落としていた）
NO_PARAPHRASE = ["なし", "無し", "そのまま", "踏襲", "原文どおり", "原文のまま"]

# 主張が手段になっていないかを見る語尾。実績：ノートの目的が「〜をお話しします」になった
MEANS_PATTERNS = [
    r"お話しします", r"説明します", r"ご説明します", r"報告します",
    r"を整理した", r"を作った", r"を作成した", r"を分類した", r"を実施します",
]

TEMPLATE = """# 設計シート（<案件名>）

作る成果物: <スライド / Excel の一覧 / 帳票 / 画面のイメージ / 手順シート>
読者: <社内教材 / 先方報告 / 自分の検討メモ>

## 読んだ材料

| 読んだもの | 何が分かったか | 出所 |
|---|---|---|
| <案件の目的が書かれた資料> | | |
| <直前の数回分の議事録・会議資料> | | |
| <上司・利用者の指示> | | |

## 入口の判定

**点ごとに決める。案件の種類で一括して決めない。**
判定は 効く / 部分的に効く / 効かない の3つ。
「効かない」は理由を、「部分的に効く」はどの部分かを書く。空欄にも既定値にもしない。

**書き方の例**（3値の中間が最も出にくい。迷ったら中間に倒す）

| # | 点 | 判定 | 内容・理由 |
|---|---|---|---|
| 4 | 型 | 部分的に効く | 全体は指標の設計で分岐は生じない。原因が既知の部分は施策実行型を借りる |
| 5 | 安全・ヒューマンエラー | 効かない | 人の作業の安全に関わる対象を扱っていない |

**ここから下を埋める（上の2行は例なので消す）**

| # | 点 | 判定 | 内容・理由 |
|---|---|---|---|
| 1 | 題材（実在／架空） | | |
| 2 | 用途 | | |
| 3 | データ | | |
| 4 | 型 | | 主たる型／借りる箇所と借りる型（`90_handoff.md` 第1章） |
| 5 | 安全・ヒューマンエラー | | |
| 6 | 読者 | | |
| 7 | 主張と位置 | | （下の確定表へ） |

## 言葉の台帳

| 種類 | 原文（誰が・いつ） | 今回使う言葉 | 言い換えたか | 確認 |
|---|---|---|---|---|
| 目的 | | | | |
| 先方への依頼 | | | | |
| 上司の指摘 | | | | |
| 用語 | | | | |
| 構成の型 | | | | |

## 主張と位置

| 項目 | 内容 | 根拠の出所 |
|---|---|---|
| 最終ゴール | | |
| 今のフェーズ | | |
| 今回の位置 | | |
| 今回の主張（1〜2文） | | |
| 今回やらないこと | | |

## 資料に載せる要素（仕分け）

| 要素 | 判定 | 置き場所 |
|---|---|---|
| 何を確認してほしいか | | |
| やったことと決めたこと | | |
| 道具の名前 | | |
| 当社からの依頼・確認事項 | | |

## 構成（枚／シート／表ごと）

| 枚 | 層 | 読者の目的 | 今回やったこと | それが目的にどう効くか | 時間軸 |
|---|---|---|---|---|---|
| 1 | 全体 | | | | |
| 2 | 考え方 | | | | |
| 3 | 進め方 | | | | |
| 4 | 具体（実物） | | | | |
"""


def sections(text):
    """見出しごとに本文を分ける。"""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def find_section(secs, *words):
    """見出しに語を含む節を返す。見出しの文言のゆれを許す。"""
    for k, v in secs.items():
        if all(w in k for w in words):
            return k, v
    return None, None


def rows(body):
    """表の行を返す（区切り行と空行を除く）。"""
    out = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        out.append(cells)
    return out


class Report:
    def __init__(self):
        self.drop, self.ask, self.ok = [], [], []

    def fail(self, name, detail, where):
        self.drop.append(f"{name}\n      {detail}\n      場所 {where}")

    def check(self, name, detail, where):
        self.ask.append(f"{name}\n      {detail}\n      場所 {where}")


def check_materials(secs, r):
    k, body = find_section(secs, "材料")
    if body is None:
        r.fail("読んだ材料の節", "見出しが無い。**材料を読む前に設計を書いていないか**",
               "## 読んだ材料")
        return
    data = [x for x in rows(body)[1:] if any(c for c in x[1:])]
    if not data:
        r.fail("読んだ材料", "行が無い（または中身が空）。読んだものと、何が分かったかを書く", k)
    else:
        r.ok.append(f"読んだ材料: {len(data)}件")


def check_entry(secs, r):
    k, body = find_section(secs, "入口")
    if body is None:
        r.fail("入口の判定", "見出しが無い", "## 入口の判定")
        return
    found = {}
    for cells in rows(body):
        for p in ENTRY_POINTS:
            if len(cells) >= 4 and p in cells[1]:
                found[p] = (cells[2], cells[3])
    missing = [p for p in ENTRY_POINTS if p not in found]
    if missing:
        r.fail("入口の点", f"行が無い点: {missing}", k)
    for p, (verdict, note) in found.items():
        if not verdict:
            r.fail(f"入口の判定（{p}）",
                   "判定が空。効く／部分的に効く／効かない のどれかを書く。**既定値で埋めない**", k)
        elif verdict not in VERDICTS:
            r.check(f"入口の判定（{p}）", f"判定が「{verdict}」。3値のどれかに寄せる", k)
        elif verdict == "効かない" and not note:
            r.fail(f"入口の判定（{p}）", "「効かない」に理由が無い。使わない理由を書く", k)
        elif verdict == "部分的に効く" and not note:
            r.fail(f"入口の判定（{p}）", "「部分的に効く」に、どの部分かが無い", k)
    if found:
        r.ok.append(f"入口の判定: {len(found)}点に判定あり")


def check_ledger(secs, r):
    k, body = find_section(secs, "言葉の台帳")
    if body is None:
        r.fail("言葉の台帳", "見出しが無い。**目的・依頼・用語・上司の指摘を、誰の言葉で書くかが決まっていない**",
               "## 言葉の台帳")
        return
    data = [x for x in rows(body)[1:] if len(x) >= 5 and any(x[1:])]
    if not data:
        r.fail("言葉の台帳", "行が無い（または中身が空）", k)
        return
    for cells in data:
        kind, src, word, para, conf = cells[0], cells[1], cells[2], cells[3], cells[4]
        if not src:
            r.fail(f"台帳の出所（{kind}）",
                   "原文が空。確かめていないなら「未確認」と書く", k)
        paraphrased = bool(para) and not any(w in para for w in NO_PARAPHRASE)
        if paraphrased and not conf:
            r.fail(f"台帳の確認（{kind}）",
                   f"「{para}」と書いてあるのに確認が空。**確認が取れるまで成果物に入れない**", k)
    r.ok.append(f"言葉の台帳: {len(data)}行")


def check_claim(secs, r):
    k, body = find_section(secs, "主張")
    if body is None:
        r.fail("主張と位置", "見出しが無い", "## 主張と位置")
        return
    table = rows(body)
    if not table:
        r.fail("主張と位置", "表が無い", k)
        return
    header = table[0]
    if not any("出所" in h for h in header):
        r.fail("主張と位置の列", "「根拠の出所」の列が無い。**出所の無い主張は、確かめていない仮説と同じ**", k)
    for cells in table[1:]:
        if len(cells) < 2:
            continue
        item, content = cells[0], cells[1]
        if not content:
            r.fail(f"主張と位置（{item}）", "内容が空。確かめていないなら「未確認」と書く", k)
        if "主張" in item and content:
            for pat in MEANS_PATTERNS:
                if re.search(pat, content):
                    r.check(f"主張の書き方（{item}）",
                            f"「{pat}」で終わっており、**手段に見える**。"
                            "読者が何が分かる状態になるかで書く", k)
                    break
    r.ok.append("主張と位置: 表あり")


def check_sort(secs, r):
    k, body = find_section(secs, "仕分け")
    if body is None:
        k, body = find_section(secs, "載せる要素")
    if body is None:
        r.fail("仕分け表", "見出しが無い", "## 資料に載せる要素（仕分け）")
        return
    data = [x for x in rows(body)[1:] if len(x) >= 2 and x[1]]
    if not data:
        r.fail("仕分け表", "判定が入った行が無い", k)
    else:
        r.ok.append(f"仕分け表: {len(data)}行")


def check_structure(secs, r):
    k, body = find_section(secs, "構成")
    if body is None:
        r.check("構成の表", "見出しが無い。資料を作らない依頼なら対象外", "## 構成")
        return
    table = rows(body)
    data = [x for x in table[1:] if len(x) >= 5 and any(x[1:])]
    if not data:
        r.check("構成の表", "行が無い。設計の段では枚が決まっていないことがある", k)
        return
    layers = " ".join(x[1] for x in data)
    if "考え方" not in layers:
        r.check("構成の層", "「考え方」の層が無い。**全体から具体へ一気に飛ぶ形になっていないか**", k)
    for cells in data:
        if not cells[4]:
            r.fail(f"効き方（枚 {cells[0]}）",
                   "「それが目的にどう効くか」が空。**空の枚は載せる理由が無い**", k)
        if "実物" in cells[1] or "画面" in " ".join(cells):
            if not cells[2]:
                r.check(f"実物の枚（枚 {cells[0]}）",
                        "何を見る画面かの1文が無いか確かめる", k)
    r.ok.append(f"構成: {len(data)}枚")


def main(argv):
    if len(argv) == 2 and argv[1] == "--new":
        print(TEMPLATE)
        return 0
    if len(argv) != 3 or argv[1] != "--check":
        print(__doc__)
        return 2
    path = Path(argv[2])
    if not path.exists():
        print(f"[エラー] {path} がありません。`--new` で雛形を出してから埋めてください。",
              file=sys.stderr)
        return 2

    secs = sections(path.read_text(encoding="utf-8"))
    r = Report()
    for fn in (check_materials, check_entry, check_ledger, check_claim,
               check_sort, check_structure):
        fn(secs, r)

    print(f"設計シート: {path}")
    for line in r.ok:
        print(f"  OK     {line}")
    for line in r.ask:
        print(f"  要確認 {line}")
    for line in r.drop:
        print(f"  NG     {line}")

    if r.drop:
        print(f"\n落とす {len(r.drop)}件 / 要確認 {len(r.ask)}件。"
              "**直してから設計案を出す。** この出力を応答に貼る。")
        return 1
    print(f"\n落とす 0件 / 要確認 {len(r.ask)}件。"
          "要確認は人が見る。**この出力を応答に貼る。**")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
