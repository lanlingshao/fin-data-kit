import time
from dataclasses import dataclass, field

from src.config.source_config import SourceConfig


# 请求上下文
# 无状态，每次请求都创建一个新的上下文对象
@dataclass
class RequestContext:
    source: str
    url: str
    method: str
    config: SourceConfig
    start_time: float = field(default_factory=time.time)

    retry_count: int = 0
    should_retry: bool = False
