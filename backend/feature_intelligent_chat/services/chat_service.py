import sqlite3
import json
import time

class ChatService:
    def __init__(self):
        self.db_path = 'dating.db'
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_message(self, session_id, sender_type, message_content, favor_change=0):
        """保存聊天消息"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 生成消息ID
            import uuid
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            
            # 插入消息记录
            cursor.execute('''
                INSERT INTO chat_messages (id, session_id, sender_type, message_content, send_time, favor_change)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (message_id, session_id, sender_type, message_content, favor_change))
            
            conn.commit()
            return message_id
        
        except Exception as e:
            conn.rollback()
            print(f"保存消息时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def get_chat_history(self, session_id, limit=50, offset=0):
        """获取聊天历史"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY send_time ASC 
                LIMIT ? OFFSET ?
            ''', (session_id, limit, offset))
            
            messages = cursor.fetchall()
            
            # 转换为字典列表
            message_list = []
            for msg in messages:
                message_dict = dict(msg)
                message_list.append(message_dict)
            
            return message_list
        
        except Exception as e:
            print(f"获取聊天历史时出错: {e}")
            return []
        
        finally:
            conn.close()
    
    def get_message_count(self, session_id):
        """获取会话消息数量"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        
        except Exception as e:
            print(f"获取消息数量时出错: {e}")
            return 0
        
        finally:
            conn.close()
    
    def get_user_conversations(self, user_id):
        """获取用户的所有会话"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT cs.*, p.title as post_title, u.username as host_name 
                FROM chat_sessions cs 
                LEFT JOIN posts p ON cs.post_id = p.id 
                LEFT JOIN users u ON cs.host_id = u.id 
                WHERE cs.visitor_id = ? 
                ORDER BY cs.updated_at DESC
            ''', (user_id,))
            
            conversations = cursor.fetchall()
            
            # 转换为字典列表
            conversation_list = []
            for conv in conversations:
                conv_dict = dict(conv)
                # 获取最后一条消息
                last_message = self._get_last_message(conv_dict['id'])
                conv_dict['last_message'] = last_message
                conversation_list.append(conv_dict)
            
            return conversation_list
        
        except Exception as e:
            print(f"获取用户会话时出错: {e}")
            return []
        
        finally:
            conn.close()
    
    def _get_last_message(self, session_id):
        """获取会话的最后一条消息"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT message_content, send_time, sender_type 
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY send_time DESC 
                LIMIT 1
            ''', (session_id,))
            
            message = cursor.fetchone()
            if message:
                return {
                    'content': message['message_content'],
                    'time': message['send_time'],
                    'sender_type': message['sender_type']
                }
            return None
        
        except Exception as e:
            print(f"获取最后一条消息时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def process_feedback(self, session_id, feedback):
        """处理对话反馈"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 创建反馈表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_feedback (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            ''')
            
            # 生成反馈ID
            import uuid
            feedback_id = f"feedback_{uuid.uuid4().hex[:8]}"
            
            # 插入反馈记录
            cursor.execute('''
                INSERT INTO chat_feedback (id, session_id, feedback)
                VALUES (?, ?, ?)
            ''', (feedback_id, session_id, json.dumps(feedback)))
            
            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(f"处理反馈时出错: {e}")
            return False
        
        finally:
            conn.close()
    
    def get_session_stats(self, session_id):
        """获取会话统计信息"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 获取会话信息
            cursor.execute('SELECT * FROM chat_sessions WHERE id = ?', (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # 获取消息统计
            cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ?', (session_id,))
            message_count = cursor.fetchone()[0]
            
            # 获取用户消息数量
            cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ? AND sender_type = ?', (session_id, 'user'))
            user_message_count = cursor.fetchone()[0]
            
            # 获取机器人消息数量
            cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ? AND sender_type = ?', (session_id, 'bot'))
            bot_message_count = cursor.fetchone()[0]
            
            # 计算好感度变化
            cursor.execute('SELECT SUM(favor_change) FROM chat_messages WHERE session_id = ?', (session_id,))
            favor_change = cursor.fetchone()[0] or 0
            
            return {
                'session_id': session['id'],
                'favor_score': session['favor_score'],
                'is_unlocked': session['is_unlocked'],
                'message_count': message_count,
                'user_message_count': user_message_count,
                'bot_message_count': bot_message_count,
                'favor_change': favor_change,
                'created_at': session['created_at'],
                'updated_at': session['updated_at']
            }
        
        except Exception as e:
            print(f"获取会话统计时出错: {e}")
            return None
        
        finally:
            conn.close()

# 创建全局实例
chat_service = ChatService()
