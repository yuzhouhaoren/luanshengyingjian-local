import json
import time
import sqlite3
from collections import defaultdict

class ProfileService:
    def __init__(self):
        self.db_path = 'dating.db'
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_user_profile(self, user_id):
        """获取用户画像"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
        
        profile = dict(user)
        # 解析profile_scores为JSON对象
        if profile.get('profile_scores'):
            try:
                profile['profile_scores'] = json.loads(profile['profile_scores'])
            except:
                profile['profile_scores'] = {}
        
        # 解析hobbies为列表
        if profile.get('hobbies'):
            try:
                profile['hobbies'] = json.loads(profile['hobbies'])
            except:
                profile['hobbies'] = []
        
        return profile
    
    def update_user_behavior(self, user_id, behavior_type, behavior_data):
        """记录用户行为数据"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 检查behavior_logs表是否存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavior_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    behavior_type TEXT,
                    behavior_data TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 生成行为日志ID
            import uuid
            log_id = str(uuid.uuid4())
            
            # 插入行为日志
            cursor.execute('''
                INSERT INTO behavior_logs (id, user_id, behavior_type, behavior_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (log_id, user_id, behavior_type, json.dumps(behavior_data), int(time.time())))
            
            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(f"记录用户行为时出错: {e}")
            return False
        
        finally:
            conn.close()
    
    def get_user_behaviors(self, user_id, days=7):
        """获取用户最近的行为数据"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # 计算时间戳范围
            start_time = int(time.time()) - (days * 24 * 60 * 60)
            
            cursor.execute('''
                SELECT behavior_type, behavior_data, timestamp
                FROM behavior_logs
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (user_id, start_time))
            
            behaviors = cursor.fetchall()
            
            # 转换为字典列表
            result = []
            for behavior in behaviors:
                try:
                    behavior_data = json.loads(behavior['behavior_data'])
                except:
                    behavior_data = {}
                
                result.append({
                    'behavior_type': behavior['behavior_type'],
                    'behavior_data': behavior_data,
                    'timestamp': behavior['timestamp']
                })
            
            return result
        
        except Exception as e:
            print(f"获取用户行为时出错: {e}")
            return []
        
        finally:
            conn.close()
    
    def extract_user_features(self, user_id):
        """提取用户特征"""
        # 获取用户基本信息
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        # 获取用户行为数据
        behaviors = self.get_user_behaviors(user_id)
        
        # 构建用户特征
        features = {
            'basic_info': {
                'age': profile.get('age', 0),
                'gender': profile.get('gender', ''),
                'location': profile.get('location', ''),
                'occupation': profile.get('occupation', ''),
                'sexual_orientation': profile.get('sexual_orientation', '')
            },
            'personality': profile.get('profile_scores', {}),
            'interests': {
                'hobbies': profile.get('hobbies', []),
                'communication_style': profile.get('communication_style', ''),
                'ideal_partner': profile.get('ideal_partner', '')
            },
            'behavior_patterns': self._analyze_behavior_patterns(behaviors)
        }
        
        return features
    
    def _analyze_behavior_patterns(self, behaviors):
        """分析用户行为模式"""
        patterns = {
            'activity_frequency': 0,
            'preferred_time': [],
            'interaction_types': defaultdict(int),
            'content_preferences': defaultdict(int)
        }
        
        if not behaviors:
            return patterns
        
        # 计算活动频率
        patterns['activity_frequency'] = len(behaviors)
        
        # 分析偏好时间
        for behavior in behaviors:
            hour = time.localtime(behavior['timestamp']).tm_hour
            patterns['preferred_time'].append(hour)
        
        # 分析交互类型
        for behavior in behaviors:
            patterns['interaction_types'][behavior['behavior_type']] += 1
        
        # 分析内容偏好（如果有）
        for behavior in behaviors:
            if 'content_type' in behavior['behavior_data']:
                patterns['content_preferences'][behavior['behavior_data']['content_type']] += 1
        
        return patterns
    
    def generate_user_prompt(self, user_id):
        """生成用户人设提示词"""
        features = self.extract_user_features(user_id)
        if not features:
            return ""
        
        # 构建提示词模板
        prompt = f"""
        【角色】
        你是{features['basic_info']['gender']}，{features['basic_info']['age']}岁，从事{features['basic_info']['occupation']}工作，住在{features['basic_info']['location']}。
        
        【性格】
        """
        
        # 添加性格特征
        personality = features['personality']
        if personality:
            prompt += "你的性格特点："
            if personality.get('extraversion', 0) > 3:
                prompt += "外向，"
            else:
                prompt += "内向，"
            if personality.get('openness', 0) > 3:
                prompt += "开放，"
            else:
                prompt += "传统，"
            if personality.get('conscientiousness', 0) > 3:
                prompt += "认真负责，"
            else:
                prompt += "随意，"
            if personality.get('agreeableness', 0) > 3:
                prompt += "友善，"
            else:
                prompt += "独立，"
            if personality.get('neuroticism', 0) > 3:
                prompt += "感性，"
            else:
                prompt += "理性，"
            prompt += "\n\n"
        
        # 添加兴趣爱好
        if features['interests']['hobbies']:
            prompt += "【兴趣爱好】\n"
            prompt += "你喜欢：" + "、".join(features['interests']['hobbies']) + "。\n\n"
        
        # 添加沟通风格
        if features['interests']['communication_style']:
            prompt += "【沟通风格】\n"
            prompt += f"你通常{features['interests']['communication_style']}。\n\n"
        
        # 添加理想伴侣
        if features['interests']['ideal_partner']:
            prompt += "【理想伴侣】\n"
            prompt += f"你希望找到{features['interests']['ideal_partner']}。\n\n"
        
        # 添加行为模式
        if features['behavior_patterns']['activity_frequency'] > 0:
            prompt += "【行为模式】\n"
            prompt += f"你是一个{('活跃' if features['behavior_patterns']['activity_frequency'] > 10 else '安静')}的人。\n"
        
        prompt += "【聊天规则】\n"
        prompt += "1. 保持真实的自己，不要说官方套话\n"
        prompt += "2. 根据好感度调整说话语气，从陌生到熟悉\n"
        prompt += "3. 记住之前的对话内容，保持上下文连贯\n"
        prompt += "4. 避免讨论敏感话题\n"
        
        return prompt

# 创建全局实例
profile_service = ProfileService()
