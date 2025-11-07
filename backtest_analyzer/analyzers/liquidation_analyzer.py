"""
爆仓分析器

深度分析爆仓交易，识别风险因素并提供预防建议
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class LiquidationAnalyzer:
    """爆仓分析器"""

    def __init__(self, trades_df: pd.DataFrame):
        """
        初始化分析器

        Args:
            trades_df: 增强后的交易DataFrame（必须包含is_liquidation列）
        """
        self.trades_df = trades_df

        # 提取爆仓交易
        if 'is_liquidation' in trades_df.columns:
            self.liq_trades = trades_df[trades_df['is_liquidation']].copy()
        else:
            # 通过exit_reason判断
            self.liq_trades = trades_df[
                trades_df['exit_reason'].str.contains('liquidation', case=False, na=False)
            ].copy()

        self.liq_count = len(self.liq_trades)
        self.total_count = len(trades_df)

    def analyze(self) -> Dict:
        """
        执行完整的爆仓分析

        Returns:
            分析结果字典
        """
        if self.liq_count == 0:
            return {
                'summary': {'liquidation_count': 0, 'message': '✓ 未发现爆仓交易'},
                'risk_pairs': pd.DataFrame(),
                'risk_modes': pd.DataFrame(),
                'recommendations': []
            }

        analysis = {
            'summary': self._get_summary(),
            'risk_pairs': self._analyze_risk_pairs(),
            'risk_modes': self._analyze_risk_modes(),
            'leverage_analysis': self._analyze_leverage(),
            'dca_analysis': self._analyze_dca_behavior(),
            'timeline_analysis': self._analyze_timeline(),
            'recommendations': self._generate_recommendations()
        }

        return analysis

    def _get_summary(self) -> Dict:
        """获取爆仓摘要"""
        summary = {
            'liquidation_count': self.liq_count,
            'liquidation_rate': self.liq_count / self.total_count * 100 if self.total_count > 0 else 0,
            'total_loss_abs': self.liq_trades['profit_abs'].sum() if 'profit_abs' in self.liq_trades.columns else 0,
            'total_loss_pct': self.liq_trades['profit_ratio'].sum() * 100 if 'profit_ratio' in self.liq_trades.columns else 0,
            'avg_loss_per_liquidation': self.liq_trades['profit_abs'].mean() if 'profit_abs' in self.liq_trades.columns else 0,
            'max_single_loss': self.liq_trades['profit_abs'].min() if 'profit_abs' in self.liq_trades.columns else 0,
        }

        # 时长统计
        if 'duration_minutes' in self.liq_trades.columns:
            summary['avg_duration_hours'] = self.liq_trades['duration_minutes'].mean() / 60
            summary['max_duration_hours'] = self.liq_trades['duration_minutes'].max() / 60

        # 杠杆统计
        if 'leverage' in self.liq_trades.columns:
            summary['avg_leverage'] = self.liq_trades['leverage'].mean()
            summary['max_leverage'] = self.liq_trades['leverage'].max()

        return summary

    def _analyze_risk_pairs(self) -> pd.DataFrame:
        """分析高风险币种"""
        if 'pair' not in self.liq_trades.columns:
            return pd.DataFrame()

        pair_liq = self.liq_trades.groupby('pair').agg({
            'profit_abs': ['count', 'sum', 'mean'],
            'duration_minutes': 'mean' if 'duration_minutes' in self.liq_trades.columns else 'count'
        }).round(4)

        pair_liq.columns = ['liq_count', 'total_loss', 'avg_loss', 'avg_duration_hours']
        if 'duration_minutes' in self.liq_trades.columns:
            pair_liq['avg_duration_hours'] = pair_liq['avg_duration_hours'] / 60

        # 添加该币种的总交易数
        total_trades_per_pair = self.trades_df.groupby('pair').size()
        pair_liq['total_trades'] = pair_liq.index.map(total_trades_per_pair)
        pair_liq['liq_rate'] = (pair_liq['liq_count'] / pair_liq['total_trades'] * 100).round(2)

        # 风险评分（0-100，越高越危险）
        # 因素：爆仓次数(40%), 爆仓率(30%), 平均亏损(30%)
        max_liq = pair_liq['liq_count'].max() if pair_liq['liq_count'].max() > 0 else 1
        max_rate = pair_liq['liq_rate'].max() if pair_liq['liq_rate'].max() > 0 else 1
        max_loss = abs(pair_liq['avg_loss'].min()) if abs(pair_liq['avg_loss'].min()) > 0 else 1

        pair_liq['risk_score'] = (
            (pair_liq['liq_count'] / max_liq * 40) +
            (pair_liq['liq_rate'] / max_rate * 30) +
            (abs(pair_liq['avg_loss']) / max_loss * 30)
        ).round(2)

        # 风险等级
        pair_liq['risk_level'] = pd.cut(
            pair_liq['risk_score'],
            bins=[0, 30, 60, 100],
            labels=['🟡 中等风险', '🟠 高风险', '🔴 极高风险']
        )

        # 按风险评分排序
        pair_liq = pair_liq.sort_values('risk_score', ascending=False)

        return pair_liq.reset_index()

    def _analyze_risk_modes(self) -> pd.DataFrame:
        """分析高风险入场模式"""
        if 'entry_mode' not in self.liq_trades.columns:
            return pd.DataFrame()

        mode_liq = self.liq_trades.groupby('entry_mode').agg({
            'profit_abs': ['count', 'sum', 'mean']
        }).round(4)

        mode_liq.columns = ['liq_count', 'total_loss', 'avg_loss']

        # 添加该模式的总交易数
        if 'entry_mode' in self.trades_df.columns:
            total_trades_per_mode = self.trades_df.groupby('entry_mode').size()
            mode_liq['total_trades'] = mode_liq.index.map(total_trades_per_mode)
            mode_liq['liq_rate'] = (mode_liq['liq_count'] / mode_liq['total_trades'] * 100).round(2)

        # 按爆仓次数排序
        mode_liq = mode_liq.sort_values('liq_count', ascending=False)

        return mode_liq.reset_index()

    def _analyze_leverage(self) -> Dict:
        """分析杠杆使用情况"""
        if 'leverage' not in self.liq_trades.columns:
            return {}

        leverage_stats = {
            'avg_leverage': self.liq_trades['leverage'].mean(),
            'median_leverage': self.liq_trades['leverage'].median(),
            'max_leverage': self.liq_trades['leverage'].max(),
            'leverage_distribution': self.liq_trades['leverage'].value_counts().to_dict()
        }

        # 对比非爆仓交易的杠杆
        non_liq = self.trades_df[~self.trades_df['is_liquidation']] if 'is_liquidation' in self.trades_df.columns else None
        if non_liq is not None and 'leverage' in non_liq.columns:
            leverage_stats['avg_leverage_non_liq'] = non_liq['leverage'].mean()
            leverage_stats['leverage_difference'] = leverage_stats['avg_leverage'] - leverage_stats['avg_leverage_non_liq']

        return leverage_stats

    def _analyze_dca_behavior(self) -> Dict:
        """分析DCA/加仓行为"""
        if 'order_count' not in self.liq_trades.columns and 'orders' not in self.liq_trades.columns:
            return {}

        # 计算订单数
        if 'order_count' not in self.liq_trades.columns:
            self.liq_trades['order_count'] = self.liq_trades['orders'].apply(
                lambda x: len(x) if isinstance(x, list) else 1
            )

        dca_stats = {
            'avg_order_count': self.liq_trades['order_count'].mean(),
            'max_order_count': self.liq_trades['order_count'].max(),
            'liq_with_dca': (self.liq_trades['order_count'] > 1).sum(),
            'liq_with_dca_rate': (self.liq_trades['order_count'] > 1).sum() / len(self.liq_trades) * 100
        }

        # 分析加仓次数与亏损的关系
        if len(self.liq_trades) > 0:
            order_loss_corr = self.liq_trades[['order_count', 'profit_abs']].corr().iloc[0, 1]
            dca_stats['order_loss_correlation'] = order_loss_corr
            dca_stats['dca_increases_risk'] = order_loss_corr < -0.3  # 负相关说明加仓越多亏损越大

        return dca_stats

    def _analyze_timeline(self) -> Dict:
        """分析爆仓时间分布"""
        if 'open_date' not in self.liq_trades.columns:
            return {}

        timeline = {}

        # 按月统计
        if 'month' in self.liq_trades.columns:
            timeline['by_month'] = self.liq_trades.groupby('month').size().to_dict()

        # 按星期几统计
        if 'day_of_week' in self.liq_trades.columns:
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            day_counts = self.liq_trades.groupby('day_of_week').size()
            timeline['by_weekday'] = {day_names[k]: v for k, v in day_counts.items()}

        # 按小时统计
        if 'hour' in self.liq_trades.columns:
            timeline['by_hour'] = self.liq_trades.groupby('hour').size().to_dict()

        return timeline

    def _generate_recommendations(self) -> List[Dict]:
        """生成预防建议"""
        recommendations = []

        # 建议1: 高风险币种
        risk_pairs = self._analyze_risk_pairs()
        if not risk_pairs.empty:
            high_risk_pairs = risk_pairs[risk_pairs['risk_score'] >= 60]
            if len(high_risk_pairs) > 0:
                recommendations.append({
                    'priority': '🔴 高优先级',
                    'type': '币种黑名单',
                    'title': f'立即拉黑 {len(high_risk_pairs)} 个高风险币种',
                    'description': f"以下币种爆仓率高或亏损严重：{', '.join(high_risk_pairs['pair'].head(5).tolist())}",
                    'action': '将这些币种添加到 blacklist 配置中',
                    'affected_pairs': high_risk_pairs['pair'].tolist()
                })

        # 建议2: 杠杆调整
        leverage_analysis = self._analyze_leverage()
        if leverage_analysis and leverage_analysis.get('avg_leverage', 0) > 10:
            recommendations.append({
                'priority': '🔴 高优先级',
                'type': '杠杆优化',
                'title': f"降低杠杆倍数（当前平均{leverage_analysis['avg_leverage']:.1f}x）",
                'description': f"爆仓交易的平均杠杆为 {leverage_analysis['avg_leverage']:.1f}x，建议降低至10x以下",
                'action': f"在配置中将 leverage 从 {leverage_analysis['avg_leverage']:.0f} 降低到 8-10"
            })

        # 建议3: DCA策略
        dca_analysis = self._analyze_dca_behavior()
        if dca_analysis and dca_analysis.get('dca_increases_risk', False):
            recommendations.append({
                'priority': '🟠 中优先级',
                'type': 'DCA策略',
                'title': '限制加仓次数或禁用高风险币种的Grind模式',
                'description': f"数据显示加仓越多亏损越大（相关系数: {dca_analysis.get('order_loss_correlation', 0):.2f}）",
                'action': '对高风险币种禁用position_adjustment或减少最大加仓次数'
            })

        # 建议4: 入场模式
        risk_modes = self._analyze_risk_modes()
        if not risk_modes.empty:
            high_risk_modes = risk_modes[risk_modes['liq_rate'] >= 20]  # 爆仓率>=20%
            if len(high_risk_modes) > 0:
                recommendations.append({
                    'priority': '🟠 中优先级',
                    'type': '入场模式',
                    'title': f'调整或禁用 {len(high_risk_modes)} 种高爆仓率入场模式',
                    'description': f"以下模式爆仓率高：{', '.join(high_risk_modes['entry_mode'].head(3).tolist())}",
                    'action': '检查策略代码，收紧这些模式的入场条件或临时禁用',
                    'affected_modes': high_risk_modes['entry_mode'].tolist()
                })

        # 建议5: 止损优化
        if 'initial_stop_loss_ratio' in self.liq_trades.columns:
            avg_sl = self.liq_trades['initial_stop_loss_ratio'].mean()
            if avg_sl < -0.15:  # 止损设置超过15%
                recommendations.append({
                    'priority': '🟡 低优先级',
                    'type': '止损优化',
                    'title': '收紧止损距离',
                    'description': f"当前平均止损距离为 {abs(avg_sl)*100:.1f}%，过于宽松可能导致爆仓前未触发",
                    'action': '将初始止损设置到5-10%范围内，配合trailing stop'
                })

        # 建议6: 持仓时长
        if 'duration_minutes' in self.liq_trades.columns:
            avg_duration = self.liq_trades['duration_minutes'].mean() / 60
            if avg_duration > 48:  # 持仓超过2天
                recommendations.append({
                    'priority': '🟡 低优先级',
                    'type': '持仓管理',
                    'title': '减少长期持仓',
                    'description': f"爆仓交易平均持仓 {avg_duration:.1f} 小时，长期持仓增加风险暴露",
                    'action': '设置最大持仓时间限制，或对长期未盈利的仓位主动止损'
                })

        # 如果没有爆仓问题，给予肯定
        if len(recommendations) == 0:
            recommendations.append({
                'priority': '✅ 优秀',
                'type': '风险控制',
                'title': '爆仓风险控制良好',
                'description': '未发现明显的高风险因素',
                'action': '继续保持当前的风险管理策略'
            })

        return recommendations

    def get_liquidation_details(self) -> pd.DataFrame:
        """
        获取爆仓交易详情表

        Returns:
            包含关键信息的DataFrame
        """
        if self.liq_count == 0:
            return pd.DataFrame()

        columns_to_show = [
            'pair', 'open_date', 'close_date', 'duration_minutes',
            'entry_mode', 'profit_abs', 'profit_ratio',
            'leverage', 'order_count', 'initial_stop_loss_ratio'
        ]

        # 只选择存在的列
        available_columns = [col for col in columns_to_show if col in self.liq_trades.columns]

        details = self.liq_trades[available_columns].copy()

        # 格式化
        if 'duration_minutes' in details.columns:
            details['duration_hours'] = (details['duration_minutes'] / 60).round(1)
            details = details.drop('duration_minutes', axis=1)

        if 'profit_ratio' in details.columns:
            details['profit_pct'] = (details['profit_ratio'] * 100).round(2)
            details = details.drop('profit_ratio', axis=1)

        if 'initial_stop_loss_ratio' in details.columns:
            details['stop_loss_pct'] = (details['initial_stop_loss_ratio'] * 100).round(2)
            details = details.drop('initial_stop_loss_ratio', axis=1)

        return details.sort_values('profit_abs')  # 按亏损排序


def quick_liquidation_analysis(trades_df: pd.DataFrame) -> Dict:
    """
    便捷函数：快速爆仓分析

    Args:
        trades_df: 交易DataFrame

    Returns:
        分析结果字典
    """
    analyzer = LiquidationAnalyzer(trades_df)
    return analyzer.analyze()
