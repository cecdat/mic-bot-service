import requests
import json
import time
from datetime import datetime, timedelta

class BingWallpaper:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 3600  # 1小时缓存
    
    def get_wallpaper_url(self):
        """获取Bing每日壁纸URL"""
        current_time = time.time()
        
        # 检查缓存
        if 'wallpaper_url' in self.cache:
            url, timestamp = self.cache['wallpaper_url']
            if current_time - timestamp < self.cache_duration:
                return url
        
        try:
            # 获取Bing每日壁纸信息
            api_url = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('images') and len(data['images']) > 0:
                image_info = data['images'][0]
                # 构建完整URL
                base_url = "https://cn.bing.com"
                wallpaper_url = base_url + image_info['url']
                
                # 缓存结果
                self.cache['wallpaper_url'] = (wallpaper_url, current_time)
                
                return wallpaper_url
            else:
                # 如果API失败，返回默认壁纸
                return "https://cn.bing.com/th?id=OHR.BingWallpaper_ZH-CN1234567890&rf=LaDigue_1920x1080.jpg&pid=hp"
                
        except Exception as e:
            print(f"获取Bing壁纸失败: {e}")
            # 返回默认壁纸
            return "https://cn.bing.com/th?id=OHR.BingWallpaper_ZH-CN1234567890&rf=LaDigue_1920x1080.jpg&pid=hp"

# 全局实例
bing_wallpaper = BingWallpaper()
