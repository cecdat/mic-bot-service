from flask import Blueprint, request, jsonify, current_app
from .db import db
from .models import UserAgent, BotAccount
from .auth import web_login_required
import json
import os

bp = Blueprint('api_user_agents', __name__, url_prefix='/web_api/user_agents')

@bp.route('/import', methods=['POST'])
@web_login_required
def import_user_agents():
    """从JSON文件导入User-Agent"""
    try:
        # 读取user_agents.json文件
        json_file_path = os.path.join(current_app.root_path, '..', 'user_agents.json')
        
        if not os.path.exists(json_file_path):
            return jsonify({'success': False, 'message': 'user_agents.json文件不存在'}), 404
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            user_agents_data = json.load(f)
        
        imported_count = 0
        skipped_count = 0
        
        for ua_data in user_agents_data:
            desktop_ua = ua_data.get('desktop', '')
            mobile_ua = ua_data.get('mobile', '')
            
            if not desktop_ua or not mobile_ua:
                skipped_count += 1
                continue
            
            # 检查是否已存在相同的User-Agent
            existing_ua = UserAgent.query.filter_by(
                desktop_ua=desktop_ua,
                mobile_ua=mobile_ua
            ).first()
            
            if existing_ua:
                skipped_count += 1
                continue
            
            # 创建新的User-Agent记录
            new_ua = UserAgent(
                desktop_ua=desktop_ua,
                mobile_ua=mobile_ua,
                is_used=False
            )
            db.session.add(new_ua)
            imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'导入完成：成功导入 {imported_count} 个，跳过 {skipped_count} 个重复项'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'}), 500

@bp.route('/list', methods=['GET'])
@web_login_required
def list_user_agents():
    """获取User-Agent列表"""
    try:
        # 获取查询参数
        show_unused_only = request.args.get('unused_only', 'false').lower() == 'true'
        
        # 构建查询
        query = UserAgent.query
        
        if show_unused_only:
            query = query.filter_by(is_used=False)
        
        user_agents = query.order_by(UserAgent.created_at.desc()).all()
        
        ua_list = []
        for ua in user_agents:
            # 获取使用该User-Agent的账户信息
            used_by_account = None
            if ua.used_by_account_id:
                used_by_account = BotAccount.query.get(ua.used_by_account_id)
            
            ua_dict = {
                'id': ua.id,
                'desktop_ua': ua.desktop_ua,
                'mobile_ua': ua.mobile_ua,
                'is_used': ua.is_used,
                'used_by_account_email': used_by_account.email if used_by_account else None,
                'used_by_account_id': ua.used_by_account_id,
                'created_at': ua.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': ua.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            ua_list.append(ua_dict)
        
        return jsonify({
            'success': True,
            'data': ua_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取User-Agent列表失败: {str(e)}'}), 500

@bp.route('/unused', methods=['GET'])
@web_login_required
def get_unused_user_agents():
    """获取未使用的User-Agent列表（用于账户管理中的选择）"""
    try:
        unused_agents = UserAgent.query.filter_by(is_used=False).order_by(UserAgent.created_at.desc()).all()
        
        ua_list = []
        for ua in unused_agents:
            ua_dict = {
                'id': ua.id,
                'desktop_ua': ua.desktop_ua,
                'mobile_ua': ua.mobile_ua,
                'display_name': f"桌面: {ua.desktop_ua[:50]}... | 移动: {ua.mobile_ua[:50]}..."
            }
            ua_list.append(ua_dict)
        
        return jsonify({
            'success': True,
            'data': ua_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取未使用User-Agent失败: {str(e)}'}), 500

@bp.route('/<int:ua_id>', methods=['DELETE'])
@web_login_required
def delete_user_agent(ua_id):
    """删除User-Agent"""
    try:
        ua = UserAgent.query.get(ua_id)
        if not ua:
            return jsonify({'success': False, 'message': 'User-Agent不存在'}), 404
        
        if ua.is_used:
            return jsonify({'success': False, 'message': '无法删除已被使用的User-Agent'}), 400
        
        db.session.delete(ua)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User-Agent删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@bp.route('/assign/<int:ua_id>', methods=['POST'])
@web_login_required
def assign_user_agent(ua_id):
    """分配User-Agent给账户"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({'success': False, 'message': '缺少账户ID参数'}), 400
        
        ua = UserAgent.query.get(ua_id)
        if not ua:
            return jsonify({'success': False, 'message': 'User-Agent不存在'}), 404
        
        if ua.is_used:
            return jsonify({'success': False, 'message': 'User-Agent已被使用'}), 400
        
        account = BotAccount.query.get(account_id)
        if not account:
            return jsonify({'success': False, 'message': '账户不存在'}), 404
        
        # 分配User-Agent
        ua.is_used = True
        ua.used_by_account_id = account_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User-Agent分配成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'分配失败: {str(e)}'}), 500

@bp.route('/unassign/<int:ua_id>', methods=['POST'])
@web_login_required
def unassign_user_agent(ua_id):
    """取消分配User-Agent"""
    try:
        ua = UserAgent.query.get(ua_id)
        if not ua:
            return jsonify({'success': False, 'message': 'User-Agent不存在'}), 404
        
        if not ua.is_used:
            return jsonify({'success': False, 'message': 'User-Agent未被使用'}), 400
        
        # 获取使用该User-Agent的账户
        account = BotAccount.query.get(ua.used_by_account_id)
        
        # 取消分配
        ua.is_used = False
        ua.used_by_account_id = None
        
        # 清除账户的User-Agent设置
        if account:
            account.user_agents = '{}'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User-Agent取消分配成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'取消分配失败: {str(e)}'}), 500
