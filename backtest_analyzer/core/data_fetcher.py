"""
K线数据获取模块

从Freqtrade的数据目录加载历史K线数据
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from freqtrade.data.history import load_pair_history
from freqtrade.configuration import Configuration


class DataFetcher:
    """历史数据获取器"""

    def __init__(self, config: Optional[Dict] = None, user_data_dir: Optional[str] = None):
        """
        初始化数据获取器

        Args:
            config: Freqtrade配置字典
            user_data_dir: 用户数据目录路径
        """
        self.config = config or self._load_default_config()
        self.user_data_dir = Path(user_data_dir or self.config.get('user_data_dir', 'user_data'))
        self.data_dir = self.user_data_dir / 'data'

        # 从配置中获取交易所和时间周期
        self.exchange = self.config.get('exchange', {}).get('name', 'binance')
        self.default_timeframe = self.config.get('timeframe', '5m')

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        try:
            config_files = [
                'user_data/config-custom.json',
                'user_data/config-private.json'
            ]
            # 检查哪些配置文件存在
            existing_files = [f for f in config_files if Path(f).exists()]

            if existing_files:
                conf = Configuration.from_files(existing_files)
                return conf.get_config()
            else:
                # 返回最小配置
                return {
                    'exchange': {'name': 'binance'},
                    'timeframe': '5m',
                    'user_data_dir': 'user_data'
                }
        except Exception as e:
            print(f"⚠ 加载配置失败，使用默认值: {e}")
            return {
                'exchange': {'name': 'binance'},
                'timeframe': '5m',
                'user_data_dir': 'user_data'
            }

    def get_pair_data(
        self,
        pair: str,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        expand_percent: float = 0.2
    ) -> pd.DataFrame:
        """
        获取指定币种的K线数据

        Args:
            pair: 交易对，如 'BTC/USDT'
            timeframe: 时间周期，如 '5m', 默认使用配置中的值
            start_date: 开始时间
            end_date: 结束时间
            expand_percent: 时间范围扩展比例（前后各扩展指定比例），用于提供上下文

        Returns:
            包含K线数据的DataFrame
        """
        timeframe = timeframe or self.default_timeframe

        try:
            # 如果提供了时间范围且需要扩展
            if start_date and end_date and expand_percent > 0:
                duration = end_date - start_date
                expansion = duration * expand_percent
                start_date = start_date - expansion
                end_date = end_date + expansion

            # 使用Freqtrade的load_pair_history
            df = load_pair_history(
                datadir=self.data_dir / self.exchange,
                timeframe=timeframe,
                pair=pair,
                data_format='feather',  # 优先使用feather格式
                candle_type='',
                timerange=None  # 完整加载，然后在内存中裁剪
            )

            if df.empty:
                # 尝试JSON格式
                df = load_pair_history(
                    datadir=self.data_dir / self.exchange,
                    timeframe=timeframe,
                    pair=pair,
                    data_format='json',
                    candle_type='',
                    timerange=None
                )

            if df.empty:
                print(f"⚠ 未找到 {pair} 的数据")
                return pd.DataFrame()

            # 时间范围裁剪
            if start_date or end_date:
                df = df.loc[start_date:end_date]

            print(f"✓ 加载 {pair} 数据: {len(df)} 根K线 ({timeframe})")
            return df

        except Exception as e:
            print(f"✗ 加载 {pair} 数据失败: {e}")
            return pd.DataFrame()

    def get_multiple_pairs_data(
        self,
        pairs: List[str],
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个币种的K线数据

        Args:
            pairs: 交易对列表
            timeframe: 时间周期
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            {pair: DataFrame} 字典
        """
        result = {}
        for pair in pairs:
            df = self.get_pair_data(pair, timeframe, start_date, end_date)
            if not df.empty:
                result[pair] = df
        return result

    def get_data_for_trade(
        self,
        pair: str,
        open_date: datetime,
        close_date: datetime,
        timeframe: Optional[str] = None,
        expand_candles: int = 100
    ) -> pd.DataFrame:
        """
        获取单笔交易时间段的K线数据（前后扩展）

        Args:
            pair: 交易对
            open_date: 开仓时间
            close_date: 平仓时间
            timeframe: 时间周期
            expand_candles: 前后扩展的K线数量

        Returns:
            K线DataFrame
        """
        timeframe = timeframe or self.default_timeframe

        # 计算扩展时间
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        expansion = timedelta(minutes=expand_candles * timeframe_minutes)

        start = open_date - expansion
        end = close_date + expansion

        return self.get_pair_data(pair, timeframe, start, end, expand_percent=0)

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """将时间周期转换为分钟数"""
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 1440
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 10080
        else:
            return 5  # 默认5分钟

    def check_data_availability(self, pairs: List[str], timeframe: Optional[str] = None) -> Dict[str, bool]:
        """
        检查数据可用性

        Args:
            pairs: 交易对列表
            timeframe: 时间周期

        Returns:
            {pair: is_available} 字典
        """
        timeframe = timeframe or self.default_timeframe
        result = {}

        for pair in pairs:
            # 检查feather文件
            feather_file = self.data_dir / self.exchange / f"{pair.replace('/', '_')}-{timeframe}.feather"
            # 检查json文件
            json_file = self.data_dir / self.exchange / f"{pair.replace('/', '_')}-{timeframe}.json"

            result[pair] = feather_file.exists() or json_file.exists()

        return result

    def get_missing_pairs(self, pairs: List[str], timeframe: Optional[str] = None) -> List[str]:
        """
        获取缺失数据的交易对列表

        Args:
            pairs: 交易对列表
            timeframe: 时间周期

        Returns:
            缺失数据的交易对列表
        """
        availability = self.check_data_availability(pairs, timeframe)
        return [pair for pair, available in availability.items() if not available]

    def download_missing_data_command(
        self,
        pairs: List[str],
        timeframe: Optional[str] = None,
        days: int = 365
    ) -> str:
        """
        生成下载缺失数据的命令

        Args:
            pairs: 交易对列表
            timeframe: 时间周期
            days: 下载天数

        Returns:
            freqtrade download-data 命令字符串
        """
        missing_pairs = self.get_missing_pairs(pairs, timeframe)

        if not missing_pairs:
            return "# 所有数据都已存在，无需下载"

        timeframe = timeframe or self.default_timeframe
        pairs_str = ' '.join(missing_pairs)

        command = f"""# 缺失 {len(missing_pairs)} 个币种的数据，执行以下命令下载：

export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

freqtrade download-data \\
  --exchange {self.exchange} \\
  --pairs {pairs_str} \\
  --timeframes {timeframe} \\
  --days {days} \\
  --dataformat-ohlcv feather
"""
        return command


def get_data_for_replay(
    pair: str,
    open_date: datetime,
    close_date: datetime,
    config: Optional[Dict] = None,
    expand_candles: int = 100
) -> pd.DataFrame:
    """
    便捷函数：获取交易复盘所需的K线数据

    Args:
        pair: 交易对
        open_date: 开仓时间
        close_date: 平仓时间
        config: 配置字典
        expand_candles: 前后扩展的K线数量

    Returns:
        K线DataFrame
    """
    fetcher = DataFetcher(config)
    return fetcher.get_data_for_trade(pair, open_date, close_date, expand_candles=expand_candles)
