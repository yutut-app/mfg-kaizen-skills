#!/usr/bin/env python3
"""パレート図を正式な書き方で描く。

30_qc7.md「パレート図 → 作図の仕様」の6項目を満たす。
手で軸を組み立てると毎回どこかが抜けるため、必ずこれを使う。

  1. 累積折れ線の起点を原点（0）から引く
  2. 左軸の最大＝総件数、そこに右軸の100%を合わせる
  3. 棒と棒の隙間をなくす（width=1.0）
  4. 件数の合計＝右軸の100%（「その他」を含めて合計する）
  5. 累積80%が何項目・何件かを図中に注記する
  6. 前後比較では左軸の目盛りをそろえる（ymax 引数）

使い方
    from plot_pareto import plot_pareto
    plot_pareto({"手順": 15, "表示・合図": 9, "体調・時間帯": 9, "足元・通路": 7},
                title="ヒヤリハット 分類別", out="pareto_before.png")

    # 効果確認の前後比較（左軸をそろえる）
    ymax = sum(before.values())
    plot_pareto(before, title="対策前", out="before.png", ymax=ymax)
    plot_pareto(after,  title="対策後", out="after.png",  ymax=ymax)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 日本語フォント（環境にあるものを順に試す）
rcParams["font.sans-serif"] = [
    "Hiragino Sans", "Yu Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False


def plot_pareto(counts, title="パレート図", ylabel="件数", out="pareto.png",
                ymax=None, focus=0.8, other_key="その他"):
    """パレート図を描いて out に保存する。

    counts   : dict[str, int|float]  項目名 -> 件数（順序は自由。降順に並べ替える）
    ymax     : float|None            左軸の最大値。前後比較のときは両方に同じ値を渡す
    focus    : float                 重点対象とする累積比率（既定 0.8）
    other_key: str                   常に末尾に置く項目名（既定「その他」）

    戻り値: dict（総件数、重点項目数、重点件数、重点の累積比率）
    """
    if not counts:
        raise ValueError("counts が空です")
    if any(v < 0 for v in counts.values()):
        raise ValueError("負の件数は扱えません")

    # 「その他」は大きさに関わらず末尾に置く（パレート図の作法）
    body = {k: v for k, v in counts.items() if k != other_key}
    items = sorted(body.items(), key=lambda kv: kv[1], reverse=True)
    if other_key in counts:
        items.append((other_key, counts[other_key]))

    labels = [k for k, _ in items]
    values = [v for _, v in items]
    total = sum(values)
    if total == 0:
        raise ValueError("件数の合計が 0 です")

    # 累積（仕様1: 起点を0にするため先頭に0を置く）
    cum = [0.0]
    run = 0.0
    for v in values:
        run += v
        cum.append(run)

    left_max = ymax if ymax is not None else total  # 仕様2・6

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # 仕様3: 棒を密着させる
    x = range(len(values))
    ax1.bar(x, values, width=1.0, edgecolor="black", linewidth=0.8,
            color="#7f9fc4", align="center")
    ax1.set_ylim(0, left_max)
    ax1.set_ylabel(ylabel)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, rotation=0)
    ax1.set_xlim(-0.5, len(values) - 0.5)
    for i, v in enumerate(values):
        ax1.text(i, v, str(v), ha="center", va="bottom", fontsize=9)

    # 仕様1: 折れ線は棒の左端・高さ0から始める
    ax2 = ax1.twinx()
    line_x = [-0.5] + list(x)
    ax2.plot(line_x, cum, marker="o", color="#c0504d", linewidth=1.6, markersize=4)
    # 仕様2・4: 左軸の最大に右軸の100%を合わせる → 累積は必ず100%で閉じる
    ax2.set_ylim(0, left_max)
    ticks = [left_max * r / 100 for r in range(0, 101, 20)]
    ax2.set_yticks(ticks)
    ax2.set_yticklabels([f"{r}%" for r in range(0, 101, 20)])
    ax2.set_ylabel("累積比率")

    # 仕様5: 累積 focus% に達する項目数と件数を注記する
    threshold = total * focus
    n_focus = next(i + 1 for i, c in enumerate(cum[1:]) if c >= threshold - 1e-9)
    focus_count = cum[n_focus]
    focus_ratio = focus_count / total
    ax2.axhline(left_max * focus, color="gray", linestyle="--", linewidth=0.8)
    ax2.annotate(
        f"累積{focus:.0%} … 上位{n_focus}項目 / {focus_count:.0f}件"
        f"（{focus_ratio:.1%}、不良合計 {total:.0f}件）",
        xy=(n_focus - 1, focus_count), xytext=(0.02, 0.92), textcoords="axes fraction",
        fontsize=9, color="black",
        arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8),
    )

    ax1.set_title(f"{title}（不良合計 {total:.0f}件）")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

    return {"total": total, "focus_items": n_focus,
            "focus_count": focus_count, "focus_ratio": focus_ratio}


if __name__ == "__main__":
    r = plot_pareto(
        {"手順": 15, "表示・合図": 9, "体調・時間帯": 9, "足元・通路": 7},
        title="ヒヤリハット 分類別（見本。題材は例）", out="pareto_sample.png",
    )
    print(r)
