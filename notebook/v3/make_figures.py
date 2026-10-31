"""Translate the chapter-1 flow map's vector labels without rerunning its circuits.

The other English figure already exists in figures/out. Keep this missing counterpart
inside the EN notebook paths; the figure stream's Japanese geometry and results are read-only.
Run with: python3 notebook/v3/make_figures.py
"""

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from localization import localize_svg

LABELS = {
    "三値のHDL": "Ternary HDL",
    "TritFlow（TritVerilog）": "TritFlow (TritVerilog)",
    "論理合成": "Logic synthesis",
    "スタンダードセル": "Standard cells",
    "TritFlow（テープアウトした回路）": "TritFlow (taped-out circuits)",
    "配置配線": "Place and route",
    "DRC・LVS": "DRC/LVS",
    "KLayout＋PDKのデッキ": "KLayout + PDK decks",
    "件": " violations",
    "不一致": "mismatch",
    "一致": "matched",
    "抽出": "Extraction",
    "配線容量の見積もり": "Wire C estimate",
    "M1/M2の面積と周長から": "From M1/M2 area and perimeter",
    "回路シミュレーション": "Circuit simulation",
    "ngspice＋PDKのモデル": "ngspice + PDK models",
    "三値の判定": "Ternary check",
}


def main():
    import cairosvg
    from PIL import Image

    source = ROOT/"figures/out/fig_flow_map_ja.svg"
    target = HERE/"assets/fig_flow_map.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    svg = localize_svg(source.read_text(), LABELS)
    for node in ET.fromstring(svg).iter():
        if node.tag.rsplit("}", 1)[-1] in ("text", "tspan") and re.search(r"[ぁ-んァ-ヶ一-龠]", node.text or ""):
            raise ValueError(f"Missing English figure label: {node.text}")
    target.write_text(svg)
    width, height = Image.open(source.with_suffix(".png")).size
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(target.with_suffix(".png")),
                    output_width=width, output_height=height)
    print(target.with_suffix(".png"))


if __name__ == "__main__":
    main()
