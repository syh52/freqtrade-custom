"""
K线可视化组件

使用Plotly创建交互式K线图，支持技术指标叠加和交易标记
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional


class KLineChartBuilder:
    """K线图构建器"""

    def __init__(self, candles_df: pd.DataFrame, pair: str = "Unknown"):
        """
        初始化

        Args:
            candles_df: K线数据（必须包含OHLCV）
            pair: 交易对名称
        """
        self.df = candles_df.copy()
        self.pair = pair

        # 确保索引是datetime
        if not isinstance(self.df.index, pd.DatetimeIndex):
            if 'date' in self.df.columns:
                self.df.set_index('date', inplace=True)
            self.df.index = pd.to_datetime(self.df.index)

    def create_chart(
        self,
        indicators: Optional[List[str]] = None,
        entry_points: Optional[List[Dict]] = None,
        exit_points: Optional[List[Dict]] = None,
        height: int = 800
    ) -> go.Figure:
        """
        创建完整的K线图

        Args:
            indicators: 要显示的指标列表，如 ['ema_12', 'rsi']
            entry_points: 入场点列表 [{'date': datetime, 'price': float, 'type': 'actual'/'optimal'}]
            exit_points: 出场点列表
            height: 图表高度

        Returns:
            Plotly Figure对象
        """
        # 创建子图（主图 + 指标副图）
        num_subplots = 1 + (1 if self._has_subplot_indicators(indicators) else 0)
        row_heights = [0.7, 0.3] if num_subplots == 2 else [1.0]

        fig = make_subplots(
            rows=num_subplots,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=[f"{self.pair} K线图", "技术指标"] if num_subplots == 2 else [f"{self.pair} K线图"]
        )

        # 添加K线
        self._add_candlestick(fig, row=1)

        # 添加主图指标（EMA等）
        if indicators:
            self._add_main_chart_indicators(fig, indicators, row=1)

        # 添加副图指标（RSI, MACD等）
        if indicators and num_subplots == 2:
            self._add_subplot_indicators(fig, indicators, row=2)

        # 添加交易标记
        if entry_points:
            self._add_entry_markers(fig, entry_points, row=1)

        if exit_points:
            self._add_exit_markers(fig, exit_points, row=1)

        # 布局设置
        fig.update_layout(
            height=height,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # X轴设置
        fig.update_xaxes(title_text="时间", row=num_subplots, col=1)

        # Y轴设置
        fig.update_yaxes(title_text="价格", row=1, col=1)
        if num_subplots == 2:
            fig.update_yaxes(title_text="指标值", row=2, col=1)

        return fig

    def _add_candlestick(self, fig: go.Figure, row: int):
        """添加K线"""
        fig.add_trace(
            go.Candlestick(
                x=self.df.index,
                open=self.df['open'],
                high=self.df['high'],
                low=self.df['low'],
                close=self.df['close'],
                name='K线',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=row,
            col=1
        )

    def _add_main_chart_indicators(self, fig: go.Figure, indicators: List[str], row: int):
        """添加主图指标（移动平均线等）"""
        # EMA/SMA等叠加在K线图上
        main_indicators = ['ema', 'sma', 'bb_upper', 'bb_middle', 'bb_lower']

        for ind_name in indicators:
            if any(main_ind in ind_name.lower() for main_ind in main_indicators):
                if ind_name in self.df.columns:
                    color = self._get_indicator_color(ind_name)
                    fig.add_trace(
                        go.Scatter(
                            x=self.df.index,
                            y=self.df[ind_name],
                            mode='lines',
                            name=ind_name,
                            line=dict(color=color, width=1.5),
                            opacity=0.7
                        ),
                        row=row,
                        col=1
                    )

    def _add_subplot_indicators(self, fig: go.Figure, indicators: List[str], row: int):
        """添加副图指标（RSI, MACD等）"""
        subplot_indicators = ['rsi', 'cci', 'mfi', 'macd']

        for ind_name in indicators:
            if any(sub_ind in ind_name.lower() for sub_ind in subplot_indicators):
                if ind_name in self.df.columns:
                    color = self._get_indicator_color(ind_name)
                    fig.add_trace(
                        go.Scatter(
                            x=self.df.index,
                            y=self.df[ind_name],
                            mode='lines',
                            name=ind_name,
                            line=dict(color=color, width=2)
                        ),
                        row=row,
                        col=1
                    )

        # 添加RSI的超买超卖线
        if any('rsi' in ind.lower() for ind in indicators):
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)

    def _add_entry_markers(self, fig: go.Figure, entry_points: List[Dict], row: int):
        """添加入场标记"""
        for entry in entry_points:
            entry_type = entry.get('type', 'actual')
            date = pd.to_datetime(entry['date'])
            price = entry['price']

            if entry_type == 'actual':
                # 实际入场点：绿色向上箭头
                marker = dict(symbol='triangle-up', size=15, color='#00ff00')
                name = '实际入场'
            else:
                # 最优入场点：蓝色虚线箭头
                marker = dict(symbol='triangle-up-open', size=15, color='#00bfff')
                name = '最优入场'

            fig.add_trace(
                go.Scatter(
                    x=[date],
                    y=[price],
                    mode='markers',
                    name=name,
                    marker=marker,
                    hovertemplate=f"{name}<br>价格: %{{y}}<br>时间: %{{x}}<extra></extra>"
                ),
                row=row,
                col=1
            )

    def _add_exit_markers(self, fig: go.Figure, exit_points: List[Dict], row: int):
        """添加出场标记"""
        for exit in exit_points:
            exit_type = exit.get('type', 'actual')
            date = pd.to_datetime(exit['date'])
            price = exit['price']

            if exit_type == 'actual':
                # 实际出场点：红色向下箭头
                marker = dict(symbol='triangle-down', size=15, color='#ff4444')
                name = '实际出场'
            else:
                # 最优出场点：橙色虚线箭头
                marker = dict(symbol='triangle-down-open', size=15, color='#ffa500')
                name = '最优出场'

            fig.add_trace(
                go.Scatter(
                    x=[date],
                    y=[price],
                    mode='markers',
                    name=name,
                    marker=marker,
                    hovertemplate=f"{name}<br>价格: %{{y}}<br>时间: %{{x}}<extra></extra>"
                ),
                row=row,
                col=1
            )

    def _has_subplot_indicators(self, indicators: Optional[List[str]]) -> bool:
        """检查是否有需要在副图显示的指标"""
        if not indicators:
            return False

        subplot_indicators = ['rsi', 'cci', 'mfi', 'macd']
        return any(
            any(sub_ind in ind.lower() for sub_ind in subplot_indicators)
            for ind in indicators
            if ind in self.df.columns
        )

    def _get_indicator_color(self, indicator_name: str) -> str:
        """获取指标颜色"""
        color_map = {
            'ema_12': '#ff6b6b',
            'ema_26': '#4ecdc4',
            'ema_50': '#45b7d1',
            'ema_200': '#f7b731',
            'sma_50': '#5f27cd',
            'sma_200': '#00d2d3',
            'rsi': '#a29bfe',
            'cci': '#fd79a8',
            'mfi': '#fdcb6e',
            'macd': '#00b894',
            'bb_upper': '#ff7675',
            'bb_middle': '#74b9ff',
            'bb_lower': '#55efc4'
        }

        return color_map.get(indicator_name, '#95a5a6')


def create_trade_replay_chart(
    candles_df: pd.DataFrame,
    pair: str,
    actual_entry: Dict,
    actual_exit: Dict,
    optimal_entry: Optional[Dict] = None,
    optimal_exit: Optional[Dict] = None,
    indicators: Optional[List[str]] = None
) -> go.Figure:
    """
    便捷函数：创建交易复盘图表

    Args:
        candles_df: K线数据
        pair: 交易对
        actual_entry: 实际入场点 {'date': datetime, 'price': float}
        actual_exit: 实际出场点
        optimal_entry: 最优入场点（可选）
        optimal_exit: 最优出场点（可选）
        indicators: 要显示的指标列表

    Returns:
        Plotly Figure
    """
    builder = KLineChartBuilder(candles_df, pair)

    entry_points = [{'date': actual_entry['date'], 'price': actual_entry['price'], 'type': 'actual'}]
    if optimal_entry:
        entry_points.append({'date': optimal_entry['date'], 'price': optimal_entry['price'], 'type': 'optimal'})

    exit_points = [{'date': actual_exit['date'], 'price': actual_exit['price'], 'type': 'actual'}]
    if optimal_exit:
        exit_points.append({'date': optimal_exit['date'], 'price': optimal_exit['price'], 'type': 'optimal'})

    return builder.create_chart(
        indicators=indicators or ['ema_12', 'ema_26', 'rsi'],
        entry_points=entry_points,
        exit_points=exit_points
    )
