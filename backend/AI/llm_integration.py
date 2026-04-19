import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Load backend/.env so local development can configure API keys without shell exports.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value, default):
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default

class LLMIntegration:
    def __init__(self):
        self.base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).rstrip("/")
        self.api_key = (
            os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("QWEN_API_KEY")
            or ""
        ).strip()
        self.model_name = os.getenv("DASHSCOPE_MODEL", "qwen3.5-flash").strip() or "qwen3.5-flash"
        self.request_timeout_seconds = _to_int(os.getenv("DASHSCOPE_TIMEOUT_SECONDS", "30"), 30)
        self.offline_fallback_enabled = _to_bool(
            os.getenv("DASHSCOPE_OFFLINE_FALLBACK", "true"),
            True,
        )
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _offline_response(self, max_tokens=100):
        # Keep local fallback short to match the existing UI expectations.
        if int(max_tokens) <= 60:
            return "离线模式：已收到，我在认真听你说。"
        return "离线模式：我已经收到你的内容，当前未配置或未连通云端模型，先用本地兜底回复保证流程可用。"
    
    def generate_response(self, prompt, max_tokens=100):
        """生成大模型响应"""
        if not self.api_key:
            if self.offline_fallback_enabled:
                return self._offline_response(max_tokens=max_tokens)
            return "Error: DASHSCOPE_API_KEY is not configured"

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
                data=json.dumps(payload),
                timeout=self.request_timeout_seconds,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                if self.offline_fallback_enabled:
                    return self._offline_response(max_tokens=max_tokens)
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            if self.offline_fallback_enabled:
                return self._offline_response(max_tokens=max_tokens)
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
    
    def generate_chat_response(self, user_message, user_profile, chat_history=None, favorability=0):
        """生成聊天回复"""
        chat_history = chat_history or []
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
