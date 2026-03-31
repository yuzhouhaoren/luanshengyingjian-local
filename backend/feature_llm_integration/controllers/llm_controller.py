from flask import Blueprint, request, jsonify
from feature_llm_integration.services.llm_service import llm_service

llm_bp = Blueprint('llm', __name__)

@llm_bp.route('/api/llm/chat', methods=['POST'])
def chat():
    """大模型聊天接口"""
    try:
        data = request.json
        user_id = data.get('user_id')
        messages = data.get('messages')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 512)
        
        if not user_id or not messages:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        # 调用大模型服务
        response = llm_service.call_llm(
            user_id=user_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify({'status': 'success', 'response': response})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@llm_bp.route('/api/llm/generate', methods=['POST'])
def generate():
    """大模型内容生成接口"""
    try:
        data = request.json
        user_id = data.get('user_id')
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 512)
        
        if not user_id or not prompt:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        # 构建消息格式
        messages = [
            {"role": "system", "content": "你是一个智能助手，能够根据用户的提示生成高质量的内容。"},
            {"role": "user", "content": prompt}
        ]
        
        # 调用大模型服务
        response = llm_service.call_llm(
            user_id=user_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify({'status': 'success', 'response': response})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
