"""
入场决策分析器 (Entry Decision Analyzer)

深度分析交易入场时刻的决策过程:
- 重现所有技术指标值
- 评估所有入场条件
- 识别触发和未触发的条件
- 生成分层诊断报告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import re


class EntryDecisionAnalyzer:
    """入场决策分析器"""

    # NostalgiaForInfinityX7 入场模式定义
    ENTRY_MODES = {
        # 做多模式
        'long_normal': list(range(1, 14)),           # 1-13
        'long_pump': list(range(21, 27)),            # 21-26
        'long_quick': list(range(41, 54)),           # 41-53
        'long_rebuy': list(range(61, 64)),           # 61-63
        'long_high_profit': [81, 82],                # 81-82
        'long_rapid': list(range(101, 111)),         # 101-110
        'long_grind': [120],                         # 120
        'long_top_coins': list(range(141, 146)),     # 141-145
        'long_scalp': list(range(161, 164)),         # 161-163

        # 做空模式
        'short_normal': list(range(501, 505)),       # 501-504
        'short_quick': list(range(541, 544)),        # 541-543
        'short_scalp': [661],                        # 661
    }

    # Top Coins 列表 (Tag 141-145适用)
    TOP_COINS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']

    # Grind Mode 币种列表 (Tag 120适用)
    GRIND_COINS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']

    def __init__(self, trade: pd.Series, candles_df: pd.DataFrame, indicators_df: pd.DataFrame):
        """
        初始化入场决策分析器

        Args:
            trade: 交易记录（Series）
            candles_df: K线数据（包含入场前后的K线）
            indicators_df: 技术指标数据（已计算好的指标）
        """
        self.trade = trade
        self.candles_df = candles_df
        self.indicators_df = indicators_df

        # 提取入场信息
        self.pair = trade['pair']
        self.enter_date = pd.to_datetime(trade['open_date'])
        self.enter_tag = str(trade.get('enter_tag', '')).strip()
        self.is_short = trade.get('is_short', False)

        # 解析触发的条件
        self.triggered_tags = self._parse_entry_tags(self.enter_tag)

        # 获取入场时刻的K线和指标
        self.entry_candle = self._get_entry_candle()
        self.entry_indicators = self._get_entry_indicators()

    def _parse_entry_tags(self, enter_tag: str) -> List[int]:
        """
        解析 entry_tag，提取触发的条件编号

        Args:
            enter_tag: 如 "142" 或 "1 42 53"

        Returns:
            条件编号列表，如 [142] 或 [1, 42, 53]
        """
        if not enter_tag:
            return []

        # 提取所有数字
        tags = re.findall(r'\d+', enter_tag)
        return [int(tag) for tag in tags]

    def _get_entry_candle(self) -> pd.Series:
        """获取入场时刻的K线数据"""
        try:
            # 找到入场时刻对应的K线
            entry_row = self.candles_df[self.candles_df['date'] == self.enter_date]
            if len(entry_row) > 0:
                return entry_row.iloc[0]
            else:
                # 如果找不到精确匹配，找最接近的K线
                idx = self.candles_df['date'].searchsorted(self.enter_date)
                if idx < len(self.candles_df):
                    return self.candles_df.iloc[idx]
                else:
                    return self.candles_df.iloc[-1]
        except Exception as e:
            print(f"获取入场K线失败: {e}")
            return pd.Series()

    def _get_entry_indicators(self) -> pd.Series:
        """获取入场时刻的技术指标"""
        try:
            # 找到入场时刻对应的指标数据
            entry_row = self.indicators_df[self.indicators_df['date'] == self.enter_date]
            if len(entry_row) > 0:
                return entry_row.iloc[0]
            else:
                # 如果找不到精确匹配，找最接近的K线
                idx = self.indicators_df['date'].searchsorted(self.enter_date)
                if idx < len(self.indicators_df):
                    return self.indicators_df.iloc[idx]
                else:
                    return self.indicators_df.iloc[-1]
        except Exception as e:
            print(f"获取入场指标失败: {e}")
            return pd.Series()

    def analyze(self) -> Dict[str, Any]:
        """
        执行完整的入场决策分析

        Returns:
            分析结果字典
        """
        # 识别入场模式
        entry_mode = self._identify_entry_mode()

        # 分析触发的条件
        triggered_analysis = []
        for tag in self.triggered_tags:
            analysis = self._analyze_condition(tag)
            if analysis:
                triggered_analysis.append(analysis)

        # 分析接近触发但未满足的条件
        near_miss_analysis = self._find_near_miss_conditions()

        # 提取所有相关指标值
        all_indicators = self._extract_all_indicators()

        return {
            'entry_date': self.enter_date,
            'pair': self.pair,
            'is_short': self.is_short,
            'entry_mode': entry_mode,
            'triggered_tags': self.triggered_tags,
            'triggered_analysis': triggered_analysis,
            'near_miss_analysis': near_miss_analysis,
            'all_indicators': all_indicators,
            'entry_candle': self.entry_candle.to_dict() if not self.entry_candle.empty else {},
        }

    def _identify_entry_mode(self) -> str:
        """识别入场模式"""
        if not self.triggered_tags:
            return "unknown"

        # 取第一个触发的tag作为主要模式
        main_tag = self.triggered_tags[0]

        for mode_name, tags in self.ENTRY_MODES.items():
            if main_tag in tags:
                return mode_name

        return "unknown"

    def _analyze_condition(self, tag: int) -> Optional[Dict[str, Any]]:
        """
        深度分析单个入场条件

        Args:
            tag: 条件编号

        Returns:
            条件分析结果
        """
        # 根据tag范围确定模式和具体条件逻辑
        condition_logic = self._get_condition_logic(tag)

        if not condition_logic:
            return None

        # 评估三层结构
        protection_result = self._evaluate_protection_layer(tag, condition_logic)
        mtf_result = self._evaluate_mtf_layer(tag, condition_logic)
        entry_logic_result = self._evaluate_entry_logic_layer(tag, condition_logic)

        return {
            'tag': tag,
            'condition_name': condition_logic.get('name', f'Condition #{tag}'),
            'layer1_protection': protection_result,
            'layer2_mtf_filter': mtf_result,
            'layer3_entry_logic': entry_logic_result,
            'all_satisfied': (
                protection_result['all_satisfied'] and
                mtf_result['all_satisfied'] and
                entry_logic_result['all_satisfied']
            )
        }

    def _get_condition_logic(self, tag: int) -> Optional[Dict]:
        """
        获取条件的逻辑定义

        这里我们为常见的条件定义逻辑结构
        实际应用中可以从策略代码动态解析，或使用预定义的配置
        """
        # 示例：Tag 142 (Top Coins Mode #2)
        if tag == 142:
            return {
                'name': 'Top Coins Mode #2',
                'mode': 'long_top_coins',
                'protection': [
                    {'type': 'top_coins_check', 'description': '币种必须在Top Coins列表'},
                    {'type': 'empty_candles', 'indicator': 'num_empty_288', 'operator': '<=', 'threshold': 20},
                    {'type': 'global_protection', 'indicator': 'protections_long_global', 'value': True},
                ],
                'mtf_filter': [
                    # 多时间框架过滤条件（简化版，实际有13个）
                    {'indicators': ['RSI_3_15m', 'RSI_3_1h', 'RSI_3_4h'], 'thresholds': [3.0, 3.0, 15.0], 'logic': 'or'},
                    {'indicators': ['RSI_3_15m', 'RSI_3_1h', 'AROONU_14_1h'], 'thresholds': [3.0, 40.0, 85.0], 'logic': 'or'},
                ],
                'entry_logic': [
                    {'indicator': 'RSI_3', 'operator': '>', 'threshold': 5.0},
                    {'indicator': 'RSI_4', 'operator': '<', 'threshold': 46.0},
                    {'indicator': 'RSI_20', 'comparison': 'decreasing'},
                    {'indicator': 'close', 'comparison': 'sma16_offset', 'offset': 0.960},
                ]
            }

        # Tag 1 (Normal Mode #1)
        elif tag == 1:
            return {
                'name': 'Normal Mode #1',
                'mode': 'long_normal',
                'protection': [
                    {'type': 'empty_candles', 'indicator': 'num_empty_288', 'operator': '<=', 'threshold': 20},
                    {'type': 'global_protection', 'indicator': 'protections_long_global', 'value': True},
                ],
                'mtf_filter': [
                    {'indicators': ['RSI_3', 'RSI_3_15m', 'RSI_3_change_pct_1h'], 'thresholds': [3.0, 3.0, -50.0], 'logic': 'or'},
                ],
                'entry_logic': [
                    {'indicator': 'RSI_14', 'operator': '<', 'threshold': 36.0},
                    {'indicator': 'AROONU_14', 'operator': '<', 'threshold': 25.0},
                    {'indicator': 'CMF_20', 'operator': '<', 'threshold': -0.0},
                    {'indicator': 'STOCHRSIk_14_14_3_3', 'operator': '<', 'threshold': 20.0},
                    {'indicator': 'ROC_9', 'operator': '<', 'threshold': -3.0},
                    {'indicator': 'close', 'comparison': 'sma16_offset', 'offset': 0.970},
                ]
            }

        # 可以继续添加更多条件定义...
        # 这里为演示目的只定义了2个条件
        # 实际应用中可以：
        # 1. 从配置文件加载所有64个条件的定义
        # 2. 使用策略代码解析器动态提取

        else:
            # 通用条件模板（当没有具体定义时）
            return {
                'name': f'Condition #{tag}',
                'mode': 'unknown',
                'protection': [],
                'mtf_filter': [],
                'entry_logic': []
            }

    def _evaluate_protection_layer(self, tag: int, condition_logic: Dict) -> Dict:
        """评估第1层：保护条件"""
        protection_conditions = condition_logic.get('protection', [])
        results = []
        all_satisfied = True

        for cond in protection_conditions:
            cond_type = cond.get('type')

            if cond_type == 'top_coins_check':
                # 检查是否在Top Coins列表
                base_currency = self.pair.split('/')[0]
                satisfied = base_currency in self.TOP_COINS
                results.append({
                    'description': cond['description'],
                    'satisfied': satisfied,
                    'details': f"{base_currency} ∈ {self.TOP_COINS}" if satisfied else f"{base_currency} ∉ {self.TOP_COINS}"
                })
                all_satisfied = all_satisfied and satisfied

            elif cond_type == 'empty_candles':
                # 检查空K线数量
                indicator_name = cond['indicator']
                threshold = cond['threshold']
                operator = cond['operator']

                actual_value = self.entry_indicators.get(indicator_name, np.nan)
                satisfied = self._compare_values(actual_value, operator, threshold)

                results.append({
                    'description': f"{indicator_name} {operator} {threshold}",
                    'satisfied': satisfied,
                    'actual_value': actual_value,
                    'details': f"实际: {actual_value}"
                })
                all_satisfied = all_satisfied and satisfied

            elif cond_type == 'global_protection':
                # 检查全局保护开关
                indicator_name = cond['indicator']
                expected_value = cond['value']

                actual_value = self.entry_indicators.get(indicator_name, False)
                satisfied = (actual_value == expected_value)

                results.append({
                    'description': f"{indicator_name} = {expected_value}",
                    'satisfied': satisfied,
                    'actual_value': actual_value,
                    'details': f"实际: {actual_value}"
                })
                all_satisfied = all_satisfied and satisfied

        return {
            'conditions': results,
            'all_satisfied': all_satisfied
        }

    def _evaluate_mtf_layer(self, tag: int, condition_logic: Dict) -> Dict:
        """评估第2层：多时间框架过滤"""
        mtf_conditions = condition_logic.get('mtf_filter', [])
        results = []
        all_satisfied = True

        for cond in mtf_conditions:
            indicators = cond['indicators']
            thresholds = cond['thresholds']
            logic = cond.get('logic', 'or')

            # 评估每个指标
            sub_results = []
            for i, indicator_name in enumerate(indicators):
                threshold = thresholds[i] if i < len(thresholds) else 0
                actual_value = self.entry_indicators.get(indicator_name, np.nan)

                # 根据指标名称推断操作符（简化版，实际需要更精确的定义）
                if 'RSI' in indicator_name:
                    operator = '>'
                    satisfied = actual_value > threshold
                elif 'AROON' in indicator_name:
                    operator = '<'
                    satisfied = actual_value < threshold
                else:
                    operator = '>'
                    satisfied = actual_value > threshold

                sub_results.append({
                    'indicator': indicator_name,
                    'operator': operator,
                    'threshold': threshold,
                    'actual_value': actual_value,
                    'satisfied': satisfied
                })

            # 根据逻辑合并结果
            if logic == 'or':
                condition_satisfied = any(r['satisfied'] for r in sub_results)
            else:  # and
                condition_satisfied = all(r['satisfied'] for r in sub_results)

            results.append({
                'logic': logic,
                'sub_conditions': sub_results,
                'satisfied': condition_satisfied
            })
            all_satisfied = all_satisfied and condition_satisfied

        return {
            'conditions': results,
            'all_satisfied': all_satisfied
        }

    def _evaluate_entry_logic_layer(self, tag: int, condition_logic: Dict) -> Dict:
        """评估第3层：入场逻辑（5m时间框架）"""
        entry_conditions = condition_logic.get('entry_logic', [])
        results = []
        all_satisfied = True

        for cond in entry_conditions:
            indicator_name = cond['indicator']

            if 'comparison' in cond:
                # 特殊比较类型
                comparison_type = cond['comparison']

                if comparison_type == 'decreasing':
                    # RSI_20 下降
                    current_value = self.entry_indicators.get(indicator_name, np.nan)

                    # 获取前一根K线的值
                    try:
                        entry_idx = self.indicators_df[self.indicators_df['date'] == self.enter_date].index[0]
                        if entry_idx > 0:
                            previous_value = self.indicators_df.iloc[entry_idx - 1][indicator_name]
                            satisfied = current_value < previous_value
                            details = f"{current_value:.2f} < {previous_value:.2f}"
                        else:
                            satisfied = False
                            details = "无前一根K线数据"
                    except:
                        satisfied = False
                        details = "无法获取前一根K线"

                    results.append({
                        'description': f"{indicator_name} 下降",
                        'satisfied': satisfied,
                        'details': details
                    })

                elif comparison_type == 'sma16_offset':
                    # Close < SMA_16 * offset
                    offset = cond.get('offset', 1.0)
                    close = self.entry_indicators.get('close', np.nan)
                    sma16 = self.entry_indicators.get('SMA_16', np.nan)
                    threshold = sma16 * offset

                    satisfied = close < threshold

                    results.append({
                        'description': f"close < SMA_16 * {offset}",
                        'satisfied': satisfied,
                        'actual_value': close,
                        'threshold': threshold,
                        'details': f"{close:.2f} < {threshold:.2f}"
                    })

                all_satisfied = all_satisfied and satisfied

            else:
                # 标准操作符比较
                operator = cond['operator']
                threshold = cond['threshold']
                actual_value = self.entry_indicators.get(indicator_name, np.nan)

                satisfied = self._compare_values(actual_value, operator, threshold)

                results.append({
                    'description': f"{indicator_name} {operator} {threshold}",
                    'satisfied': satisfied,
                    'actual_value': actual_value,
                    'threshold': threshold,
                    'details': f"实际: {actual_value:.2f}"
                })
                all_satisfied = all_satisfied and satisfied

        return {
            'conditions': results,
            'all_satisfied': all_satisfied
        }

    def _compare_values(self, actual: float, operator: str, threshold: float) -> bool:
        """比较两个值"""
        if pd.isna(actual):
            return False

        if operator == '>':
            return actual > threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '>=':
            return actual >= threshold
        elif operator == '<=':
            return actual <= threshold
        elif operator == '==':
            return actual == threshold
        elif operator == '!=':
            return actual != threshold
        else:
            return False

    def _find_near_miss_conditions(self) -> List[Dict]:
        """
        查找接近触发但未满足的条件

        Returns:
            接近触发的条件列表
        """
        near_miss_conditions = []

        # 获取当前方向的所有可能条件
        if self.is_short:
            all_possible_tags = []
            for mode_tags in [self.ENTRY_MODES['short_normal'],
                             self.ENTRY_MODES['short_quick'],
                             self.ENTRY_MODES['short_scalp']]:
                all_possible_tags.extend(mode_tags)
        else:
            all_possible_tags = []
            for mode_tags in [self.ENTRY_MODES['long_normal'],
                             self.ENTRY_MODES['long_pump'],
                             self.ENTRY_MODES['long_quick'],
                             self.ENTRY_MODES['long_rapid'],
                             self.ENTRY_MODES['long_top_coins']]:
                all_possible_tags.extend(mode_tags)

        # 排除已经触发的条件
        candidates = [tag for tag in all_possible_tags if tag not in self.triggered_tags]

        # 只检查前5个候选条件（避免计算量过大）
        for tag in candidates[:5]:
            analysis = self._analyze_condition(tag)
            if analysis:
                # 计算接近程度（有多少层满足）
                layers_satisfied = 0
                if analysis['layer1_protection']['all_satisfied']:
                    layers_satisfied += 1
                if analysis['layer2_mtf_filter']['all_satisfied']:
                    layers_satisfied += 1
                if analysis['layer3_entry_logic']['all_satisfied']:
                    layers_satisfied += 1

                # 如果至少有2层满足，认为是"接近触发"
                if layers_satisfied >= 2:
                    # 找出未满足的条件
                    unsatisfied_details = self._get_unsatisfied_details(analysis)

                    near_miss_conditions.append({
                        'tag': tag,
                        'condition_name': analysis['condition_name'],
                        'layers_satisfied': layers_satisfied,
                        'unsatisfied_details': unsatisfied_details
                    })

        return near_miss_conditions

    def _get_unsatisfied_details(self, analysis: Dict) -> List[str]:
        """获取未满足的条件详情"""
        unsatisfied = []

        # 检查第1层
        if not analysis['layer1_protection']['all_satisfied']:
            for cond in analysis['layer1_protection']['conditions']:
                if not cond['satisfied']:
                    unsatisfied.append(f"[保护层] {cond['description']} - {cond.get('details', '')}")

        # 检查第2层
        if not analysis['layer2_mtf_filter']['all_satisfied']:
            for cond in analysis['layer2_mtf_filter']['conditions']:
                if not cond['satisfied']:
                    for sub in cond['sub_conditions']:
                        if not sub['satisfied']:
                            unsatisfied.append(
                                f"[多时间框架] {sub['indicator']} {sub['operator']} {sub['threshold']} "
                                f"(实际: {sub['actual_value']:.2f})"
                            )

        # 检查第3层
        if not analysis['layer3_entry_logic']['all_satisfied']:
            for cond in analysis['layer3_entry_logic']['conditions']:
                if not cond['satisfied']:
                    unsatisfied.append(f"[入场逻辑] {cond['description']} - {cond.get('details', '')}")

        return unsatisfied

    def _extract_all_indicators(self) -> Dict[str, Any]:
        """提取所有相关的技术指标值"""
        if self.entry_indicators.empty:
            return {}

        # 常用指标列表
        common_indicators = [
            # RSI 系列
            'RSI_3', 'RSI_4', 'RSI_14', 'RSI_20',
            'RSI_3_15m', 'RSI_3_1h', 'RSI_3_4h',
            'RSI_14_15m', 'RSI_14_1h', 'RSI_14_4h',

            # AROON 系列
            'AROONU_14', 'AROOND_14',
            'AROONU_14_15m', 'AROONU_14_1h', 'AROONU_14_4h',

            # Stochastic RSI
            'STOCHRSIk_14_14_3_3',
            'STOCHRSIk_14_14_3_3_15m',
            'STOCHRSIk_14_14_3_3_1h',

            # 其他常用指标
            'CMF_20', 'ROC_9',
            'SMA_16', 'EMA_12', 'EMA_26',

            # 价格
            'open', 'high', 'low', 'close', 'volume',
        ]

        indicators = {}
        for ind_name in common_indicators:
            if ind_name in self.entry_indicators.index:
                value = self.entry_indicators[ind_name]
                if not pd.isna(value):
                    indicators[ind_name] = float(value)

        return indicators


def format_entry_diagnosis_report(analysis: Dict) -> str:
    """
    将入场分析结果格式化为可读的诊断报告

    Args:
        analysis: 分析结果字典

    Returns:
        格式化的报告文本
    """
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append(f"📍 入场决策诊断报告")
    report_lines.append("=" * 60)
    report_lines.append(f"币种: {analysis['pair']}")
    report_lines.append(f"入场时间: {analysis['entry_date']}")
    report_lines.append(f"方向: {'做空' if analysis['is_short'] else '做多'}")
    report_lines.append(f"入场模式: {analysis['entry_mode']}")
    report_lines.append(f"触发条件: {', '.join(f'Tag {tag}' for tag in analysis['triggered_tags'])}")
    report_lines.append("-" * 60)

    # 显示每个触发条件的详细分析
    for triggered in analysis['triggered_analysis']:
        report_lines.append(f"\n✅ {triggered['condition_name']} (Tag {triggered['tag']})")
        report_lines.append(f"   整体结果: {'✅ 全部满足' if triggered['all_satisfied'] else '❌ 部分不满足'}")

        # 第1层：保护条件
        layer1 = triggered['layer1_protection']
        report_lines.append(f"\n   ▼ 第1层: 保护条件 {'✅' if layer1['all_satisfied'] else '❌'}")
        for cond in layer1['conditions']:
            icon = '✅' if cond['satisfied'] else '❌'
            report_lines.append(f"      {icon} {cond['description']} - {cond.get('details', '')}")

        # 第2层：多时间框架过滤
        layer2 = triggered['layer2_mtf_filter']
        report_lines.append(f"\n   ▼ 第2层: 多时间框架过滤 {'✅' if layer2['all_satisfied'] else '❌'}")
        for i, cond in enumerate(layer2['conditions'][:3], 1):  # 只显示前3个
            icon = '✅' if cond['satisfied'] else '❌'
            report_lines.append(f"      {icon} 条件组 {i} ({cond['logic'].upper()}逻辑)")
            for sub in cond['sub_conditions']:
                sub_icon = '✅' if sub['satisfied'] else '❌'
                report_lines.append(
                    f"         {sub_icon} {sub['indicator']} {sub['operator']} {sub['threshold']} "
                    f"(实际: {sub['actual_value']:.2f})"
                )

        # 第3层：入场逻辑
        layer3 = triggered['layer3_entry_logic']
        report_lines.append(f"\n   ▼ 第3层: 入场逻辑 (5m) {'✅' if layer3['all_satisfied'] else '❌'}")
        for cond in layer3['conditions']:
            icon = '✅' if cond['satisfied'] else '❌'
            report_lines.append(f"      {icon} {cond['description']} - {cond.get('details', '')}")

    # 显示接近触发的条件
    if analysis['near_miss_analysis']:
        report_lines.append(f"\n{'=' * 60}")
        report_lines.append("🔍 接近触发但未满足的条件:")
        for near_miss in analysis['near_miss_analysis']:
            report_lines.append(f"\n⚠️  {near_miss['condition_name']} (Tag {near_miss['tag']})")
            report_lines.append(f"   满足层数: {near_miss['layers_satisfied']}/3")
            report_lines.append(f"   未满足的条件:")
            for detail in near_miss['unsatisfied_details'][:5]:  # 只显示前5个
                report_lines.append(f"      ❌ {detail}")

    report_lines.append(f"\n{'=' * 60}")

    return '\n'.join(report_lines)
