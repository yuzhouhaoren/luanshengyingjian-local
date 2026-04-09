import json

class FavorabilitySystem:
    def __init__(self):
        self.max_favorability = 100
        self.min_favorability = 0
    
    def calculate_favorability(self, current_favorability, user_message, user_profile):
        """计算好感度变化"""
        # 基础加分：有效对话
        change = 1
        
        # 检查是否提及用户爱好
        if user_profile.get('hobbies'):
            hobbies = user_profile['hobbies'].split(',')
            for hobby in hobbies:
                if hobby in user_message:
                    change += 5
                    break
        
        # 检查是否有冒犯性内容
        offensive_words = ['侮辱', '辱骂', '歧视', '脏话']
        for word in offensive_words:
            if word in user_message:
                change = -10
                break
        
        # 确保好感度在有效范围内
        new_favorability = current_favorability + change
        new_favorability = max(self.min_favorability, min(self.max_favorability, new_favorability))
        
        return new_favorability, change
    
    def get_favorability_level(self, favorability):
        """获取好感度等级"""
        if favorability >= 80:
            return "信任期"
        elif favorability >= 50:
            return "好感升温期"
        elif favorability >= 20:
            return "初识熟悉期"
        else:
            return "陌生冷淡期"
    
    def should_unlock_contact(self, favorability):
        """判断是否解锁联系信息"""
        return favorability >= 70
