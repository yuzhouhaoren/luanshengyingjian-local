from flask import Blueprint, request, jsonify
from feature_user_profile.services.profile_service import profile_service

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profile/features/<user_id>', methods=['GET'])
def get_user_features(user_id):
    """获取用户特征"""
    try:
        features = profile_service.extract_user_features(user_id)
        if not features:
            return jsonify({'status': 'error', 'message': '用户不存在'})
        
        return jsonify({'status': 'success', 'features': features})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@profile_bp.route('/api/profile/behavior', methods=['POST'])
def record_behavior():
    """记录用户行为"""
    try:
        data = request.json
        user_id = data.get('user_id')
        behavior_type = data.get('behavior_type')
        behavior_data = data.get('behavior_data', {})
        
        if not user_id or not behavior_type:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        success = profile_service.update_user_behavior(user_id, behavior_type, behavior_data)
        if not success:
            return jsonify({'status': 'error', 'message': '记录行为失败'})
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@profile_bp.route('/api/profile/behaviors/<user_id>', methods=['GET'])
def get_user_behaviors(user_id):
    """获取用户行为数据"""
    try:
        days = request.args.get('days', 7, type=int)
        behaviors = profile_service.get_user_behaviors(user_id, days)
        return jsonify({'status': 'success', 'behaviors': behaviors})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@profile_bp.route('/api/profile/prompt/<user_id>', methods=['GET'])
def get_user_prompt(user_id):
    """获取用户人设提示词"""
    try:
        prompt = profile_service.generate_user_prompt(user_id)
        if not prompt:
            return jsonify({'status': 'error', 'message': '用户不存在'})
        
        return jsonify({'status': 'success', 'prompt': prompt})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
