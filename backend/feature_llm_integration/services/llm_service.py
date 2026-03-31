import requests
import time
import random
from functools import lru_cache

class LLMService:
    def __init__(self):
        self.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.api_key = "sk-70f4585cc18047fc8ecc50682eb330de"
        self.timeout = 30  # 30秒超时
        self.max_retries = 3  # 最多3次重试
        self.rate_limit = {}  # 频率限制，格式: {user_id: [timestamp1, timestamp2, ...]}
        self.max_requests_per_minute = 60  # 每分钟最多60次请求
    
    def _check_rate_limit(self, user_id):
        """检查用户请求频率限制"""
        current_time = time.time()
        if user_id not in self.rate_limit:
            self.rate_limit[user_id] = []
        
        # 清理1分钟前的请求记录
        self.rate_limit[user_id] = [t for t in self.rate_limit[user_id] if current_time - t < 60]
        
        # 检查是否超过频率限制
        if len(self.rate_limit[user_id]) >= self.max_requests_per_minute:
            return False
        
        # 记录本次请求
        self.rate_limit[user_id].append(current_time)
        return True
    
    def _exponential_backoff(self, retry_count):
        """指数退避策略"""
        base_delay = 1  # 基础延迟1秒
        max_delay = 10  # 最大延迟10秒
        delay = min(base_delay * (2 ** retry_count) + random.uniform(0, 1), max_delay)
        time.sleep(delay)
    
    def call_llm(self, user_id, messages, model="qwen3.5-flash", temperature=0.7, max_tokens=512):
        """调用大模型API
        
        Args:
            user_id: 用户ID
            messages: 消息列表，格式: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 tokens
            
        Returns:
            生成的文本内容
        """
        # 检查频率限制
        if not self._check_rate_limit(user_id):
            raise Exception("请求过于频繁，请稍后再试")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 重试机制
        for retry in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    if retry < self.max_retries - 1:
                        self._exponential_backoff(retry)
                        continue
                    else:
                        raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
            except requests.exceptions.Timeout:
                if retry < self.max_retries - 1:
                    self._exponential_backoff(retry)
                    continue
                else:
                    raise Exception("API调用超时")
            
            except requests.exceptions.RequestException as e:
                if retry < self.max_retries - 1:
                    self._exponential_backoff(retry)
                    continue
                else:
                    raise Exception(f"API调用异常: {str(e)}")

# 创建全局实例
llm_service = LLMService()
