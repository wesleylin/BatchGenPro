"""
每日图片生成限额管理器
使用Redis存储每个用户每天的生成数量，防止被攻击和薅羊毛

每日限额：100张图片
"""
from datetime import datetime, timedelta
import redis
import os

# Redis连接
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_password = os.getenv('REDIS_PASSWORD', None)
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0, decode_responses=True)

# 每日限额配置：100张图片/天
DAILY_IMAGE_LIMIT = 100


class DailyLimitManager:
    """每日限额管理器"""
    
    def __init__(self, daily_limit=DAILY_IMAGE_LIMIT):
        """
        初始化限额管理器
        
        Args:
            daily_limit: 每日限额，默认100张图片
        """
        self.redis_client = redis_client
        self.daily_limit = daily_limit
        self.counter_prefix = "daily_image_limit:"
    
    def _make_counter_key(self, user_id):
        """生成计数器Redis key"""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"{self.counter_prefix}{user_id}:{today}"
    
    def get_user_daily_count(self, user_id):
        """
        获取用户今天的生成数量
        
        Args:
            user_id: 用户标识（session_id或IP地址）
        
        Returns:
            int: 今天已生成的图片数量
        """
        counter_key = self._make_counter_key(user_id)
        count = self.redis_client.get(counter_key)
        if count is None:
            return 0
        return int(count)
    
    def check_and_increment(self, user_id, image_count=1):
        """
        检查用户是否可以生成图片，如果可以则增加计数
        
        Args:
            user_id: 用户标识（session_id或IP地址）
            image_count: 本次请求要生成的图片数量
        
        Returns:
            tuple: (是否允许, 当前已使用数量, 剩余可用数量)
        """
        counter_key = self._make_counter_key(user_id)
        current_count = self.get_user_daily_count(user_id)
        
        # 检查是否超过限额
        if current_count + image_count > self.daily_limit:
            remaining = max(0, self.daily_limit - current_count)
            return False, current_count, remaining
        
        # 增加计数，并设置过期时间为今天结束
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        expire_seconds = int((tomorrow - now).total_seconds()) + 1  # 多加1秒确保过期
        
        # 使用Redis的INCR命令原子性增加计数
        new_count = self.redis_client.incrby(counter_key, image_count)
        self.redis_client.expire(counter_key, expire_seconds)
        
        remaining = self.daily_limit - new_count
        return True, new_count, remaining


# 全局限额管理器实例
daily_limit_manager = DailyLimitManager()

