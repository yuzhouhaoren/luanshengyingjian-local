import json
import time
import uuid
from feature_llm_integration.services.llm_service import llm_service
from feature_user_profile.services.profile_service import profile_service

class ContentService:
    def __init__(self):
        self.content_templates = {
            'dating_post': {
                'prompt': """
                【任务】
                为用户生成一条交友帖子，内容要真实、自然，符合用户的性格和兴趣爱好。
                
                【用户信息】
                {user_info}
                
                【帖子要求】
                1. 标题：吸引眼球，简洁明了（10-20字）
                2. 内容：分享自己的生活、兴趣或交友期望，真实自然，避免官方套话
                3. 风格：符合用户的性格特点和沟通风格
                4. 长度：30-100字，不要太长
                5. 标签：根据内容添加2-3个相关标签
                
                【输出格式】
                请按照以下JSON格式输出：
                {{
                    "title": "帖子标题",
                    "content": "帖子内容",
                    "tags": ["标签1", "标签2", "标签3"]
                }}
                """,
                'temperature': 0.8,
                'max_tokens': 512
            },
            'introduction': {
                'prompt': """
                【任务】
                为用户生成一段自我介绍，用于交友场景。
                
                【用户信息】
                {user_info}
                
                【要求】
                1. 风格：自然、真实，符合用户的性格特点
                2. 内容：包括基本信息、兴趣爱好、交友期望
                3. 长度：50-150字
                4. 语气：友好、真诚
                """,
                'temperature': 0.7,
                'max_tokens': 256
            }
        }
    
    def generate_content(self, user_id, content_type, additional_context=None):
        """生成内容
        
        Args:
            user_id: 用户ID
            content_type: 内容类型（dating_post, introduction等）
            additional_context: 额外上下文信息
            
        Returns:
            生成的内容
        """
        # 获取用户画像
        user_profile = profile_service.get_user_profile(user_id)
        if not user_profile:
            return None
        
        # 生成用户信息字符串
        user_info = self._generate_user_info_string(user_profile)
        
        # 获取内容模板
        if content_type not in self.content_templates:
            return None
        
        template = self.content_templates[content_type]
        prompt = template['prompt'].format(user_info=user_info)
        
        # 如果有额外上下文，添加到提示词中
        if additional_context:
            prompt += f"\n【额外信息】\n{additional_context}"
        
        # 构建消息格式
        messages = [
            {"role": "system", "content": "你是一个专业的内容创作助手，能够根据用户信息生成高质量的交友内容。"},
            {"role": "user", "content": prompt}
        ]
        
        # 调用大模型
        try:
            response = llm_service.call_llm(
                user_id=user_id,
                messages=messages,
                temperature=template['temperature'],
                max_tokens=template['max_tokens']
            )
            
            # 解析响应
            if content_type == 'dating_post':
                try:
                    # 尝试解析JSON
                    content = json.loads(response)
                    return content
                except:
                    # 如果不是JSON格式，返回原始响应
                    return {'title': '生成的帖子', 'content': response, 'tags': []}
            else:
                return {'content': response}
        
        except Exception as e:
            print(f"生成内容时出错: {e}")
            return None
    
    def _generate_user_info_string(self, user_profile):
        """生成用户信息字符串"""
        info = []
        
        # 基本信息
        if user_profile.get('age'):
            info.append(f"年龄：{user_profile['age']}岁")
        if user_profile.get('gender'):
            info.append(f"性别：{user_profile['gender']}")
        if user_profile.get('location'):
            info.append(f"所在地：{user_profile['location']}")
        if user_profile.get('occupation'):
            info.append(f"职业：{user_profile['occupation']}")
        
        # 兴趣爱好
        if user_profile.get('hobbies'):
            try:
                hobbies = json.loads(user_profile['hobbies'])
                if hobbies:
                    info.append(f"兴趣爱好：{', '.join(hobbies)}")
            except:
                if user_profile['hobbies']:
                    info.append(f"兴趣爱好：{user_profile['hobbies']}")
        
        # 性格特点
        if user_profile.get('personality'):
            info.append(f"性格：{user_profile['personality']}")
        
        # 沟通风格
        if user_profile.get('communication_style'):
            info.append(f"沟通风格：{user_profile['communication_style']}")
        
        # 理想伴侣
        if user_profile.get('ideal_partner'):
            info.append(f"理想伴侣：{user_profile['ideal_partner']}")
        
        return '\n'.join(info)
    
    def filter_content(self, content):
        """过滤违规或低质量内容"""
        # 简单的内容过滤规则
        forbidden_words = [
            '违法', '赌博', '色情', '暴力', '毒品',
            '政治', '宗教', '广告', '推销', '诈骗'
        ]
        
        # 检查标题和内容
        if isinstance(content, dict):
            # 检查标题
            if 'title' in content:
                for word in forbidden_words:
                    if word in content['title']:
                        return False, f"标题包含违规内容: {word}"
            
            # 检查内容
            if 'content' in content:
                for word in forbidden_words:
                    if word in content['content']:
                        return False, f"内容包含违规内容: {word}"
            
            # 检查标签
            if 'tags' in content:
                for tag in content['tags']:
                    for word in forbidden_words:
                        if word in tag:
                            return False, f"标签包含违规内容: {word}"
        
        # 检查内容长度
        if isinstance(content, dict) and 'content' in content:
            content_length = len(content['content'])
            if content_length < 10:
                return False, "内容太短"
            if content_length > 500:
                return False, "内容太长"
        
        return True, "内容正常"

# 创建全局实例
content_service = ContentService()
