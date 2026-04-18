import requests
import json

class LLMIntegration:
    def __init__(self):
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.api_key = "sk-70f4585cc18047fc8ecc50682eb330de"
        self.model_name = "qwen3.5-flash"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, prompt, max_tokens=100):
        """生成大模型响应"""
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_post(self, user_profile, intent_type):
        """生成交友帖子"""
        # 读取creat.txt中的标准执行规范
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        creat_file_path = os.path.join(current_dir, 'creat.txt')
        with open(creat_file_path, 'r', encoding='utf-8') as f:
            creat_spec = f.read()
        
        prompt = f"{creat_spec}\n"
        prompt += f"【用户人设信息】{json.dumps(user_profile, ensure_ascii=False)}\n"
        prompt += f"【生成锁定要求】\n"
        prompt += "1. 100%贴合上述人设，绝对不能编造人设外的任何信息\n"
        prompt += "2. 严格按照规范的分模块规则生成，完全符合小红书交友帖的流量逻辑\n"
        prompt += "3. 彻底去除AI感,像真人随手发布的原创内容,自然不生硬\n"
        prompt += "4. 核心用途是用户交友，不是带货、探店、科普等其他用途\n"
        prompt += f"5. 生成的帖子类型：{intent_type}\n"
        prompt += "【最终生成结果】"
        
        return self.generate_response(prompt, max_tokens=300)
    
    def generate_chat_response(self, user_message, user_profile, chat_history=[], favorability=0):
        """生成聊天回复"""
        prompt = f"你是一个基于用户画像的聊天助手，根据以下用户信息和聊天历史，生成一个自然的回复：\n"
        prompt += f"用户信息：{json.dumps(user_profile, ensure_ascii=False)}\n"
        prompt += f"当前好感度：{favorability}\n"
        
        if chat_history:
            prompt += "聊天历史：\n"
            for msg in chat_history:
                role = "用户" if msg['isUser'] else "你"
                prompt += f"{role}：{msg['content']}\n"
        
        prompt += f"用户最新消息：{user_message}\n"
        prompt += "请生成一个符合用户画像的自然回复,保持口语化,长度控制在20字以内。"
        
        return self.generate_response(prompt, max_tokens=50)
