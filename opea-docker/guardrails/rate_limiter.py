import time
import redis
from typing import Optional, Tuple
from config import config
from loguru import logger

class RateLimiter:
    def __init__(self):
        self.enabled = config.rate_limit_enabled
        self.max_requests = config.rate_limit_requests
        self.period = config.rate_limit_period
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    password=config.redis_password,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                logger.warning("Rate limiting will be disabled")
                self.enabled = False
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """Check if the client is rate limited.
        
        Args:
            client_id: A unique identifier for the client (e.g., IP address)
            
        Returns:
            Tuple of (is_limited, retry_after)
        """
        if not self.enabled or not self.redis_client:
            return False, None
            
        try:
            # Use a sliding window for rate limiting
            current_time = int(time.time())
            key = f"rate_limit:{client_id}"
            
            # Remove requests older than the time window
            self.redis_client.zremrangebyscore(key, 0, current_time - self.period)
            
            # Count current requests in the window
            current_count = self.redis_client.zcard(key)
            
            # Check if rate limit exceeded
            if current_count >= self.max_requests:
                # Get the oldest request timestamp to calculate retry-after
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = int(oldest[0][1])
                    retry_after = max(1, oldest_timestamp + self.period - current_time)
                    return True, retry_after
                return True, self.period
            
            # Add current request to the window
            self.redis_client.zadd(key, {str(current_time): current_time})
            # Set expiration on the key to auto-cleanup
            self.redis_client.expire(key, self.period * 2)
            
            return False, None
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # If there's an error, don't rate limit
            return False, None

# Create a global rate limiter instance
rate_limiter = RateLimiter()