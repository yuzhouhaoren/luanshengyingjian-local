import json
import time
import uuid
import sqlite3

class PostService:
    def __init__(self):
        self.db_path = 'dating.db'
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_post(self, user_id, title, content, tags):
        """创建帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 生成帖子ID
            post_id = f"post_{uuid.uuid4().hex[:8]}"
            
            # 插入帖子数据
            cursor.execute('''
                INSERT INTO posts (id, user_id, title, content, tags, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (post_id, user_id, title, json.dumps(content), json.dumps(tags), 'published'))
            
            conn.commit()
            return post_id
        
        except Exception as e:
            conn.rollback()
            print(f"创建帖子时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def get_post(self, post_id):
        """获取帖子详情"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return None
            
            # 转换为字典
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
            
            return post_dict
        
        except Exception as e:
            print(f"获取帖子时出错: {e}")
            return None
        
        finally:
            conn.close()
    
    def get_user_posts(self, user_id):
        """获取用户的所有帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM posts 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
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
            print(f"获取用户帖子时出错: {e}")
            return []
        
        finally:
            conn.close()
    
    def get_all_posts(self, limit=20, offset=0):
        """获取所有帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM posts 
                WHERE status = 'published'
                ORDER BY created_at DESC
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
            print(f"获取所有帖子时出错: {e}")
            return []
        
        finally:
            conn.close()
    
    def update_post(self, post_id, title=None, content=None, tags=None, status=None):
        """更新帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 构建更新语句
            update_fields = []
            update_values = []
            
            if title is not None:
                update_fields.append('title = ?')
                update_values.append(title)
            
            if content is not None:
                update_fields.append('content = ?')
                update_values.append(json.dumps(content))
            
            if tags is not None:
                update_fields.append('tags = ?')
                update_values.append(json.dumps(tags))
            
            if status is not None:
                update_fields.append('status = ?')
                update_values.append(status)
            
            # 添加更新时间
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            
            if not update_fields:
                return False
            
            # 构建SQL语句
            sql = f"UPDATE posts SET {', '.join(update_fields)} WHERE id = ?"
            update_values.append(post_id)
            
            cursor.execute(sql, update_values)
            conn.commit()
            
            return cursor.rowcount > 0
        
        except Exception as e:
            conn.rollback()
            print(f"更新帖子时出错: {e}")
            return False
        
        finally:
            conn.close()
    
    def delete_post(self, post_id):
        """删除帖子"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        
        except Exception as e:
            conn.rollback()
            print(f"删除帖子时出错: {e}")
            return False
        
        finally:
            conn.close()

# 创建全局实例
post_service = PostService()
