from flask import Blueprint, request, jsonify, current_app
from .db import db
from .models import PushConfig
from .auth import web_login_required
import json

bp = Blueprint('api_push', __name__, url_prefix='/web_api/push')

@bp.route('/configs', methods=['GET'])
@web_login_required
def get_push_configs():
    """获取推送配置列表"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 检查表是否存在
        try:
            query = PushConfig.query
            total = query.count()
            configs = query.offset((page - 1) * limit).limit(limit).all()
            
            current_app.logger.info(f"获取推送配置列表: 总数={total}, 当前页={page}, 每页={limit}, 返回={len(configs)}条")
            
            return jsonify({
                'code': 0,
                'msg': '获取成功',
                'count': total,
                'data': [config.to_dict() for config in configs]
            })
        except Exception as db_error:
            # 如果表不存在，返回空数据
            if 'does not exist' in str(db_error):
                return jsonify({
                    'code': 0,
                    'msg': '数据库表不存在，请先执行数据库升级',
                    'count': 0,
                    'data': []
                })
            else:
                raise db_error
                
    except Exception as e:
        current_app.logger.error(f"获取推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'获取失败: {str(e)}'}), 500

@bp.route('/configs', methods=['POST'])
@web_login_required
def create_push_config():
    """创建推送配置"""
    try:
        data = request.get_json()
        current_app.logger.info(f"收到创建推送配置请求: {data}")
        
        # 验证必填字段
        if not data.get('channel'):
            current_app.logger.warning("缺少必填字段: channel")
            return jsonify({'code': 1, 'msg': '缺少必填字段: channel'}), 400
        
        # 自动生成name字段（如果未提供）
        if not data.get('name'):
            channel_labels = {
                'bark': 'Bark推送',
                'server_chan': 'Server酱',
                'telegram': 'Telegram',
                'dingding': '钉钉',
                'qq': 'QQ推送',
                'pushplus': 'PushPlus',
                'wecom_app': '企业微信应用',
                'wecom_key': '企业微信机器人',
                'feishu': '飞书',
                'webhook': '自定义Webhook',
                'xiatuisha': '虾推啥'
            }
            data['name'] = channel_labels.get(data['channel'], '推送配置')
        
        # 验证渠道是否支持
        supported_channels = ['bark', 'server_chan', 'telegram', 'dingding', 'qq', 
                            'pushplus', 'wecom_app', 'wecom_key', 'feishu', 'webhook', 'xiatuisha']
        if data['channel'] not in supported_channels:
            return jsonify({'code': 1, 'msg': f'不支持的推送渠道: {data["channel"]}'}), 400
        
        # 验证配置数据
        config_data = data.get('config_data', {})
        current_app.logger.info(f"配置数据: {config_data}")
        if not _validate_config_data(data['channel'], config_data):
            current_app.logger.warning(f"配置数据验证失败: channel={data['channel']}, config_data={config_data}")
            return jsonify({'code': 1, 'msg': '配置数据验证失败'}), 400
        
        # 创建配置
        current_app.logger.info(f"开始创建推送配置: name={data['name']}, channel={data['channel']}")
        
        # 布尔值转换函数
        def to_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'on', 'yes')
            return bool(value)
        
        config = PushConfig(
            name=data['name'],
            channel=data['channel'],
            is_enabled=to_bool(data.get('is_enabled', True)),
            config_data=json.dumps(config_data),
            notify_on_node_online=to_bool(data.get('notify_on_node_online', False)),
            notify_on_node_offline=to_bool(data.get('notify_on_node_offline', False)),
            notify_on_account_error=to_bool(data.get('notify_on_account_error', False)),
            notify_on_verification_code=to_bool(data.get('notify_on_verification_code', False)),
            notify_on_task_completed=to_bool(data.get('notify_on_task_completed', False)),
            notify_on_system_alert=to_bool(data.get('notify_on_system_alert', False)),
            notify_on_task_start=to_bool(data.get('notify_on_task_start', False)),
            notify_on_task_finish=to_bool(data.get('notify_on_task_finish', False))
        )
        
        db.session.add(config)
        current_app.logger.info(f"配置对象已添加到session: {config.name}")
        
        db.session.commit()
        current_app.logger.info(f"数据库提交成功，配置ID: {config.id}")
        
        # 验证数据是否真的写入数据库
        saved_config = PushConfig.query.get(config.id)
        if saved_config:
            current_app.logger.info(f"验证成功: 配置已保存到数据库 - {saved_config.name} ({saved_config.channel})")
        else:
            current_app.logger.error(f"验证失败: 配置未找到 - ID: {config.id}")
        
        current_app.logger.info(f"推送配置创建成功: {config.name} ({config.channel})")
        return jsonify({'code': 0, 'msg': '创建成功', 'data': config.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'创建失败: {str(e)}'}), 500

@bp.route('/configs/<int:config_id>', methods=['GET'])
@web_login_required
def get_push_config(config_id):
    """获取单个推送配置"""
    try:
        config = PushConfig.query.get(config_id)
        if not config:
            return jsonify({'code': 1, 'msg': '配置不存在'}), 404
        
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': config.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"获取推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'获取失败: {str(e)}'}), 500

@bp.route('/configs/<int:config_id>', methods=['PUT'])
@web_login_required
def update_push_config(config_id):
    """更新推送配置"""
    try:
        config = PushConfig.query.get_or_404(config_id)
        data = request.get_json()
        
        # 布尔值转换函数
        def to_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'on', 'yes')
            return bool(value)
        
        # 更新字段
        if 'name' in data:
            config.name = data['name']
        if 'channel' in data:
            if data['channel'] not in ['bark', 'xiatuisha', 'server_chan', 'telegram', 'dingding', 'qq', 
                                     'pushplus', 'wecom_app', 'wecom_key', 'feishu', 'webhook']:
                return jsonify({'code': 1, 'msg': f'不支持的推送渠道: {data["channel"]}'}), 400
            config.channel = data['channel']
        if 'is_enabled' in data:
            config.is_enabled = to_bool(data['is_enabled'])
        if 'config_data' in data:
            if not _validate_config_data(config.channel, data['config_data']):
                return jsonify({'code': 1, 'msg': '配置数据验证失败'}), 400
            config.config_data = json.dumps(data['config_data'])
        
        # 更新通知设置
        notify_fields = ['notify_on_node_online', 'notify_on_node_offline', 'notify_on_account_error',
                        'notify_on_verification_code', 'notify_on_task_completed', 'notify_on_system_alert',
                        'notify_on_task_start', 'notify_on_task_finish']
        for field in notify_fields:
            if field in data:
                setattr(config, field, to_bool(data[field]))
        
        db.session.commit()
        
        return jsonify({'code': 0, 'msg': '更新成功', 'data': config.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'更新失败: {str(e)}'}), 500

@bp.route('/configs/<int:config_id>', methods=['DELETE'])
@web_login_required
def delete_push_config(config_id):
    """删除推送配置"""
    try:
        config = PushConfig.query.get_or_404(config_id)
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'code': 0, 'msg': '删除成功'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'删除失败: {str(e)}'}), 500

@bp.route('/test', methods=['POST'])
@web_login_required
def test_push_config():
    """测试推送配置"""
    try:
        data = request.get_json()
        channel = data.get('channel')
        config_data = data.get('config_data', {})
        title = data.get('title', '测试推送')
        content = data.get('content', '这是一条测试推送消息')
        
        if not channel:
            return jsonify({'code': 1, 'msg': '缺少推送渠道'}), 400
        
        # 导入推送服务
        from .push_service import push_service
        
        # 创建临时配置对象进行测试
        temp_config = PushConfig(
            name='测试配置',
            channel=channel,
            is_enabled=True,
            config_data=json.dumps(config_data),
            notify_on_node_online=True,
            notify_on_node_offline=True,
            notify_on_account_error=True,
            notify_on_verification_code=True
        )
        
        try:
            # 发送测试推送
            result = push_service.send_test_notification(temp_config, title, content)
            return jsonify({
                'code': 0, 
                'msg': '测试成功' if result else '测试失败',
                'success': result
            })
        except Exception as e:
            return jsonify({
                'code': 1, 
                'msg': f'测试失败: {str(e)}',
                'success': False
            })
            
    except Exception as e:
        current_app.logger.error(f"测试推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'测试失败: {str(e)}'}), 500

@bp.route('/channels', methods=['GET'])
@web_login_required
def get_supported_channels():
    """获取支持的推送渠道列表"""
    channels = [
        {
            'value': 'bark',
            'label': 'Bark',
            'description': 'iOS推送服务',
            'required_fields': ['bark_token'],
            'optional_fields': ['bark_push_url']
        },
        {
            'value': 'xiatuisha',
            'label': '虾推啥',
            'description': '虾推啥微信推送服务',
            'required_fields': ['xiatuisha_token'],
            'optional_fields': []
        },
        {
            'value': 'server_chan',
            'label': 'Server酱',
            'description': '微信推送服务',
            'required_fields': ['push_key'],
            'optional_fields': []
        },
        {
            'value': 'telegram',
            'label': 'Telegram',
            'description': 'Telegram机器人',
            'required_fields': ['tg_bot_token', 'tg_user_id'],
            'optional_fields': ['tg_api_host', 'tg_proxy_ip', 'tg_proxy_port']
        },
        {
            'value': 'dingding',
            'label': '钉钉',
            'description': '钉钉机器人',
            'required_fields': ['dd_bot_token', 'dd_bot_secret'],
            'optional_fields': []
        },
        {
            'value': 'qq',
            'label': 'QQ',
            'description': 'QQ机器人',
            'required_fields': ['qq_skey', 'qq_mode'],
            'optional_fields': []
        },
        {
            'value': 'pushplus',
            'label': 'PushPlus',
            'description': 'PushPlus推送',
            'required_fields': ['pushplus_token'],
            'optional_fields': []
        },
        {
            'value': 'wecom_app',
            'label': '企业微信应用',
            'description': '企业微信应用推送',
            'required_fields': ['qywx_am'],
            'optional_fields': []
        },
        {
            'value': 'wecom_key',
            'label': '企业微信机器人',
            'description': '企业微信机器人推送',
            'required_fields': ['wecom_key'],
            'optional_fields': []
        },
        {
            'value': 'feishu',
            'label': '飞书',
            'description': '飞书机器人',
            'required_fields': ['fs_key'],
            'optional_fields': []
        },
        {
            'value': 'webhook',
            'label': '自定义Webhook',
            'description': '自定义Webhook推送',
            'required_fields': ['webhook_url'],
            'optional_fields': ['method', 'headers', 'template']
        }
    ]
    
    return jsonify({'code': 0, 'msg': '获取成功', 'data': channels})

@bp.route('/debug/configs', methods=['GET'])
@web_login_required
def debug_push_configs():
    """调试用：直接查询数据库中的推送配置"""
    try:
        # 直接查询数据库
        configs = PushConfig.query.all()
        current_app.logger.info(f"数据库中的推送配置总数: {len(configs)}")
        
        result = []
        for config in configs:
            config_info = {
                'id': config.id,
                'name': config.name,
                'channel': config.channel,
                'is_enabled': config.is_enabled,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'config_data': config.config_data
            }
            result.append(config_info)
            current_app.logger.info(f"配置 {config.id}: {config.name} ({config.channel})")
        
        return jsonify({
            'code': 0,
            'msg': f'数据库中共有 {len(configs)} 个推送配置',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"调试查询推送配置失败: {e}")
        return jsonify({'code': 1, 'msg': f'查询失败: {str(e)}'}), 500

def _validate_config_data(channel, config_data):
    """验证配置数据"""
    if not isinstance(config_data, dict):
        return False
    
    # 根据渠道验证必填字段
    required_fields_map = {
        'bark': ['bark_token'], 
        'server_chan': ['push_key'],
        'telegram': ['tg_bot_token', 'tg_user_id'],
        'dingding': ['dd_bot_token', 'dd_bot_secret'],
        'qq': ['qq_skey', 'qq_mode'],
        'pushplus': ['pushplus_token'],
        'wecom_app': ['qywx_am'],
        'wecom_key': ['wecom_key'],
        'feishu': ['fs_key'],
        'webhook': ['webhook_url'],
        'xiatuisha': ['xiatuisha_token']
    }
    
    required_fields = required_fields_map.get(channel, [])
    for field in required_fields:
        if not config_data.get(field):
            return False
    
    return True
