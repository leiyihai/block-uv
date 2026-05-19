"""
将 6 张立方体贴图拼接为 4x3 横向十字布局 UV 贴图。
用法: python cubemap_to_uv.py <folder_path1> [folder_path2 ...]
"""

import sys
from pathlib import Path

from PIL import Image

FACE_NAMES = ["top", "left", "front", "right", "back", "bottom"]
GRID_POSITIONS = {
    "top":    (1, 0),
    "left":   (0, 1),
    "front":  (1, 1),
    "right":  (2, 1),
    "back":   (3, 1),
    "bottom": (1, 2),
}
EXTENSIONS = {".png", ".jpg", ".jpeg"}


def find_faces(folder: Path) -> dict[str, Path] | None:
    """扫描文件夹，返回 {face_name: file_path} 字典；缺失则返回 None。"""
    faces: dict[str, Path] = {}
    for name in FACE_NAMES:
        candidates = [folder / f"{name}{ext}" for ext in EXTENSIONS]
        found = [p for p in candidates if p.is_file()]
        if not found:
            print(f"  [跳过] 缺少 '{name}' 图片，文件夹: {folder}")
            return None
        faces[name] = found[0]
    return faces


def load_and_normalize(faces: dict[str, Path]) -> dict[str, Image.Image]:
    """加载 6 张图，统一缩放到最大尺寸，保持宽高比。"""
    images: dict[str, Image.Image] = {}
    for name, path in faces.items():
        img = Image.open(path).convert("RGBA")
        images[name] = img
        print(f"  加载: {path.name} ({img.width}x{img.height})")

    max_w = max(img.width for img in images.values())
    max_h = max(img.height for img in images.values())

    if any(img.size != (max_w, max_h) for img in images.values()):
        print(f"  归一化目标尺寸: {max_w}x{max_h}")
        for name, img in images.items():
            if img.size != (max_w, max_h):
                images[name] = img.resize((max_w, max_h), Image.Resampling.LANCZOS)

    return images


def compose(images: dict[str, Image.Image], width: int, height: int) -> Image.Image:
    """按 4x3 横向十字布局拼接。"""
    canvas = Image.new("RGBA", (width * 4, height * 3), (0, 0, 0, 0))

    for name, img in images.items():
        col, row = GRID_POSITIONS[name]
        x, y = col * width, row * height
        # 传入自身作为 mask 保留透明度
        canvas.paste(img, (x, y), img)

    return canvas


def process_folder(folder: Path) -> None:
    print(f"\n处理文件夹: {folder}")

    faces = find_faces(folder)
    if faces is None:
        return

    try:
        images = load_and_normalize(faces)
        w, h = next(iter(images.values())).size
        result = compose(images, w, h)

        out_path = folder / "uv_out.png"
        result.save(out_path, "PNG")
        print(f"  [成功] 已导出: {out_path} ({result.width}x{result.height})")
    except Exception as e:
        print(f"  [错误] 处理失败: {e}")


def main(folder_paths: list[str]) -> None:
    for fp in folder_paths:
        folder = Path(fp)
        if not folder.is_dir():
            print(f"[跳过] 路径不存在或不是文件夹: {fp}")
            continue
        process_folder(folder)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python cubemap_to_uv.py <folder_path1> [folder_path2 ...]")
        sys.exit(1)
    main(sys.argv[1:])
