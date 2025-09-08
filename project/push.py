import requests
from .models import PushConfig
from .db import db
from .push_service import push_service
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
    event_type: 'node_online', 'node_offline', 'account_error', 'verification_code', 'task_completed', 'system_alert'
    """
    logger.info(f"触发推送通知: {event_type} - {title} - {body}")
    
    try:
        # 使用新的推送服务
        result = push_service.send_notification(title, body, event_type)
        
        if result:
            logger.info(f"✅ 推送通知发送成功: {event_type}")
        else:
            logger.warning(f"⚠️ 推送通知发送失败: {event_type}")
        
        return result
            
    except Exception as e:
        logger.error(f"❌ 触发推送通知时出错: {e}")
        
        # 如果新推送服务失败，尝试使用旧的Bark推送作为备用
        try:
            logger.info("尝试使用备用Bark推送...")
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
            elif event_type == 'task_completed':
                configs_to_notify = PushConfig.query.filter_by(notify_on_task_completed=True, status=1).all()
            elif event_type == 'system_alert':
                configs_to_notify = PushConfig.query.filter_by(notify_on_system_alert=True, status=1).all()
            elif event_type == 'task_start':
                configs_to_notify = PushConfig.query.filter_by(notify_on_task_start=True, status=1).all()
            elif event_type == 'task_finish':
                configs_to_notify = PushConfig.query.filter_by(notify_on_task_finish=True, status=1).all()
            else:
                logger.warning(f"未知的事件类型: {event_type}")
                return False

            logger.info(f"找到 {len(configs_to_notify)} 个配置订阅了 {event_type} 事件")
            
            if not configs_to_notify:
                logger.warning(f"没有找到订阅 {event_type} 事件的推送配置")
                return False
            
            success_count = 0
            for config in configs_to_notify:
                # 检查是否是Bark配置
                if config.channel == 'bark' and config.config_data:
                    import json
                    config_data = json.loads(config.config_data) if isinstance(config.config_data, str) else config.config_data
                    token = config_data.get('token')
                    if token:
                        url = f"https://api.day.app/{token}"
                        logger.info(f"发送Bark通知到: {url}")
                        if send_bark_notification(url, title, body):
                            success_count += 1
            
            logger.info(f"备用推送完成: {success_count}/{len(configs_to_notify)} 成功")
            return success_count > 0
            
        except Exception as backup_error:
            logger.error(f"备用推送也失败了: {backup_error}")
            return False
