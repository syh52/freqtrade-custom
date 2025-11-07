"""
策略运行模块

加载策略并重新计算技术指标，用于深度分析
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from freqtrade.resolvers import StrategyResolver
from freqtrade.configuration import Configuration
from freqtrade.data.dataprovider import DataProvider
from freqtrade.exchange import Exchange


class StrategyRunner:
    """策略运行器 - 重新计算技术指标"""

    def __init__(
        self,
        strategy_name: Optional[str] = None,
        config: Optional[Dict] = None,
        strategy_path: Optional[str] = None
    ):
        """
        初始化策略运行器

        Args:
            strategy_name: 策略名称（如果在user_data/strategies目录下）
            config: Freqtrade配置字典
            strategy_path: 策略文件的完整路径（用于加载回测快照中的策略）
        """
        self.config = config or self._load_default_config()

        # 如果提供了策略路径，临时添加到策略搜索路径
        if strategy_path:
            strategy_dir = Path(strategy_path).parent
            if 'strategy_path' not in self.config:
                self.config['strategy_path'] = []
            self.config['strategy_path'].append(str(strategy_dir))
            strategy_name = strategy_name or Path(strategy_path).stem

        self.strategy_name = strategy_name or self.config.get('strategy', 'NostalgiaForInfinityX7')

        # 加载策略
        self.strategy = self._load_strategy()

        # 初始化DataProvider（策略需要）
        self.dp = None
        if self.strategy:
            self._init_dataprovider()

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        try:
            config_files = [
                'user_data/config-custom.json',
                'user_data/config-private.json'
            ]
            existing_files = [f for f in config_files if Path(f).exists()]

            if existing_files:
                conf = Configuration.from_files(existing_files)
                return conf.get_config()
            else:
                return {
                    'exchange': {'name': 'binance'},
                    'timeframe': '5m',
                    'user_data_dir': 'user_data',
                    'strategy': 'NostalgiaForInfinityX7'
                }
        except Exception as e:
            print(f"⚠ 加载配置失败，使用默认值: {e}")
            return {
                'exchange': {'name': 'binance'},
                'timeframe': '5m',
                'user_data_dir': 'user_data',
                'strategy': 'NostalgiaForInfinityX7'
            }

    def _load_strategy(self):
        """加载策略"""
        try:
            # 设置策略名称到配置
            self.config['strategy'] = self.strategy_name

            # 使用StrategyResolver加载策略
            strategy = StrategyResolver.load_strategy(self.config)

            print(f"✓ 成功加载策略: {self.strategy_name}")
            return strategy
        except Exception as e:
            print(f"✗ 加载策略失败: {e}")
            print(f"  策略名称: {self.strategy_name}")
            print(f"  搜索路径: {self.config.get('strategy_path', 'user_data/strategies')}")
            return None

    def _init_dataprovider(self):
        """初始化DataProvider"""
        try:
            # 创建简化的DataProvider（不需要实际连接交易所）
            self.dp = DataProvider(self.config, None, None)
            self.strategy.dp = self.dp
            print(f"✓ DataProvider已初始化")
        except Exception as e:
            print(f"⚠ DataProvider初始化失败: {e}")

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        运行策略的populate_indicators方法

        Args:
            dataframe: 原始K线数据
            metadata: 元数据字典，必须包含 'pair' 键

        Returns:
            添加了技术指标的DataFrame
        """
        if self.strategy is None:
            print("✗ 策略未加载，无法计算指标")
            return dataframe

        try:
            # 调用策略的populate_indicators
            df_with_indicators = self.strategy.populate_indicators(dataframe.copy(), metadata)

            print(f"✓ 成功计算 {metadata['pair']} 的技术指标")
            print(f"  原始列数: {len(dataframe.columns)}, 新增指标: {len(df_with_indicators.columns) - len(dataframe.columns)}")

            return df_with_indicators
        except Exception as e:
            print(f"✗ 计算指标失败: {e}")
            import traceback
            traceback.print_exc()
            return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        运行策略的入场信号计算

        Args:
            dataframe: 包含指标的DataFrame
            metadata: 元数据字典

        Returns:
            添加了入场信号的DataFrame
        """
        if self.strategy is None:
            return dataframe

        try:
            df_with_entry = self.strategy.populate_entry_trend(dataframe.copy(), metadata)
            print(f"✓ 成功计算 {metadata['pair']} 的入场信号")
            return df_with_entry
        except Exception as e:
            print(f"✗ 计算入场信号失败: {e}")
            return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        运行策略的出场信号计算

        Args:
            dataframe: 包含指标的DataFrame
            metadata: 元数据字典

        Returns:
            添加了出场信号的DataFrame
        """
        if self.strategy is None:
            return dataframe

        try:
            df_with_exit = self.strategy.populate_exit_trend(dataframe.copy(), metadata)
            print(f"✓ 成功计算 {metadata['pair']} 的出场信号")
            return df_with_exit
        except Exception as e:
            print(f"✗ 计算出场信号失败: {e}")
            return dataframe

    def analyze_ticker(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        运行完整的策略分析流程（指标 + 入场 + 出场）

        Args:
            dataframe: 原始K线数据
            metadata: 元数据字典

        Returns:
            完整分析后的DataFrame
        """
        if self.strategy is None:
            return dataframe

        try:
            # 调用策略的analyze_ticker（内部会依次调用populate_indicators、entry、exit）
            df_analyzed = self.strategy.analyze_ticker(dataframe.copy(), metadata)

            print(f"✓ 成功完成 {metadata['pair']} 的策略分析")
            return df_analyzed
        except Exception as e:
            print(f"✗ 策略分析失败: {e}")
            import traceback
            traceback.print_exc()
            return dataframe

    def get_entry_signal_columns(self) -> list:
        """获取入场信号列名"""
        # NostalgiaForInfinityX7 使用 enter_long 和 enter_short
        return ['enter_long', 'enter_short', 'enter_tag']

    def get_exit_signal_columns(self) -> list:
        """获取出场信号列名"""
        return ['exit_long', 'exit_short', 'exit_tag']

    def get_indicator_list(self) -> list:
        """
        获取策略使用的主要指标列表（用于可视化）

        Returns:
            指标列名列表
        """
        if self.strategy is None:
            return []

        # 常见的技术指标（可以通过分析策略代码自动提取）
        common_indicators = [
            # 移动平均线
            'ema_12', 'ema_26', 'ema_50', 'ema_200',
            'sma_50', 'sma_200',

            # 振荡器
            'rsi', 'rsi_14',
            'cci', 'cci_20',
            'mfi',

            # MACD
            'macd', 'macdsignal', 'macdhist',

            # 布林带
            'bb_lower', 'bb_middle', 'bb_upper',

            # ATR
            'atr',

            # 成交量
            'volume',
        ]

        return common_indicators

    def get_strategy_info(self) -> Dict:
        """
        获取策略信息

        Returns:
            策略信息字典
        """
        if self.strategy is None:
            return {}

        return {
            'name': self.strategy_name,
            'timeframe': self.strategy.timeframe,
            'startup_candle_count': getattr(self.strategy, 'startup_candle_count', 0),
            'stoploss': self.strategy.stoploss,
            'can_short': getattr(self.strategy, 'can_short', False),
            'position_adjustment_enable': getattr(self.strategy, 'position_adjustment_enable', False),
        }


def quick_analyze(
    dataframe: pd.DataFrame,
    pair: str,
    strategy_name: Optional[str] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    便捷函数：快速分析K线数据

    Args:
        dataframe: K线数据
        pair: 交易对
        strategy_name: 策略名称
        config: 配置字典

    Returns:
        添加了指标和信号的DataFrame
    """
    runner = StrategyRunner(strategy_name, config)
    metadata = {'pair': pair}
    return runner.analyze_ticker(dataframe, metadata)
