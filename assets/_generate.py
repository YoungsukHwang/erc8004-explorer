"""Generate the project logo and cover image.

Run from the repo root:
    python assets/_generate.py

Outputs:
    assets/logo.png    — 512×512 square, ETHGlobal submission "Logo" slot
    assets/cover.png   — 1280×720 (16:9), submission "Cover image" slot
"""
from __future__ import annotations
import os
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects

OUT = os.path.dirname(os.path.abspath(__file__))

# --- Palette (Streamlit-style) ----------------------------------------------
BG       = "#0E1117"
TEXT     = "#FAFAFA"
RED      = "#FF4B4B"
ORANGE   = "#FF8C42"
DIM      = "#A0A0A0"
SUBDIM   = "#666666"


def make_logo() -> None:
    fig, ax = plt.subplots(figsize=(5.12, 5.12), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    # Thin red border ring
    for x, y, w, h in [(0.04, 0.04, 0.92, 0.92)]:
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=False,
                                   edgecolor=RED, linewidth=2.0))

    # Big "8004" in red
    ax.text(0.5, 0.62, "8004",
            fontsize=130, color=RED, ha="center", va="center",
            fontweight="black", family="monospace")

    # Underline / divider
    ax.plot([0.22, 0.78], [0.42, 0.42], color=RED, linewidth=2.0, alpha=0.6)

    # "REALITY CHECK" small caps below — spacing faked with extra spaces
    ax.text(0.5, 0.32, "R E A L I T Y   C H E C K",
            fontsize=18, color=TEXT, ha="center", va="center",
            fontweight="bold", family="monospace")

    # Tiny tagline at the bottom
    ax.text(0.5, 0.17, "decoded from raw on-chain bytes",
            fontsize=10, color=DIM, ha="center", va="center",
            family="sans-serif", style="italic")

    plt.tight_layout(pad=0)
    out = os.path.join(OUT, "logo.png")
    plt.savefig(out, dpi=100, facecolor=BG, edgecolor="none",
                bbox_inches="tight", pad_inches=0)
    plt.close()
    print(f"wrote {out}  (512×512)")


def make_cover() -> None:
    # 1280×720 = 16:9, scale safely past ETHGlobal's 640×360 requirement
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_axis_off()

    # --- Title block ---
    ax.text(0.7, 7.6, "ERC 8004",
            fontsize=80, color=RED, ha="left", va="center",
            fontweight="black", family="monospace")
    ax.text(0.7, 6.4, "REALITY  CHECK",
            fontsize=40, color=TEXT, ha="left", va="center",
            fontweight="bold", family="monospace")

    # --- Tagline ---
    ax.text(0.7, 5.4,
            "What's actually inside the ERC-8004 registry — decoded from raw "
            "Ethereum mainnet events.",
            fontsize=14, color=DIM, ha="left", va="center", family="sans-serif")

    # --- Funnel ladder ---
    funnel = [
        ("34,569", "Registered"),
        ("9,520",  "Has card"),
        ("4,645",  "Claims x402"),
        ("216",    "Rated + x402"),
        ("6",      "Trustworthy +\nPayable"),
        ("2",      "Actually paid"),
    ]
    x0, x1 = 1.6, 14.4
    n = len(funnel)
    spacing = (x1 - x0) / (n - 1)
    y_num = 3.0
    y_lbl = 1.8

    # Connector line behind
    ax.plot([x0, x1], [y_num + 0.1, y_num + 0.1], color=SUBDIM, linewidth=1.5,
            zorder=0)

    for i, (number, label) in enumerate(funnel):
        x = x0 + i * spacing
        # number
        col = RED if i == n - 1 else (ORANGE if i == n - 2 else TEXT)
        weight = "black" if i >= n - 2 else "bold"
        ax.text(x, y_num, number,
                fontsize=26 if i < n - 2 else 36,
                color=col, ha="center", va="center",
                fontweight=weight, family="monospace",
                path_effects=[PathEffects.withStroke(linewidth=4, foreground=BG)])
        # label
        ax.text(x, y_lbl, label,
                fontsize=11, color=DIM, ha="center", va="center",
                family="sans-serif")

    # --- Stack strap ---
    ax.text(8.0, 0.45,
            "BigQuery  ·  Cloud Run  ·  Vertex AI Gemini  ·  ENS  ·  Streamlit",
            fontsize=12, color=SUBDIM, ha="center", va="center",
            family="monospace")

    plt.tight_layout(pad=0)
    out = os.path.join(OUT, "cover.png")
    plt.savefig(out, dpi=100, facecolor=BG, edgecolor="none",
                bbox_inches="tight", pad_inches=0)
    plt.close()
    print(f"wrote {out}  (1280×720)")


if __name__ == "__main__":
    make_logo()
    make_cover()
