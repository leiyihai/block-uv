"""用两个摄像机分别渲染到 E:\block-uv 目录。
用法: blender --background block-uv.blend --python render_cameras.py
"""
import bpy
import os

OUTPUT_DIR = r"E:\block-uv"
CAMERAS = ["图标相机", "拍脸图相机"]

os.chdir(OUTPUT_DIR)
scene = bpy.context.scene

# 确保 EEVEE 渲染
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100

for cam_name in CAMERAS:
    cam_obj = bpy.data.objects.get(cam_name)
    if not cam_obj or cam_obj.type != 'CAMERA':
        print(f"[跳过] 摄像机 '{cam_name}' 未找到")
        continue

    scene.camera = cam_obj
    out_path = os.path.join(OUTPUT_DIR, f"render_{cam_name}.png")
    scene.render.filepath = out_path

    print(f"渲染中: {cam_name} → {out_path}")
    bpy.ops.render.render(write_still=True)
    print(f"  完成!")

print("\n全部渲染完成!")
