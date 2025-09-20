#!/usr/bin/env python3
"""
生成机器人样式的favicon.ico文件
"""

from PIL import Image, ImageDraw
import os

def create_robot_favicon():
    """创建机器人样式的favicon"""
    
    # 创建32x32的图像
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 定义颜色
    blue = (30, 159, 255)  # #1E9FFF
    dark_blue = (13, 124, 232)  # #0D7CE8
    white = (255, 255, 255)
    red = (255, 107, 107)  # #FF6B6B
    green = (95, 184, 120)  # #5FB878
    
    # 机器人头部 (8,4) 到 (24,16)
    draw.rounded_rectangle([8, 4, 24, 16], radius=2, fill=blue, outline=dark_blue, width=1)
    
    # 机器人眼睛
    draw.ellipse([10, 6, 14, 10], fill=white)  # 左眼
    draw.ellipse([18, 6, 22, 10], fill=white)  # 右眼
    draw.ellipse([11, 7, 13, 9], fill=blue)    # 左眼珠
    draw.ellipse([19, 7, 21, 9], fill=blue)    # 右眼珠
    
    # 机器人嘴巴
    draw.rounded_rectangle([14, 11, 18, 13], radius=1, fill=white)
    
    # 机器人天线
    draw.line([16, 4, 16, 2], fill=red, width=2)
    draw.ellipse([15, 1, 17, 3], fill=red)
    
    # 机器人身体 (6,16) 到 (26,28)
    draw.rounded_rectangle([6, 16, 26, 28], radius=2, fill=blue, outline=dark_blue, width=1)
    
    # 机器人胸部面板
    draw.rounded_rectangle([10, 18, 22, 26], radius=1, fill=white)
    
    # 机器人手臂
    draw.rounded_rectangle([2, 18, 6, 26], radius=2, fill=blue, outline=dark_blue, width=1)   # 左臂
    draw.rounded_rectangle([26, 18, 30, 26], radius=2, fill=blue, outline=dark_blue, width=1) # 右臂
    
    # 机器人腿部
    draw.rounded_rectangle([8, 28, 14, 32], radius=1, fill=blue, outline=dark_blue, width=1)   # 左腿
    draw.rounded_rectangle([18, 28, 24, 32], radius=1, fill=blue, outline=dark_blue, width=1)  # 右腿
    
    # 装饰性元素
    draw.ellipse([11, 21, 13, 23], fill=green)  # 左装饰
    draw.ellipse([19, 21, 21, 23], fill=green)  # 右装饰
    
    return img

def main():
    """主函数"""
    try:
        # 创建favicon图像
        favicon_img = create_robot_favicon()
        
        # 保存为PNG格式（用于预览）
        favicon_img.save('static/favicon.png', 'PNG')
        print("✅ 已生成 favicon.png")
        
        # 创建不同尺寸的图标
        sizes = [16, 32, 48]
        images = []
        
        for size in sizes:
            resized = favicon_img.resize((size, size), Image.Resampling.LANCZOS)
            images.append(resized)
        
        # 保存为ICO格式
        images[0].save('static/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
        print("✅ 已生成 favicon.ico")
        
        print("\n🎉 机器人favicon生成完成！")
        print("📁 文件位置:")
        print("   - static/favicon.ico (浏览器使用)")
        print("   - static/favicon.png (预览用)")
        
    except Exception as e:
        print(f"❌ 生成favicon失败: {e}")

if __name__ == "__main__":
    main()
