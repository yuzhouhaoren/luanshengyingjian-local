from flask import Blueprint, request, jsonify
from feature_content_generation.services.content_service import content_service

content_bp = Blueprint('content', __name__)

@content_bp.route('/api/content/generate', methods=['POST'])
def generate_content():
    """生成内容"""
    try:
        data = request.json
        user_id = data.get('user_id')
        content_type = data.get('content_type', 'dating_post')
        additional_context = data.get('additional_context')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少用户ID'})
        
        # 生成内容
        content = content_service.generate_content(user_id, content_type, additional_context)
        if not content:
            return jsonify({'status': 'error', 'message': '生成内容失败'})
        
        # 过滤内容
        is_valid, message = content_service.filter_content(content)
        if not is_valid:
            return jsonify({'status': 'error', 'message': message})
        
        return jsonify({'status': 'success', 'content': content})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
