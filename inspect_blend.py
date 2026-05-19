"""在 Blender 中运行，列出所有物体、材质和纹理节点。
用法: blender --background block-uv.blend --python inspect_blend.py
"""
import bpy
import os

os.chdir(r"E:\block-uv")

print("=" * 60)
print("物体列表:")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"\n物体: {obj.name} (MESH)")
        if obj.data.materials:
            for slot in obj.material_slots:
                mat = slot.material
                if mat:
                    print(f"  材质: {mat.name}")
                    if mat.use_nodes:
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                img_path = node.image.filepath if node.image else "无图片"
                                print(f"    纹理节点 '{node.name}': {img_path}")
                else:
                    print(f"  材质槽: 空")
        else:
            print("  无材质")

print("\n" + "=" * 60)
print("所有图片资源:")
for img in bpy.data.images:
    print(f"  {img.name}: {img.filepath} ({img.size[0]}x{img.size[1]})")
