import sqlite3
import json
import time

class FavorService:
    def __init__(self):
        self.db_path = 'dating.db'
        self.default_threshold = 50  # 默认好感度阈值
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_chat_session(self, post_id, host_id, visitor_id):
        """创建聊天会话"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 生成会话ID
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # 插入会话记录
            cursor.execute('''
                INSERT INTO chat_sessions (id, post_id, host_id, visitor_id, favor_score, is_unlocked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, post_id, host_id, visitor_id, 0, False))
            
            conn.commit()
            return session_id
        
        except Exception as e:
            conn.rollback()
            print(f"创建聊天会话时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def get_chat_session(self, session_id):
        """获取聊天会话信息"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM chat_sessions WHERE id = ?', (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return None
            
            return dict(session)
        
        except Exception as e:
            print(f"获取聊天会话时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def update_favor_score(self, session_id, score_change):
        """更新好感度分数"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 获取当前好感度
            cursor.execute('SELECT favor_score FROM chat_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            current_score = result['favor_score']
            new_score = max(0, min(100, current_score + score_change))
            
            # 检查是否达到阈值
            is_unlocked = new_score >= self.default_threshold
            
            # 更新好感度和解锁状态
            cursor.execute('''
                UPDATE chat_sessions 
                SET favor_score = ?, is_unlocked = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_score, is_unlocked, session_id))
            
            conn.commit()
            return True, new_score, is_unlocked
        
        except Exception as e:
            conn.rollback()
            print(f"更新好感度时出错: {e}")
            return False, 0, False
        
        finally:
            conn.close()
    
    def calculate_favor_score(self, message, context):
        """计算好感度变化
        
        Args:
            message: 当前消息内容
            context: 对话上下文
            
        Returns:
            好感度变化值
        """
        score_change = 0
        
        # 基础加分：每次有效对话 +1
        score_change += 1
        
        # 关键词加分
        positive_keywords = ['你好', '谢谢', '喜欢', '开心', '高兴', '好的', '不错', '很棒', '优秀']
        negative_keywords = ['不好', '讨厌', '生气', '难过', '失望', '无聊', '烦']
        
        message_lower = message.lower()
        for keyword in positive_keywords:
            if keyword in message_lower:
                score_change += 2
                break
        
        for keyword in negative_keywords:
            if keyword in message_lower:
                score_change -= 2
                break
        
        # 对话长度加分
        if len(message) > 50:
            score_change += 1
        elif len(message) < 5:
            score_change -= 1
        
        # 连续对话加分
        if len(context) > 5:
            score_change += 1
        
        return score_change
    
    def get_contact_info(self, user_id, session_id):
        """获取用户联系方式"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 检查会话是否解锁
            cursor.execute('SELECT is_unlocked FROM chat_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result or not result['is_unlocked']:
                return None, "好感度未达到阈值"
            
            # 获取用户邮箱
            cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user or not user['email']:
                return None, "用户未设置邮箱"
            
            return user['email'], ""
        
        except Exception as e:
            print(f"获取联系方式时出错: {e}")
            return None, "获取联系方式失败"
        
        finally:
            conn.close()
    
    def get_favor_threshold(self):
        """获取好感度阈值"""
        return self.default_threshold
    
    def set_favor_threshold(self, threshold):
        """设置好感度阈值"""
        if 0 < threshold < 100:
            self.default_threshold = threshold
            return True
        return False

# 创建全局实例
favor_service = FavorService()
