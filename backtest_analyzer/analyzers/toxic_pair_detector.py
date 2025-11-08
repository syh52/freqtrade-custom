"""
毒瘤币检测器

识别高风险币种并生成黑名单配置
扩展自 scripts/analyze_toxic_pairs.py
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import json


class ToxicPairDetector:
    """毒瘤币检测器"""

    def __init__(self, trades_df: pd.DataFrame):
        """
        初始化检测器

        Args:
            trades_df: 增强后的交易DataFrame
        """
        self.trades_df = trades_df
        self.pair_stats = self._calculate_pair_stats()

    def analyze(self) -> Dict:
        """
        执行完整的毒瘤币分析

        Returns:
            分析结果字典
        """
        results = {
            'level1_deadly': [],  # 致命风险，立即拉黑
            'level2_warning': [],  # 警告风险，限制模式
            'level3_monitor': [],  # 监控币种
            'safe_pairs': [],      # 安全币种
            'summary': {},
            'blacklist_config': {}
        }

        # 分析每个币种
        for pair, stats in self.pair_stats.items():
            # Level 1: 致命信号
            is_deadly, deadly_reason = self._is_deadly_toxic(stats)
            if is_deadly:
                results['level1_deadly'].append({
                    'pair': pair,
                    'reason': deadly_reason,
                    'stats': stats
                })
                continue

            # Level 2: 警告信号
            is_warning, warning_signals = self._is_warning_toxic(stats)
            if is_warning:
                results['level2_warning'].append({
                    'pair': pair,
                    'signals': warning_signals,
                    'stats': stats
                })
                continue

            # Level 3: 需要监控
            if self._needs_monitoring(stats):
                results['level3_monitor'].append({
                    'pair': pair,
                    'stats': stats
                })
            else:
                # 安全币种
                results['safe_pairs'].append({
                    'pair': pair,
                    'stats': stats
                })

        # 生成摘要
        results['summary'] = {
            'total_pairs': len(self.pair_stats),
            'level1_count': len(results['level1_deadly']),
            'level2_count': len(results['level2_warning']),
            'level3_count': len(results['level3_monitor']),
            'safe_count': len(results['safe_pairs'])
        }

        # 生成黑名单配置
        results['blacklist_config'] = self._generate_blacklist_config(results)

        return results

    def _calculate_pair_stats(self) -> Dict:
        """计算每个币种的统计数据"""
        stats = {}

        for pair in self.trades_df['pair'].unique():
            pair_trades = self.trades_df[self.trades_df['pair'] == pair]

            # 基础统计
            total_trades = len(pair_trades)
            wins = len(pair_trades[pair_trades['profit_ratio'] > 0])
            win_rate = wins / total_trades * 100 if total_trades > 0 else 0

            # Grind模式统计
            grind_trades = pair_trades[pair_trades['is_grind_entry']] if 'is_grind_entry' in pair_trades.columns else pd.DataFrame()
            grind_count = len(grind_trades)
            grind_wins = len(grind_trades[grind_trades['profit_ratio'] > 0]) if grind_count > 0 else 0
            grind_win_rate = grind_wins / grind_count * 100 if grind_count > 0 else 100

            # 盈亏统计
            total_profit = pair_trades['profit_abs'].sum() if 'profit_abs' in pair_trades.columns else 0
            max_single_loss = pair_trades['profit_abs'].min() if 'profit_abs' in pair_trades.columns else 0
            grind_profit = grind_trades['profit_abs'].sum() if len(grind_trades) > 0 and 'profit_abs' in grind_trades.columns else 0

            # 持仓时长
            avg_duration = pair_trades['duration_minutes'].mean() / 60 if 'duration_minutes' in pair_trades.columns else 0
            grind_avg_duration = grind_trades['duration_minutes'].mean() / 60 if len(grind_trades) > 0 and 'duration_minutes' in grind_trades.columns else 0

            # 爆仓统计
            liq_count = pair_trades['is_liquidation'].sum() if 'is_liquidation' in pair_trades.columns else 0

            stats[pair] = {
                'total_trades': total_trades,
                'wins': wins,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'max_single_loss': max_single_loss,
                'avg_duration': avg_duration,
                'grind_trades': grind_count,
                'grind_wins': grind_wins,
                'grind_win_rate': grind_win_rate,
                'grind_profit': grind_profit,
                'grind_avg_duration': grind_avg_duration,
                'liquidation_count': liq_count
            }

        return stats

    def _is_deadly_toxic(self, stats: Dict) -> Tuple[bool, str]:
        """
        Level 1: 致命信号检测

        满足任一条件立即拉黑：
        1. 总亏损超过1500U
        2. 长期深套（持仓>7天且Grind亏损>3000U）
        3. 极端单笔亏损（>5000U）
        4. Grind模式巨额亏损（>2000U）
        5. 有爆仓记录
        """
        # 信号1: 总亏损严重
        if stats.get('total_profit', 0) < -1500:
            return True, f"总亏损{stats['total_profit']:.0f}U"

        # 信号2: 长期深套
        if (stats.get('grind_avg_duration', 0) > 168 and
            stats.get('grind_profit', 0) < -3000):
            return True, f"长期深套（{stats['grind_avg_duration']/24:.1f}天，亏损{stats['grind_profit']:.0f}U）"

        # 信号3: 极端单笔亏损
        if stats.get('max_single_loss', 0) < -5000:
            return True, f"极端亏损（{stats['max_single_loss']:.0f}U）"

        # 信号4: Grind模式巨额亏损
        if stats.get('grind_profit', 0) < -2000:
            return True, f"Grind巨亏{stats['grind_profit']:.0f}U"

        # 信号5: 爆仓记录
        if stats.get('liquidation_count', 0) > 0:
            return True, f"爆仓{stats['liquidation_count']}次"

        return False, None

    def _is_warning_toxic(self, stats: Dict) -> Tuple[bool, List[str]]:
        """
        Level 2: 警告信号检测

        满足2+条件为中等风险：
        1. 整体胜率<70%
        2. Grind胜率<70%（≥2笔）
        3. 单笔亏损<-1000U
        4. 长期持仓但亏损（>5天且亏损）
        5. Grind净亏损<-1000U
        """
        signals = []

        # 信号1: 整体胜率低
        if stats.get('win_rate', 100) < 70:
            signals.append(f"整体胜率{stats['win_rate']:.1f}%")

        # 信号2: Grind表现差
        if (stats.get('grind_trades', 0) >= 2 and
            stats.get('grind_win_rate', 100) < 70):
            signals.append(f"Grind胜率{stats['grind_win_rate']:.1f}%")

        # 信号3: 大额单笔亏损
        if stats.get('max_single_loss', 0) < -1000:
            signals.append(f"单笔亏损{stats['max_single_loss']:.0f}U")

        # 信号4: 长期持仓但亏损
        if (stats.get('grind_avg_duration', 0) > 120 and
            stats.get('grind_profit', 0) < 0):
            signals.append(f"长期持仓亏损（{stats['grind_avg_duration']/24:.1f}天）")

        # 信号5: Grind净亏损
        if stats.get('grind_profit', 0) < -1000:
            signals.append(f"Grind累计亏损{stats['grind_profit']:.0f}U")

        return len(signals) >= 2, signals

    def _needs_monitoring(self, stats: Dict) -> bool:
        """判断是否需要监控"""
        # 胜率偏低但不至于拉黑
        if 60 <= stats.get('win_rate', 100) < 70:
            return True

        # 有一定亏损但不严重
        if -1000 < stats.get('total_profit', 0) < -500:
            return True

        # Grind有亏损但不多
        if -1000 < stats.get('grind_profit', 0) < -300:
            return True

        return False

    def _generate_blacklist_config(self, results: Dict) -> Dict:
        """生成黑名单配置"""
        # Level 1: 完全拉黑
        full_blacklist = [item['pair'] for item in results['level1_deadly']]

        # Level 2: 限制Grind（可选）
        grind_restricted = [item['pair'] for item in results['level2_warning']]

        config = {
            'full_blacklist': full_blacklist,
            'grind_restricted': grind_restricted,
            'monitor_list': [item['pair'] for item in results['level3_monitor']],
            'freqtrade_format': {
                'exchange': {
                    'pair_blacklist': full_blacklist
                }
            }
        }

        return config

    def get_detailed_report(self, results: Dict) -> str:
        """生成详细的文本报告"""
        report = []
        report.append("=" * 80)
        report.append("毒瘤币检测报告")
        report.append("=" * 80)
        report.append("")

        # 摘要
        summary = results['summary']
        report.append(f"总币种数: {summary['total_pairs']}")
        report.append(f"  🔴 Level 1 (致命风险): {summary['level1_count']} 个 - 立即拉黑")
        report.append(f"  🟠 Level 2 (警告风险): {summary['level2_count']} 个 - 限制Grind模式")
        report.append(f"  🟡 Level 3 (需要监控): {summary['level3_count']} 个")
        report.append(f"  ✅ 安全币种: {summary['safe_count']} 个")
        report.append("")

        # Level 1 详情
        if results['level1_deadly']:
            report.append("🔴 Level 1: 致命风险币种（立即拉黑）")
            report.append("-" * 80)
            for item in results['level1_deadly']:
                stats = item['stats']
                report.append(f"{item['pair']:12} | {item['reason']:30} | "
                             f"交易{stats['total_trades']}笔 胜率{stats['win_rate']:.1f}% "
                             f"总盈亏{stats['total_profit']:+.0f}U")
            report.append("")

        # Level 2 详情
        if results['level2_warning']:
            report.append("🟠 Level 2: 警告风险币种（建议限制Grind模式）")
            report.append("-" * 80)
            for item in results['level2_warning']:
                stats = item['stats']
                signals_str = " | ".join(item['signals'])
                report.append(f"{item['pair']:12} | {signals_str}")
                report.append(f"             交易{stats['total_trades']}笔 "
                             f"胜率{stats['win_rate']:.1f}% 盈亏{stats['total_profit']:+.0f}U")
            report.append("")

        # 黑名单配置
        if results['blacklist_config']['full_blacklist']:
            report.append("📋 生成的黑名单配置")
            report.append("-" * 80)
            report.append(json.dumps(results['blacklist_config']['freqtrade_format'], indent=2))
            report.append("")

        return "\n".join(report)


def quick_toxic_analysis(trades_df: pd.DataFrame) -> Dict:
    """
    便捷函数：快速毒瘤币分析

    Args:
        trades_df: 交易DataFrame

    Returns:
        分析结果字典
    """
    detector = ToxicPairDetector(trades_df)
    return detector.analyze()
