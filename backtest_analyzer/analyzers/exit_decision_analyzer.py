"""
出场决策分析器 (Exit Decision Analyzer)

深度分析交易出场时刻的决策过程:
- 识别使用的出场函数
- 追踪custom_exit()的决策路径
- 评估所有出场条件
- 重现出场时刻的技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import re


class ExitDecisionAnalyzer:
    """出场决策分析器"""

    # 入场模式到出场函数的映射
    ENTRY_MODE_TO_EXIT_FUNCTION = {
        # 做多出场函数
        'long_normal': 'long_exit_normal',
        'long_pump': 'long_exit_pump',
        'long_quick': 'long_exit_quick',
        'long_rebuy': 'long_exit_rebuy',
        'long_high_profit': 'long_exit_high_profit',
        'long_rapid': 'long_exit_rapid',
        'long_grind': 'long_exit_grind',
        'long_top_coins': 'long_exit_top_coins',
        'long_scalp': 'long_exit_scalp',

        # 做空出场函数
        'short_normal': 'short_exit_normal',
        'short_quick': 'short_exit_quick',
        'short_scalp': 'short_exit_scalp',
    }

    # Tag到模式的映射（复用入场分析器的定义）
    TAG_TO_MODE = {
        **{tag: 'long_normal' for tag in range(1, 14)},
        **{tag: 'long_pump' for tag in range(21, 27)},
        **{tag: 'long_quick' for tag in range(41, 54)},
        **{tag: 'long_rebuy' for tag in range(61, 64)},
        **{81: 'long_high_profit', 82: 'long_high_profit'},
        **{tag: 'long_rapid' for tag in range(101, 111)},
        **{120: 'long_grind'},
        **{tag: 'long_top_coins' for tag in range(141, 146)},
        **{tag: 'long_scalp' for tag in range(161, 164)},
        **{tag: 'short_normal' for tag in range(501, 505)},
        **{tag: 'short_quick' for tag in range(541, 544)},
        **{661: 'short_scalp'},
    }

    def __init__(self, trade: pd.Series, candles_df: pd.DataFrame, indicators_df: pd.DataFrame):
        """
        初始化出场决策分析器

        Args:
            trade: 交易记录（Series）
            candles_df: K线数据（包含出场前后的K线）
            indicators_df: 技术指标数据（已计算好的指标）
        """
        self.trade = trade
        self.candles_df = candles_df
        self.indicators_df = indicators_df

        # 提取出场信息
        self.pair = trade['pair']
        self.exit_date = pd.to_datetime(trade['close_date'])
        self.exit_reason = str(trade.get('exit_reason', '')).strip()
        self.enter_tag = str(trade.get('enter_tag', '')).strip()
        self.is_short = trade.get('is_short', False)

        # 交易盈亏信息
        self.profit_ratio = trade.get('profit_ratio', 0.0)
        self.profit_abs = trade.get('profit_abs', 0.0)

        # 持仓时间
        self.open_date = pd.to_datetime(trade['open_date'])
        self.holding_time = self.exit_date - self.open_date

        # 获取出场时刻的K线和指标
        self.exit_candle = self._get_exit_candle()
        self.exit_indicators = self._get_exit_indicators()

    def _get_exit_candle(self) -> pd.Series:
        """获取出场时刻的K线数据"""
        try:
            exit_row = self.candles_df[self.candles_df['date'] == self.exit_date]
            if len(exit_row) > 0:
                return exit_row.iloc[0]
            else:
                idx = self.candles_df['date'].searchsorted(self.exit_date)
                if idx < len(self.candles_df):
                    return self.candles_df.iloc[idx]
                else:
                    return self.candles_df.iloc[-1]
        except Exception as e:
            print(f"获取出场K线失败: {e}")
            return pd.Series()

    def _get_exit_indicators(self) -> pd.Series:
        """获取出场时刻的技术指标"""
        try:
            exit_row = self.indicators_df[self.indicators_df['date'] == self.exit_date]
            if len(exit_row) > 0:
                return exit_row.iloc[0]
            else:
                idx = self.indicators_df['date'].searchsorted(self.exit_date)
                if idx < len(self.indicators_df):
                    return self.indicators_df.iloc[idx]
                else:
                    return self.indicators_df.iloc[-1]
        except Exception as e:
            print(f"获取出场指标失败: {e}")
            return pd.Series()

    def analyze(self) -> Dict[str, Any]:
        """
        执行完整的出场决策分析

        Returns:
            分析结果字典
        """
        # 识别出场函数
        exit_function = self._identify_exit_function()

        # 分类出场信号类型
        exit_signal_type = self._classify_exit_signal()

        # 追踪决策路径
        decision_path = self._trace_decision_path(exit_function)

        # 评估所有可能的出场条件
        all_checks = self._evaluate_all_exit_conditions(exit_function)

        # 提取所有相关指标值
        all_indicators = self._extract_all_indicators()

        return {
            'exit_date': self.exit_date,
            'pair': self.pair,
            'is_short': self.is_short,
            'exit_reason': self.exit_reason,
            'exit_function': exit_function,
            'exit_signal_type': exit_signal_type,
            'profit_ratio': self.profit_ratio,
            'profit_abs': self.profit_abs,
            'holding_time': self.holding_time,
            'decision_path': decision_path,
            'all_checks': all_checks,
            'all_indicators': all_indicators,
            'exit_candle': self.exit_candle.to_dict() if not self.exit_candle.empty else {},
        }

    def _identify_exit_function(self) -> str:
        """识别使用的出场函数"""
        # 解析entry_tag
        tags = re.findall(r'\d+', self.enter_tag)
        if not tags:
            return "unknown"

        # 取第一个tag确定模式
        main_tag = int(tags[0])
        mode = self.TAG_TO_MODE.get(main_tag, "unknown")

        # 查找对应的出场函数
        return self.ENTRY_MODE_TO_EXIT_FUNCTION.get(mode, "unknown")

    def _classify_exit_signal(self) -> str:
        """
        分类出场信号类型

        Returns:
            信号类型: stoploss, profit, technical, trend_reversal, time_based, custom, roi, etc.
        """
        reason = self.exit_reason.lower()

        # 基于exit_reason的关键词分类
        if 'stop' in reason or 'loss' in reason:
            return 'stoploss'
        elif 'profit' in reason or 'roi' in reason:
            return 'profit'
        elif 'force' in reason:
            return 'force_exit'
        elif 'trailing' in reason:
            return 'trailing_stop'
        elif 'signal' in reason or 'exit' in reason:
            # 需要进一步分析exit_reason的具体内容
            if 'williams' in reason:
                return 'technical_williams'
            elif 'rsi' in reason:
                return 'technical_rsi'
            elif 'ema' in reason:
                return 'technical_ema'
            elif 'aroon' in reason:
                return 'trend_reversal'
            else:
                return 'custom_signal'
        elif 'time' in reason:
            return 'time_based'
        else:
            return 'custom'

    def _trace_decision_path(self, exit_function: str) -> List[Dict[str, Any]]:
        """
        追踪custom_exit()的决策路径

        模拟策略的出场逻辑，记录每个检查点
        """
        decision_path = []

        # 根据出场函数类型追踪不同的决策路径
        if 'top_coins' in exit_function:
            decision_path = self._trace_top_coins_exit_path()
        elif 'normal' in exit_function:
            decision_path = self._trace_normal_exit_path()
        elif 'quick' in exit_function:
            decision_path = self._trace_quick_exit_path()
        elif 'grind' in exit_function:
            decision_path = self._trace_grind_exit_path()
        else:
            # 通用出场路径
            decision_path = self._trace_generic_exit_path()

        return decision_path

    def _trace_top_coins_exit_path(self) -> List[Dict]:
        """追踪Top Coins模式的出场路径"""
        path = []

        # Step 1: 检查是否盈利
        profit_check = {
            'step': 1,
            'check_type': 'profit_check',
            'description': '检查是否盈利',
            'condition': 'profit_init_ratio > 0.0',
            'satisfied': self.profit_ratio > 0.0,
            'details': f"当前收益率: {self.profit_ratio * 100:.2f}%",
            'checked': True
        }
        path.append(profit_check)

        if self.profit_ratio > 0.0:
            # 如果盈利，检查盈利相关出场信号

            # Step 2: 原始出场信号
            path.append({
                'step': 2,
                'check_type': 'original_exit_signals',
                'description': '检查原始出场信号',
                'details': '检查基于技术指标的出场信号',
                'checked': True
            })

            # Step 3: 主要出场信号
            path.append({
                'step': 3,
                'check_type': 'main_exit_signals',
                'description': '检查主要出场信号',
                'details': '检查盈利目标、技术指标超买等',
                'checked': True
            })

            # Step 4: Williams R 出场信号
            path.append({
                'step': 4,
                'check_type': 'williams_exit_signals',
                'description': '检查Williams %R出场信号',
                'details': 'Williams %R超买检查',
                'checked': True
            })

        else:
            # 如果亏损，检查止损条件

            # Step 2: 止损检查
            stoploss_threshold = -0.10  # Top Coins模式的止损阈值
            stoploss_check = {
                'step': 2,
                'check_type': 'stoploss_check',
                'description': '检查止损条件',
                'condition': f'profit < {stoploss_threshold * 100:.1f}%',
                'satisfied': self.profit_ratio < stoploss_threshold,
                'details': f"当前收益率: {self.profit_ratio * 100:.2f}% {'<' if self.profit_ratio < stoploss_threshold else '>='} {stoploss_threshold * 100:.1f}%",
                'checked': True
            }
            path.append(stoploss_check)

            if stoploss_check['satisfied']:
                # 触发止损
                path.append({
                    'step': 3,
                    'check_type': 'stoploss_triggered',
                    'description': '🔴 止损触发',
                    'details': f"持仓时间: {self.holding_time}, 亏损: {self.profit_ratio * 100:.2f}%",
                    'triggered': True,
                    'checked': True
                })

        return path

    def _trace_normal_exit_path(self) -> List[Dict]:
        """追踪Normal模式的出场路径"""
        path = []

        # 类似top_coins的逻辑，但使用不同的阈值
        profit_check = {
            'step': 1,
            'check_type': 'profit_check',
            'description': '检查是否盈利',
            'satisfied': self.profit_ratio > 0.0,
            'details': f"当前收益率: {self.profit_ratio * 100:.2f}%",
            'checked': True
        }
        path.append(profit_check)

        if self.profit_ratio > 0.0:
            # 盈利检查路径
            path.append({
                'step': 2,
                'check_type': 'profit_targets',
                'description': '检查盈利目标',
                'details': '检查是否达到预设盈利目标',
                'checked': True
            })
        else:
            # 止损检查
            stoploss_threshold = -0.10
            path.append({
                'step': 2,
                'check_type': 'stoploss_check',
                'description': '检查止损条件',
                'satisfied': self.profit_ratio < stoploss_threshold,
                'details': f"止损阈值: {stoploss_threshold * 100:.1f}%, 当前: {self.profit_ratio * 100:.2f}%",
                'checked': True
            })

        return path

    def _trace_quick_exit_path(self) -> List[Dict]:
        """追踪Quick模式的出场路径（快速进出）"""
        # Quick模式通常有更激进的止损和止盈
        return self._trace_normal_exit_path()  # 简化版，使用normal路径

    def _trace_grind_exit_path(self) -> List[Dict]:
        """追踪Grind模式的出场路径（网格模式）"""
        path = []

        # Grind模式有独特的出场逻辑（考虑多次加仓）
        path.append({
            'step': 1,
            'check_type': 'grind_profit_check',
            'description': '检查Grind模式盈利',
            'details': f"平均成本基础上的收益: {self.profit_ratio * 100:.2f}%",
            'checked': True
        })

        # Grind模式允许更大的回撤
        stoploss_threshold = -0.15
        path.append({
            'step': 2,
            'check_type': 'grind_stoploss',
            'description': '检查Grind止损',
            'satisfied': self.profit_ratio < stoploss_threshold,
            'details': f"Grind止损阈值: {stoploss_threshold * 100:.1f}%, 当前: {self.profit_ratio * 100:.2f}%",
            'checked': True
        })

        return path

    def _trace_generic_exit_path(self) -> List[Dict]:
        """通用出场路径（用于未知或未实现的模式）"""
        path = []

        path.append({
            'step': 1,
            'check_type': 'generic_check',
            'description': '通用出场条件检查',
            'details': f"exit_reason: {self.exit_reason}",
            'checked': True
        })

        return path

    def _evaluate_all_exit_conditions(self, exit_function: str) -> List[Dict]:
        """
        评估所有可能的出场条件

        Returns:
            所有出场条件的检查结果
        """
        all_checks = []

        # 1. 盈利目标检查
        profit_targets = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]  # 1%, 2%, 5%, 10%, 15%, 20%
        for target in profit_targets:
            satisfied = self.profit_ratio >= target
            all_checks.append({
                'category': 'profit_target',
                'description': f"盈利目标 {target * 100:.0f}%",
                'satisfied': satisfied,
                'checked': self.profit_ratio > 0.0,  # 只有盈利时才会检查
                'details': f"当前收益: {self.profit_ratio * 100:.2f}%"
            })

        # 2. 止损检查
        # 根据模式使用不同的止损阈值
        if 'top_coins' in exit_function or 'normal' in exit_function:
            stoploss_threshold = -0.10
        elif 'grind' in exit_function:
            stoploss_threshold = -0.15
        elif 'rapid' in exit_function or 'scalp' in exit_function:
            stoploss_threshold = -0.20
        else:
            stoploss_threshold = -0.10

        stoploss_satisfied = self.profit_ratio < stoploss_threshold
        all_checks.append({
            'category': 'stoploss',
            'description': f"止损 {stoploss_threshold * 100:.0f}%",
            'satisfied': stoploss_satisfied,
            'checked': True,
            'details': f"当前收益: {self.profit_ratio * 100:.2f}%",
            'triggered': stoploss_satisfied  # 如果满足，很可能就是这个触发的
        })

        # 3. 技术指标检查
        # RSI超买
        rsi_14 = self.exit_indicators.get('RSI_14', np.nan)
        if not pd.isna(rsi_14):
            rsi_overbought = rsi_14 > 80
            all_checks.append({
                'category': 'technical_rsi',
                'description': 'RSI_14 超买 (> 80)',
                'satisfied': rsi_overbought,
                'checked': self.profit_ratio > 0.0,  # 通常只在盈利时检查
                'details': f"RSI_14 = {rsi_14:.2f}"
            })

        # Williams %R超买
        williams_r = self.exit_indicators.get('WILLR_14', np.nan)
        if not pd.isna(williams_r):
            williams_overbought = williams_r > -20
            all_checks.append({
                'category': 'technical_williams',
                'description': 'Williams %R 超买 (> -20)',
                'satisfied': williams_overbought,
                'checked': self.profit_ratio > 0.0,
                'details': f"Williams %R = {williams_r:.2f}"
            })

        # 4. 趋势反转检查
        # AROON下降趋势
        aroond_14 = self.exit_indicators.get('AROOND_14', np.nan)
        if not pd.isna(aroond_14):
            aroon_downtrend = aroond_14 > 70
            all_checks.append({
                'category': 'trend_reversal',
                'description': 'AROON下降趋势 (> 70)',
                'satisfied': aroon_downtrend,
                'checked': True,
                'details': f"AROOND_14 = {aroond_14:.2f}"
            })

        # 5. 时间止损检查
        # 持仓超过24小时且亏损
        time_stoploss_satisfied = (
            self.holding_time > timedelta(hours=24) and
            self.profit_ratio < -0.05
        )
        all_checks.append({
            'category': 'time_based',
            'description': '时间止损 (持仓>24h且亏损>5%)',
            'satisfied': time_stoploss_satisfied,
            'checked': True,
            'details': f"持仓时间: {self.holding_time}, 收益: {self.profit_ratio * 100:.2f}%"
        })

        # 6. 最大盈利回撤检查（需要max_profit数据）
        max_profit = self.trade.get('max_profit', 0.0)
        if max_profit > 0.05:  # 曾经盈利超过5%
            drawdown_from_peak = max_profit - self.profit_ratio
            profit_drawback_satisfied = drawdown_from_peak > 0.07  # 回撤超过7%
            all_checks.append({
                'category': 'profit_drawback',
                'description': '盈利回撤 (从峰值回撤>7%)',
                'satisfied': profit_drawback_satisfied,
                'checked': True,
                'details': f"最大盈利: {max_profit * 100:.2f}%, 当前: {self.profit_ratio * 100:.2f}%, 回撤: {drawdown_from_peak * 100:.2f}%"
            })

        return all_checks

    def _extract_all_indicators(self) -> Dict[str, Any]:
        """提取所有相关的技术指标值"""
        if self.exit_indicators.empty:
            return {}

        # 常用指标列表（出场相关）
        exit_indicators = [
            # RSI 系列
            'RSI_14', 'RSI_20',
            'RSI_14_15m', 'RSI_14_1h',

            # AROON 系列（趋势反转）
            'AROONU_14', 'AROOND_14',

            # Williams %R
            'WILLR_14',

            # EMA（趋势）
            'EMA_12', 'EMA_26', 'EMA_50',

            # CMF（资金流）
            'CMF_20',

            # 价格
            'open', 'high', 'low', 'close', 'volume',
        ]

        indicators = {}
        for ind_name in exit_indicators:
            if ind_name in self.exit_indicators.index:
                value = self.exit_indicators[ind_name]
                if not pd.isna(value):
                    indicators[ind_name] = float(value)

        # 添加交易统计信息
        indicators['current_profit_pct'] = self.profit_ratio * 100
        indicators['current_profit_abs'] = self.profit_abs
        indicators['holding_hours'] = self.holding_time.total_seconds() / 3600

        return indicators


def format_exit_diagnosis_report(analysis: Dict) -> str:
    """
    将出场分析结果格式化为可读的诊断报告

    Args:
        analysis: 分析结果字典

    Returns:
        格式化的报告文本
    """
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append(f"🚪 出场决策诊断报告")
    report_lines.append("=" * 60)
    report_lines.append(f"币种: {analysis['pair']}")
    report_lines.append(f"出场时间: {analysis['exit_date']}")
    report_lines.append(f"方向: {'做空' if analysis['is_short'] else '做多'}")
    report_lines.append(f"出场函数: {analysis['exit_function']}")
    report_lines.append(f"出场原因: {analysis['exit_reason']}")
    report_lines.append(f"信号类型: {analysis['exit_signal_type']}")
    report_lines.append(f"收益率: {analysis['profit_ratio'] * 100:.2f}% ({analysis['profit_abs']:.2f} USDT)")
    report_lines.append(f"持仓时长: {analysis['holding_time']}")
    report_lines.append("-" * 60)

    # 显示决策路径
    report_lines.append("\n🛤️  决策路径追踪:")
    for step in analysis['decision_path']:
        step_num = step.get('step', '?')
        check_type = step.get('check_type', '')
        description = step.get('description', '')
        details = step.get('details', '')
        satisfied = step.get('satisfied')
        triggered = step.get('triggered', False)

        if triggered:
            icon = '🔴'
        elif satisfied is True:
            icon = '✅'
        elif satisfied is False:
            icon = '❌'
        else:
            icon = '🔍'

        report_lines.append(f"\n   {step_num}️⃣  {icon} {description}")
        if details:
            report_lines.append(f"      {details}")
        if satisfied is not None:
            condition = step.get('condition', '')
            if condition:
                report_lines.append(f"      条件: {condition}")
        if triggered:
            report_lines.append(f"      → 【触发出场】")

    # 显示所有检查的出场条件
    report_lines.append(f"\n{'=' * 60}")
    report_lines.append("📋 所有出场条件检查:")

    # 按类别分组
    categories = {}
    for check in analysis['all_checks']:
        cat = check['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(check)

    category_names = {
        'profit_target': '💰 盈利目标',
        'stoploss': '🛑 止损',
        'technical_rsi': '📊 技术指标 (RSI)',
        'technical_williams': '📊 技术指标 (Williams %R)',
        'trend_reversal': '🔄 趋势反转',
        'time_based': '⏰ 时间止损',
        'profit_drawback': '📉 盈利回撤'
    }

    for cat, checks in categories.items():
        cat_name = category_names.get(cat, cat)
        report_lines.append(f"\n   {cat_name}:")

        for check in checks:
            if not check.get('checked', False):
                icon = '⏭️'  # 未检查
                status = '(未检查)'
            elif check.get('triggered', False):
                icon = '🔴'  # 触发
                status = '【已触发】'
            elif check['satisfied']:
                icon = '✅'  # 满足
                status = ''
            else:
                icon = '❌'  # 不满足
                status = ''

            report_lines.append(f"      {icon} {check['description']} {status}")
            report_lines.append(f"         {check.get('details', '')}")

    # 显示出场时刻的指标值
    report_lines.append(f"\n{'=' * 60}")
    report_lines.append("📊 出场时刻技术指标:")
    indicators = analysis['all_indicators']

    for ind_name, value in list(indicators.items())[:10]:  # 只显示前10个
        report_lines.append(f"   {ind_name}: {value:.2f}")

    report_lines.append(f"\n{'=' * 60}")

    return '\n'.join(report_lines)
