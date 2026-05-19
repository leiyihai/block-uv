"""列出场景中所有摄像机及渲染设置。"""
import bpy

print("=" * 60)
print("摄像机列表:")
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        print(f"  {obj.name}")
        cam = obj.data
        print(f"    位置: {obj.location}")
        print(f"    旋转: {obj.rotation_euler}")
        print(f"    类型: {cam.type}")
        print(f"    焦距: {cam.lens}mm")
        print(f"    分辨率X: {bpy.context.scene.render.resolution_x}")
        print(f"    分辨率Y: {bpy.context.scene.render.resolution_y}")
        print(f"    分辨率百分比: {bpy.context.scene.render.resolution_percentage}%")
        print()

print("渲染引擎:", bpy.context.scene.render.engine)
print("输出格式:", bpy.context.scene.render.image_settings.file_format)

# 检查是否设为当前活动摄像机
scene = bpy.context.scene
print(f"当前活动摄像机: {scene.camera.name if scene.camera else '无'}")
