"""
数据清洗和增强模块

对回测交易数据进行清洗、特征工程和增强
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_and_enhance_trades(trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗并增强交易数据

        Args:
            trades_df: 原始交易DataFrame

        Returns:
            增强后的DataFrame
        """
        df = trades_df.copy()

        # 时间特征
        df = DataCleaner._add_time_features(df)

        # 解析标签
        df = DataCleaner._parse_tags(df)

        # 计算衍生指标
        df = DataCleaner._add_derived_metrics(df)

        # 标记特殊交易
        df = DataCleaner._mark_special_trades(df)

        print(f"✓ 数据增强完成，新增 {len(df.columns) - len(trades_df.columns)} 列")
        return df

    @staticmethod
    def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """添加时间相关特征"""
        if 'open_date' in df.columns:
            df['open_date'] = pd.to_datetime(df['open_date'])
            df['hour'] = df['open_date'].dt.hour
            df['day_of_week'] = df['open_date'].dt.dayofweek  # 0=周一, 6=周日
            df['day_of_month'] = df['open_date'].dt.day
            df['month'] = df['open_date'].dt.month
            df['year'] = df['open_date'].dt.year
            df['is_weekend'] = df['day_of_week'].isin([5, 6])

        if 'close_date' in df.columns:
            df['close_date'] = pd.to_datetime(df['close_date'])

        # 交易时长（分钟）
        if 'open_date' in df.columns and 'close_date' in df.columns:
            df['duration_minutes'] = (df['close_date'] - df['open_date']).dt.total_seconds() / 60

        return df

    @staticmethod
    def _parse_tags(df: pd.DataFrame) -> pd.DataFrame:
        """解析入场和出场标签"""
        # 解析入场标签（enter_tag）
        if 'enter_tag' in df.columns:
            df['enter_tag_str'] = df['enter_tag'].astype(str)

            # 提取数字标签（如 "141", "120"等）
            df['enter_tag_num'] = pd.to_numeric(df['enter_tag_str'], errors='coerce')

            # 分类入场模式
            df['entry_mode'] = df['enter_tag_num'].apply(DataCleaner._classify_entry_mode)

            # 是否是Grind模式
            df['is_grind_entry'] = df['enter_tag_num'] == 120

            # 是否是Top Coins模式
            df['is_top_coins'] = df['enter_tag_num'].isin([141, 142, 143, 144, 145])

        # 解析出场原因（exit_reason）
        if 'exit_reason' in df.columns:
            df['exit_reason_str'] = df['exit_reason'].astype(str)

            # 是否是爆仓
            df['is_liquidation'] = df['exit_reason_str'].str.contains('liquidation', case=False, na=False)

            # 是否是Grind出场
            df['is_grind_exit'] = df['exit_reason_str'].str.contains('grind', case=False, na=False)

            # 是否是技术条件出场
            df['is_tc_exit'] = df['exit_reason_str'].str.contains('_tc_', case=False, na=False)

            # 出场类型分类
            df['exit_type'] = df['exit_reason_str'].apply(DataCleaner._classify_exit_type)

        return df

    @staticmethod
    def _classify_entry_mode(tag: float) -> str:
        """
        分类入场模式

        NostalgiaForInfinityX7的入场模式：
        - Long Normal: 1-13
        - Long Pump: 21-26
        - Long Quick: 41-53
        - Long Rebuy: 61-63
        - Long High Profit: 81-82
        - Long Rapid: 101-110
        - Long Grind: 120
        - Long Top Coins: 141-145
        - Long Scalp: 161-163
        - Short Normal: 501-502
        - Short Pump: 521-526
        - Short Quick: 541-550
        - Short Rebuy: 561
        - Short High Profit: 581-582
        - Short Rapid: 601-610
        - Short Grind: 620
        - Short Top Coins: 641-642
        - Short Scalp: 661
        """
        if pd.isna(tag):
            return 'Unknown'

        tag = int(tag)

        # Long模式
        if 1 <= tag <= 13:
            return 'Long Normal'
        elif 21 <= tag <= 26:
            return 'Long Pump'
        elif 41 <= tag <= 53:
            return 'Long Quick'
        elif 61 <= tag <= 63:
            return 'Long Rebuy'
        elif 81 <= tag <= 82:
            return 'Long High Profit'
        elif 101 <= tag <= 110:
            return 'Long Rapid'
        elif tag == 120:
            return 'Long Grind'
        elif 141 <= tag <= 145:
            return 'Long Top Coins'
        elif 161 <= tag <= 163:
            return 'Long Scalp'

        # Short模式
        elif 501 <= tag <= 502:
            return 'Short Normal'
        elif 521 <= tag <= 526:
            return 'Short Pump'
        elif 541 <= tag <= 550:
            return 'Short Quick'
        elif tag == 561:
            return 'Short Rebuy'
        elif 581 <= tag <= 582:
            return 'Short High Profit'
        elif 601 <= tag <= 610:
            return 'Short Rapid'
        elif tag == 620:
            return 'Short Grind'
        elif 641 <= tag <= 642:
            return 'Short Top Coins'
        elif tag == 661:
            return 'Short Scalp'

        else:
            return 'Other'

    @staticmethod
    def _classify_exit_type(reason: str) -> str:
        """分类出场类型"""
        if pd.isna(reason):
            return 'Unknown'

        reason_lower = reason.lower()

        if 'liquidation' in reason_lower:
            return 'Liquidation'
        elif 'grind' in reason_lower:
            return 'Grind Exit'
        elif '_tc_' in reason_lower:
            return 'Technical Condition'
        elif 'stop' in reason_lower or 'sl' in reason_lower:
            return 'Stop Loss'
        elif 'roi' in reason_lower:
            return 'ROI'
        elif 'signal' in reason_lower:
            return 'Exit Signal'
        elif 'trailing' in reason_lower:
            return 'Trailing Stop'
        else:
            return 'Other'

    @staticmethod
    def _add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """添加衍生指标"""
        # R-multiple (风险回报比)
        if 'profit_ratio' in df.columns and 'initial_stop_loss_ratio' in df.columns:
            # initial_stop_loss_ratio 是负数
            df['risk'] = abs(df['initial_stop_loss_ratio'])
            df['reward'] = df['profit_ratio']
            df['r_multiple'] = df['reward'] / df['risk'].replace(0, 1)

        # 最大有利偏移 (MFE - Maximum Favorable Excursion)
        if 'max_rate' in df.columns and 'open_rate' in df.columns:
            df['mfe_ratio'] = (df['max_rate'] - df['open_rate']) / df['open_rate']

        # 最大不利偏移 (MAE - Maximum Adverse Excursion)
        if 'min_rate' in df.columns and 'open_rate' in df.columns:
            df['mae_ratio'] = (df['min_rate'] - df['open_rate']) / df['open_rate']

        # 盈利效率 (实际收益 / 最大可能收益)
        if 'profit_ratio' in df.columns and 'mfe_ratio' in df.columns:
            df['profit_efficiency'] = df['profit_ratio'] / df['mfe_ratio'].replace(0, 1)
            df['profit_efficiency'] = df['profit_efficiency'].clip(0, 1)  # 限制在0-1之间

        # 盈利分类
        if 'profit_ratio' in df.columns:
            df['profit_category'] = pd.cut(
                df['profit_ratio'],
                bins=[-np.inf, -0.05, -0.01, 0, 0.01, 0.03, 0.05, 0.10, np.inf],
                labels=['Large Loss', 'Medium Loss', 'Small Loss', 'Break Even',
                        'Small Win', 'Medium Win', 'Large Win', 'Huge Win']
            )

        # 持仓时长分类
        if 'duration_minutes' in df.columns:
            df['duration_category'] = pd.cut(
                df['duration_minutes'],
                bins=[0, 30, 120, 360, 1440, 4320, np.inf],
                labels=['Ultra Short (<30m)', 'Scalp (<2h)', 'Intraday (<6h)',
                        'Day (<24h)', 'Swing (<3d)', 'Position (>3d)']
            )

        return df

    @staticmethod
    def _mark_special_trades(df: pd.DataFrame) -> pd.DataFrame:
        """标记特殊交易"""
        # 多订单交易 (DCA/Grind)
        if 'orders' in df.columns:
            df['order_count'] = df['orders'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df['has_multiple_orders'] = df['order_count'] > 1

        # 高风险交易
        df['is_high_risk'] = False
        if 'is_liquidation' in df.columns:
            df['is_high_risk'] |= df['is_liquidation']
        if 'profit_ratio' in df.columns:
            df['is_high_risk'] |= (df['profit_ratio'] < -0.10)  # 亏损超过10%
        if 'duration_minutes' in df.columns:
            df['is_high_risk'] |= (df['duration_minutes'] > 10080)  # 持仓超过7天

        # 优质交易
        df['is_quality_trade'] = False
        if 'profit_ratio' in df.columns:
            df['is_quality_trade'] = (df['profit_ratio'] > 0.05)  # 收益超过5%
        if 'r_multiple' in df.columns:
            df.loc[df['r_multiple'] > 3, 'is_quality_trade'] = True  # R倍数>3

        # 差交易（需要深度分析）
        df['needs_review'] = False
        if 'is_liquidation' in df.columns:
            df['needs_review'] |= df['is_liquidation']
        if 'profit_ratio' in df.columns:
            df['needs_review'] |= (df['profit_ratio'] < 0)  # 所有亏损交易
        if 'profit_ratio' in df.columns:
            df.loc[(df['profit_ratio'] > 0) & (df['profit_ratio'] < 0.01), 'needs_review'] = True  # 微利交易

        return df

    @staticmethod
    def get_statistics_summary(df: pd.DataFrame) -> Dict:
        """
        获取统计摘要

        Args:
            df: 增强后的交易DataFrame

        Returns:
            统计信息字典
        """
        summary = {}

        # 基础统计
        summary['total_trades'] = len(df)
        summary['unique_pairs'] = df['pair'].nunique() if 'pair' in df.columns else 0

        # 盈亏统计
        if 'profit_ratio' in df.columns:
            summary['win_rate'] = (df['profit_ratio'] > 0).sum() / len(df) * 100
            summary['avg_profit'] = df['profit_ratio'].mean() * 100
            summary['median_profit'] = df['profit_ratio'].median() * 100

        # 特殊交易统计
        if 'is_liquidation' in df.columns:
            summary['liquidation_count'] = df['is_liquidation'].sum()
            summary['liquidation_rate'] = df['is_liquidation'].sum() / len(df) * 100

        if 'has_multiple_orders' in df.columns:
            summary['multi_order_count'] = df['has_multiple_orders'].sum()
            summary['multi_order_rate'] = df['has_multiple_orders'].sum() / len(df) * 100

        if 'is_grind_entry' in df.columns:
            summary['grind_count'] = df['is_grind_entry'].sum()
            summary['grind_rate'] = df['is_grind_entry'].sum() / len(df) * 100

        if 'is_high_risk' in df.columns:
            summary['high_risk_count'] = df['is_high_risk'].sum()
            summary['high_risk_rate'] = df['is_high_risk'].sum() / len(df) * 100

        if 'needs_review' in df.columns:
            summary['needs_review_count'] = df['needs_review'].sum()
            summary['needs_review_rate'] = df['needs_review'].sum() / len(df) * 100

        # 时间统计
        if 'duration_minutes' in df.columns:
            summary['avg_duration_hours'] = df['duration_minutes'].mean() / 60
            summary['median_duration_hours'] = df['duration_minutes'].median() / 60

        # 入场模式统计
        if 'entry_mode' in df.columns:
            mode_counts = df['entry_mode'].value_counts()
            summary['top_entry_modes'] = mode_counts.head(5).to_dict()

        return summary
