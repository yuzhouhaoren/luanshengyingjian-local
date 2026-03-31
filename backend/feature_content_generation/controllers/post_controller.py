from flask import Blueprint, request, jsonify
from feature_content_generation.services.post_service import post_service

post_bp = Blueprint('post', __name__)

@post_bp.route('/api/posts', methods=['POST'])
def create_post():
    """创建帖子"""
    try:
        data = request.json
        user_id = data.get('user_id')
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', [])
        
        if not user_id or not title or not content:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        post_id = post_service.create_post(user_id, title, content, tags)
        if not post_id:
            return jsonify({'status': 'error', 'message': '创建帖子失败'})
        
        return jsonify({'status': 'success', 'post_id': post_id})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@post_bp.route('/api/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """获取帖子详情"""
    try:
        post = post_service.get_post(post_id)
        if not post:
            return jsonify({'status': 'error', 'message': '帖子不存在'})
        
        return jsonify({'status': 'success', 'post': post})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@post_bp.route('/api/posts/user/<user_id>', methods=['GET'])
def get_user_posts(user_id):
    """获取用户的所有帖子"""
    try:
        posts = post_service.get_user_posts(user_id)
        return jsonify({'status': 'success', 'posts': posts})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@post_bp.route('/api/posts', methods=['GET'])
def get_all_posts():
    """获取所有帖子"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        posts = post_service.get_all_posts(limit, offset)
        return jsonify({'status': 'success', 'posts': posts})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@post_bp.route('/api/posts/<post_id>', methods=['PUT'])
def update_post(post_id):
    """更新帖子"""
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags')
        status = data.get('status')
        
        success = post_service.update_post(post_id, title, content, tags, status)
        if not success:
            return jsonify({'status': 'error', 'message': '更新帖子失败'})
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@post_bp.route('/api/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """删除帖子"""
    try:
        success = post_service.delete_post(post_id)
        if not success:
            return jsonify({'status': 'error', 'message': '删除帖子失败'})
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
