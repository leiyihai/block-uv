"""
PSB 图层替换 + PSD PNG 导出。
- b1.psb: render 图层替换后保存回 PSB
- b2.psb: render 图层替换后保存回 PSB
- bg.psd, tab.psd, lobby.psd → 导出为同名 PNG
"""
import os
import numpy as np
from PIL import Image
from psd_tools import PSDImage

BASE = r"E:\block-uv"

# PSB 图层替换: (文件名, 替换图层名, 替换图片来源)
REPLACE_TASKS = [
    ("b1.psb", "render", "render_拍脸图相机.png"),
    ("b2.psb", "render", "render_图标相机.png"),
]

# 直接导出 PSD → PNG
EXPORT_PSD = ["bg.psd", "tab.psd", "lobby.psd"]


def find_layer_by_name(layers, name):
    for layer in layers:
        if layer.name == name:
            return layer
        if hasattr(layer, '__iter__'):
            result = find_layer_by_name(layer, name)
            if result:
                return result
    return None


def replace_layer_pixels(psd, layer_name, replacement_path):
    """直接在 PSD 结构中替换图层像素数据。"""
    layer = find_layer_by_name(psd, layer_name)
    if layer is None:
        print(f"  [警告] 未找到图层 '{layer_name}'")
        return False

    if not hasattr(layer, 'topil'):
        print(f"  [错误] 图层 '{layer_name}' 不是像素图层，无法替换")
        return False

    print(f"  图层 '{layer_name}': {layer.width}x{layer.height}")

    replacement = Image.open(os.path.join(BASE, replacement_path)).convert("RGBA")
    replacement = replacement.resize((layer.width, layer.height), Image.Resampling.LANCZOS)

    # 通过 numpy 写入图层像素
    new_data = np.array(replacement)
    layer_data = layer.numpy()
    if layer_data is None:
        print(f"  [错误] 无法读取图层 '{layer_name}' 的像素数据")
        return False

    # 确保 channel 数匹配
    if new_data.shape[2] == 4 and layer_data.shape[2] == 3:
        new_data = new_data[:, :, :3]
    elif new_data.shape[2] == 3 and layer_data.shape[2] == 4:
        alpha = np.full((new_data.shape[0], new_data.shape[1], 1), 255, dtype=np.uint8)
        new_data = np.dstack([new_data, alpha])

    layer_data[:] = new_data
    print(f"  已替换图层 '{layer_name}' → {replacement_path}")
    return True


def main():
    # 1. 替换 PSB 图层，保存回 PSB
    for psb_name, layer_name, replace_png in REPLACE_TASKS:
        psb_path = os.path.join(BASE, psb_name)
        if not os.path.exists(psb_path):
            print(f"[跳过] {psb_name} 不存在")
            continue

        print(f"\n处理: {psb_name}")
        psd = PSDImage.open(psb_path)
        print(f"  尺寸: {psd.width}x{psd.height}")

        if replace_layer_pixels(psd, layer_name, replace_png):
            try:
                psd.save(psb_path)
                print(f"  已保存回: {psb_path}")
            except Exception as e:
                print(f"  [错误] 保存 PSB 失败: {e}")

    # 2. 导出 PSD → PNG
    for psd_name in EXPORT_PSD:
        psd_path = os.path.join(BASE, psd_name)
        if not os.path.exists(psd_path):
            print(f"[跳过] {psd_name} 不存在")
            continue

        print(f"\n处理: {psd_name}")
        psd = PSDImage.open(psd_path)
        print(f"  尺寸: {psd.width}x{psd.height}")

        composite = psd.composite(force=True)
        if composite is None:
            print(f"  [错误] {psd_name} 合成失败")
            continue

        out_path = os.path.join(BASE, os.path.splitext(psd_name)[0] + ".png")
        composite.save(out_path, "PNG")
        print(f"  已保存: {out_path}")

    print("\n全部完成!")


if __name__ == "__main__":
    main()
