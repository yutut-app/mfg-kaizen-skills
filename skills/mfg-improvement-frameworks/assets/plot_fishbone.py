#!/usr/bin/env python3
"""特性要因図を正式な書き方で描く。

30_qc7.md「特性要因図 → 作図の仕様：各階層に何を書くか」に従う。

  特性（背骨）: 解決すべき結果。1つだけ。数値があれば添える
  大骨        : 分類の切り口（4M など）
  中骨        : 具体的な要因。現場で起きている事象（名詞・状態）
  小骨        : 中骨を掘り下げた理由（名詞・状態）

書かないもの
  - 「知らない／できない」などの発想の型。型は作成時の道具で、図には出さない
  - 「〜不足」だけの語。何がどう不足しているかを書く

小骨の本数は大骨ごとに揃える。本数の差は「そこが主要因」と読まれるため。
揃わない場合は check_balance() が警告する。

使い方
    from plot_fishbone import plot_fishbone
    plot_fishbone(
        "ねじの緩み（1.8%）",
        {
            "Man": {"締付順序が人によって違う": ["作業標準書に順序の記載がない"],
                    "増し締めの判断が個人差": ["判断基準が数値化されていない"]},
            "Machine": {"トルクレンチの精度が落ちる": ["校正の期限が切れている"],
                        "工具の当たりが悪い": ["ソケットが摩耗している"]},
            "Material": {"座面の仕上げがばらつく": ["前工程の面粗度が管理外"],
                         "ワッシャの硬度がばらつく": ["受入検査の項目にない"]},
            "Method": {"締付トルクがばらつく": ["トルク値が範囲指定で幅が広い"],
                       "increments が定義されていない": ["段階締めの指示がない"]},
        },
        out="fishbone.png")
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = [
    "Hiragino Sans", "Yu Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False

# 図に書いてはいけない語（発想の型。仕様の「型は図に書かない」）
_TYPE_WORDS = ["知らない", "できない", "やらない", "しない人", "知識不足", "意識不足"]


def check_balance(bones):
    """小骨の本数の偏りと、型が混入していないかを点検する。

    戻り値: 警告文のリスト（空なら問題なし）
    """
    warns = []
    counts = {big: sum(len(v) for v in mids.values()) for big, mids in bones.items()}
    if counts:
        lo, hi = min(counts.values()), max(counts.values())
        if hi - lo >= 2:
            warns.append(
                f"小骨の本数が大骨ごとに偏っています {counts}。"
                "掘り方の差が『そこが主要因』と読まれます。均等に掘るか、"
                "掘れない理由を図の外に注記してください。"
            )
    for big, mids in bones.items():
        for mid, smalls in mids.items():
            for text in [mid, *smalls]:
                for w in _TYPE_WORDS:
                    if w in text:
                        warns.append(
                            f"「{text}」は発想の型です（{big}）。"
                            "型は図に書かず、事象で書いてください"
                            "（例:『作業標準書に締付トルクの記載がない』）。"
                        )
    return warns


def plot_fishbone(characteristic, bones, out="fishbone.png", title=None, strict=False):
    """特性要因図を描いて out に保存する。

    characteristic : str   特性（背骨の右端）
    bones          : dict  {大骨: {中骨: [小骨, ...], ...}, ...}
    strict         : True なら点検の警告を例外にする
    """
    warns = check_balance(bones)
    if warns:
        if strict:
            raise ValueError("\n".join(warns))
        for w in warns:
            print("[警告]", w)

    bigs = list(bones.keys())
    n_top = (len(bigs) + 1) // 2
    n_bot = len(bigs) - n_top

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis("off")
    spine_y = 0.5
    spine_x0, spine_x1 = 0.04, 0.80

    # 背骨
    ax.annotate("", xy=(spine_x1, spine_y), xytext=(spine_x0, spine_y),
                arrowprops=dict(arrowstyle="-|>", linewidth=2.2, color="black"))
    ax.text(spine_x1 + 0.012, spine_y, characteristic, va="center", ha="left",
            fontsize=13, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#fdf1d6", edgecolor="black"))

    def draw_side(names, upper):
        if not names:
            return
        sign = 1 if upper else -1
        span = spine_x1 - spine_x0 - 0.10
        for i, big in enumerate(names):
            # 大骨の根元を背骨上に等間隔で置く
            base_x = spine_x0 + 0.09 + span * (i + 0.5) / len(names)
            tip_x = base_x - 0.085
            tip_y = spine_y + sign * 0.33
            ax.annotate("", xy=(base_x, spine_y), xytext=(tip_x, tip_y),
                        arrowprops=dict(arrowstyle="-|>", linewidth=1.8, color="#333333"))
            ax.text(tip_x, tip_y + sign * 0.035, big, ha="center",
                    va="bottom" if upper else "top", fontsize=12, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#dce6f1",
                              edgecolor="#333333"))

            mids = bones[big]
            for j, (mid, smalls) in enumerate(mids.items()):
                # 中骨: 大骨に斜めに接続する
                t = (j + 1) / (len(mids) + 1)
                mx = base_x - 0.085 * t
                my = spine_y + sign * 0.33 * t
                m_end_x = mx - 0.115
                ax.annotate("", xy=(mx, my), xytext=(m_end_x, my),
                            arrowprops=dict(arrowstyle="-", linewidth=1.2, color="#555555"))
                ax.text(m_end_x - 0.004, my, mid, ha="right", va="center", fontsize=9.5)

                # 小骨: 中骨に短い斜線でぶら下げる
                for k, small in enumerate(smalls):
                    u = (k + 1) / (len(smalls) + 1)
                    sx = m_end_x + 0.115 * u
                    sy = my
                    s_tip_x = sx - 0.030
                    s_tip_y = sy + sign * 0.085
                    ax.annotate("", xy=(sx, sy), xytext=(s_tip_x, s_tip_y),
                                arrowprops=dict(arrowstyle="-", linewidth=0.9,
                                                color="#888888"))
                    ax.text(s_tip_x - 0.004, s_tip_y, small, ha="right",
                            va="bottom" if upper else "top", fontsize=8, color="#333333")

    draw_side(bigs[:n_top], upper=True)
    draw_side(bigs[n_top:n_top + n_bot], upper=False)

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    if title:
        ax.set_title(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return warns


if __name__ == "__main__":
    w = plot_fishbone(
        "ねじの緩み（1.8%）",
        {
            "Man": {"締付順序が人によって違う": ["作業標準書に順序の記載がない"],
                    "増し締めの判断に個人差がある": ["判断基準が数値化されていない"]},
            "Machine": {"トルクレンチの精度が落ちる": ["校正の期限が切れている"],
                        "工具の当たりが悪い": ["ソケットが摩耗している"]},
            "Material": {"座面の仕上げがばらつく": ["前工程の面粗度が管理外"],
                         "ワッシャの硬度がばらつく": ["受入検査の項目にない"]},
            "Method": {"締付トルクがばらつく": ["トルク値が範囲指定で幅が広い"],
                       "段階締めの手順がない": ["標準書に締付回数の指示がない"]},
        },
        out="fishbone_sample.png",
    )
    print("警告:", w or "なし")
