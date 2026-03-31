from flask import Blueprint, request, jsonify
from feature_llm_integration.services.session_service import session_manager

session_bp = Blueprint('session', __name__)

@session_bp.route('/api/session/create', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少用户ID'})
        
        session_id = session_manager.create_session(user_id)
        return jsonify({'status': 'success', 'session_id': session_id})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@session_bp.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话信息"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'status': 'error', 'message': '会话不存在'})
        
        return jsonify({
            'status': 'success',
            'session': {
                'user_id': session['user_id'],
                'context': session['context'],
                'params': session['params'],
                'last_activity': session['last_activity']
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@session_bp.route('/api/session/<session_id>/update', methods=['POST'])
def update_session(session_id):
    """更新会话"""
    try:
        data = request.json
        message = data.get('message')
        role = data.get('role', 'user')
        params = data.get('params')
        
        if message:
            session_manager.update_context(session_id, message, role)
        
        if params:
            session_manager.update_params(session_id, params)
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@session_bp.route('/api/session/<session_id>/delete', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            return jsonify({'status': 'error', 'message': '会话不存在'})
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@session_bp.route('/api/sessions/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    """获取用户的所有会话"""
    try:
        sessions = session_manager.get_user_sessions(user_id)
        return jsonify({'status': 'success', 'sessions': sessions})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@session_bp.route('/api/session/cleanup', methods=['POST'])
def cleanup_sessions():
    """清理过期会话"""
    try:
        count = session_manager.cleanup_expired_sessions()
        return jsonify({'status': 'success', 'cleaned_count': count})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
