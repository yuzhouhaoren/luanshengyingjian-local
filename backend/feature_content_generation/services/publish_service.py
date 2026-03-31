import json
import time
import sqlite3

class PublishService:
    def __init__(self):
        self.db_path = 'dating.db'
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def publish_to_square(self, post_id):
        """将帖子发布到聊天广场"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 开始事务
            conn.execute('BEGIN TRANSACTION')
            
            # 更新帖子状态为published
            cursor.execute('''
                UPDATE posts 
                SET status = 'published', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (post_id,))
            
            # 检查帖子是否存在
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "帖子不存在"
            
            # 获取帖子信息
            cursor.execute('SELECT user_id, title FROM posts WHERE id = ?', (post_id,))
            post = cursor.fetchone()
            
            if not post:
                conn.rollback()
                return False, "帖子不存在"
            
            # 记录发布日志
            publish_id = f"publish_{int(time.time())}"
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publish_logs (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    user_id TEXT,
                    status TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO publish_logs (id, post_id, user_id, status)
                VALUES (?, ?, ?, ?)
            ''', (publish_id, post_id, post['user_id'], 'success'))
            
            # 提交事务
            conn.commit()
            
            # 发送通知（这里只是记录，实际项目中可以实现消息队列或WebSocket通知）
            self._send_notification(post['user_id'], post_id, post['title'])
            
            return True, "发布成功"
        
        except Exception as e:
            conn.rollback()
            print(f"发布帖子时出错: {e}")
            return False, str(e)
        
        finally:
            conn.close()
    
    def _send_notification(self, user_id, post_id, post_title):
        """发送发布通知"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 创建通知表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    type TEXT,
                    title TEXT,
                    content TEXT,
                    is_read BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 生成通知
            notification_id = f"notif_{int(time.time())}"
            content = f"你的帖子《{post_title}》已成功发布到聊天广场"
            
            cursor.execute('''
                INSERT INTO notifications (id, user_id, type, title, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (notification_id, user_id, 'post_published', '帖子发布成功', content))
            
            conn.commit()
        
        except Exception as e:
            print(f"发送通知时出错: {e}")
        
        finally:
            conn.close()
    
    def get_publish_status(self, post_id):
        """获取帖子发布状态"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT status, published_at 
                FROM publish_logs 
                WHERE post_id = ? 
                ORDER BY published_at DESC 
                LIMIT 1
            ''', (post_id,))
            
            log = cursor.fetchone()
            
            if not log:
                return None
            
            return {
                'status': log['status'],
                'published_at': log['published_at']
            }
        
        except Exception as e:
            print(f"获取发布状态时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def get_square_posts(self, limit=20, offset=0):
        """获取聊天广场的帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.*, u.username, u.avatar 
                FROM posts p 
                LEFT JOIN users u ON p.user_id = u.id 
                WHERE p.status = 'published' 
                ORDER BY p.created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            posts = cursor.fetchall()
            
            # 转换为字典列表
            post_list = []
            for post in posts:
                post_dict = dict(post)
                
                # 解析tags
                if post_dict.get('tags'):
                    try:
                        post_dict['tags'] = json.loads(post_dict['tags'])
                    except:
                        post_dict['tags'] = []
                
                # 解析content
                if post_dict.get('content'):
                    try:
                        post_dict['content'] = json.loads(post_dict['content'])
                    except:
                        pass
                
                post_list.append(post_dict)
            
            return post_list
        
        except Exception as e:
            print(f"获取聊天广场帖子时出错: {e}")
            return []
        
        finally:
            conn.close()

# 创建全局实例
publish_service = PublishService()
