#!/usr/bin/env python3
"""管理図を正式な書き方で描く。

30_qc7.md「管理図 → 管理線の計算式」に従い、**管理線をデータから計算する**。
それらしい値を置かない。

  p  : CL = p̄,     UCL/LCL = p̄ ± 3√(p̄(1−p̄)/n)   ※ n が群ごとに変わると限界線も上下する
  np : CL = n·p̄,   UCL/LCL = n·p̄ ± 3√(n·p̄(1−p̄))
  c  : CL = c̄,     UCL/LCL = c̄ ± 3√c̄
  u  : CL = ū,     UCL/LCL = ū ± 3√(ū/n)

LCL が負になる場合は LCL なし（0 を下回る不良率・欠点数は存在しない）。

判定ルール（judge が返す）
  - 管理限界の外に出た点
  - 連続9点が中心線の片側
  - 連続6点の上昇または下降

注意: 管理図は「ばらつきを判断する」道具。**件数を減らすテーマには使わない**
（00_mapping.md 第5章 ステップ7）。

使い方
    from plot_control_chart import plot_control_chart
    # p 管理図（不良数と検査数）
    plot_control_chart("p", defects=[3,5,2,...], sizes=[200,210,195,...],
                       title="A工程 不良率", out="pchart.png")
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


def compute_limits(kind, defects, sizes=None):
    """管理線を計算する。戻り値: (points, cl, ucl_list, lcl_list)"""
    k = len(defects)
    if k < 20:
        print(f"[警告] 群が {k} で20未満です。管理限界が定まりません（30_qc7.md 件数の早見表）。")

    if kind == "p":
        if not sizes or len(sizes) != k:
            raise ValueError("p 管理図には群ごとの検査数 sizes が要ります")
        pbar = sum(defects) / sum(sizes)
        pts = [d / n for d, n in zip(defects, sizes)]
        cl = pbar
        ucl = [pbar + 3 * math.sqrt(pbar * (1 - pbar) / n) for n in sizes]
        lcl = [pbar - 3 * math.sqrt(pbar * (1 - pbar) / n) for n in sizes]
    elif kind == "np":
        if not sizes:
            raise ValueError("np 管理図には一定の検査数 sizes（同一値）が要ります")
        n = sizes[0]
        if any(s != n for s in sizes):
            raise ValueError("np 管理図は検査数が一定のときだけ使えます。p 管理図にしてください")
        pbar = sum(defects) / (n * k)
        pts = list(defects)
        cl = n * pbar
        e = 3 * math.sqrt(n * pbar * (1 - pbar))
        ucl = [cl + e] * k
        lcl = [cl - e] * k
    elif kind == "c":
        cbar = sum(defects) / k
        pts = list(defects)
        cl = cbar
        e = 3 * math.sqrt(cbar)
        ucl = [cl + e] * k
        lcl = [cl - e] * k
    elif kind == "u":
        if not sizes or len(sizes) != k:
            raise ValueError("u 管理図には群ごとの単位数 sizes が要ります")
        ubar = sum(defects) / sum(sizes)
        pts = [d / n for d, n in zip(defects, sizes)]
        cl = ubar
        ucl = [ubar + 3 * math.sqrt(ubar / n) for n in sizes]
        lcl = [ubar - 3 * math.sqrt(ubar / n) for n in sizes]
    else:
        raise ValueError(f"未対応の管理図: {kind}（p / np / c / u）")

    # LCL が負なら「なし」
    lcl = [None if v < 0 else v for v in lcl]
    return pts, cl, ucl, lcl


def judge(pts, cl, ucl, lcl):
    """判定ルールを当てて、見つかった異常を文字列で返す。"""
    found = []
    for i, (v, u, l) in enumerate(zip(pts, ucl, lcl), start=1):
        if v > u:
            found.append(f"群{i}: 管理限界(UCL)の外")
        if l is not None and v < l:
            found.append(f"群{i}: 管理限界(LCL)の外")

    # 連続9点が中心線の片側
    run = 0
    side = 0
    for i, v in enumerate(pts, start=1):
        s = 1 if v > cl else (-1 if v < cl else 0)
        run = run + 1 if s == side and s != 0 else 1
        side = s
        if run == 9:
            where = "上側" if s > 0 else "下側"
            found.append(f"群{i-8}〜{i}: 連続9点が中心線の{where}")

    # 連続6点の上昇/下降
    up = dn = 1
    for i in range(1, len(pts)):
        up = up + 1 if pts[i] > pts[i - 1] else 1
        dn = dn + 1 if pts[i] < pts[i - 1] else 1
        if up == 6:
            found.append(f"群{i-4}〜{i+1}: 連続6点の上昇")
        if dn == 6:
            found.append(f"群{i-4}〜{i+1}: 連続6点の下降")
    return found


def plot_control_chart(kind, defects, sizes=None, title="管理図",
                       ylabel=None, out="control_chart.png", spec=None):
    """管理図を描いて out に保存する。

    spec : 規格限界 (lower, upper)。**管理限界とは別物**なので線種を変えて引く
    """
    pts, cl, ucl, lcl = compute_limits(kind, defects, sizes)
    x = list(range(1, len(pts) + 1))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, pts, marker="o", color="#1f4e79", linewidth=1.3, markersize=4, label="測定値")
    ax.step(x, ucl, where="mid", color="#c0504d", linewidth=1.2, label="UCL")
    ax.axhline(cl, color="#4f6228", linewidth=1.2, label="CL")
    if any(v is not None for v in lcl):
        ax.step(x, [v if v is not None else 0 for v in lcl], where="mid",
                color="#c0504d", linewidth=1.2, label="LCL")
    else:
        print("[注記] LCL は負のため引いていません（0 未満は存在しないため）")

    # 規格限界は管理限界と別物。線種を分ける
    if spec:
        for v, name in zip(spec, ("LSL", "USL")):
            if v is not None:
                ax.axhline(v, color="#7030a0", linestyle=":", linewidth=1.2, label=name)

    anomalies = judge(pts, cl, ucl, lcl)
    for a in anomalies:
        g = int(a.split("群")[1].split(":")[0].split("〜")[0])
        ax.plot(g, pts[g - 1], marker="o", markersize=10, markerfacecolor="none",
                markeredgecolor="red", markeredgewidth=1.5)

    ax.set_xlabel("群")
    ax.set_ylabel(ylabel or {"p": "不良率", "np": "不良個数",
                             "c": "欠点数", "u": "単位あたり欠点数"}[kind])
    ax.set_title(f"{title}（{kind} 管理図、{len(pts)}群）")
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

    return {"cl": cl, "ucl": ucl, "lcl": lcl, "anomalies": anomalies}


if __name__ == "__main__":
    d = [6, 4, 8, 5, 7, 3, 9, 5, 6, 4, 7, 5, 8, 6, 4, 5, 7, 6, 5, 8, 4, 6, 5, 7, 6]
    n = [200] * 25
    r = plot_control_chart("p", d, n, title="A工程 不良率", out="control_chart_sample.png")
    print("CL =", round(r["cl"], 4), "/ 異常:", r["anomalies"] or "なし")
