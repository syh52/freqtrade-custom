#!/usr/bin/env python3
"""
分析回测结果中最差的交易
识别失败交易的共同特征并提出策略优化建议
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from datetime import datetime, timedelta

class WorstTradesAnalyzer:
    def __init__(self, backtest_results_path: str, data_dir: str):
        """
        初始化分析器

        Args:
            backtest_results_path: 回测结果JSON文件路径
            data_dir: K线数据目录路径
        """
        self.backtest_results_path = Path(backtest_results_path)
        self.data_dir = Path(data_dir)
        self.results = None
        self.trades_df = None
        self.worst_trades = None

    def load_backtest_results(self):
        """加载回测结果"""
        print(f"加载回测结果: {self.backtest_results_path}")
        with open(self.backtest_results_path, 'r') as f:
            self.results = json.load(f)

        # 转换交易记录为DataFrame
        if 'strategy' in self.results:
            strategy_name = list(self.results['strategy'].keys())[0]
            trades = self.results['strategy'][strategy_name]['trades']
        else:
            trades = self.results.get('trades', [])

        self.trades_df = pd.DataFrame(trades)

        if len(self.trades_df) == 0:
            print("⚠️  警告: 没有找到交易记录！")
            return False

        # 计算利润百分比
        if 'profit_ratio' in self.trades_df.columns:
            self.trades_df['profit_pct'] = self.trades_df['profit_ratio'] * 100
        elif 'profit_abs' in self.trades_df.columns and 'stake_amount' in self.trades_df.columns:
            self.trades_df['profit_pct'] = (self.trades_df['profit_abs'] / self.trades_df['stake_amount']) * 100

        print(f"✓ 成功加载 {len(self.trades_df)} 笔交易")
        return True

    def identify_worst_trades(self, n_worst: int = 20):
        """识别最差的N笔交易"""
        print(f"\n{'='*80}")
        print(f"识别最差的 {n_worst} 笔交易")
        print(f"{'='*80}")

        # 按利润排序
        self.worst_trades = self.trades_df.nsmallest(n_worst, 'profit_pct')

        print(f"\n最差交易统计:")
        print(f"  总亏损: {self.worst_trades['profit_pct'].sum():.2f}%")
        print(f"  平均亏损: {self.worst_trades['profit_pct'].mean():.2f}%")
        print(f"  最大单笔亏损: {self.worst_trades['profit_pct'].min():.2f}%")

        # 显示最差的前10笔
        print(f"\n最差的前10笔交易:")
        print("-" * 120)
        for idx, trade in self.worst_trades.head(10).iterrows():
            print(f"{trade.get('pair', 'N/A'):15} | "
                  f"入场: {trade.get('open_date', 'N/A')} | "
                  f"出场: {trade.get('close_date', 'N/A')} | "
                  f"利润: {trade.get('profit_pct', 0):.2f}% | "
                  f"持仓时长: {trade.get('trade_duration', 0)} min")

        return self.worst_trades

    def analyze_common_patterns(self):
        """分析最差交易的共同特征"""
        print(f"\n{'='*80}")
        print("分析最差交易的共同特征")
        print(f"{'='*80}")

        patterns = {}

        # 1. 币对分布
        print("\n1. 币对分布:")
        pair_distribution = self.worst_trades['pair'].value_counts()
        print(pair_distribution.head(10))
        patterns['worst_pairs'] = pair_distribution.head(10).to_dict()

        # 2. 持仓时长分布
        if 'trade_duration' in self.worst_trades.columns:
            print("\n2. 持仓时长统计 (分钟):")
            duration_stats = self.worst_trades['trade_duration'].describe()
            print(duration_stats)
            patterns['duration_stats'] = duration_stats.to_dict()

            # 分析持仓时长分布
            short_trades = len(self.worst_trades[self.worst_trades['trade_duration'] < 60])
            medium_trades = len(self.worst_trades[(self.worst_trades['trade_duration'] >= 60) &
                                                   (self.worst_trades['trade_duration'] < 240)])
            long_trades = len(self.worst_trades[self.worst_trades['trade_duration'] >= 240])

            print(f"  短期持仓 (<1小时): {short_trades} 笔 ({short_trades/len(self.worst_trades)*100:.1f}%)")
            print(f"  中期持仓 (1-4小时): {medium_trades} 笔 ({medium_trades/len(self.worst_trades)*100:.1f}%)")
            print(f"  长期持仓 (>4小时): {long_trades} 笔 ({long_trades/len(self.worst_trades)*100:.1f}%)")

        # 3. 入场时间分析 (小时)
        if 'open_date' in self.worst_trades.columns:
            print("\n3. 入场时间分布 (UTC小时):")
            self.worst_trades['open_hour'] = pd.to_datetime(self.worst_trades['open_date']).dt.hour
            hour_distribution = self.worst_trades['open_hour'].value_counts().sort_index()
            print(hour_distribution)
            patterns['worst_hours'] = hour_distribution.to_dict()

        # 4. 出场原因分析
        if 'exit_reason' in self.worst_trades.columns:
            print("\n4. 出场原因分布:")
            exit_distribution = self.worst_trades['exit_reason'].value_counts()
            print(exit_distribution)
            patterns['exit_reasons'] = exit_distribution.to_dict()

        # 5. 比较最差交易与所有交易的统计差异
        print("\n5. 最差交易 vs 全部交易对比:")
        print(f"{'指标':<30} {'最差交易':<20} {'全部交易':<20} {'差异':<20}")
        print("-" * 90)

        metrics = ['profit_pct', 'trade_duration']
        for metric in metrics:
            if metric in self.trades_df.columns:
                worst_mean = self.worst_trades[metric].mean()
                all_mean = self.trades_df[metric].mean()
                diff = worst_mean - all_mean
                unit = '%' if metric == 'profit_pct' else 'min'
                print(f"{metric:<30} {worst_mean:>15.2f} {unit:<4} {all_mean:>15.2f} {unit:<4} {diff:>15.2f} {unit:<4}")

        return patterns

    def load_ohlcv_data(self, pair: str, timeframe: str, start_date: str, end_date: str):
        """
        加载指定币对和时间范围的K线数据

        Args:
            pair: 交易对 (例如: BTC/USDT:USDT)
            timeframe: 时间周期 (例如: 5m, 1h)
            start_date: 开始日期
            end_date: 结束日期
        """
        # 转换交易对格式为文件名格式
        pair_filename = pair.replace('/', '_').replace(':', '')

        # 尝试不同的文件扩展名
        for ext in ['.feather', '.json', '.parquet']:
            file_path = self.data_dir / f"{pair_filename}-{timeframe}{ext}"

            if file_path.exists():
                try:
                    if ext == '.feather':
                        df = pd.read_feather(file_path)
                    elif ext == '.json':
                        df = pd.read_json(file_path)
                    elif ext == '.parquet':
                        df = pd.read_parquet(file_path)

                    # 设置时间索引
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)

                    # 筛选时间范围
                    mask = (df.index >= start_date) & (df.index <= end_date)
                    return df.loc[mask]

                except Exception as e:
                    print(f"加载 {file_path} 失败: {e}")
                    continue

        print(f"⚠️  警告: 找不到 {pair} 的 {timeframe} K线数据")
        return None

    def analyze_trade_context(self, trade: pd.Series, context_candles: int = 100):
        """
        分析单笔交易的市场环境和技术指标

        Args:
            trade: 交易记录
            context_candles: 前后各取多少根K线进行分析
        """
        print(f"\n{'='*80}")
        print(f"详细分析交易: {trade.get('pair')} | 利润: {trade.get('profit_pct', 0):.2f}%")
        print(f"{'='*80}")

        pair = trade.get('pair')
        open_date = trade.get('open_date')
        close_date = trade.get('close_date')

        if not all([pair, open_date, close_date]):
            print("⚠️  交易信息不完整，跳过分析")
            return None

        # 扩展时间范围以获取上下文
        start_date = pd.to_datetime(open_date) - timedelta(hours=24)
        end_date = pd.to_datetime(close_date) + timedelta(hours=24)

        # 加载K线数据
        df = self.load_ohlcv_data(pair, '5m', start_date.strftime('%Y-%m-%d'),
                                   end_date.strftime('%Y-%m-%d'))

        if df is None or len(df) == 0:
            return None

        # 找到入场和出场的具体K线
        entry_candle = df.iloc[df.index.get_indexer([open_date], method='nearest')[0]]
        exit_candle = df.iloc[df.index.get_indexer([close_date], method='nearest')[0]]

        print(f"\n入场信息:")
        print(f"  时间: {open_date}")
        print(f"  价格: {trade.get('open_rate', 0):.4f}")
        print(f"  K线: O:{entry_candle['open']:.4f} H:{entry_candle['high']:.4f} "
              f"L:{entry_candle['low']:.4f} C:{entry_candle['close']:.4f}")

        print(f"\n出场信息:")
        print(f"  时间: {close_date}")
        print(f"  价格: {trade.get('close_rate', 0):.4f}")
        print(f"  K线: O:{exit_candle['open']:.4f} H:{exit_candle['high']:.4f} "
              f"L:{exit_candle['low']:.4f} C:{exit_candle['close']:.4f}")

        # 计算理想入场/出场点
        trade_period = df[open_date:close_date]
        if len(trade_period) > 0:
            ideal_entry = trade_period['low'].min()
            ideal_exit = trade_period['high'].max()
            actual_entry = trade.get('open_rate', 0)
            actual_exit = trade.get('close_rate', 0)

            print(f"\n理想化分析:")
            print(f"  实际入场价: {actual_entry:.4f}")
            print(f"  理想入场价 (最低点): {ideal_entry:.4f}")
            print(f"  入场滑点: {((actual_entry - ideal_entry) / ideal_entry * 100):.2f}%")

            print(f"\n  实际出场价: {actual_exit:.4f}")
            print(f"  理想出场价 (最高点): {ideal_exit:.4f}")
            print(f"  出场滑点: {((ideal_exit - actual_exit) / ideal_exit * 100):.2f}%")

            ideal_profit_pct = ((ideal_exit - ideal_entry) / ideal_entry) * 100
            actual_profit_pct = trade.get('profit_pct', 0)

            print(f"\n  实际利润: {actual_profit_pct:.2f}%")
            print(f"  理想利润: {ideal_profit_pct:.2f}%")
            print(f"  改进空间: {(ideal_profit_pct - actual_profit_pct):.2f}%")

        # 市场环境分析
        print(f"\n市场环境分析:")
        context_df = df[start_date:end_date]
        if len(context_df) > 20:
            # 波动率
            returns = context_df['close'].pct_change()
            volatility = returns.std() * np.sqrt(288)  # 年化波动率 (5分钟周期)
            print(f"  波动率: {volatility*100:.2f}%")

            # 趋势
            ma_short = context_df['close'].rolling(20).mean()
            ma_long = context_df['close'].rolling(50).mean()
            if len(ma_short) > 0 and len(ma_long) > 0:
                trend = "上升" if ma_short.iloc[-1] > ma_long.iloc[-1] else "下降"
                print(f"  趋势: {trend}")

            # 价格范围
            price_range = (context_df['high'].max() - context_df['low'].min()) / context_df['low'].min() * 100
            print(f"  价格波动范围: {price_range:.2f}%")

        return {
            'pair': pair,
            'entry_data': entry_candle.to_dict(),
            'exit_data': exit_candle.to_dict(),
            'ideal_entry': ideal_entry if len(trade_period) > 0 else None,
            'ideal_exit': ideal_exit if len(trade_period) > 0 else None,
            'market_context': context_df
        }

    def generate_optimization_suggestions(self, patterns: Dict):
        """根据分析结果生成策略优化建议"""
        print(f"\n{'='*80}")
        print("策略优化建议")
        print(f"{'='*80}")

        suggestions = []

        # 基于币对分布的建议
        if 'worst_pairs' in patterns:
            worst_pairs = list(patterns['worst_pairs'].keys())[:5]
            suggestions.append({
                'category': '币对过滤',
                'issue': f'某些币对表现特别差: {", ".join(worst_pairs)}',
                'suggestion': '考虑将表现最差的币对加入黑名单，或者为这些币对设置更严格的入场条件',
                'potential_impact': '可能减少 10-20% 的亏损交易',
                'implementation': f'在配置文件的 pair_blacklist 中添加: {worst_pairs}'
            })

        # 基于持仓时长的建议
        if 'duration_stats' in patterns:
            avg_duration = patterns['duration_stats'].get('mean', 0)
            if avg_duration < 60:
                suggestions.append({
                    'category': '止损策略',
                    'issue': f'最差交易的平均持仓时长仅 {avg_duration:.0f} 分钟，说明快速止损',
                    'suggestion': '考虑放宽止损阈值，或添加时间止损避免过早离场',
                    'potential_impact': '可能提高 5-10% 的胜率',
                    'implementation': '调整策略中的 stoploss 参数，或实现 custom_stoploss() 方法'
                })
            elif avg_duration > 240:
                suggestions.append({
                    'category': '止损策略',
                    'issue': f'最差交易的平均持仓时长 {avg_duration/60:.1f} 小时，持仓过长',
                    'suggestion': '考虑实现时间止损，避免长时间陷入亏损仓位',
                    'potential_impact': '可能减少 15-25% 的最大回撤',
                    'implementation': '在策略中实现时间止损逻辑，例如: if current_time - trade.open_date > 4h: exit'
                })

        # 基于入场时间的建议
        if 'worst_hours' in patterns:
            worst_hours = sorted(patterns['worst_hours'].items(), key=lambda x: x[1], reverse=True)[:3]
            worst_hour_list = [h[0] for h in worst_hours]
            suggestions.append({
                'category': '交易时段',
                'issue': f'这些时段的交易表现最差: {worst_hour_list} (UTC)',
                'suggestion': '考虑避免在这些时段开仓，或者为这些时段设置更保守的参数',
                'potential_impact': '可能提高 8-15% 的整体盈利',
                'implementation': '在 populate_entry_trend() 中添加时间过滤: dataframe.loc[dataframe[\'hour\'].isin([...]), \'enter_long\'] = 0'
            })

        # 基于出场原因的建议
        if 'exit_reasons' in patterns:
            exit_reasons = patterns['exit_reasons']
            if 'stop_loss' in exit_reasons or 'stoploss' in exit_reasons:
                sl_count = exit_reasons.get('stop_loss', 0) + exit_reasons.get('stoploss', 0)
                suggestions.append({
                    'category': '止损优化',
                    'issue': f'有 {sl_count} 笔交易因止损离场',
                    'suggestion': '考虑实现动态止损或trailing stop，在利润时保护收益',
                    'potential_impact': '可能将部分亏损转为盈利，改善 10-20% 的结果',
                    'implementation': '启用 trailing_stop 或实现自定义的 custom_stoploss() 方法'
                })

        # 打印建议
        for idx, sug in enumerate(suggestions, 1):
            print(f"\n建议 {idx}: {sug['category']}")
            print(f"  问题: {sug['issue']}")
            print(f"  建议: {sug['suggestion']}")
            print(f"  潜在影响: {sug['potential_impact']}")
            print(f"  实施方法: {sug['implementation']}")

        # 总体影响评估
        print(f"\n{'='*80}")
        print("整体影响评估")
        print(f"{'='*80}")
        print("""
应用这些微调可能带来的影响:

正面影响:
  ✓ 减少特定币对的亏损交易 (10-20%)
  ✓ 改善止损策略的有效性 (5-15%)
  ✓ 优化交易时段选择 (8-15%)
  ✓ 提高整体盈利能力 (15-30%)

潜在风险:
  ⚠ 过度优化可能导致过拟合历史数据
  ⚠ 减少交易频率可能降低整体收益
  ⚠ 某些调整可能在未来市场环境中失效

建议:
  1. 分阶段应用这些优化，每次只改变一个参数
  2. 在新的时间段上进行回测验证
  3. 使用前向测试 (walk-forward analysis) 验证稳定性
  4. 先在模拟环境测试 1-2 周再上实盘
        """)

        return suggestions

    def run_full_analysis(self, n_worst: int = 20, n_detailed: int = 5):
        """
        运行完整的分析流程

        Args:
            n_worst: 识别最差的N笔交易
            n_detailed: 对其中前N笔进行详细分析
        """
        print(f"\n{'#'*80}")
        print(f"# 回测结果 - 最差交易深度分析")
        print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")

        # 1. 加载回测结果
        if not self.load_backtest_results():
            return

        # 2. 识别最差交易
        self.identify_worst_trades(n_worst)

        # 3. 分析共同特征
        patterns = self.analyze_common_patterns()

        # 4. 详细分析前N笔最差交易
        print(f"\n{'='*80}")
        print(f"详细分析最差的 {n_detailed} 笔交易")
        print(f"{'='*80}")

        detailed_analyses = []
        for idx, (_, trade) in enumerate(self.worst_trades.head(n_detailed).iterrows(), 1):
            print(f"\n[{idx}/{n_detailed}] 分析第 {idx} 差的交易...")
            analysis = self.analyze_trade_context(trade)
            if analysis:
                detailed_analyses.append(analysis)

        # 5. 生成优化建议
        suggestions = self.generate_optimization_suggestions(patterns)

        # 6. 保存分析报告
        report_path = self.backtest_results_path.parent / f"worst_trades_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = {
            'analysis_time': datetime.now().isoformat(),
            'total_trades': len(self.trades_df),
            'worst_trades_count': n_worst,
            'patterns': patterns,
            'suggestions': suggestions,
            'detailed_analyses': [
                {k: v for k, v in analysis.items() if k != 'market_context'}
                for analysis in detailed_analyses
            ]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n{'='*80}")
        print(f"✓ 分析报告已保存到: {report_path}")
        print(f"{'='*80}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分析回测结果中最差的交易')
    parser.add_argument('--backtest-results', type=str, required=True,
                       help='回测结果JSON文件路径')
    parser.add_argument('--data-dir', type=str, default='user_data/data/binance',
                       help='K线数据目录路径')
    parser.add_argument('--n-worst', type=int, default=20,
                       help='分析最差的N笔交易 (默认: 20)')
    parser.add_argument('--n-detailed', type=int, default=5,
                       help='详细分析前N笔交易 (默认: 5)')

    args = parser.parse_args()

    # 检查文件是否存在
    if not Path(args.backtest_results).exists():
        print(f"❌ 错误: 找不到回测结果文件: {args.backtest_results}")
        print(f"\n提示: 请先运行回测:")
        print(f"  freqtrade backtesting --strategy NostalgiaForInfinityX7 --config config_backtest_futures.json --timerange 20250101-20251001")
        sys.exit(1)

    # 创建分析器并运行
    analyzer = WorstTradesAnalyzer(args.backtest_results, args.data_dir)
    analyzer.run_full_analysis(n_worst=args.n_worst, n_detailed=args.n_detailed)


if __name__ == '__main__':
    main()
