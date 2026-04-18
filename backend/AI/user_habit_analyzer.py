import json
import uuid
from .llm_integration import LLMIntegration

class UserHabitAnalyzer:
    def __init__(self):
        self.llm = LLMIntegration()
        self.interview_questions = [
            "你平时喜欢做什么？",
            "你的说话风格是什么样的？",
            "你有什么特别的爱好吗？",
            "你喜欢和什么样的人交朋友？",
            "你平时聊天有什么习惯？"
        ]
    
    def generate_interview_question(self, user_id, current_question_index=0):
        """生成访谈问题"""
        if current_question_index < len(self.interview_questions):
            return self.interview_questions[current_question_index]
        return None
    
    def analyze_response(self, user_id, question, response):
        """分析用户回答"""
        prompt = f"分析用户对问题的回答，提取用户的说话习惯和爱好：\n"
        prompt += f"问题：{question}\n"
        prompt += f"回答：{response}\n"
        prompt += "请提取用户的说话风格、常用词汇、爱好等信息，保持简洁。"
        
        analysis = self.llm.generate_response(prompt, max_tokens=100)
        return analysis
    
    def generate_summary(self, user_id, interview_data):
        """生成用户习惯总结"""
        prompt = f"基于以下访谈数据，生成用户习惯总结：\n"
        prompt += f"访谈数据：{json.dumps(interview_data, ensure_ascii=False)}\n"
        prompt += "请总结用户的说话习惯、爱好和性格特点，保持简洁。"
        
        summary = self.llm.generate_response(prompt, max_tokens=150)
        return summary
    
    def reset_interview(self, user_id, db_connection):
        """重置访谈数据"""
        cursor = db_connection.cursor()
        cursor.execute('DELETE FROM user_habits WHERE user_id = ?', (user_id,))
        db_connection.commit()
        return True
