#!/usr/bin/env python3
"""散布図を読める形で描く。

30_qc7.md「散布図 → 作図の仕様」に従う。次の4つを既定で描く。

  1. 何の値を決めるための散布図かを、図の表題に書く（purpose は必須）
  2. 基準線（規格・判定の境）を引く
  3. 基準を外れる領域を塗り、何の領域かを書き込む
  4. 群のラベルを、凡例ではなく点の近くに書く

基準（y_limits / x_limits）を渡さないと警告を出す。基準のない散布図は、
点がどこにあれば問題なのかが読めない。

使い方
    from plot_scatter import plot_scatter
    plot_scatter(
        {"1号機": (x1, y1), "2号機": (x2, y2)},
        purpose="切込み量の設定値で外径が決まっているかを判断する",
        xlabel="切込み量（mm）", ylabel="外径（mm）",
        y_limits=(9.95, 10.05), y_limit_name="外径の規格",
        out="scatter.png")

下の見本は外径寸法（ケース1）。数値は書き方を示すための架空の値で、
題材は案件ごとに差し替える。
"""

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = [
    "Hiragino Sans", "Yu Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False

_MARKERS = ["o", "s", "^", "D", "v", "P"]
_COLORS = ["#1f4e79", "#c0504d", "#4f6228", "#7030a0", "#b8860b", "#2e75b6"]


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def plot_scatter(groups, purpose, xlabel, ylabel, out="scatter.png",
                 y_limits=None, y_limit_name="基準", x_limits=None, x_limit_name="基準"):
    """散布図を描いて out に保存する。

    groups  : dict[str, (list[x], list[y])]  群名 -> (x の並び, y の並び)。群が1つでも dict で渡す
    purpose : str   何の値を決めるための散布図か（必須。表題になる）
    y_limits: (下限, 上限)  結果側（縦軸）の基準。片側だけなら None を入れる
    x_limits: (下限, 上限)  原因側（横軸）の基準（設定値の許容範囲など）。任意

    戻り値: dict（全体の相関係数、群ごとの相関係数、群ごとの点数、警告）
    """
    if not purpose or not purpose.strip():
        raise ValueError("purpose（何の値を決めるための散布図か）を書いてください。"
                         "書けない散布図は、描く理由がありません。")
    warns = []
    if y_limits is None and x_limits is None:
        warns.append("基準（y_limits / x_limits）がありません。どこにあれば問題なのかが読めない図になります。")

    all_x, all_y = [], []
    for name, (xs, ys) in groups.items():
        if len(xs) != len(ys):
            raise ValueError(f"{name}: x と y の数が違います（{len(xs)} と {len(ys)}）")
        all_x += list(xs)
        all_y += list(ys)
    if len(all_x) < 30:
        warns.append(f"点が{len(all_x)}組で30組未満です。傾向が読めない可能性があります（30_qc7.md 件数の早見表）。")

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # 軸の範囲：点と基準の両方が入るように取る
    xs_span = list(all_x) + [v for v in (x_limits or ()) if v is not None]
    ys_span = list(all_y) + [v for v in (y_limits or ()) if v is not None]
    xpad = (max(xs_span) - min(xs_span)) * 0.15 or 1.0
    ypad = (max(ys_span) - min(ys_span)) * 0.15 or 1.0
    xmin, xmax = min(xs_span) - xpad, max(xs_span) + xpad
    ymin, ymax = min(ys_span) - ypad, max(ys_span) + ypad
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    # 仕様2・3：基準線と、外れる領域
    if y_limits:
        lo, hi = y_limits
        if lo is not None:
            ax.axhspan(ymin, lo, color="#f4cccc", alpha=0.6, zorder=0)
            ax.axhline(lo, color="#c00000", linewidth=1.3, zorder=1)
            ax.text(xmax, lo, f" {y_limit_name} 下限 {lo:g}", va="center", ha="left",
                    fontsize=9, color="#c00000", clip_on=False)
            ax.text(xmin + (xmax - xmin) * 0.02, (ymin + lo) / 2, f"{y_limit_name}を下回る領域",
                    va="center", fontsize=9, color="#990000")
        if hi is not None:
            ax.axhspan(hi, ymax, color="#f4cccc", alpha=0.6, zorder=0)
            ax.axhline(hi, color="#c00000", linewidth=1.3, zorder=1)
            ax.text(xmax, hi, f" {y_limit_name} 上限 {hi:g}", va="center", ha="left",
                    fontsize=9, color="#c00000", clip_on=False)
            ax.text(xmin + (xmax - xmin) * 0.02, (hi + ymax) / 2, f"{y_limit_name}を上回る領域",
                    va="center", fontsize=9, color="#990000")
    if x_limits:
        lo, hi = x_limits
        for v, side in ((lo, "下限"), (hi, "上限")):
            if v is not None:
                ax.axvline(v, color="#7030a0", linewidth=1.1, linestyle="--", zorder=1)
                ax.text(v, ymax, f"{x_limit_name} {side} {v:g}", rotation=90, va="top",
                        ha="right", fontsize=8, color="#7030a0")
        if lo is not None:
            ax.axvspan(xmin, lo, color="#e4dcef", alpha=0.5, zorder=0)
        if hi is not None:
            ax.axvspan(hi, xmax, color="#e4dcef", alpha=0.5, zorder=0)

    # 点と、仕様4：群のラベルを点の近くに
    per_group = {}
    for k, (name, (xs, ys)) in enumerate(groups.items()):
        c = _COLORS[k % len(_COLORS)]
        ax.scatter(xs, ys, s=28, marker=_MARKERS[k % len(_MARKERS)], color=c,
                   edgecolor="white", linewidth=0.5, zorder=3)
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        r = _pearson(list(xs), list(ys))
        per_group[name] = {"n": len(xs), "r": r}
        ax.annotate(f"{name}（{len(xs)}点）", xy=(cx, cy),
                    xytext=(cx + (xmax - xmin) * 0.06, cy + (ymax - ymin) * 0.08),
                    fontsize=10, color=c, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=c, linewidth=0.8), zorder=4)

    r_all = _pearson(all_x, all_y)
    ax.text(0.98, 0.03, f"全体の相関係数 r = {r_all:.2f}（{len(all_x)}組）",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#999999"))

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(purpose, fontsize=12)  # 仕様1
    ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)

    for w in warns:
        print("[警告]", w)
    return {"r_all": r_all, "groups": per_group, "warnings": warns}


if __name__ == "__main__":
    # 見本（架空の値）：外径寸法（ケース1）。号機ごとに切込み量の設定が違い、外径の中心がずれる
    def make(x0, n, phase):
        xs = [round(x0 + 0.004 * math.sin(i * 1.7 + phase) + 0.001 * (i % 5 - 2), 4) for i in range(n)]
        ys = [round(10.000 + 1.3 * (x - 0.335) + 0.004 * math.cos(i * 2.3 + phase), 4)
              for i, x in enumerate(xs)]
        return xs, ys
    r = plot_scatter(
        {"1号機": make(0.350, 20, 0.0), "2号機": make(0.320, 20, 1.0)},
        purpose="切込み量の設定値で外径が決まっているかを判断する（見本・架空の値）",
        xlabel="切込み量（mm）", ylabel="外径（mm）",
        y_limits=(9.95, 10.05), y_limit_name="外径の規格",
        out="scatter_sample.png",
    )
    print({"r_all": round(r["r_all"], 2),
           "groups": {k: {"n": v["n"], "r": round(v["r"], 2)} for k, v in r["groups"].items()}})
