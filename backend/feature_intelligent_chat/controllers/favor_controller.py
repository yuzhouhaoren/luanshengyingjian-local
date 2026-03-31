from flask import Blueprint, request, jsonify
from feature_intelligent_chat.services.favor_service import favor_service

favor_bp = Blueprint('favor', __name__)

@favor_bp.route('/api/favor/session', methods=['POST'])
def create_chat_session():
    """创建聊天会话"""
    try:
        data = request.json
        post_id = data.get('post_id')
        host_id = data.get('host_id')
        visitor_id = data.get('visitor_id')
        
        if not post_id or not host_id or not visitor_id:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        session_id = favor_service.create_chat_session(post_id, host_id, visitor_id)
        if not session_id:
            return jsonify({'status': 'error', 'message': '创建会话失败'})
        
        return jsonify({'status': 'success', 'session_id': session_id})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/session/<session_id>', methods=['GET'])
def get_chat_session(session_id):
    """获取聊天会话信息"""
    try:
        session = favor_service.get_chat_session(session_id)
        if not session:
            return jsonify({'status': 'error', 'message': '会话不存在'})
        
        return jsonify({'status': 'success', 'session': session})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/score', methods=['POST'])
def update_favor_score():
    """更新好感度分数"""
    try:
        data = request.json
        session_id = data.get('session_id')
        score_change = data.get('score_change', 0)
        
        if not session_id:
            return jsonify({'status': 'error', 'message': '缺少会话ID'})
        
        success, new_score, is_unlocked = favor_service.update_favor_score(session_id, score_change)
        if not success:
            return jsonify({'status': 'error', 'message': '更新好感度失败'})
        
        return jsonify({'status': 'success', 'favor_score': new_score, 'is_unlocked': is_unlocked})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/calculate', methods=['POST'])
def calculate_favor_score():
    """计算好感度变化"""
    try:
        data = request.json
        message = data.get('message')
        context = data.get('context', [])
        
        if not message:
            return jsonify({'status': 'error', 'message': '缺少消息内容'})
        
        score_change = favor_service.calculate_favor_score(message, context)
        return jsonify({'status': 'success', 'score_change': score_change})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/contact', methods=['POST'])
def get_contact_info():
    """获取用户联系方式"""
    try:
        data = request.json
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        if not user_id or not session_id:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        email, message = favor_service.get_contact_info(user_id, session_id)
        if not email:
            return jsonify({'status': 'error', 'message': message})
        
        return jsonify({'status': 'success', 'email': email})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/threshold', methods=['GET'])
def get_favor_threshold():
    """获取好感度阈值"""
    try:
        threshold = favor_service.get_favor_threshold()
        return jsonify({'status': 'success', 'threshold': threshold})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@favor_bp.route('/api/favor/threshold', methods=['POST'])
def set_favor_threshold():
    """设置好感度阈值"""
    try:
        data = request.json
        threshold = data.get('threshold')
        
        if threshold is None:
            return jsonify({'status': 'error', 'message': '缺少阈值参数'})
        
        success = favor_service.set_favor_threshold(threshold)
        if not success:
            return jsonify({'status': 'error', 'message': '阈值设置失败，阈值必须在0-100之间'})
        
        return jsonify({'status': 'success', 'threshold': threshold})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
