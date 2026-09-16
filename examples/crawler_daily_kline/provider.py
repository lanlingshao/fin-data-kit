from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

from examples.crawler_daily_kline.constant import FinDataSource, AdjustType, FinCapability, ApiMethod, CustomException
from src.findatakit.provider.provider import Provider
from src.findatakit.provider.provider_class_registry import register_provider
from src.findatakit.provider.provider_client import ProviderClient


@dataclass
class DailyKline:
    symbol: str
    adjust: AdjustType
    open: float
    close: float
    high: float
    low: float
    volume: int # 成交量
    amount: float # 成交额
    change: float # 涨跌额
    percent_change: float # 涨跌幅（%）
    turnover_rate : float # 换手率（%）

    date: date = None
    timestamp: int = None


@register_provider
class XueqiuProvider(Provider):
    source = FinDataSource.Xueqiu
    capabilities = {
        FinCapability.DailyKine: ApiMethod.GetDailyKline,
    }

    def __init__(self, client: ProviderClient):
        self._client = client

    async def get_daily_kline(self, symbol: str, start: date, end: date, adjust: AdjustType = None) -> list[DailyKline]:
        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        params = {
            "symbol": symbol,
            "begin": start,
            "end": end,
            "period": "day",
            "indicator": "kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance",
        }
        if adjust == AdjustType.POST:
            params["type"] = "after"
        elif adjust == AdjustType.PRE:
            params["type"] = "before"
        else:
            params["type"] = "normal"
        res = await self._client.get(url, params=params, timeout=10)
        json_data = res.json()
        data = json_data["data"]
        if "item" not in data or "column" not in data:
            # 退市的股票或者symbol错误（A股symbol前面要加上SH、SZ、BJ）
            raise CustomException(code=res.json().get("error_code", 0), msg=res.json().get("error_description", ""))

        klines = []
        if len(data["item"]) == 0:
            return klines
        df = pd.DataFrame(data["item"], columns=data["column"])
        num_cols = df.select_dtypes(include=["number"]).columns
        df[num_cols] = df[num_cols].fillna(0)
        for index, row in df.iterrows():
            kline = DailyKline(
                symbol=symbol,
                timestamp=row["timestamp"],
                adjust=adjust,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                amount=row["amount"],
                change=row["chg"],
                percent_change=row["percent"],
                turnover_rate=row["turnoverrate"],
            )
            klines.append(kline)
        return klines


@register_provider
class EastmoneyProvider(Provider):
    source = FinDataSource.Eastmoney
    capabilities = {
        FinCapability.DailyKine: ApiMethod.GetDailyKline,
    }

    def __init__(self, client: ProviderClient):
        self._client = client

    async def get_daily_kline(self, symbol: str, start: date, end: date, adjust: AdjustType = None) -> list[DailyKline]:
        start_date = start.strftime("%Y%m%d")
        end_date = end.strftime("%Y%m%d")
        market_code = 1 if symbol.startswith("6") else 0
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        # adjust_dict = {"pre": "1", "post": "2", "no": "0"}
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period_dict["daily"],
            "fqt": adjust,
            "secid": f"{market_code}.{symbol}",
            "beg": start_date,
            "end": end_date,
        }
        r = await self._client.get(url, params=params, timeout=10)
        data_json = r.json()
        klines: list[DailyKline] = []
        if not (data_json["data"] and data_json["data"]["klines"]):
            return klines
        for kline in data_json["data"]["klines"]:
            data = kline.split(",")
            stock_price = DailyKline(
                symbol=symbol,
                date=datetime.strptime(data[0], "%Y-%m-%d").date(),
                open=float(data[1]),
                close=float(data[2]),
                high=float(data[3]),
                low=float(data[4]),
                volume=data[5],
                amount=float(data[6]),
                change=float(data[9]),
                percent_change=float(data[8]),
                turnover_rate=float(data[10]),
                adjust=adjust,
            )
            klines.append(stock_price)
        return klines
