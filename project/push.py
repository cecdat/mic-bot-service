import requests
from .models import PushConfig
from .db import db
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('push_service')

def send_bark_notification(url, title, body):
    """向指定的 Bark URL 发送推送。"""
    try:
        # Bark URL 格式通常是 https://api.day.app/YOUR_KEY/
        # 我们需要将标题和内容附加到路径中
        full_url = f"{url.rstrip('/')}/{requests.utils.quote(title)}/{requests.utils.quote(body)}"
        logger.info(f"发送Bark推送: {full_url}")
        
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        
        logger.info(f"✅ 成功发送Bark推送到 {url}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 发送Bark推送失败 {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 发送Bark推送时发生未知错误 {url}: {e}")
        return False

def trigger_push_notification(event_type, title, body):
    """
    根据事件类型，查找所有订阅了该事件的配置，并发送推送。
    event_type: 'node_online', 'node_offline', 'account_error', 'verification_code'
    """
    logger.info(f"触发推送通知: {event_type} - {title} - {body}")
    
    try:
        configs_to_notify = []
        
        # 查询订阅了该事件的推送配置
        if event_type == 'node_online':
            configs_to_notify = PushConfig.query.filter_by(notify_on_node_online=True, status=1).all()
        elif event_type == 'node_offline':
            configs_to_notify = PushConfig.query.filter_by(notify_on_node_offline=True, status=1).all()
        elif event_type == 'account_error':
            configs_to_notify = PushConfig.query.filter_by(notify_on_account_error=True, status=1).all()
        elif event_type == 'verification_code':
            configs_to_notify = PushConfig.query.filter_by(notify_on_verification_code=True, status=1).all()
        else:
            logger.warning(f"未知的事件类型: {event_type}")
            return False

        logger.info(f"找到 {len(configs_to_notify)} 个配置订阅了 {event_type} 事件")
        
        if not configs_to_notify:
            logger.warning(f"没有找到订阅 {event_type} 事件的推送配置")
            return False
        
        success_count = 0
        for config in configs_to_notify:
            logger.info(f"发送通知到: {config.url}")
            if send_bark_notification(config.url, title, body):
                success_count += 1
        
        logger.info(f"推送完成: {success_count}/{len(configs_to_notify)} 成功")
        return success_count > 0
            
    except Exception as e:
        logger.error(f"❌ 触发推送通知时出错: {e}")
        
        # 如果数据库查询失败，尝试直接发送到已知的URL
        try:
            logger.info("尝试直接查询数据库...")
            # 从数据库直接查询
            import subprocess
            result = subprocess.run([
                "docker", "exec", "postgres-db-service", "psql", 
                "-U", "user", "-d", "rewards_db",
                "-c", f"SELECT url FROM push_configs WHERE notify_on_{event_type} = true AND status = 1;"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('https://'):
                        url = line.strip()
                        logger.info(f"直接发送到: {url}")
                        send_bark_notification(url, title, body)
        except Exception as direct_error:
            logger.error(f"直接发送也失败了: {direct_error}")
        
        return False
