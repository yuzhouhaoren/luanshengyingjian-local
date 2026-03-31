import time
import uuid

class SessionManager:
    def __init__(self):
        self.sessions = {}  # 格式: {session_id: {user_id, context, last_activity, params}}
        self.session_timeout = 2 * 60 * 60  # 2小时超时
    
    def create_session(self, user_id):
        """创建新的用户会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id,
            'context': [],  # 对话历史
            'last_activity': time.time(),
            'params': {  # 模型参数
                'temperature': 0.7,
                'max_tokens': 512,
                'top_p': 0.9
            }
        }
        return session_id
    
    def get_session(self, session_id):
        """获取会话信息"""
        if session_id not in self.sessions:
            return None
        
        # 更新最后活动时间
        self.sessions[session_id]['last_activity'] = time.time()
        return self.sessions[session_id]
    
    def update_context(self, session_id, message, role):
        """更新会话上下文"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]['context'].append({
            'role': role,
            'content': message
        })
        self.sessions[session_id]['last_activity'] = time.time()
        
        # 限制上下文长度，只保留最近的20条消息
        if len(self.sessions[session_id]['context']) > 20:
            self.sessions[session_id]['context'] = self.sessions[session_id]['context'][-20:]
        
        return True
    
    def update_params(self, session_id, params):
        """更新会话参数"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]['params'].update(params)
        self.sessions[session_id]['last_activity'] = time.time()
        return True
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_user_sessions(self, user_id):
        """获取用户的所有会话"""
        user_sessions = []
        for session_id, session in self.sessions.items():
            if session['user_id'] == user_id:
                user_sessions.append({
                    'session_id': session_id,
                    'last_activity': session['last_activity'],
                    'message_count': len(session['context'])
                })
        return user_sessions
    
    def delete_session(self, session_id):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

# 创建全局实例
session_manager = SessionManager()
