"""检查 PSB/PSD 文件的图层结构。"""
import os
from psd_tools import PSDImage

BASE = r"E:\block-uv"
files = ["b1.psb", "b2.psb", "bg.psd", "tab.psd", "lobby.psd"]

for fname in files:
    path = os.path.join(BASE, fname)
    print(f"\n{'='*60}")
    print(f"文件: {fname}")
    try:
        psd = PSDImage.open(path)
        print(f"  尺寸: {psd.width}x{psd.height}")
        print(f"  色彩模式: {psd.color_mode}")
        print(f"  图层数: {len(list(psd.descendants()))}")

        def print_layers(layers, indent=0):
            for layer in layers:
                prefix = "  " + "  " * indent
                visible = "V" if layer.visible else "H"
                print(f"{prefix}{visible} [{layer.kind}] '{layer.name}' ({layer.width}x{layer.height})")
                if hasattr(layer, '__iter__'):
                    print_layers(layer, indent + 1)

        print_layers(psd)
    except Exception as e:
        print(f"  错误: {e}")
