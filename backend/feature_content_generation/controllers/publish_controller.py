from flask import Blueprint, request, jsonify
from feature_content_generation.services.publish_service import publish_service

publish_bp = Blueprint('publish', __name__)

@publish_bp.route('/api/publish/square', methods=['POST'])
def publish_to_square():
    """发布帖子到聊天广场"""
    try:
        data = request.json
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({'status': 'error', 'message': '缺少帖子ID'})
        
        success, message = publish_service.publish_to_square(post_id)
        if not success:
            return jsonify({'status': 'error', 'message': message})
        
        return jsonify({'status': 'success', 'message': message})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@publish_bp.route('/api/publish/status/<post_id>', methods=['GET'])
def get_publish_status(post_id):
    """获取帖子发布状态"""
    try:
        status = publish_service.get_publish_status(post_id)
        if not status:
            return jsonify({'status': 'error', 'message': '发布记录不存在'})
        
        return jsonify({'status': 'success', 'status': status})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@publish_bp.route('/api/square/posts', methods=['GET'])
def get_square_posts():
    """获取聊天广场的帖子"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        posts = publish_service.get_square_posts(limit, offset)
        return jsonify({'status': 'success', 'posts': posts})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
