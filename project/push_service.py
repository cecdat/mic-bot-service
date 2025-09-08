#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import re
import logging
from datetime import datetime
from .models import PushConfig
from .db import db

# 配置推送服务日志记录器
logger = logging.getLogger('push_service')

class PushService:
    """推送服务类，支持多种推送渠道"""
    
    def __init__(self):
        self.channels = {
            'bark': self._send_bark,
            'server_chan': self._send_server_chan,
            'telegram': self._send_telegram,
            'dingding': self._send_dingding,
            'qq': self._send_qq,
            'pushplus': self._send_pushplus,
            'wecom_app': self._send_wecom_app,
            'wecom_key': self._send_wecom_key,
            'feishu': self._send_feishu,
            'webhook': self._send_webhook,
            'xiatuisha': self._send_xiatuisha
        }
    
    def send_notification(self, title, content, event_type=None):
        """发送通知到所有启用的推送渠道"""
        try:
            # 获取所有启用的推送配置
            configs = PushConfig.query.filter_by(is_enabled=True, status=1).all()
            
            if not configs:
                logger.debug("没有启用的推送配置")
                return False
            
            success_count = 0
            total_count = len(configs)
            
            for config in configs:
                # 检查事件类型是否匹配
                if event_type and not self._should_notify(config, event_type):
                    continue
                
                try:
                    # 获取推送函数
                    send_func = self.channels.get(config.channel)
                    if not send_func:
                        logger.warning(f"不支持的推送渠道: {config.channel}")
                        continue
                    
                    # 解析配置数据
                    config_data = json.loads(config.config_data) if config.config_data else {}
                    
                    # 发送推送
                    result = send_func(title, content, config_data)
                    if result:
                        success_count += 1
                        logger.info(f"推送成功: {config.name} ({config.channel})")
                    else:
                        logger.warning(f"推送失败: {config.name} ({config.channel})")
                        
                except Exception as e:
                    logger.error(f"推送异常: {config.name} ({config.channel}) - {str(e)}")
            
            logger.info(f"推送完成: {success_count}/{total_count} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"推送服务异常: {str(e)}")
            return False
    
    def send_test_notification(self, config, title, content):
        """发送测试推送通知"""
        try:
            logger.info(f"开始测试推送: 渠道={config.channel}, 标题={title}")
            
            # 获取推送函数
            send_func = self.channels.get(config.channel)
            if not send_func:
                logger.warning(f"不支持的推送渠道: {config.channel}")
                return False
            
            # 解析配置数据
            config_data = json.loads(config.config_data) if config.config_data else {}
            logger.debug(f"配置数据: {config_data}")
            
            # 发送推送
            result = send_func(title, content, config_data)
            logger.info(f"推送结果: {result}")
            return result
                
        except Exception as e:
            logger.error(f"测试推送失败: {str(e)}")
            return False
    
    def _should_notify(self, config, event_type):
        """检查配置是否应该发送该类型的事件通知"""
        event_mapping = {
            'node_online': config.notify_on_node_online,
            'node_offline': config.notify_on_node_offline,
            'account_error': config.notify_on_account_error,
            'verification_code': config.notify_on_verification_code,
            'task_completed': config.notify_on_task_completed,
            'system_alert': config.notify_on_system_alert,
            'task_start': config.notify_on_task_start,
            'task_finish': config.notify_on_task_finish
        }
        return event_mapping.get(event_type, False)
    
    def _send_bark(self, title, content, config_data):
        """Bark推送"""
        try:
            # 支持新旧字段名
            token = config_data.get('bark_token') or config_data.get('token')
            if not token:
                logger.warning("Bark推送失败: 缺少token")
                return False
            
            # 检查是否有自定义服务器地址
            push_url = config_data.get('bark_push_url') or config_data.get('push_url')
            if push_url:
                # 使用自定义服务器
                if not push_url.endswith('/'):
                    push_url += '/'
                url = f"{push_url}{token}/{title}/{urllib.parse.quote_plus(content)}"
                logger.debug(f"Bark自定义服务器推送URL: {url}")
            else:
                # 使用官方服务器
                url = f"https://api.day.app/{token}/{title}/{urllib.parse.quote_plus(content)}"
                logger.debug(f"Bark官方服务器推送URL: {url}")
            
            response = requests.get(url, timeout=10)
            logger.debug(f"Bark推送响应: {response.status_code}, {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Bark推送异常: {e}")
            return False
    
    def _send_server_chan(self, title, content, config_data):
        """Server酱推送"""
        try:
            push_key = config_data.get('push_key')
            if not push_key:
                return False
            
            url = f"https://sctapi.ftqq.com/{push_key}.send"
            data = {
                "text": title,
                "desp": content.replace("\n", "\n\n")
            }
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            return result.get('errno') == 0
        except:
            return False
    
    def _send_telegram(self, title, content, config_data):
        """Telegram推送"""
        try:
            # 支持新旧字段名
            bot_token = config_data.get('tg_bot_token') or config_data.get('bot_token')
            user_id = config_data.get('tg_user_id') or config_data.get('user_id')
            api_host = config_data.get('tg_api_host') or config_data.get('api_host')
            proxy_ip = config_data.get('tg_proxy_ip') or config_data.get('proxy_ip')
            proxy_port = config_data.get('tg_proxy_port') or config_data.get('proxy_port')
            
            if not bot_token or not user_id:
                return False
            
            if api_host:
                if 'http' in api_host:
                    url = f"{api_host}/bot{bot_token}/sendMessage"
                else:
                    url = f"https://{api_host}/bot{bot_token}/sendMessage"
            else:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {
                'chat_id': str(user_id),
                'text': f'{title}\n\n{content}',
                'disable_web_page_preview': 'true'
            }
            
            proxies = None
            if proxy_ip and proxy_port:
                proxy_str = f"http://{proxy_ip}:{proxy_port}"
                proxies = {"http": proxy_str, "https": proxy_str}
            
            response = requests.post(url=url, headers=headers, params=payload, proxies=proxies, timeout=10)
            result = response.json()
            return result.get('ok', False)
        except:
            return False
    
    def _send_dingding(self, title, content, config_data):
        """钉钉推送"""
        try:
            # 支持新旧字段名
            bot_token = config_data.get('dd_bot_token') or config_data.get('bot_token')
            bot_secret = config_data.get('dd_bot_secret') or config_data.get('bot_secret')
            
            if not bot_token or not bot_secret:
                return False
            
            timestamp = str(round(time.time() * 1000))
            secret_enc = bot_secret.encode('utf-8')
            string_to_sign = f'{timestamp}\n{bot_secret}'
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            
            url = f'https://oapi.dingtalk.com/robot/send?access_token={bot_token}&timestamp={timestamp}&sign={sign}'
            headers = {'Content-Type': 'application/json;charset=utf-8'}
            data = {
                'msgtype': 'text',
                'text': {'content': f'{title}\n\n{content}'}
            }
            
            response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=15)
            result = response.json()
            return result.get('errcode') == 0
        except:
            return False
    
    def _send_qq(self, title, content, config_data):
        """QQ推送"""
        try:
            # 支持新旧字段名
            skey = config_data.get('qq_skey') or config_data.get('skey')
            mode = config_data.get('qq_mode') or config_data.get('mode')
            
            if not skey or not mode:
                return False
            
            url = f"https://qmsg.zendee.cn/{mode}/{skey}"
            payload = {'msg': f"{title}\n\n{content}".encode('utf-8')}
            response = requests.post(url=url, params=payload, timeout=10)
            result = response.json()
            return result.get('code') == 0
        except:
            return False
    
    def _send_pushplus(self, title, content, config_data):
        """PushPlus推送"""
        try:
            # 支持新旧字段名
            token = config_data.get('pushplus_token') or config_data.get('token')
            if not token:
                return False
            
            url = 'http://www.pushplus.plus/send'
            data = {
                "token": token,
                "title": title,
                "content": content
            }
            response = requests.post(url=url, data=json.dumps(data), timeout=10)
            result = response.json()
            return result.get('code') == 200
        except:
            return False
    
    def _send_wecom_app(self, title, content, config_data):
        """企业微信应用推送"""
        try:
            qywx_am = config_data.get('qywx_am')
            if not qywx_am:
                return False
            
            qywx_am_list = re.split(',', qywx_am)
            if len(qywx_am_list) < 4:
                return False
            
            corpid = qywx_am_list[0]
            corpsecret = qywx_am_list[1]
            touser = qywx_am_list[2]
            agentid = qywx_am_list[3]
            
            # 获取access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}"
            token_response = requests.get(token_url, timeout=10)
            token_result = token_response.json()
            
            if token_result.get('errcode') != 0:
                return False
            
            access_token = token_result.get('access_token')
            
            # 发送消息
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            data = {
                "touser": touser,
                "msgtype": "text",
                "agentid": agentid,
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }
            
            response = requests.post(send_url, data=json.dumps(data), timeout=10)
            result = response.json()
            return result.get('errcode') == 0
        except:
            return False
    
    def _send_wecom_key(self, title, content, config_data):
        """企业微信机器人推送"""
        try:
            # 支持新旧字段名
            key = config_data.get('wecom_key') or config_data.get('key')
            if not key:
                return False
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }
            
            response = requests.post(url=url, data=json.dumps(data), timeout=10)
            result = response.json()
            return result.get('errcode') == 0
        except:
            return False
    
    def _send_feishu(self, title, content, config_data):
        """飞书推送"""
        try:
            # 支持新旧字段名
            key = config_data.get('fs_key') or config_data.get('key')
            if not key:
                return False
            
            url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{key}"
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n\n{content}"
                }
            }
            
            response = requests.post(url=url, data=json.dumps(data), timeout=10)
            result = response.json()
            return result.get('code') == 0
        except:
            return False
    
    def _send_webhook(self, title, content, config_data):
        """自定义Webhook推送"""
        try:
            # 支持新旧字段名
            url = config_data.get('webhook_url') or config_data.get('url')
            method = config_data.get('webhook_method') or config_data.get('method', 'POST')
            headers = config_data.get('webhook_headers') or config_data.get('headers', {})
            template = config_data.get('webhook_template') or config_data.get('template', '{title}\n\n{content}')
            
            if not url:
                return False
            
            # 格式化消息内容
            message = template.format(title=title, content=content)
            
            if method == 'GET':
                params = {'title': title, 'content': content, 'message': message}
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                data = {
                    'title': title,
                    'content': content,
                    'message': message,
                    'timestamp': int(time.time())
                }
                response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
            
            return response.status_code in [200, 201, 202]
        except:
            return False

    def _send_xiatuisha(self, title, content, config_data):
        """虾推啥推送"""
        try:
            # 获取token
            token = config_data.get('xiatuisha_token') or config_data.get('token')
            if not token:
                logger.warning("虾推啥推送失败: 缺少token")
                return False
            
            # 构建请求URL
            base_url = "https://wx.xtuis.cn/{}.send".format(token)
            
            # 准备参数
            params = {
                'text': title or '通知',
                'desp': content or ''
            }
            
            # 发送GET请求
            response = requests.get(base_url, params=params, timeout=10)
            
            # 检查响应
            if response.status_code == 200:
                response_text = response.text.strip()
                if 'success' in response_text.lower():
                    logger.info("虾推啥推送成功")
                    return True
                else:
                    logger.warning(f"虾推啥推送失败: {response_text}")
                    return False
            else:
                logger.warning(f"虾推啥推送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"虾推啥推送异常: {str(e)}")
            return False

# 全局推送服务实例
push_service = PushService()
