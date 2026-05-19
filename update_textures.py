"""替换 block-uv.blend 中方块材质的贴图引用为 uv_out.png。
用法: blender --background block-uv.blend --python update_textures.py
"""
import bpy
import os

BASE = r"E:\block-uv"

# 材质名 → 对应 uv_out.png 路径
MATERIAL_MAP = {
    "羊毛":   os.path.join(BASE, "羊毛", "uv_out.png"),
    "橡木板": os.path.join(BASE, "橡木板", "uv_out.png"),
    "末地石": os.path.join(BASE, "末地石", "uv_out.png"),
    "黑曜石": os.path.join(BASE, "黑曜石", "uv_out.png"),
}

os.chdir(BASE)

for mat_name, new_path in MATERIAL_MAP.items():
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        print(f"[跳过] 材质 '{mat_name}' 不存在")
        continue

    if not mat.node_tree:
        print(f"[跳过] 材质 '{mat_name}' 没有节点树")
        continue

    replaced = 0
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            old_path = node.image.filepath
            print(f"[{mat_name}] {old_path}  →  {new_path}")

            # 加载新图片替换
            new_img = bpy.data.images.load(new_path)
            node.image = new_img
            replaced += 1

            # 移除旧图片数据块（如果没有其他引用）
            old_img = bpy.data.images.get(os.path.basename(old_path))
            if old_img and old_img.users == 0:
                bpy.data.images.remove(old_img)

    if replaced == 0:
        print(f"[警告] 材质 '{mat_name}' 中未找到纹理节点")

print("\n保存文件...")
bpy.ops.wm.save_mainfile()
print("完成！")
