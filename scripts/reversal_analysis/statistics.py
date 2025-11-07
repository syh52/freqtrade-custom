"""
Reversal Statistics Module

Provides statistical analysis tools for reversal detection results:
- Basic statistics (counts, means, medians)
- Distribution analysis (magnitude, time intervals)
- Method comparison
- Performance metrics
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pandas import DataFrame
import numpy as np
from datetime import datetime, timedelta


class ReversalStatistics:
    """
    Statistical analysis tools for reversal detection results.

    Provides comprehensive metrics and comparisons for evaluating
    reversal detection quality and characteristics.
    """

    def __init__(self):
        """Initialize statistics calculator."""
        pass

    def calculate_basic_stats(self, reversals: DataFrame) -> Dict[str, Any]:
        """
        Calculate basic statistics for reversal points.

        Args:
            reversals: DataFrame containing only reversal points

        Returns:
            Dictionary with basic statistics
        """
        if len(reversals) == 0:
            return {
                'total_count': 0,
                'top_count': 0,
                'bottom_count': 0,
                'top_ratio': 0.0,
                'bottom_ratio': 0.0,
                'avg_magnitude': 0.0,
                'median_magnitude': 0.0,
                'max_magnitude': 0.0,
                'min_magnitude': 0.0,
                'std_magnitude': 0.0,
                'avg_confidence': 0.0,
            }

        top_reversals = reversals[reversals['reversal_type'] == 'top']
        bottom_reversals = reversals[reversals['reversal_type'] == 'bottom']

        stats = {
            'total_count': len(reversals),
            'top_count': len(top_reversals),
            'bottom_count': len(bottom_reversals),
            'top_ratio': len(top_reversals) / len(reversals) * 100,
            'bottom_ratio': len(bottom_reversals) / len(reversals) * 100,
            'avg_magnitude': reversals['reversal_magnitude'].mean(),
            'median_magnitude': reversals['reversal_magnitude'].median(),
            'max_magnitude': reversals['reversal_magnitude'].max(),
            'min_magnitude': reversals['reversal_magnitude'].min(),
            'std_magnitude': reversals['reversal_magnitude'].std(),
            'avg_confidence': reversals['confidence'].mean(),
        }

        return stats

    def calculate_time_distribution(self, reversals: DataFrame) -> Dict[str, Any]:
        """
        Analyze time distribution of reversals.

        Args:
            reversals: DataFrame containing only reversal points

        Returns:
            Dictionary with time-based statistics
        """
        if len(reversals) < 2:
            return {
                'avg_interval': None,
                'median_interval': None,
                'min_interval': None,
                'max_interval': None,
            }

        # Sort by date
        reversals_sorted = reversals.sort_values('date')

        # Calculate time differences
        time_diffs = reversals_sorted['date'].diff()
        time_diffs = time_diffs.dropna()

        stats = {
            'avg_interval': time_diffs.mean(),
            'median_interval': time_diffs.median(),
            'min_interval': time_diffs.min(),
            'max_interval': time_diffs.max(),
            'std_interval': time_diffs.std(),
        }

        # Calculate reversals per day/week/month
        date_range = reversals_sorted['date'].max() - reversals_sorted['date'].min()
        total_days = date_range.days

        if total_days > 0:
            stats['reversals_per_day'] = len(reversals) / total_days
            stats['reversals_per_week'] = len(reversals) / (total_days / 7)
            stats['reversals_per_month'] = len(reversals) / (total_days / 30)

        return stats

    def calculate_magnitude_distribution(self, reversals: DataFrame) -> Dict[str, Any]:
        """
        Analyze magnitude distribution of reversals.

        Args:
            reversals: DataFrame containing only reversal points

        Returns:
            Dictionary with magnitude distribution statistics
        """
        if len(reversals) == 0:
            return {}

        magnitudes = reversals['reversal_magnitude']

        # Define magnitude bins
        bins = [0, 3, 5, 7, 10, 15, 20, float('inf')]
        labels = ['< 3%', '3-5%', '5-7%', '7-10%', '10-15%', '15-20%', '> 20%']

        # Count reversals in each bin
        magnitude_counts = pd.cut(magnitudes, bins=bins, labels=labels).value_counts()

        distribution = {
            'bins': labels,
            'counts': magnitude_counts.to_dict(),
            'percentages': (magnitude_counts / len(reversals) * 100).to_dict(),
        }

        # Percentile analysis
        distribution['percentiles'] = {
            'p25': magnitudes.quantile(0.25),
            'p50': magnitudes.quantile(0.50),
            'p75': magnitudes.quantile(0.75),
            'p90': magnitudes.quantile(0.90),
            'p95': magnitudes.quantile(0.95),
        }

        return distribution

    def compare_methods(
        self,
        results: Dict[str, DataFrame],
        original_df: DataFrame
    ) -> Dict[str, Any]:
        """
        Compare results from different detection methods.

        Args:
            results: Dictionary mapping method names to result DataFrames
            original_df: Original OHLCV dataframe

        Returns:
            Dictionary with comparison metrics
        """
        comparison = {}

        for method_name, df in results.items():
            reversals = df[df['is_reversal'] == True]

            comparison[method_name] = {
                'count': len(reversals),
                'top_count': len(reversals[reversals['reversal_type'] == 'top']),
                'bottom_count': len(reversals[reversals['reversal_type'] == 'bottom']),
                'avg_magnitude': reversals['reversal_magnitude'].mean() if len(reversals) > 0 else 0,
                'coverage_pct': len(reversals) / len(original_df) * 100,
            }

        return comparison

    def calculate_overlap(
        self,
        results: Dict[str, DataFrame],
        time_tolerance_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Calculate overlap between different detection methods.

        Args:
            results: Dictionary mapping method names to result DataFrames
            time_tolerance_minutes: Minutes tolerance for considering reversals as "same"

        Returns:
            Dictionary with overlap statistics
        """
        if len(results) < 2:
            return {}

        method_names = list(results.keys())
        overlap_matrix = {}

        for i, method1 in enumerate(method_names):
            for method2 in method_names[i+1:]:
                # Get reversal points
                rev1 = results[method1][results[method1]['is_reversal'] == True]['date'].values
                rev2 = results[method2][results[method2]['is_reversal'] == True]['date'].values

                # Count overlapping reversals (within time tolerance)
                overlap_count = 0
                tolerance = pd.Timedelta(minutes=time_tolerance_minutes)

                for date1 in rev1:
                    for date2 in rev2:
                        if abs(pd.Timestamp(date1) - pd.Timestamp(date2)) <= tolerance:
                            overlap_count += 1
                            break

                key = f"{method1} vs {method2}"
                overlap_matrix[key] = {
                    'overlap_count': overlap_count,
                    'method1_total': len(rev1),
                    'method2_total': len(rev2),
                    'overlap_pct_method1': overlap_count / len(rev1) * 100 if len(rev1) > 0 else 0,
                    'overlap_pct_method2': overlap_count / len(rev2) * 100 if len(rev2) > 0 else 0,
                }

        return overlap_matrix

    def generate_summary_report(
        self,
        reversals: DataFrame,
        pair: str,
        detector_name: str,
        timerange: Optional[str] = None
    ) -> str:
        """
        Generate a text summary report of the analysis.

        Args:
            reversals: DataFrame containing only reversal points
            pair: Trading pair name
            detector_name: Name of the detector used
            timerange: Time range string (optional)

        Returns:
            Formatted text report
        """
        basic_stats = self.calculate_basic_stats(reversals)
        time_stats = self.calculate_time_distribution(reversals)
        mag_dist = self.calculate_magnitude_distribution(reversals)

        report = f"""
{'='*70}
反转点分析报告
{'='*70}

交易对: {pair}
识别方法: {detector_name}
时间范围: {timerange or '未指定'}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
基础统计
{'='*70}

总反转点数量: {basic_stats['total_count']}
  - 顶部反转: {basic_stats['top_count']} ({basic_stats['top_ratio']:.1f}%)
  - 底部反转: {basic_stats['bottom_count']} ({basic_stats['bottom_ratio']:.1f}%)

反转幅度统计:
  - 平均: {basic_stats['avg_magnitude']:.2f}%
  - 中位数: {basic_stats['median_magnitude']:.2f}%
  - 最大: {basic_stats['max_magnitude']:.2f}%
  - 最小: {basic_stats['min_magnitude']:.2f}%
  - 标准差: {basic_stats['std_magnitude']:.2f}%

平均置信度: {basic_stats['avg_confidence']:.2f}

{'='*70}
时间分布
{'='*70}
"""

        if time_stats.get('avg_interval'):
            report += f"""
反转间隔时间:
  - 平均: {time_stats['avg_interval']}
  - 中位数: {time_stats['median_interval']}
  - 最小: {time_stats['min_interval']}
  - 最大: {time_stats['max_interval']}

反转频率:
  - 每天: {time_stats.get('reversals_per_day', 0):.2f} 次
  - 每周: {time_stats.get('reversals_per_week', 0):.2f} 次
  - 每月: {time_stats.get('reversals_per_month', 0):.2f} 次
"""

        report += f"""
{'='*70}
幅度分布
{'='*70}
"""

        if mag_dist:
            for label in mag_dist['bins']:
                count = mag_dist['counts'].get(label, 0)
                pct = mag_dist['percentages'].get(label, 0)
                report += f"  {label:>10}: {count:4d} ({pct:5.1f}%)\n"

            report += f"""
百分位数:
  - 25%: {mag_dist['percentiles']['p25']:.2f}%
  - 50%: {mag_dist['percentiles']['p50']:.2f}%
  - 75%: {mag_dist['percentiles']['p75']:.2f}%
  - 90%: {mag_dist['percentiles']['p90']:.2f}%
  - 95%: {mag_dist['percentiles']['p95']:.2f}%
"""

        report += f"\n{'='*70}\n"

        return report

    def export_to_csv(self, reversals: DataFrame, output_path: str) -> str:
        """
        Export reversal points to CSV file.

        Args:
            reversals: DataFrame containing only reversal points
            output_path: Path to save CSV file

        Returns:
            Path to the created CSV file
        """
        # Select relevant columns
        export_cols = [
            'date', 'open', 'high', 'low', 'close', 'volume',
            'reversal_type', 'reversal_magnitude', 'forward_return',
            'confidence', 'detector_name'
        ]

        # Only export columns that exist
        export_cols = [col for col in export_cols if col in reversals.columns]

        reversals[export_cols].to_csv(output_path, index=False)

        return output_path
