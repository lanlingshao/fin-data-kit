from enum import IntEnum, StrEnum

from src.findatakit.provider.enum import DataSourceId, CapabilityId


class FinDataSource(DataSourceId):
    SSEExchange = "sse_exchange" # china shanghai exchange 上海证券交易所
    Xueqiu = "xueqiu"
    Eastmoney = "eastmoney"


class FinCapability(CapabilityId):
    SSEStockList = "sse_stock_list"
    CnDailyKine = "cn_daily_kline"


class ApiMethod(StrEnum):
    GetSSEStockList = "get_sse_stock_list"
    GetDailyKline = "get_daily_kline"


class CustomException(Exception):
    """
    自定义异常基类
    """

    def __init__(
        self,
        code: int | None,
        msg: str | None,
    ) -> None:
        """
        - code (int): 业务状态码。
        - msg (str): 错误消息。
        """
        super().__init__(msg)  # 调用父类初始化方法
        self.code: int | None = code
        self.msg: str | None = msg

    def __str__(self) -> str | None:
        """返回异常消息

        返回:
        - str: 异常消息
        """
        return self.msg