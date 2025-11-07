#!/usr/bin/env python3
"""
Cryptocurrency Reversal Point Analysis Tool

Identifies and visualizes price reversal points in historical cryptocurrency data
using multiple detection methods.

⚠️ FORWARD-LOOKING BIAS WARNING ⚠️
This tool uses future data to label historical reversal points.
Only use for training data creation and historical analysis!

Usage:
    python scripts/analyze_reversals.py --pairs BTC/USDT --method all
    python scripts/analyze_reversals.py --pairs BTC/USDT ETH/USDT --timerange 20241001-20241231
    python scripts/analyze_reversals.py --config user_data/reversal_config.json
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from pandas import DataFrame

# Freqtrade imports
from freqtrade.data.history import load_pair_history
from freqtrade.configuration import TimeRange
from freqtrade.enums import CandleType

# Reversal analysis imports
from reversal_analysis import (
    create_detector,
    ReversalVisualizer,
    ReversalStatistics,
)


class ReversalAnalyzer:
    """
    Main class for running reversal point analysis.

    Coordinates data loading, detection, visualization, and reporting.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize analyzer with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.stats_calculator = ReversalStatistics()

    def load_data(
        self,
        pair: str,
        timeframe: str,
        datadir: Path,
        timerange: Optional[TimeRange] = None,
        candle_type: CandleType = CandleType.FUTURES
    ) -> DataFrame:
        """
        Load historical OHLCV data for a trading pair.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '5m')
            datadir: Data directory path
            timerange: Optional time range filter
            candle_type: SPOT or FUTURES

        Returns:
            DataFrame with OHLCV data
        """
        print(f"  加载数据: {pair} ({timeframe})...")

        df = load_pair_history(
            pair=pair,
            timeframe=timeframe,
            datadir=datadir,
            timerange=timerange,
            data_format='feather',
            candle_type=candle_type
        )

        if df.empty:
            raise ValueError(f"未找到 {pair} 的数据。请先使用 'freqtrade download-data' 下载数据。")

        print(f"    ✓ 加载了 {len(df)} 条K线数据")
        print(f"    ✓ 时间范围: {df['date'].min()} 到 {df['date'].max()}")

        return df

    def run_detection(
        self,
        dataframe: DataFrame,
        method: str,
        params: Dict[str, Any]
    ) -> DataFrame:
        """
        Run reversal detection on the dataframe.

        Args:
            dataframe: OHLCV data
            method: Detection method ('fixed', 'adaptive', or 'extreme')
            params: Detector parameters

        Returns:
            DataFrame with reversal detection results
        """
        print(f"  运行 {method} 检测方法...")

        detector = create_detector(method, params)
        result_df = detector.detect(dataframe)

        reversals = result_df[result_df['is_reversal'] == True]
        print(f"    ✓ 发现 {len(reversals)} 个反转点")
        print(f"      - 顶部: {len(reversals[reversals['reversal_type'] == 'top'])}")
        print(f"      - 底部: {len(reversals[reversals['reversal_type'] == 'bottom'])}")

        return result_df

    def generate_visualization(
        self,
        dataframe: DataFrame,
        pair: str,
        detector_name: str,
        output_path: str
    ) -> str:
        """
        Generate interactive HTML visualization.

        Args:
            dataframe: Data with reversal detection results
            pair: Trading pair name
            detector_name: Name of the detector
            output_path: Output file path

        Returns:
            Path to the created HTML file
        """
        print(f"  生成可视化...")

        viz_config = self.config.get('visualization', {})
        visualizer = ReversalVisualizer(viz_config)

        html_path = visualizer.create_complete_html(
            dataframe=dataframe,
            pair=pair,
            detector_name=detector_name,
            output_path=output_path
        )

        print(f"    ✓ HTML文件已保存: {html_path}")

        return html_path

    def generate_report(
        self,
        dataframe: DataFrame,
        pair: str,
        detector_name: str,
        timerange: Optional[str] = None
    ) -> str:
        """
        Generate text summary report.

        Args:
            dataframe: Data with reversal detection results
            pair: Trading pair name
            detector_name: Name of the detector
            timerange: Time range string

        Returns:
            Report text
        """
        reversals = dataframe[dataframe['is_reversal'] == True]

        report = self.stats_calculator.generate_summary_report(
            reversals=reversals,
            pair=pair,
            detector_name=detector_name,
            timerange=timerange
        )

        return report

    def analyze_pair(
        self,
        pair: str,
        methods: List[str]
    ) -> Dict[str, DataFrame]:
        """
        Run complete analysis for a single trading pair.

        Args:
            pair: Trading pair to analyze
            methods: List of detection methods to use

        Returns:
            Dictionary mapping method names to result DataFrames
        """
        print(f"\n{'='*70}")
        print(f"分析交易对: {pair}")
        print(f"{'='*70}\n")

        # Load configuration
        timeframe = self.config.get('default_timeframe', '5m')
        datadir = Path(self.config.get('datadir', 'user_data/data/binance'))
        candle_type_str = self.config.get('candle_type', 'futures')
        candle_type = CandleType.FUTURES if candle_type_str == 'futures' else CandleType.SPOT

        # Parse timerange
        timerange_str = self.config.get('timerange')
        timerange = TimeRange.parse_timerange(timerange_str) if timerange_str else None

        # Load data
        df = self.load_data(pair, timeframe, datadir, timerange, candle_type)

        # Run detection for each method
        results = {}

        for method in methods:
            method_params = self.config.get('detectors', {}).get(method, {})
            method_params['timeframe_minutes'] = self._timeframe_to_minutes(timeframe)

            result_df = self.run_detection(df, method, method_params)
            results[method] = result_df

            # Generate outputs for this method
            output_dir = Path(self.config.get('output', {}).get('directory', 'user_data/reversal_results'))
            output_dir.mkdir(parents=True, exist_ok=True)

            # Clean pair name for filename
            pair_clean = pair.replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Generate HTML
            html_filename = f"{pair_clean}_{method}_{timestamp}.html"
            html_path = output_dir / html_filename
            self.generate_visualization(result_df, pair, method, str(html_path))

            # Generate text report
            report = self.generate_report(result_df, pair, method, timerange_str)
            print(report)

            # Export CSV
            reversals = result_df[result_df['is_reversal'] == True]
            if len(reversals) > 0:
                csv_filename = f"{pair_clean}_{method}_{timestamp}.csv"
                csv_path = output_dir / csv_filename
                self.stats_calculator.export_to_csv(reversals, str(csv_path))
                print(f"\n  ✓ CSV导出: {csv_path}")

        return results

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])

        if unit == 'm':
            return value
        elif unit == 'h':
            return value * 60
        elif unit == 'd':
            return value * 60 * 24
        elif unit == 'w':
            return value * 60 * 24 * 7
        else:
            raise ValueError(f"Unknown timeframe unit: {unit}")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.

    Args:
        config_path: Path to JSON config file (optional)

    Returns:
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        'default_pairs': ['BTC/USDT'],
        'default_timeframe': '5m',
        'default_timerange_days': 90,
        'candle_type': 'futures',
        'datadir': 'user_data/data/binance',
        'detectors': {
            'fixed': {
                'forward_window_hours': 6,
                'threshold_pct': 3.0,
            },
            'adaptive': {
                'forward_window_hours': 6,
                'volatility_window_days': 30,
                'threshold_multiplier': 2.0,
            },
            'extreme': {
                'swing_window': 5,
                'confirmation_threshold_pct': 3.0,
                'forward_window_hours': 6,
            }
        },
        'visualization': {
            'chart_height': 1000,
            'show_volume': True,
            'show_statistics': True,
            'color_scheme': {
                'up_candle': '#26a69a',
                'down_candle': '#ef5350',
                'top_reversal': '#d32f2f',
                'bottom_reversal': '#388e3c',
            }
        },
        'output': {
            'directory': 'user_data/reversal_results',
        }
    }

    # Load from file if provided
    if config_path and Path(config_path).exists():
        print(f"加载配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)

        # Merge user config with defaults (user config takes precedence)
        def deep_merge(default, user):
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        config = deep_merge(default_config, user_config)
    else:
        config = default_config

    return config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='加密货币反转点识别和可视化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法 - 分析BTC最近3个月数据（使用默认激进参数：6小时窗口，3%阈值）
  python scripts/analyze_reversals.py --pairs BTC/USDT

  # 分析多个交易对
  python scripts/analyze_reversals.py --pairs BTC/USDT ETH/USDT BNB/USDT

  # 指定时间范围和方法
  python scripts/analyze_reversals.py --pairs BTC/USDT --timerange 20240101-20241231 --methods fixed adaptive

  # 使用配置文件
  python scripts/analyze_reversals.py --config user_data/reversal_config.json

  # 分析现货数据
  python scripts/analyze_reversals.py --pairs BTC/USDT --candle-type spot

⚠️  注意: 此工具使用前瞻数据，仅用于历史分析和训练数据创建！
        """
    )

    parser.add_argument(
        '--pairs',
        nargs='+',
        help='交易对列表 (例如: BTC/USDT ETH/USDT)'
    )

    parser.add_argument(
        '--methods',
        nargs='+',
        choices=['fixed', 'adaptive', 'extreme', 'all'],
        default=['all'],
        help='识别方法: fixed=固定阈值, adaptive=自适应阈值, extreme=局部极值, all=所有方法'
    )

    parser.add_argument(
        '--timerange',
        type=str,
        help='时间范围 (格式: YYYYMMDD-YYYYMMDD, 例如: 20241001-20241231)'
    )

    parser.add_argument(
        '--timeframe',
        type=str,
        default='5m',
        help='K线周期 (默认: 5m)'
    )

    parser.add_argument(
        '--datadir',
        type=str,
        help='数据目录路径 (默认: user_data/data/binance)'
    )

    parser.add_argument(
        '--candle-type',
        choices=['spot', 'futures'],
        default='futures',
        help='市场类型 (默认: futures)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='输出目录 (默认: user_data/reversal_results)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径 (JSON格式)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         加密货币反转点识别和可视化系统 v1.0                      ║
║                                                                  ║
║  ⚠️  前瞻偏差警告：此工具使用未来数据标记历史反转点               ║
║     仅用于训练数据创建和历史分析，不可直接用于实盘交易！         ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Parse arguments
    args = parse_arguments()

    # Load configuration
    config = load_config(args.config)

    # Override config with command line arguments
    if args.pairs:
        config['default_pairs'] = args.pairs

    if args.timerange:
        config['timerange'] = args.timerange
    elif 'timerange' not in config:
        # Default: last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        config['timerange'] = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"

    if args.timeframe:
        config['default_timeframe'] = args.timeframe

    if args.datadir:
        config['datadir'] = args.datadir

    if args.candle_type:
        config['candle_type'] = args.candle_type

    if args.output:
        config['output']['directory'] = args.output

    # Determine methods to use
    methods = args.methods
    if 'all' in methods:
        methods = ['fixed', 'adaptive', 'extreme']

    # Create analyzer
    analyzer = ReversalAnalyzer(config)

    # Process each pair
    all_results = {}
    pairs = config['default_pairs']

    for pair in pairs:
        try:
            results = analyzer.analyze_pair(pair, methods)
            all_results[pair] = results
        except Exception as e:
            print(f"\n❌ 错误: 处理 {pair} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print(f"\n{'='*70}")
    print("分析完成！")
    print(f"{'='*70}")
    print(f"  处理的交易对: {len(all_results)}")
    print(f"  使用的方法: {', '.join(methods)}")
    print(f"  输出目录: {config['output']['directory']}")
    print(f"\n打开HTML文件即可查看交互式可视化结果。")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
