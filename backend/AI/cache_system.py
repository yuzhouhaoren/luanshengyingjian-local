import time
import threading

class UserCache:
    def __init__(self, max_size=1000, expiration_time=3600):
        """
        初始化用户缓存
        :param max_size: 缓存最大容量
        :param expiration_time: 缓存过期时间（秒）
        """
        self.cache = {}
        self.max_size = max_size
        self.expiration_time = expiration_time
        self.lock = threading.RLock()
        
    def _is_expired(self, timestamp):
        """检查缓存项是否过期"""
        return time.time() - timestamp > self.expiration_time
    
    def get(self, key):
        """获取缓存项"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if not self._is_expired(timestamp):
                    # 更新访问时间
                    self.cache[key] = (data, time.time())
                    return data
                else:
                    # 移除过期项
                    del self.cache[key]
            return None
    
    def set(self, key, value):
        """设置缓存项"""
        with self.lock:
            # 检查缓存大小
            if len(self.cache) >= self.max_size:
                # 移除最旧的缓存项
                oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            # 设置缓存项
            self.cache[key] = (value, time.time())
    
    def delete(self, key):
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def size(self):
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)

# 初始化用户缓存实例
user_cache = UserCache()
