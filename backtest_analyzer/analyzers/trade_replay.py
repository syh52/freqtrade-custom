"""
交易复盘引擎

核心功能：针对每笔交易进行深度复盘，分析最优入场/出场点，检查拒绝信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class TradeReplayEngine:
    """交易复盘引擎"""

    def __init__(
        self,
        trade_row: pd.Series,
        candles_df: pd.DataFrame,
        indicators_df: Optional[pd.DataFrame] = None
    ):
        """
        初始化复盘引擎

        Args:
            trade_row: 单笔交易的Series（来自trades_df的一行）
            candles_df: K线数据（需包含交易前后的数据）
            indicators_df: 带技术指标的K线数据（可选，如果提供则不重新计算）
        """
        self.trade = trade_row
        self.candles = candles_df.copy()
        self.indicators = indicators_df if indicators_df is not None else candles_df.copy()

        # 交易基本信息
        self.pair = trade_row.get('pair', 'Unknown')
        self.open_date = pd.to_datetime(trade_row['open_date'])
        self.close_date = pd.to_datetime(trade_row['close_date'])
        self.open_rate = trade_row['open_rate']
        self.close_rate = trade_row['close_rate']
        self.profit_ratio = trade_row.get('profit_ratio', 0)
        self.is_short = trade_row.get('is_short', False)

        # 交易时段的K线
        self.trade_candles = self.indicators[
            (self.indicators.index >= self.open_date) &
            (self.indicators.index <= self.close_date)
        ]

    def analyze(self) -> Dict:
        """
        执行完整的交易复盘

        Returns:
            复盘结果字典
        """
        analysis = {
            'trade_info': self._get_trade_info(),
            'entry_analysis': self._analyze_entry(),
            'holding_analysis': self._analyze_holding_period(),
            'exit_analysis': self._analyze_exit(),
            'optimal_points': self._find_optimal_points(),
            'rejected_signals': self._analyze_rejected_signals(),
            'reflection': self._generate_reflection(),
            'recommendations': self._generate_recommendations()
        }

        return analysis

    def _get_trade_info(self) -> Dict:
        """获取交易基本信息"""
        return {
            'pair': self.pair,
            'direction': 'Short' if self.is_short else 'Long',
            'open_date': str(self.open_date),
            'close_date': str(self.close_date),
            'open_rate': self.open_rate,
            'close_rate': self.close_rate,
            'profit_pct': self.profit_ratio * 100,
            'profit_abs': self.trade.get('profit_abs', 0),
            'duration_hours': (self.close_date - self.open_date).total_seconds() / 3600,
            'enter_tag': self.trade.get('enter_tag', 'Unknown'),
            'exit_reason': self.trade.get('exit_reason', 'Unknown'),
        }

    def _analyze_entry(self) -> Dict:
        """分析入场点"""
        entry_analysis = {}

        # 获取入场时的K线
        entry_candle = self.indicators[self.indicators.index >= self.open_date].iloc[0] if len(self.indicators[self.indicators.index >= self.open_date]) > 0 else None

        if entry_candle is not None:
            entry_analysis['entry_candle'] = {
                'date': str(entry_candle.name),
                'open': entry_candle.get('open', 0),
                'high': entry_candle.get('high', 0),
                'low': entry_candle.get('low', 0),
                'close': entry_candle.get('close', 0),
                'volume': entry_candle.get('volume', 0)
            }

            # 提取关键指标（如果存在）
            indicators = {}
            indicator_names = ['rsi', 'rsi_14', 'cci', 'cci_20', 'mfi', 'ema_12', 'ema_26', 'ema_50', 'ema_200']
            for ind in indicator_names:
                if ind in entry_candle:
                    indicators[ind] = float(entry_candle[ind]) if not pd.isna(entry_candle[ind]) else None

            entry_analysis['indicators'] = indicators

            # 入场评估
            entry_analysis['assessment'] = self._assess_entry_conditions(entry_candle)

        return entry_analysis

    def _assess_entry_conditions(self, candle: pd.Series) -> List[str]:
        """评估入场条件"""
        issues = []

        # RSI检查
        if 'rsi' in candle or 'rsi_14' in candle:
            rsi = candle.get('rsi', candle.get('rsi_14', None))
            if rsi is not None and not pd.isna(rsi):
                if self.is_short and rsi < 30:
                    issues.append(f"❌ 空头入场时RSI={rsi:.1f}（超卖区），不适合做空")
                elif not self.is_short and rsi > 70:
                    issues.append(f"❌ 多头入场时RSI={rsi:.1f}（超买区），不适合做多")
                elif 40 <= rsi <= 60:
                    issues.append(f"✓ RSI={rsi:.1f}（中性区），入场时机合理")

        # CCI检查
        if 'cci' in candle or 'cci_20' in candle:
            cci = candle.get('cci', candle.get('cci_20', None))
            if cci is not None and not pd.isna(cci):
                if self.is_short and cci < -100:
                    issues.append(f"❌ 空头入场时CCI={cci:.1f}（超卖），不适合做空")
                elif not self.is_short and cci > 100:
                    issues.append(f"❌ 多头入场时CCI={cci:.1f}（超买），不适合做多")

        # 如果没有发现问题
        if len(issues) == 0:
            issues.append("✓ 未发现明显的入场时机问题")

        return issues

    def _analyze_holding_period(self) -> Dict:
        """分析持仓期间"""
        holding_analysis = {}

        if len(self.trade_candles) == 0:
            return holding_analysis

        # MFE和MAE
        if self.is_short:
            # 空头：最高点是最不利，最低点是最有利
            mfe_price = self.trade_candles['low'].min()
            mae_price = self.trade_candles['high'].max()
        else:
            # 多头：最高点是最有利，最低点是最不利
            mfe_price = self.trade_candles['high'].max()
            mae_price = self.trade_candles['low'].min()

        mfe_ratio = (mfe_price - self.open_rate) / self.open_rate
        mae_ratio = (mae_price - self.open_rate) / self.open_rate

        if self.is_short:
            mfe_ratio = -mfe_ratio  # 空头收益是负向的
            mae_ratio = -mae_ratio

        holding_analysis['mfe'] = {
            'price': mfe_price,
            'ratio_pct': mfe_ratio * 100,
            'date': str(self.trade_candles['high'].idxmax()) if not self.is_short else str(self.trade_candles['low'].idxmin())
        }

        holding_analysis['mae'] = {
            'price': mae_price,
            'ratio_pct': mae_ratio * 100,
            'date': str(self.trade_candles['low'].idxmin()) if not self.is_short else str(self.trade_candles['high'].idxmax())
        }

        # 盈利效率
        if mfe_ratio > 0:
            profit_efficiency = self.profit_ratio / mfe_ratio
            holding_analysis['profit_efficiency'] = {
                'ratio': profit_efficiency,
                'assessment': '✓ 优秀' if profit_efficiency > 0.7 else '⚠ 一般' if profit_efficiency > 0.4 else '❌ 较差'
            }

        # DCA分析
        if 'orders' in self.trade and isinstance(self.trade['orders'], list):
            orders = self.trade['orders']
            if len(orders) > 1:
                holding_analysis['dca_orders'] = [
                    {
                        'date': order.get('order_filled_timestamp', 'Unknown'),
                        'price': order.get('safe_price', 0),
                        'amount': order.get('amount', 0),
                        'is_entry': order.get('ft_is_entry', True),
                        'tag': order.get('ft_order_tag', '')
                    }
                    for order in orders
                ]

        return holding_analysis

    def _analyze_exit(self) -> Dict:
        """分析出场点"""
        exit_analysis = {}

        # 获取出场时的K线
        exit_candle = self.indicators[self.indicators.index >= self.close_date].iloc[0] if len(self.indicators[self.indicators.index >= self.close_date]) > 0 else None

        if exit_candle is not None:
            exit_analysis['exit_candle'] = {
                'date': str(exit_candle.name),
                'close': exit_candle.get('close', 0),
            }

            # 出场评估
            exit_reason = self.trade.get('exit_reason', '')
            exit_analysis['reason'] = exit_reason
            exit_analysis['assessment'] = self._assess_exit_timing(exit_candle, exit_reason)

        return exit_analysis

    def _assess_exit_timing(self, candle: pd.Series, reason: str) -> List[str]:
        """评估出场时机"""
        issues = []

        # 爆仓
        if 'liquidation' in reason.lower():
            issues.append("🔴 爆仓出场 - 风险管理失败")
            return issues

        # 止损
        if 'stop' in reason.lower() or 'sl' in reason.lower():
            if abs(self.profit_ratio) < 0.05:
                issues.append("✓ 小幅止损，风险控制良好")
            else:
                issues.append(f"⚠ 大幅止损（亏损{abs(self.profit_ratio)*100:.1f}%），可考虑收紧止损")

        # 盈利出场
        if self.profit_ratio > 0:
            if self.profit_ratio > 0.05:
                issues.append(f"✓ 盈利出场（+{self.profit_ratio*100:.1f}%）")
            else:
                issues.append(f"⚠ 微利出场（+{self.profit_ratio*100:.1f}%），可能过早")

        return issues

    def _find_optimal_points(self) -> Dict:
        """寻找最优入场/出场点"""
        optimal = {}

        # 扩展搜索范围：入场前后N根K线
        search_window = 20  # 20根K线

        # 最优入场点搜索
        entry_idx = self.indicators.index.get_indexer([self.open_date], method='nearest')[0]
        entry_search_start = max(0, entry_idx - search_window)
        entry_search_end = min(len(self.indicators), entry_idx + search_window)
        entry_search_candles = self.indicators.iloc[entry_search_start:entry_search_end]

        if len(entry_search_candles) > 0:
            # 对于多头：找最低点；对于空头：找最高点
            if self.is_short:
                optimal_entry_idx = entry_search_candles['high'].idxmax()
                optimal_entry_price = entry_search_candles.loc[optimal_entry_idx, 'high']
            else:
                optimal_entry_idx = entry_search_candles['low'].idxmin()
                optimal_entry_price = entry_search_candles.loc[optimal_entry_idx, 'low']

            # 计算如果在最优点入场的收益
            optimal_entry_profit = (self.close_rate - optimal_entry_price) / optimal_entry_price
            if self.is_short:
                optimal_entry_profit = -optimal_entry_profit

            optimal['entry'] = {
                'date': str(optimal_entry_idx),
                'price': optimal_entry_price,
                'profit_if_used_pct': optimal_entry_profit * 100,
                'improvement_pct': (optimal_entry_profit - self.profit_ratio) * 100,
                'time_diff_minutes': (optimal_entry_idx - self.open_date).total_seconds() / 60
            }

        # 最优出场点搜索
        exit_idx = self.indicators.index.get_indexer([self.close_date], method='nearest')[0]
        exit_search_start = max(entry_idx, exit_idx - search_window)
        exit_search_end = min(len(self.indicators), exit_idx + search_window)
        exit_search_candles = self.indicators.iloc[exit_search_start:exit_search_end]

        if len(exit_search_candles) > 0:
            # 对于多头：找最高点；对于空头：找最低点
            if self.is_short:
                optimal_exit_idx = exit_search_candles['low'].idxmin()
                optimal_exit_price = exit_search_candles.loc[optimal_exit_idx, 'low']
            else:
                optimal_exit_idx = exit_search_candles['high'].idxmax()
                optimal_exit_price = exit_search_candles.loc[optimal_exit_idx, 'high']

            # 计算如果在最优点出场的收益
            optimal_exit_profit = (optimal_exit_price - self.open_rate) / self.open_rate
            if self.is_short:
                optimal_exit_profit = -optimal_exit_profit

            optimal['exit'] = {
                'date': str(optimal_exit_idx),
                'price': optimal_exit_price,
                'profit_if_used_pct': optimal_exit_profit * 100,
                'improvement_pct': (optimal_exit_profit - self.profit_ratio) * 100,
                'time_diff_minutes': (optimal_exit_idx - self.close_date).total_seconds() / 60
            }

        # 理论最优收益（最优入场 + 最优出场）
        if 'entry' in optimal and 'exit' in optimal:
            theoretical_profit = (optimal['exit']['price'] - optimal['entry']['price']) / optimal['entry']['price']
            if self.is_short:
                theoretical_profit = -theoretical_profit

            optimal['theoretical_best'] = {
                'profit_pct': theoretical_profit * 100,
                'vs_actual_diff_pct': (theoretical_profit - self.profit_ratio) * 100
            }

        return optimal

    def _analyze_rejected_signals(self) -> List[Dict]:
        """
        分析被拒绝的信号（需要从回测结果中提供）

        注：这个功能需要回测结果包含rejected_signals数据
        """
        # 这是一个占位实现，实际需要从loader传入rejected_signals
        # 在实际使用中，应该在初始化时传入完整的rejected_signals列表

        rejected = []

        # TODO: 实现rejected_signals的筛选和分析
        # 需要筛选出与当前交易时间段重叠的拒绝信号

        return rejected

    def _generate_reflection(self) -> Dict:
        """生成反思报告"""
        reflection = {
            'problems': [],
            'strengths': [],
            'what_if': []
        }

        # 问题识别
        if self.profit_ratio < 0:
            reflection['problems'].append({
                'severity': '🔴',
                'issue': f"交易亏损 {abs(self.profit_ratio)*100:.2f}%",
                'impact': '直接损失'
            })

        # 入场问题
        entry_analysis = self._analyze_entry()
        if 'assessment' in entry_analysis:
            for assessment in entry_analysis['assessment']:
                if '❌' in assessment:
                    reflection['problems'].append({
                        'severity': '🟠',
                        'issue': assessment.replace('❌ ', ''),
                        'impact': '入场时机不佳'
                    })

        # 出场问题
        holding = self._analyze_holding_period()
        if 'profit_efficiency' in holding:
            efficiency = holding['profit_efficiency']['ratio']
            if efficiency < 0.5:
                mfe_pct = holding['mfe']['ratio_pct']
                actual_pct = self.profit_ratio * 100
                reflection['problems'].append({
                    'severity': '🟡',
                    'issue': f"盈利效率低（{efficiency:.1%}），最高曾达+{mfe_pct:.2f}%但仅获利+{actual_pct:.2f}%",
                    'impact': '利润回吐'
                })

        # 优点识别
        if self.profit_ratio > 0.03:
            reflection['strengths'].append("✓ 盈利交易，策略有效")

        if 'profit_efficiency' in holding and holding['profit_efficiency']['ratio'] > 0.7:
            reflection['strengths'].append("✓ 盈利效率高，出场时机把握良好")

        # 反事实分析
        optimal = self._find_optimal_points()
        if 'entry' in optimal and optimal['entry']['improvement_pct'] > 1:
            reflection['what_if'].append({
                'scenario': f"如果在{optimal['entry']['date']}入场（{optimal['entry']['time_diff_minutes']:.0f}分钟{'后' if optimal['entry']['time_diff_minutes'] > 0 else '前'}）",
                'result': f"收益可提升 {optimal['entry']['improvement_pct']:.2f}%"
            })

        if 'exit' in optimal and optimal['exit']['improvement_pct'] > 1:
            reflection['what_if'].append({
                'scenario': f"如果在{optimal['exit']['date']}出场（{optimal['exit']['time_diff_minutes']:.0f}分钟{'后' if optimal['exit']['time_diff_minutes'] > 0 else '前'}）",
                'result': f"收益可提升 {optimal['exit']['improvement_pct']:.2f}%"
            })

        if 'theoretical_best' in optimal:
            reflection['what_if'].append({
                'scenario': "如果使用最优入场和出场点",
                'result': f"理论最优收益 +{optimal['theoretical_best']['profit_pct']:.2f}%（vs实际 {self.profit_ratio*100:.2f}%）"
            })

        return reflection

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于反思生成建议
        reflection = self._generate_reflection()

        # 针对问题的建议
        for problem in reflection['problems']:
            if 'RSI' in problem['issue'] and '超买' in problem['issue']:
                recommendations.append("增加RSI过滤：禁止在RSI>70时做多")
            elif 'RSI' in problem['issue'] and '超卖' in problem['issue']:
                recommendations.append("增加RSI过滤：禁止在RSI<30时做空")
            elif '盈利效率低' in problem['issue']:
                recommendations.append("改进出场策略：考虑使用移动止盈（trailing stop）锁定利润")
            elif '亏损' in problem['issue'] and abs(self.profit_ratio) > 0.10:
                recommendations.append("加强止损：当前止损过于宽松，建议收紧到5-8%")

        # 基于入场模式的建议
        enter_tag = self.trade.get('enter_tag', '')
        if enter_tag and self.profit_ratio < 0:
            recommendations.append(f"检查入场模式 {enter_tag} 的条件设置，可能过于激进")

        # 基于币种的建议
        if self.profit_ratio < -0.05:
            recommendations.append(f"将 {self.pair} 添加到监控列表，如持续表现不佳则考虑拉黑")

        # 如果没有明显问题
        if len(recommendations) == 0 and self.profit_ratio > 0:
            recommendations.append("✓ 交易执行良好，继续保持")

        return recommendations


def replay_trade(
    trade_row: pd.Series,
    candles_df: pd.DataFrame,
    indicators_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    便捷函数：复盘单笔交易

    Args:
        trade_row: 交易记录
        candles_df: K线数据
        indicators_df: 带指标的K线数据

    Returns:
        复盘结果字典
    """
    engine = TradeReplayEngine(trade_row, candles_df, indicators_df)
    return engine.analyze()
