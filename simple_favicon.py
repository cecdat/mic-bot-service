#!/usr/bin/env python3
# 简单的favicon生成器
import struct
import os

def create_simple_ico():
    """创建一个简单的16x16 ICO文件"""
    
    # ICO文件头 (6字节)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type, Count
    
    # 图像目录项 (16字节)
    width = 16
    height = 16
    colors = 0
    reserved = 0
    planes = 1
    bits_per_pixel = 24
    image_size = width * height * 3  # RGB
    image_offset = 22  # 6 + 16
    
    ico_dir = struct.pack('<BBBBHHII', 
                          width, height, colors, reserved,
                          planes, bits_per_pixel, image_size, image_offset)
    
    # 创建简单的蓝色图像数据
    image_data = b''
    for y in range(height):
        for x in range(width):
            # BGR格式
            if (x > 2 and x < 13 and y > 2 and y < 13):
                image_data += b'\xFF\x9F\x1E'  # 蓝色 #1E9FFF
            else:
                image_data += b'\xFF\xFF\xFF'  # 白色
    
    # 组合完整的ICO文件
    ico_data = ico_header + ico_dir + image_data
    
    # 写入文件
    with open('static/favicon.ico', 'wb') as f:
        f.write(ico_data)
    
    return len(ico_data)

if __name__ == "__main__":
    try:
        size = create_simple_ico()
        print(f"Generated favicon.ico ({size} bytes)")
    except Exception as e:
        print(f"Error: {e}")
