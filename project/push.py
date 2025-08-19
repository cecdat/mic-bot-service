import requests
from .models import PushConfig
from .db import db

def send_bark_notification(url, title, body):
    """向指定的 Bark URL 发送推送。"""
    try:
        # Bark URL 格式通常是 https://api.day.app/YOUR_KEY/
        # 我们需要将标题和内容附加到路径中
        full_url = f"{url.rstrip('/')}/{requests.utils.quote(title)}/{requests.utils.quote(body)}"
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        print(f"Successfully sent Bark notification to {url}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Bark notification to {url}: {e}")

def trigger_push_notification(event_type, title, body):
    """
    根据事件类型，查找所有订阅了该事件的配置，并发送推送。
    event_type: 'node_online', 'node_offline', 'account_error', 'verification_code'
    """
    try:
        configs_to_notify = []
        if event_type == 'node_online':
            configs_to_notify = PushConfig.query.filter_by(notify_on_node_online=True, status=1).all()
        elif event_type == 'node_offline':
            configs_to_notify = PushConfig.query.filter_by(notify_on_node_offline=True, status=1).all()
        elif event_type == 'account_error':
            configs_to_notify = PushConfig.query.filter_by(notify_on_account_error=True, status=1).all()
        elif event_type == 'verification_code':
            configs_to_notify = PushConfig.query.filter_by(notify_on_verification_code=True, status=1).all()

        print(f"Found {len(configs_to_notify)} configs for {event_type} event")
        
        for config in configs_to_notify:
            print(f"Sending notification to: {config.url}")
            send_bark_notification(config.url, title, body)
            
    except Exception as e:
        print(f"Error in trigger_push_notification: {e}")
        # 如果数据库查询失败，尝试直接发送到已知的URL
        try:
            # 从数据库直接查询
            import subprocess
            result = subprocess.run([
                "docker", "exec", "postgres-db-service", "psql", 
                "-U", "user", "-d", "rewards_db",
                "-c", "SELECT url FROM push_configs WHERE notify_on_verification_code = true AND status = 1;"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('https://'):
                        url = line.strip()
                        print(f"Direct sending to: {url}")
                        send_bark_notification(url, title, body)
        except Exception as direct_error:
            print(f"Direct sending also failed: {direct_error}")
