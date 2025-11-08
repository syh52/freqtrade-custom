"""
入场模式分析器

分析NostalgiaForInfinityX7的17种入场模式效果
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class EntryModeAnalyzer:
    """入场模式分析器"""

    def __init__(self, trades_df: pd.DataFrame):
        """
        初始化分析器

        Args:
            trades_df: 增强后的交易DataFrame（必须包含entry_mode列）
        """
        self.trades_df = trades_df

        if 'entry_mode' not in trades_df.columns:
            raise ValueError("trades_df必须包含entry_mode列，请先运行DataCleaner.clean_and_enhance_trades()")

    def analyze(self) -> Dict:
        """
        执行完整的入场模式分析

        Returns:
            分析结果字典
        """
        analysis = {
            'mode_performance': self._analyze_mode_performance(),
            'mode_comparison': self._compare_long_vs_short(),
            'mode_rankings': self._rank_modes(),
            'underutilized_modes': self._find_underutilized_modes(),
            'problematic_modes': self._find_problematic_modes(),
            'entry_tag_analysis': self._analyze_entry_tags(),  # 新增：entry tag 详细分析
            'exit_tag_analysis': self._analyze_exit_tags(),    # 新增：exit tag 详细分析
            'recommendations': self._generate_recommendations()
        }

        return analysis

    def _analyze_mode_performance(self) -> pd.DataFrame:
        """分析每种模式的表现"""
        mode_stats = self.trades_df.groupby('entry_mode').agg({
            'profit_ratio': ['count', 'mean', 'median', 'sum'],
            'profit_abs': ['sum', 'mean'],
            'duration_minutes': 'mean' if 'duration_minutes' in self.trades_df.columns else 'count'
        }).round(4)

        # 重命名列
        mode_stats.columns = ['trades', 'avg_profit_pct', 'median_profit_pct', 'total_profit_pct',
                              'total_profit_abs', 'avg_profit_abs', 'avg_duration_hours']

        # 转换百分比
        mode_stats['avg_profit_pct'] *= 100
        mode_stats['median_profit_pct'] *= 100
        mode_stats['total_profit_pct'] *= 100

        if 'duration_minutes' in self.trades_df.columns:
            mode_stats['avg_duration_hours'] /= 60

        # 计算胜率
        wins_per_mode = self.trades_df[self.trades_df['profit_ratio'] > 0].groupby('entry_mode').size()
        mode_stats['wins'] = wins_per_mode
        mode_stats['wins'] = mode_stats['wins'].fillna(0).astype(int)
        mode_stats['win_rate'] = (mode_stats['wins'] / mode_stats['trades'] * 100).round(2)

        # 计算风险调整后收益（Sharpe-like）
        profit_std = self.trades_df.groupby('entry_mode')['profit_ratio'].std()
        mode_stats['profit_std'] = profit_std
        mode_stats['sharpe_like'] = (mode_stats['avg_profit_pct'] / (mode_stats['profit_std'] * 100)).fillna(0).round(2)

        # 重新排序列
        cols_order = ['trades', 'wins', 'win_rate', 'avg_profit_pct', 'median_profit_pct',
                     'total_profit_abs', 'avg_duration_hours', 'sharpe_like']
        mode_stats = mode_stats[[col for col in cols_order if col in mode_stats.columns]]

        return mode_stats.sort_values('total_profit_abs', ascending=False).reset_index()

    def _compare_long_vs_short(self) -> Dict:
        """对比Long和Short模式"""
        comparison = {}

        # 提取Long和Short交易
        long_trades = self.trades_df[self.trades_df['entry_mode'].str.contains('Long', na=False)]
        short_trades = self.trades_df[self.trades_df['entry_mode'].str.contains('Short', na=False)]

        comparison['long'] = {
            'count': len(long_trades),
            'win_rate': (long_trades['profit_ratio'] > 0).sum() / len(long_trades) * 100 if len(long_trades) > 0 else 0,
            'avg_profit_pct': long_trades['profit_ratio'].mean() * 100 if len(long_trades) > 0 else 0,
            'total_profit_abs': long_trades['profit_abs'].sum() if len(long_trades) > 0 and 'profit_abs' in long_trades.columns else 0
        }

        comparison['short'] = {
            'count': len(short_trades),
            'win_rate': (short_trades['profit_ratio'] > 0).sum() / len(short_trades) * 100 if len(short_trades) > 0 else 0,
            'avg_profit_pct': short_trades['profit_ratio'].mean() * 100 if len(short_trades) > 0 else 0,
            'total_profit_abs': short_trades['profit_abs'].sum() if len(short_trades) > 0 and 'profit_abs' in short_trades.columns else 0
        }

        # 判断哪个方向更好
        if comparison['long']['total_profit_abs'] > comparison['short']['total_profit_abs']:
            comparison['winner'] = 'Long'
        elif comparison['short']['total_profit_abs'] > comparison['long']['total_profit_abs']:
            comparison['winner'] = 'Short'
        else:
            comparison['winner'] = 'Tie'

        return comparison

    def _rank_modes(self) -> Dict:
        """对模式进行排名"""
        perf = self._analyze_mode_performance()

        rankings = {
            'by_profit': perf.nlargest(5, 'total_profit_abs')[['entry_mode', 'total_profit_abs', 'trades']].to_dict('records'),
            'by_win_rate': perf.nlargest(5, 'win_rate')[['entry_mode', 'win_rate', 'trades']].to_dict('records'),
            'by_sharpe': perf.nlargest(5, 'sharpe_like')[['entry_mode', 'sharpe_like', 'trades']].to_dict('records'),
            'by_usage': perf.nlargest(5, 'trades')[['entry_mode', 'trades', 'total_profit_abs']].to_dict('records')
        }

        return rankings

    def _find_underutilized_modes(self) -> List[Dict]:
        """找出使用不足但表现优秀的模式"""
        perf = self._analyze_mode_performance()

        # 定义"使用不足"：交易数少于总数的5%
        total_trades = perf['trades'].sum()
        threshold = total_trades * 0.05

        underutilized = perf[
            (perf['trades'] < threshold) &  # 使用少
            (perf['avg_profit_pct'] > 1) &  # 平均收益好
            (perf['win_rate'] > 60)         # 胜率不错
        ]

        return underutilized[['entry_mode', 'trades', 'avg_profit_pct', 'win_rate']].to_dict('records')

    def _find_problematic_modes(self) -> List[Dict]:
        """找出表现不佳的模式"""
        perf = self._analyze_mode_performance()

        # 定义"问题模式"：胜率<50% 或 平均亏损
        problematic = perf[
            (perf['win_rate'] < 50) |
            (perf['avg_profit_pct'] < 0)
        ]

        return problematic[['entry_mode', 'trades', 'win_rate', 'avg_profit_pct', 'total_profit_abs']].to_dict('records')

    def _generate_recommendations(self) -> List[Dict]:
        """生成优化建议"""
        recommendations = []

        # 基于Long vs Short对比
        comparison = self._compare_long_vs_short()
        if comparison['winner'] == 'Long':
            if comparison['short']['total_profit_abs'] < 0:
                recommendations.append({
                    'priority': '🔴 高优先级',
                    'type': '方向选择',
                    'title': '考虑禁用Short模式',
                    'description': f"Short模式总亏损 {comparison['short']['total_profit_abs']:.0f} USDT，而Long模式盈利 {comparison['long']['total_profit_abs']:.0f} USDT",
                    'action': '在策略中设置 can_short = False 或收紧Short入场条件'
                })
        elif comparison['winner'] == 'Short':
            if comparison['long']['total_profit_abs'] < 0:
                recommendations.append({
                    'priority': '🔴 高优先级',
                    'type': '方向选择',
                    'title': '考虑禁用Long模式',
                    'description': f"Long模式总亏损 {comparison['long']['total_profit_abs']:.0f} USDT，而Short模式盈利 {comparison['short']['total_profit_abs']:.0f} USDT",
                    'action': '收紧Long入场条件或仅在特定市场环境下做多'
                })

        # 基于问题模式
        problematic = self._find_problematic_modes()
        if problematic:
            top_problems = sorted(problematic, key=lambda x: x['total_profit_abs'])[:3]
            for prob in top_problems:
                recommendations.append({
                    'priority': '🟠 中优先级',
                    'type': '模式优化',
                    'title': f"检查 {prob['entry_mode']} 模式",
                    'description': f"该模式胜率 {prob['win_rate']:.1f}%，平均收益 {prob['avg_profit_pct']:.2f}%",
                    'action': '检查策略代码，收紧入场条件或临时禁用此模式'
                })

        # 基于未充分利用的模式
        underutilized = self._find_underutilized_modes()
        if underutilized:
            for mode in underutilized[:2]:  # 只推荐前2个
                recommendations.append({
                    'priority': '🟡 低优先级',
                    'type': '扩大应用',
                    'title': f"扩大 {mode['entry_mode']} 模式应用",
                    'description': f"该模式表现优秀（胜率{mode['win_rate']:.1f}%，平均+{mode['avg_profit_pct']:.2f}%）但仅{mode['trades']}笔交易",
                    'action': '放宽该模式的入场条件，增加信号数量'
                })

        # 如果没有明显问题
        if len(recommendations) == 0:
            recommendations.append({
                'priority': '✅ 优秀',
                'type': '模式平衡',
                'title': '入场模式整体表现良好',
                'description': '各模式收益平衡，无明显短板',
                'action': '继续保持当前配置，可根据市场环境微调'
            })

        return recommendations

    def get_mode_details(self, mode_name: str) -> Dict:
        """
        获取特定模式的详细信息

        Args:
            mode_name: 模式名称，如 "Long Grind"

        Returns:
            详细信息字典
        """
        mode_trades = self.trades_df[self.trades_df['entry_mode'] == mode_name]

        if len(mode_trades) == 0:
            return {'error': f'未找到模式 {mode_name} 的交易'}

        details = {
            'mode_name': mode_name,
            'total_trades': len(mode_trades),
            'wins': len(mode_trades[mode_trades['profit_ratio'] > 0]),
            'losses': len(mode_trades[mode_trades['profit_ratio'] <= 0]),
            'win_rate': len(mode_trades[mode_trades['profit_ratio'] > 0]) / len(mode_trades) * 100,
            'profit_stats': {
                'mean': mode_trades['profit_ratio'].mean() * 100,
                'median': mode_trades['profit_ratio'].median() * 100,
                'std': mode_trades['profit_ratio'].std() * 100,
                'max': mode_trades['profit_ratio'].max() * 100,
                'min': mode_trades['profit_ratio'].min() * 100
            },
            'duration_stats': {},
            'top_pairs': [],
            'worst_pairs': []
        }

        # 持仓时长统计
        if 'duration_minutes' in mode_trades.columns:
            details['duration_stats'] = {
                'mean_hours': mode_trades['duration_minutes'].mean() / 60,
                'median_hours': mode_trades['duration_minutes'].median() / 60,
                'max_hours': mode_trades['duration_minutes'].max() / 60
            }

        # 该模式下表现最好的币种
        if 'pair' in mode_trades.columns:
            pair_perf = mode_trades.groupby('pair')['profit_abs'].sum().sort_values(ascending=False)
            details['top_pairs'] = pair_perf.head(5).to_dict()
            details['worst_pairs'] = pair_perf.tail(5).to_dict()

        return details

    def _analyze_entry_tags(self) -> Dict:
        """
        详细分析 entry_tag 的表现

        Entry Tag 直接对应策略代码中的入场条件，比 entry_mode 更精确
        """
        tag_analysis = {}

        # 提取 entry_tag（从 enter_tag 列或 open_order_type 中）
        if 'enter_tag' in self.trades_df.columns:
            tags_df = self.trades_df.copy()
            tags_df['entry_tag'] = tags_df['enter_tag']
        else:
            # 如果没有 enter_tag，尝试从其他字段提取
            return {'error': 'No enter_tag column found'}

        # 按 tag 分组统计
        tag_stats = tags_df.groupby('entry_tag').agg({
            'profit_ratio': ['count', 'mean', 'median'],
            'profit_abs': ['sum', 'mean'],
        }).round(4)

        tag_stats.columns = ['trades', 'avg_profit_pct', 'median_profit_pct', 'total_profit_abs', 'avg_profit_abs']
        tag_stats['avg_profit_pct'] *= 100
        tag_stats['median_profit_pct'] *= 100

        # 计算胜率
        wins_per_tag = tags_df[tags_df['profit_ratio'] > 0].groupby('entry_tag').size()
        tag_stats['wins'] = wins_per_tag
        tag_stats['wins'] = tag_stats['wins'].fillna(0).astype(int)
        tag_stats['win_rate'] = (tag_stats['wins'] / tag_stats['trades'] * 100).round(2)

        # 按总收益排序
        tag_stats = tag_stats.sort_values('total_profit_abs', ascending=False).reset_index()

        # 提取 tag 编号（如果tag包含数字）
        import re
        def extract_tag_number(tag):
            """提取tag中的数字"""
            if pd.isna(tag):
                return None
            match = re.search(r'\(?\s*(\d+)\s*\)?', str(tag))
            return int(match.group(1)) if match else None

        tag_stats['tag_number'] = tag_stats['entry_tag'].apply(extract_tag_number)

        # 分类：Long tags (1-163) vs Short tags (501-661)
        tag_stats['tag_type'] = tag_stats['tag_number'].apply(
            lambda x: 'Long' if x and 1 <= x <= 163 else ('Short' if x and 501 <= x <= 661 else 'Unknown')
        )

        tag_analysis['tag_performance'] = tag_stats

        # Top 10 最佳 tags
        tag_analysis['top_tags'] = tag_stats.nlargest(10, 'total_profit_abs')[
            ['entry_tag', 'tag_number', 'trades', 'win_rate', 'total_profit_abs']
        ].to_dict('records')

        # Top 10 最差 tags
        tag_analysis['worst_tags'] = tag_stats.nsmallest(10, 'total_profit_abs')[
            ['entry_tag', 'tag_number', 'trades', 'win_rate', 'total_profit_abs']
        ].to_dict('records')

        # 高频但低效的tags（需要优化的重点）
        high_frequency_threshold = tag_stats['trades'].quantile(0.75)
        tag_analysis['high_frequency_low_performance'] = tag_stats[
            (tag_stats['trades'] >= high_frequency_threshold) &
            (tag_stats['avg_profit_pct'] < 1)
        ][['entry_tag', 'tag_number', 'trades', 'win_rate', 'avg_profit_pct', 'total_profit_abs']].to_dict('records')

        # 低频但高效的tags（可以扩大使用）
        low_frequency_threshold = tag_stats['trades'].quantile(0.25)
        tag_analysis['low_frequency_high_performance'] = tag_stats[
            (tag_stats['trades'] <= low_frequency_threshold) &
            (tag_stats['win_rate'] > 70) &
            (tag_stats['avg_profit_pct'] > 2)
        ][['entry_tag', 'tag_number', 'trades', 'win_rate', 'avg_profit_pct']].to_dict('records')

        return tag_analysis

    def _analyze_exit_tags(self) -> Dict:
        """
        详细分析 exit_reason (包含 exit tag) 的表现

        Exit Reason 包含出场原因和tag，可以定位到代码中的出场条件
        """
        exit_analysis = {}

        if 'exit_reason' not in self.trades_df.columns:
            return {'error': 'No exit_reason column found'}

        # 按 exit_reason 分组统计
        exit_stats = self.trades_df.groupby('exit_reason').agg({
            'profit_ratio': ['count', 'mean', 'median'],
            'profit_abs': ['sum', 'mean'],
        }).round(4)

        exit_stats.columns = ['trades', 'avg_profit_pct', 'median_profit_pct', 'total_profit_abs', 'avg_profit_abs']
        exit_stats['avg_profit_pct'] *= 100
        exit_stats['median_profit_pct'] *= 100

        # 计算胜率
        wins_per_exit = self.trades_df[self.trades_df['profit_ratio'] > 0].groupby('exit_reason').size()
        exit_stats['wins'] = wins_per_exit
        exit_stats['wins'] = exit_stats['wins'].fillna(0).astype(int)
        exit_stats['win_rate'] = (exit_stats['wins'] / exit_stats['trades'] * 100).round(2)

        # 按交易数量排序
        exit_stats = exit_stats.sort_values('trades', ascending=False).reset_index()

        # 提取 exit tag 编号
        import re
        def extract_exit_tag(reason):
            """提取exit reason中的tag数字"""
            if pd.isna(reason):
                return None
            match = re.search(r'\(\s*(\d+)\s*\)', str(reason))
            return int(match.group(1)) if match else None

        exit_stats['exit_tag'] = exit_stats['exit_reason'].apply(extract_exit_tag)

        # 分类exit原因
        def categorize_exit(reason):
            reason_str = str(reason).lower()
            if 'roi' in reason_str:
                return 'ROI (止盈)'
            elif 'stoploss' in reason_str or 'stop_loss' in reason_str:
                return 'Stop Loss (止损)'
            elif 'liquidation' in reason_str:
                return 'Liquidation (爆仓)'
            elif 'trailing' in reason_str:
                return 'Trailing Stop (移动止损)'
            elif 'signal' in reason_str or 'exit' in reason_str:
                return 'Signal Exit (信号出场)'
            else:
                return 'Other (其他)'

        exit_stats['exit_category'] = exit_stats['exit_reason'].apply(categorize_exit)

        exit_analysis['exit_performance'] = exit_stats

        # 按分类汇总
        category_summary = self.trades_df.copy()
        category_summary['exit_category'] = category_summary['exit_reason'].apply(categorize_exit)
        category_stats = category_summary.groupby('exit_category').agg({
            'profit_ratio': ['count', 'mean'],
            'profit_abs': 'sum'
        }).round(4)
        category_stats.columns = ['trades', 'avg_profit_pct', 'total_profit_abs']
        category_stats['avg_profit_pct'] *= 100
        exit_analysis['category_summary'] = category_stats.reset_index().to_dict('records')

        # 最常见的出场原因
        exit_analysis['most_common_exits'] = exit_stats.nlargest(10, 'trades')[
            ['exit_reason', 'exit_tag', 'trades', 'win_rate', 'avg_profit_pct']
        ].to_dict('records')

        # 表现最差的出场原因（通常是止损或爆仓）
        exit_analysis['worst_exits'] = exit_stats.nsmallest(10, 'avg_profit_pct')[
            ['exit_reason', 'exit_tag', 'trades', 'win_rate', 'avg_profit_pct', 'total_profit_abs']
        ].to_dict('records')

        return exit_analysis


def quick_entry_mode_analysis(trades_df: pd.DataFrame) -> Dict:
    """
    便捷函数：快速入场模式分析

    Args:
        trades_df: 交易DataFrame

    Returns:
        分析结果字典
    """
    analyzer = EntryModeAnalyzer(trades_df)
    return analyzer.analyze()
