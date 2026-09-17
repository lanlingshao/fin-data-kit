import time
from dataclasses import dataclass, field

from findatakit.config.source_config import SourceConfig


@dataclass
class RequestContext:
    """
    Stateless, each request creates a new context.
    无状态，每次请求都创建一个新的上下文对象
    """
    source: str
    url: str
    method: str
    config: SourceConfig
    start_time: float = field(default_factory=time.time)

    retry_count: int = 0
    should_retry: bool = False
