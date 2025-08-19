from flask import Blueprint, request, jsonify, g, render_template
from .db import db
from .models import VerificationCode, BotNode, BotAccount
from .auth import bot_api_required, web_login_required
from datetime import datetime, timezone, timedelta
import json

bp = Blueprint('api_verification', __name__, url_prefix='/web_api/verification')

@bp.route('/request', methods=['POST'])
@bot_api_required
def request_verification_code():
    """Node端请求验证码接口"""
    data = request.get_json()
    node = g.node
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': '缺少邮箱参数'}), 400
    
    try:
        # 清理过期的验证码记录
        expired_codes = VerificationCode.query.filter(
            VerificationCode.node_id == node.id,
            VerificationCode.email == email,
            VerificationCode.status.in_(['pending', 'expired'])
        ).all()
        
        for expired_code in expired_codes:
            db.session.delete(expired_code)
        
        # 创建新的验证码请求
        verification_code = VerificationCode(
            node_id=node.id,
            email=email,
            status='pending'
        )
        
        db.session.add(verification_code)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '验证码请求已创建',
            'verification_id': verification_code.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建验证码请求失败: {str(e)}'}), 500

@bp.route('/check/<int:verification_id>', methods=['GET'])
@bot_api_required
def check_verification_code(verification_id):
    """Node端检查验证码状态接口"""
    node = g.node
    
    try:
        verification_code = VerificationCode.query.filter_by(
            id=verification_id,
            node_id=node.id
        ).first()
        
        if not verification_code:
            return jsonify({'success': False, 'message': '验证码记录不存在'}), 404
        
        # 检查是否过期 - 使用本地时间进行比较
        current_time = datetime.now()
        # 确保时间比较时都使用相同的时区格式
        if verification_code.expires_at.replace(tzinfo=None) < current_time:
            verification_code.status = 'expired'
            db.session.commit()
            return jsonify({
                'success': False, 
                'message': '验证码已过期',
                'status': 'expired'
            })
        
        if verification_code.status == 'completed' and verification_code.code:
            return jsonify({
                'success': True,
                'message': '验证码已获取',
                'status': 'completed',
                'code': verification_code.code
            })
        else:
            return jsonify({
                'success': True,
                'message': '等待验证码输入',
                'status': 'pending'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查验证码失败: {str(e)}'}), 500

@bp.route('/list', methods=['GET'])
@web_login_required
def list_verification_codes():
    """Service端查看验证码列表"""
    try:
        # 获取所有待处理的验证码
        pending_codes = VerificationCode.query.filter_by(status='pending').order_by(
            VerificationCode.created_at.desc()
        ).all()
        
        codes_data = []
        for code in pending_codes:
            # 查找对应的账户信息
            account = BotAccount.query.filter_by(email=code.email).first()
            auxiliary_email = account.auxiliary_email if account else None
            
            codes_data.append({
                'id': code.id,
                'node_name': code.node.node_name,
                'email': code.email,  # 主账户邮箱
                'auxiliary_email': auxiliary_email,  # 辅助邮箱
                'created_at': code.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'expires_at': code.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                'status': code.status
            })
        
        return jsonify({
            'success': True,
            'data': codes_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取验证码列表失败: {str(e)}'}), 500

@bp.route('/input/<int:verification_id>', methods=['POST'])
@web_login_required
def input_verification_code(verification_id):
    """Service端输入验证码接口"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'success': False, 'message': '缺少验证码参数'}), 400
    
    try:
        verification_code = VerificationCode.query.get(verification_id)
        
        if not verification_code:
            return jsonify({'success': False, 'message': '验证码记录不存在'}), 404
        
        if verification_code.status != 'pending':
            return jsonify({'success': False, 'message': '验证码状态不正确'}), 400
        
        if verification_code.expires_at.replace(tzinfo=None) < datetime.now():
            verification_code.status = 'expired'
            db.session.commit()
            return jsonify({'success': False, 'message': '验证码已过期'}), 400
        
        # 更新验证码
        verification_code.code = code
        verification_code.status = 'completed'
        verification_code.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '验证码已输入'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'输入验证码失败: {str(e)}'}), 500

@bp.route('/page', methods=['GET'])
@web_login_required
def verification_page():
    """验证码输入页面"""
    return render_template('verification.html')
