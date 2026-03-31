from flask import Blueprint, request, jsonify
from feature_intelligent_chat.services.chat_service import chat_service

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat/message', methods=['POST'])
def save_message():
    """保存聊天消息"""
    try:
        data = request.json
        session_id = data.get('session_id')
        sender_type = data.get('sender_type')
        message_content = data.get('message_content')
        favor_change = data.get('favor_change', 0)
        
        if not session_id or not sender_type or not message_content:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        message_id = chat_service.save_message(session_id, sender_type, message_content, favor_change)
        if not message_id:
            return jsonify({'status': 'error', 'message': '保存消息失败'})
        
        return jsonify({'status': 'success', 'message_id': message_id})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@chat_bp.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """获取聊天历史"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        messages = chat_service.get_chat_history(session_id, limit, offset)
        return jsonify({'status': 'success', 'messages': messages})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@chat_bp.route('/api/chat/conversations/<user_id>', methods=['GET'])
def get_user_conversations(user_id):
    """获取用户的所有会话"""
    try:
        conversations = chat_service.get_user_conversations(user_id)
        return jsonify({'status': 'success', 'conversations': conversations})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@chat_bp.route('/api/chat/feedback', methods=['POST'])
def process_feedback():
    """处理对话反馈"""
    try:
        data = request.json
        session_id = data.get('session_id')
        feedback = data.get('feedback')
        
        if not session_id or not feedback:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        success = chat_service.process_feedback(session_id, feedback)
        if not success:
            return jsonify({'status': 'error', 'message': '处理反馈失败'})
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@chat_bp.route('/api/chat/stats/<session_id>', methods=['GET'])
def get_session_stats(session_id):
    """获取会话统计信息"""
    try:
        stats = chat_service.get_session_stats(session_id)
        if not stats:
            return jsonify({'status': 'error', 'message': '会话不存在'})
        
        return jsonify({'status': 'success', 'stats': stats})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
