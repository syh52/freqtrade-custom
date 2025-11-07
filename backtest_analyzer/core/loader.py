"""
数据加载模块

复用Freqtrade内置API加载回测结果数据
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from freqtrade.data.btanalysis import (
    load_backtest_stats,
    load_backtest_data,
    trade_list_to_dataframe
)


class BacktestResultLoader:
    """回测结果加载器"""

    def __init__(self, backtest_file: str):
        """
        初始化加载器

        Args:
            backtest_file: 回测结果文件路径（支持.json或.zip）
        """
        self.backtest_file = Path(backtest_file)
        if not self.backtest_file.exists():
            raise FileNotFoundError(f"回测文件不存在: {backtest_file}")

        self.stats = None
        self.trades_df = None
        self.config = None
        self.strategy_code = None
        self.market_change = None

    def load_all(self) -> Dict:
        """
        加载所有数据

        Returns:
            包含所有数据的字典
        """
        # 加载统计数据
        self.stats = self._load_stats()

        # 加载交易数据
        self.trades_df = self._load_trades()

        # 如果是ZIP文件，加载额外数据
        if self.backtest_file.suffix == '.zip':
            self._load_from_zip()

        return {
            'stats': self.stats,
            'trades': self.trades_df,
            'config': self.config,
            'strategy_code': self.strategy_code,
            'market_change': self.market_change
        }

    def _load_stats(self) -> Dict:
        """加载统计数据"""
        try:
            stats = load_backtest_stats(self.backtest_file)
            print(f"✓ 成功加载回测统计数据")
            return stats
        except Exception as e:
            print(f"✗ 加载统计数据失败: {e}")
            raise

    def _load_trades(self) -> pd.DataFrame:
        """加载交易列表并转换为DataFrame"""
        try:
            # 使用load_backtest_data获取交易列表
            backtest_data = load_backtest_data(self.backtest_file)

            # 检查数据是否为空（支持dict和DataFrame）
            if isinstance(backtest_data, dict):
                if not backtest_data:
                    raise ValueError("回测数据为空")
                # 获取第一个策略的交易数据
                strategy_name = list(backtest_data.keys())[0]
                trades = backtest_data[strategy_name]
            elif isinstance(backtest_data, pd.DataFrame):
                if backtest_data.empty:
                    raise ValueError("回测数据为空")
                trades = backtest_data
            else:
                raise TypeError(f"不支持的数据类型: {type(backtest_data)}")

            # 转换为DataFrame（如果还不是）
            if not isinstance(trades, pd.DataFrame):
                trades_df = trade_list_to_dataframe(trades)
            else:
                trades_df = trades

            print(f"✓ 成功加载 {len(trades_df)} 笔交易")
            return trades_df

        except Exception as e:
            print(f"✗ 加载交易数据失败: {e}")
            raise

    def _load_from_zip(self):
        """从ZIP文件中提取额外数据"""
        try:
            with zipfile.ZipFile(self.backtest_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                base_name = self.backtest_file.stem  # 不含.zip的文件名

                # 加载配置文件
                config_file = f"{base_name}_config.json"
                if config_file in file_list:
                    with zip_ref.open(config_file) as f:
                        self.config = json.load(f)
                    print(f"✓ 成功加载配置快照")

                # 加载策略代码
                strategy_files = [f for f in file_list if f.endswith('.py')]
                if strategy_files:
                    with zip_ref.open(strategy_files[0]) as f:
                        self.strategy_code = f.read().decode('utf-8')
                    print(f"✓ 成功加载策略代码快照: {strategy_files[0]}")

                # 加载市场变化数据
                market_change_file = f"{base_name}_market_change.feather"
                if market_change_file in file_list:
                    # 需要先提取到临时文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.feather', delete=False) as tmp:
                        tmp.write(zip_ref.read(market_change_file))
                        tmp_path = tmp.name

                    self.market_change = pd.read_feather(tmp_path)
                    Path(tmp_path).unlink()  # 删除临时文件
                    print(f"✓ 成功加载市场变化数据: {len(self.market_change)} 行")

        except Exception as e:
            print(f"⚠ 从ZIP加载额外数据时出错: {e}")
            # 不抛出异常，因为额外数据是可选的

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        if self.stats:
            return list(self.stats['strategy'].keys())[0]
        return "Unknown"

    def get_timerange(self) -> Tuple[str, str]:
        """获取回测时间范围"""
        if self.trades_df is not None and not self.trades_df.empty:
            start = self.trades_df['open_date'].min()
            end = self.trades_df['close_date'].max()
            return str(start), str(end)
        return "Unknown", "Unknown"

    def get_rejected_signals(self) -> Optional[pd.DataFrame]:
        """
        获取被拒绝的信号

        Returns:
            被拒绝信号的DataFrame，如果不存在则返回None
        """
        if self.stats is None:
            return None

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        # 检查是否有rejected_signals字段
        if 'rejected_signals' in strategy_stats:
            rejected = strategy_stats['rejected_signals']
            if rejected and isinstance(rejected, list):
                return pd.DataFrame(rejected)

        return None

    def get_summary(self) -> Dict:
        """
        获取回测摘要信息

        Returns:
            摘要信息字典
        """
        if self.stats is None or self.trades_df is None:
            return {}

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        # 计算基本统计（从trades_df直接计算，更可靠）
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['profit_ratio'] > 0])
        losing_trades = len(self.trades_df[self.trades_df['profit_ratio'] <= 0])

        # 提取关键指标
        summary = {
            'strategy': strategy_name,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_profit_pct': strategy_stats.get('profit_total', 0) * 100,
            'total_profit_abs': strategy_stats.get('profit_total_abs', 0),
            'max_drawdown_pct': abs(strategy_stats.get('max_drawdown', 0)) * 100,
            'sharpe_ratio': strategy_stats.get('sharpe', 0),
            'sortino_ratio': strategy_stats.get('sortino', 0),
            'calmar_ratio': strategy_stats.get('calmar', 0),
            'profit_factor': strategy_stats.get('profit_factor', 0),
            'expectancy': strategy_stats.get('expectancy', 0),
            'avg_profit_pct': self.trades_df['profit_ratio'].mean() * 100,
            'timerange': self.get_timerange(),
        }

        return summary

    def get_pairs_performance(self) -> pd.DataFrame:
        """获取各币种表现"""
        if self.stats is None:
            return pd.DataFrame()

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        if 'results_per_pair' in strategy_stats:
            pairs_perf = pd.DataFrame(strategy_stats['results_per_pair'])
            # 按总收益排序
            if 'profit_total_abs' in pairs_perf.columns:
                pairs_perf = pairs_perf.sort_values('profit_total_abs', ascending=False)
            return pairs_perf

        return pd.DataFrame()

    def get_enter_tag_performance(self) -> pd.DataFrame:
        """获取入场标签表现"""
        if self.stats is None:
            return pd.DataFrame()

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        if 'results_per_enter_tag' in strategy_stats:
            enter_perf = pd.DataFrame(strategy_stats['results_per_enter_tag'])
            # 按交易数量排序
            if 'trades' in enter_perf.columns:
                enter_perf = enter_perf.sort_values('trades', ascending=False)
            return enter_perf

        return pd.DataFrame()

    def get_exit_reason_performance(self) -> pd.DataFrame:
        """获取出场原因表现"""
        if self.stats is None:
            return pd.DataFrame()

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        if 'exit_reason_summary' in strategy_stats:
            exit_perf = pd.DataFrame(strategy_stats['exit_reason_summary'])
            # 按交易数量排序
            if 'trades' in exit_perf.columns:
                exit_perf = exit_perf.sort_values('trades', ascending=False)
            return exit_perf

        return pd.DataFrame()

    def get_mix_tag_performance(self) -> pd.DataFrame:
        """获取入场+出场组合表现"""
        if self.stats is None:
            return pd.DataFrame()

        strategy_name = self.get_strategy_name()
        strategy_stats = self.stats['strategy'][strategy_name]

        if 'mix_tag_stats' in strategy_stats:
            mix_perf = pd.DataFrame(strategy_stats['mix_tag_stats'])
            # 按总收益排序
            if 'profit_total_abs' in mix_perf.columns:
                mix_perf = mix_perf.sort_values('profit_total_abs', ascending=False)
            return mix_perf

        return pd.DataFrame()


def quick_load(backtest_file: str) -> Tuple[pd.DataFrame, Dict]:
    """
    快速加载函数

    Args:
        backtest_file: 回测文件路径

    Returns:
        (trades_df, stats) 元组
    """
    loader = BacktestResultLoader(backtest_file)
    data = loader.load_all()
    return data['trades'], data['stats']
