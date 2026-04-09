import json
from .llm_integration import LLMIntegration
from .cache_system import user_cache

class RAGSystem:
    def __init__(self):
        self.llm = LLMIntegration()
    
    def retrieve_user_data(self, user_id, db_connection):
        """检索用户数据"""
        # 先尝试从缓存获取
        cached_user_data = user_cache.get(f"user_data:{user_id}")
        if cached_user_data:
            return cached_user_data
        
        cursor = db_connection.cursor()
        
        # 获取用户基本信息
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        # 获取用户习惯数据
        cursor.execute('SELECT * FROM user_habits WHERE user_id = ?', (user_id,))
        habits = cursor.fetchone()
        
        # 获取用户帖子数据
        cursor.execute('SELECT * FROM user_posts WHERE user_id = ?', (user_id,))
        posts = cursor.fetchall()
        
        # 构建用户数据
        user_data = {
            'user': dict(user) if user else {},
            'habits': dict(habits) if habits else {},
            'posts': [dict(post) for post in posts] if posts else []
        }
        
        # 存入缓存
        user_cache.set(f"user_data:{user_id}", user_data)
        
        return user_data
    
    def generate_rag_prompt(self, user_id, user_message, chat_history=[], db_connection=None):
        """生成RAG增强的提示词"""
        prompt = "你是一个基于用户画像的聊天助手，根据以下用户数据和聊天历史，生成一个自然的回复：\n"
        
        if db_connection:
            # 检索用户数据
            user_data = self.retrieve_user_data(user_id, db_connection)
            prompt += f"用户数据：{json.dumps(user_data, ensure_ascii=False)}\n"
        
        if chat_history:
            prompt += "聊天历史：\n"
            for msg in chat_history:
                # 处理不同格式的聊天历史数据
                if isinstance(msg, dict):
                    # 检查常见的用户标识键
                    is_user = False
                    if 'isUser' in msg:
                        is_user = msg['isUser']
                    elif 'sender' in msg:
                        is_user = msg['sender'] == 'user'
                    elif 'role' in msg:
                        is_user = msg['role'] == 'user'
                    role = "用户" if is_user else "你"
                    content = msg.get('content', '')
                    prompt += f"{role}：{content}\n"
        
        prompt += f"用户最新消息：{user_message}\n"
        prompt += "请生成一个符合用户画像的自然回复,保持口语化,长度控制在20字以内。"
        
        return prompt
    
    def generate_response_with_rag(self, user_id, user_message, chat_history=[], db_connection=None):
        """使用RAG生成响应"""
        prompt = self.generate_rag_prompt(user_id, user_message, chat_history, db_connection)
        return self.llm.generate_response(prompt, max_tokens=50)
    
    def update_user_data_display(self, user_id, db_connection):
        """更新用户数据显示"""
        # 这里可以实现用户数据的更新和显示逻辑
        # 例如，更新用户的聊天统计数据、互动次数等
        pass
