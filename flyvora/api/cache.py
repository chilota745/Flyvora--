"""
Local cache simulation mimicking Redis.
Built to allow easy swapping to django-redis in the future.
"""
from typing import Any, Optional

# In-memory dictionary acting as our simple Redis alternative for now.
_local_cache = {}

def set_cache(key: str, value: Any, timeout_seconds: int = 3600) -> bool:
    """
    Simulates saving data to Redis cache.
    Note: Real implementation would use: django.core.cache.cache.set(key, value, timeout_seconds)
    """
    _local_cache[key] = value
    return True

def get_cache(key: str) -> Optional[Any]:
    """
    Simulates retrieving data from Redis cache.
    Note: Real implementation would use: django.core.cache.cache.get(key)
    """
    return _local_cache.get(key)

def clear_cache(key: str) -> bool:
    """
    Simulates deleting key from Redis cache.
    Note: Real implementation would use: django.core.cache.cache.delete(key)
    """
    if key in _local_cache:
        del _local_cache[key]
        return True
    return False
