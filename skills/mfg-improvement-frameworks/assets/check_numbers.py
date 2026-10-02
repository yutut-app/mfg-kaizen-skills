#!/usr/bin/env python3
"""数値骨格を照合する。合わなければ異常終了する。

SKILL.md「出力の作法9（検算）」と `90_handoff.md` 第9章（数値の連鎖）を機械で見る。
**資料を作る前にこれを通す。** 検算を文章の規約で守ろうとして、同じ食い違いが6回出た。

使い方
    python3 check_numbers.py data/skeleton-<案件>.yml
    python3 check_numbers.py data/skeleton-<案件>.json

骨格のファイルは**スキルの外**（案件のリポジトリや作業フォルダ）に置く。
スキルは様式だけを持つ。見本は assets/skeleton-example.yml。

見るもの
    1. 層の件数の縦計 ＝ 全体の件数
    2. 層の母数の縦計 ＝ 全体の母数
    3. 率 ＝ 件数 ÷ 母数（層ごとと全体）
    4. 目標の積み上げ ＝ 全体の削減件数
    5. 月ごとの段（到達値・単調減少・各段の取り組み）
    6. 題材の前提（上位何項目で累積何割か）
    7. 架空の事例で置いた条件に出所があるか

終了コード: 0 = すべて一致 / 1 = 不一致あり / 2 = ファイルや様式の誤り
"""

import json
import sys
from pathlib import Path

# 率の許容差。小数第2位まで書く運用のため、表示桁の丸め分だけ許す。
RATE_TOLERANCE = 0.006


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".json",):
        return json.loads(text)
    try:
        import yaml  # type: ignore
    except ImportError:
        print("[エラー] YAML を読むには pyyaml が必要です。"
              "`pip install pyyaml` か、JSON で書いてください。", file=sys.stderr)
        sys.exit(2)
    return yaml.safe_load(text)


class Report:
    def __init__(self):
        self.ng = []
        self.ok = []
        self.skipped = []

    def check(self, name, expected, actual, where, tol=0):
        if expected is None or actual is None:
            self.skipped.append(f"{name}（値がない: {where}）")
            return
        if abs(expected - actual) <= tol:
            self.ok.append(f"{name}: {actual:g}")
        else:
            self.ng.append(f"{name}\n      期待 {expected:g} / 実際 {actual:g}\n      場所 {where}")

    def fail(self, name, detail, where):
        self.ng.append(f"{name}\n      {detail}\n      場所 {where}")

    def skip(self, name):
        self.skipped.append(name)


def check_strata(d, r):
    overall = d.get("overall") or {}
    strata = d.get("strata") or []
    if not strata:
        r.skip("層別の照合（strata が無い）")
        return
    r.check("層の件数の縦計", overall.get("count"), sum(s["count"] for s in strata),
            "overall.count と strata[].count")
    if all("base" in s for s in strata) and "base" in overall:
        r.check("層の母数の縦計", overall["base"], sum(s["base"] for s in strata),
                "overall.base と strata[].base")
    for s in strata:
        if "rate_percent" not in s:
            continue
        if not s.get("base"):
            r.fail(f"率（{s['name']}）", "母数が無いのに率が書かれている", f"strata[{s['name']}]")
            continue
        r.check(f"率（{s['name']}）", s["count"] / s["base"] * 100, s["rate_percent"],
                f"strata[{s['name']}].rate_percent", tol=RATE_TOLERANCE)
    if "rate_percent" in overall and overall.get("base"):
        r.check("率（全体）", overall["count"] / overall["base"] * 100, overall["rate_percent"],
                "overall.rate_percent", tol=RATE_TOLERANCE)


def check_target(d, r):
    t = d.get("target") or {}
    if not t:
        r.skip("目標の積み上げ（target が無い）")
        return
    base, goal = t.get("baseline_count"), t.get("target_count")
    if goal == 0:
        r.fail("目標値", "ゼロを目標にしている。到達下限を根拠つきで置く",
               "target.target_count")
    items = t.get("items") or []
    if base is not None and goal is not None and items:
        r.check("目標の積み上げ", base - goal, sum(i["reduction"] for i in items),
                "target.items[].reduction の合計")
    elif not items:
        r.fail("目標の積み上げ", "items が無い。逆算で置いた目標は根拠を示せない", "target.items")


def check_monthly(d, r):
    months = d.get("monthly") or []
    t = d.get("target") or {}
    if not months:
        r.skip("月ごとの段（monthly が無い）")
        return
    goal = t.get("target_count")
    if goal is not None:
        r.check("月ごとの段の到達値", goal, months[-1]["count"], "monthly[-1].count")
    prev = None
    for m in months:
        if prev is not None and m["count"] > prev:
            r.fail("月ごとの段", f"{m['month']} で件数が増えている（{prev} → {m['count']}）",
                   f"monthly[{m['month']}].count")
        prev = m["count"]
        if not m.get("actions"):
            r.fail("月ごとの段の取り組み",
                   f"{m['month']} に、その月に効く取り組みが書かれていない",
                   f"monthly[{m['month']}].actions")


def check_premises(d, r):
    pr = d.get("premises") or {}
    if not pr:
        r.skip("題材の前提（premises が無い）")
        return
    top_n = pr.get("cumulative_top_n")
    share = pr.get("cumulative_share")
    strata = d.get("strata") or []
    overall = d.get("overall") or {}
    if top_n and share and strata and overall.get("count"):
        counts = sorted((s["count"] for s in strata), reverse=True)
        actual = sum(counts[:top_n]) / overall["count"]
        if actual < share:
            r.fail("題材の前提（累積比率）",
                   f"上位{top_n}項目で {actual:.1%}。前提の {share:.0%} を満たしていない",
                   "premises.cumulative_share と strata[].count")
        else:
            r.ok.append(f"題材の前提（上位{top_n}項目の累積）: {actual:.1%}")
    else:
        r.skip("題材の前提（cumulative_top_n / cumulative_share が無い）")


def check_conditions(d, r):
    if not d.get("fictional"):
        r.skip("条件の出所（fictional: false のため対象外）")
        return
    conds = d.get("conditions") or []
    if not conds:
        r.fail("条件の出所",
               "架空の事例（fictional: true）なのに conditions が無い。"
               "置いた条件と出所を書く（10_qc-story.md 第7章）", "conditions")
        return
    for c in conds:
        if not c.get("source"):
            r.fail(f"条件の出所（{c.get('name')}）",
                   "出所が空。検算が通っても条件が現実離れしていると落ちる",
                   f"conditions[{c.get('name')}].source")
        else:
            r.ok.append(f"条件の出所（{c['name']}）: {c['source']}")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"[エラー] {path} がありません。"
              "骨格のファイルを作ってから通してください（見本: assets/skeleton-example.yml）。",
              file=sys.stderr)
        return 2
    d = load(path)
    if not isinstance(d, dict):
        print("[エラー] 中身が辞書ではありません。見本の様式に合わせてください。", file=sys.stderr)
        return 2

    r = Report()
    for fn in (check_strata, check_target, check_monthly, check_premises, check_conditions):
        fn(d, r)

    print(f"数値骨格: {path}（{d.get('title', '題名なし')}）")
    for line in r.ok:
        print(f"  OK   {line}")
    for line in r.skipped:
        print(f"  未確認 {line}")
    for line in r.ng:
        print(f"  NG   {line}")

    if r.ng:
        print(f"\n{len(r.ng)}件が合っていません。**資料を直す前に骨格の表を直す。**"
              "骨格を直してから、そこから作り直す（90_handoff.md 第9章）。")
        return 1
    print("\nすべて一致。未確認の項目は、その値を骨格に書いていないという意味。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
