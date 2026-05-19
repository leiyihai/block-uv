"""
一键流水线：cubemap 贴图 → Blender 渲染 → PSB/PSD 导出。
用法: python run.py

前置要求:
  - pip install Pillow psd-tools aggdraw
  - Blender 5.0 位于 C:\blender-5.0.0-windows-x64\blender.exe
  - input/{羊毛,橡木板,末地石,黑曜石}/ 各含 6 张 cubemap 散图

输出: output/bg.png, output/tab.png, output/lobby.png
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# ============================================================
# 配置
# ============================================================
BLENDER = r"C:\blender-5.0.0-windows-x64\blender.exe"
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
WORK_DIR = BASE_DIR / ".work"

FOLDERS = ["羊毛", "橡木板", "末地石", "黑曜石"]
FACE_NAMES = ["top", "left", "front", "right", "back", "bottom"]
EXTENSIONS = {".png", ".jpg", ".jpeg"}

# 4x3 横向十字布局坐标
GRID = {
    "top": (1, 0), "left": (0, 1), "front": (1, 1),
    "right": (2, 1), "back": (3, 1), "bottom": (1, 2),
}

# ============================================================
# Step 1: Cubemap → uv_out.png
# ============================================================

def step1_cubemap():
    """在每个 input 子文件夹中生成 uv_out.png。"""
    print("=" * 50)
    print("Step 1: Cubemap 拼接 → uv_out.png")
    print("=" * 50)

    for folder_name in FOLDERS:
        folder = INPUT_DIR / folder_name
        if not folder.is_dir():
            print(f"  [跳过] 文件夹不存在: {folder}")
            continue

        # 扫描 6 张散图
        faces = _find_faces(folder)
        if faces is None:
            continue

        # 加载并归一化尺寸
        images = _load_and_normalize(faces)
        w, h = next(iter(images.values())).size

        # 拼接
        canvas = Image.new("RGBA", (w * 4, h * 3), (0, 0, 0, 0))
        for name, img in images.items():
            col, row = GRID[name]
            canvas.paste(img, (col * w, row * h), img)

        out_path = folder / f"uv_out_{folder_name}.png"
        canvas.save(out_path, "PNG")
        print(f"  [完成] {folder_name}/{out_path.name} ({canvas.width}x{canvas.height})")


def _find_faces(folder):
    faces = {}
    for name in FACE_NAMES:
        candidates = [folder / f"{name}{ext}" for ext in EXTENSIONS]
        found = [p for p in candidates if p.is_file()]
        if not found:
            print(f"  [跳过] {folder.name}: 缺少 '{name}'")
            return None
        faces[name] = found[0]
    return faces


def _load_and_normalize(faces):
    images = {}
    for name, path in faces.items():
        img = Image.open(path).convert("RGBA")
        images[name] = img
        print(f"  加载: {path.name} ({img.width}x{img.height})")

    max_w = max(img.width for img in images.values())
    max_h = max(img.height for img in images.values())
    for name, img in images.items():
        if img.size != (max_w, max_h):
            images[name] = img.resize((max_w, max_h), Image.Resampling.LANCZOS)
    return images


# ============================================================
# Step 2: Blender 贴图更新 + 渲染
# ============================================================

def step2_blender():
    """调用 Blender 更新纹理引用并渲染两个摄像机。"""
    print("\n" + "=" * 50)
    print("Step 2: Blender 纹理更新 + 渲染")
    print("=" * 50)

    if not os.path.exists(BLENDER):
        print(f"  [错误] Blender 未找到: {BLENDER}")
        return False

    WORK_DIR.mkdir(exist_ok=True)

    # 生成 Blender 执行脚本
    blender_script = _generate_blender_script()
    script_path = BASE_DIR / "_blender_task.py"
    script_path.write_text(blender_script, encoding="utf-8")

    blend_path = ASSETS_DIR / "block-uv.blend"

    print(f"  启动 Blender...")
    result = subprocess.run(
        [BLENDER, "--background", str(blend_path), "--python", str(script_path)],
        cwd=str(BASE_DIR),
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  [错误] Blender 退出码: {result.returncode}")
        if result.stderr:
            print(f"  stderr: {result.stderr[:500]}")
        script_path.unlink(missing_ok=True)
        return False

    script_path.unlink(missing_ok=True)

    # 验证渲染输出
    renders = ["render_图标相机.png", "render_拍脸图相机.png"]
    for r in renders:
        p = WORK_DIR / r
        if p.is_file():
            print(f"  [渲染完成] {r} ({p.stat().st_size / 1024:.0f} KB)")
        else:
            print(f"  [错误] 渲染缺失: {r}")
            return False
    return True


def _generate_blender_script():
    """生成 Blender 内部执行的 Python 脚本。"""
    return f'''
import bpy
import os

BASE_DIR = r"{BASE_DIR}"
INPUT_DIR = os.path.join(BASE_DIR, "input")
WORK_DIR = os.path.join(BASE_DIR, ".work")
os.makedirs(WORK_DIR, exist_ok=True)

# 材质 → uv_out 映射
MATERIAL_MAP = {{
    "羊毛":   os.path.join(INPUT_DIR, "羊毛", "uv_out_羊毛.png"),
    "橡木板": os.path.join(INPUT_DIR, "橡木板", "uv_out_橡木板.png"),
    "末地石": os.path.join(INPUT_DIR, "末地石", "uv_out_末地石.png"),
    "黑曜石": os.path.join(INPUT_DIR, "黑曜石", "uv_out_黑曜石.png"),
}}

print("--- 更新纹理引用 ---")
for mat_name, tex_path in MATERIAL_MAP.items():
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.node_tree:
        print(f"  [跳过] 材质: {{mat_name}}")
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            old = node.image.filepath
            new_img = bpy.data.images.load(tex_path)
            node.image = new_img
            print(f"  [{{mat_name}}] {{old}} → {{tex_path}}")

            old_img_name = os.path.basename(old)
            if old_img_name in bpy.data.images and bpy.data.images[old_img_name].users == 0:
                bpy.data.images.remove(bpy.data.images[old_img_name])

print("--- 渲染摄像机 ---")
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100

for cam_name in ["图标相机", "拍脸图相机"]:
    cam = bpy.data.objects.get(cam_name)
    if not cam or cam.type != 'CAMERA':
        print(f"  [跳过] 摄像机: {{cam_name}}")
        continue
    scene.camera = cam
    out = os.path.join(WORK_DIR, f"render_{{cam_name}}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"  渲染: {{out}}")

bpy.ops.wm.save_mainfile()
print("--- Blender 任务完成 ---")
'''


# ============================================================
# Step 3: 固定尺寸覆盖 PSD 图层 + 导出 PNG
# ============================================================

def step3_psd():
    """用 Blender 渲染图直接替换 PSD 中的图层，使用固定尺寸，保持原位置。"""
    print("\n" + "=" * 50)
    print("Step 3: 渲染图 → PSD 图层替换 + 导出 (固定尺寸方案)")
    print("=" * 50)

    from psd_tools import PSDImage

    OUTPUT_DIR.mkdir(exist_ok=True)

    # PSD → (目标图层名, 对应渲染图, 用户指定固定宽, 用户指定固定高)
    psd_tasks = [
        ("bg.psd",    "render", "render_拍脸图相机.png", 724, 346),
        ("tab.psd",   "render", "render_图标相机.png",    63,  66),
        ("lobby.psd", "render", "render_图标相机.png",    53,  55),
    ]

    for psd_name, layer_name, replace_png, target_w, target_h in psd_tasks:
        psd_path = ASSETS_DIR / psd_name
        if not psd_path.is_file():
            print(f"  [跳过] {psd_name} 不存在")
            continue

        render_path = WORK_DIR / replace_png
        if not render_path.is_file():
            print(f"    [错误] 渲染图不存在: {replace_png}")
            continue

        print(f"  处理: {psd_name} (强制尺寸: {target_w}x{target_h})")
        psd = PSDImage.open(str(psd_path))
        _replace_layer_in_psd(psd, layer_name, render_path, target_w, target_h)
        psd.save(str(psd_path))

        # 合成导出
        composite = psd.composite(force=True)
        if composite is None:
            print(f"    [错误] {psd_name} 合成失败")
            continue

        out = OUTPUT_DIR / f"{psd_path.stem}.png"
        composite.save(str(out), "PNG")
        print(f"    已导出: output/{out.name} ({composite.width}x{composite.height})")


def _replace_layer_in_psd(psd, layer_name, replacement_path, target_w, target_h):
    """精确替换 PSD 中的图层，先裁切有效像素再缩放到目标尺寸，保持原位置。"""
    from psd_tools.api.layers import PixelLayer
    from PIL import Image

    old = _find_layer(psd, layer_name)
    if old is None:
        print(f"    [提示] 未找到 '{layer_name}' 图层，跳过")
        return False

    # 1. 锁定原图层坐标和混合属性
    orig_left, orig_top = old.left, old.top
    blend_mode = old.blend_mode
    opacity = old.opacity
    visible = old.visible

    parent = old.parent
    siblings = list(parent)
    old_index = siblings.index(old)

    # 2. 先裁切有效像素区域，再缩放到目标尺寸
    replacement = Image.open(str(replacement_path)).convert("RGBA")
    replacement = _crop_effective(replacement)
    if replacement.size != (target_w, target_h):
        print(f"    [缩放] 裁切后 {replacement.size} → 调整为 {target_w}x{target_h}")
        replacement = replacement.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # 3. 移除旧图层
    parent.remove(old)

    # 4. 在原位置创建新图层
    new_layer = PixelLayer.frompil(
        replacement, parent,
        name=layer_name,
        top=orig_top, left=orig_left,
    )
    new_layer.blend_mode = blend_mode
    new_layer.opacity = opacity
    new_layer.visible = visible

    # 5. 还原图层深度
    steps_down = len(list(parent)) - 1 - old_index
    for _ in range(steps_down):
        new_layer.move_down()

    print(f"    [成功] '{layer_name}' 已在原坐标({orig_left}, {orig_top})处安全替换。")
    return True


def _crop_effective(img):
    """裁切掉完全透明的边缘区域，保留有效像素。"""
    import numpy as np
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    if not rows.any() or not cols.any():
        return img
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    return img.crop((x_min, y_min, x_max + 1, y_max + 1))


def _find_layer(layers, name):
    for layer in layers:
        if layer.name == name:
            return layer
        if hasattr(layer, '__iter__'):
            result = _find_layer(layer, name)
            if result:
                return result
    return None


# ============================================================
# 主流程
# ============================================================

def main():
    print("Block-UV 一键流水线")
    print(f"工作目录: {BASE_DIR}\n")

    # Step 1
    try:
        step1_cubemap()
    except Exception as e:
        print(f"\n[严重错误] Step 1 失败: {e}")
        sys.exit(1)

    # Step 2
    try:
        ok = step2_blender()
        if not ok:
            print(f"\n[严重错误] Step 2 失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n[严重错误] Step 2 失败: {e}")
        sys.exit(1)

    # Step 3
    try:
        step3_psd()
    except Exception as e:
        print(f"\n[严重错误] Step 3 失败: {e}")
        sys.exit(1)

    # 清理临时目录
    if WORK_DIR.is_dir():
        shutil.rmtree(WORK_DIR)
        print(f"\n已清理临时目录: .work/")

    print(f"\n{'=' * 50}")
    print("全部完成! 输出文件:")
    for f in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"  output/{f.name} ({f.stat().st_size / 1024:.0f} KB)")
    print("=" * 50)


if __name__ == "__main__":
    main()
