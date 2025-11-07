"""
Reversal Visualization Module

Creates interactive Plotly visualizations for reversal analysis:
- Candlestick charts with volume
- Reversal point markers
- Interactive time range selectors
- Statistical panels
- Reversal point tables
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pandas import DataFrame
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime


class ReversalVisualizer:
    """
    Creates interactive visualizations for reversal analysis results.

    Features:
    - Professional candlestick charts
    - Volume subplots
    - Reversal markers with hover information
    - Time range selectors
    - Statistics panel
    - Reversal list table
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize visualizer with configuration.

        Args:
            config: Visualization configuration with keys:
                - chart_height: Total chart height in pixels
                - show_volume: Whether to show volume subplot
                - show_statistics: Whether to show statistics panel
                - color_scheme: Dictionary of colors for different elements
        """
        self.config = config or {}
        self.chart_height = self.config.get('chart_height', 1000)
        self.show_volume = self.config.get('show_volume', True)
        self.show_statistics = self.config.get('show_statistics', True)

        # Default color scheme
        default_colors = {
            'up_candle': '#26a69a',      # Green for up candles
            'down_candle': '#ef5350',    # Red for down candles
            'top_reversal': '#d32f2f',   # Dark red for top reversals
            'bottom_reversal': '#388e3c', # Dark green for bottom reversals
            'volume': '#64b5f6',         # Blue for volume
        }
        self.colors = self.config.get('color_scheme', default_colors)

    def create_chart(
        self,
        dataframe: DataFrame,
        pair: str,
        detector_name: str = "Unknown",
        title_suffix: str = ""
    ) -> go.Figure:
        """
        Create a complete interactive chart with all features.

        Args:
            dataframe: OHLCV data with reversal detection results
            pair: Trading pair name
            detector_name: Name of the detector used
            title_suffix: Additional text for the title

        Returns:
            Plotly Figure object
        """
        # Prepare data
        df = dataframe.copy()
        reversals = df[df['is_reversal'] == True].copy()

        # Create subplot layout
        if self.show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(f'{pair} - 反转点分析 ({detector_name}){title_suffix}', '成交量')
            )
        else:
            fig = go.Figure()

        # Add candlestick chart
        self._add_candlestick(fig, df, row=1)

        # Add volume subplot
        if self.show_volume:
            self._add_volume(fig, df, row=2)

        # Add reversal markers
        self._add_reversal_markers(fig, reversals, row=1)

        # Update layout
        self._update_layout(fig, pair)

        # Add range selector buttons
        self._add_range_selector(fig)

        return fig

    def _add_candlestick(self, fig: go.Figure, df: DataFrame, row: int = 1) -> None:
        """Add candlestick trace to the figure."""
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
                increasing_line_color=self.colors['up_candle'],
                decreasing_line_color=self.colors['down_candle'],
                showlegend=True
            ),
            row=row, col=1
        )

    def _add_volume(self, fig: go.Figure, df: DataFrame, row: int = 2) -> None:
        """Add volume bar chart to the figure."""
        # Color volume bars based on price movement
        colors = [
            self.colors['up_candle'] if close >= open_price else self.colors['down_candle']
            for close, open_price in zip(df['close'], df['open'])
        ]

        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='成交量',
                marker_color=colors,
                showlegend=True,
                opacity=0.7
            ),
            row=row, col=1
        )

    def _add_reversal_markers(self, fig: go.Figure, reversals: DataFrame, row: int = 1) -> None:
        """Add reversal point markers with hover information."""
        if len(reversals) == 0:
            return

        # Separate top and bottom reversals
        top_reversals = reversals[reversals['reversal_type'] == 'top']
        bottom_reversals = reversals[reversals['reversal_type'] == 'bottom']

        # Add top reversal markers (red down triangles)
        if len(top_reversals) > 0:
            hover_text_top = [
                f"<b>顶部反转</b><br>"
                f"时间: {date.strftime('%Y-%m-%d %H:%M')}<br>"
                f"价格: ${price:,.2f}<br>"
                f"后续跌幅: {mag:.2f}%<br>"
                f"置信度: {conf:.2f}"
                for date, price, mag, conf in zip(
                    top_reversals['date'],
                    top_reversals['high'],
                    top_reversals['reversal_magnitude'],
                    top_reversals['confidence']
                )
            ]

            fig.add_trace(
                go.Scatter(
                    x=top_reversals['date'],
                    y=top_reversals['high'],
                    mode='markers',
                    name='顶部反转',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color=self.colors['top_reversal'],
                        line=dict(width=1, color='white')
                    ),
                    text=hover_text_top,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

        # Add bottom reversal markers (green up triangles)
        if len(bottom_reversals) > 0:
            hover_text_bottom = [
                f"<b>底部反转</b><br>"
                f"时间: {date.strftime('%Y-%m-%d %H:%M')}<br>"
                f"价格: ${price:,.2f}<br>"
                f"后续涨幅: {mag:.2f}%<br>"
                f"置信度: {conf:.2f}"
                for date, price, mag, conf in zip(
                    bottom_reversals['date'],
                    bottom_reversals['low'],
                    bottom_reversals['reversal_magnitude'],
                    bottom_reversals['confidence']
                )
            ]

            fig.add_trace(
                go.Scatter(
                    x=bottom_reversals['date'],
                    y=bottom_reversals['low'],
                    mode='markers',
                    name='底部反转',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color=self.colors['bottom_reversal'],
                        line=dict(width=1, color='white')
                    ),
                    text=hover_text_bottom,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

    def _add_range_selector(self, fig: go.Figure) -> None:
        """Add time range selector buttons."""
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1周", step="day", stepmode="backward"),
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=3, label="3月", step="month", stepmode="backward"),
                    dict(count=6, label="6月", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all", label="全部")
                ]),
                bgcolor="lightgray",
                activecolor="gray",
                x=0,
                y=1.02,
            ),
            rangeslider=dict(visible=False),
            type="date"
        )

    def _update_layout(self, fig: go.Figure, pair: str) -> None:
        """Update figure layout with styling and configuration."""
        fig.update_layout(
            height=self.chart_height,
            template='plotly_dark',
            hovermode='x unified',
            xaxis_title="日期",
            yaxis_title="价格 (USDT)",
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="gray",
                borderwidth=1
            ),
            margin=dict(l=60, r=50, t=100, b=50)
        )

        # Update y-axis for volume (if present)
        if self.show_volume:
            fig.update_yaxes(title_text="成交量", row=2, col=1)

    def create_statistics_html(self, reversals: DataFrame, pair: str) -> str:
        """
        Generate HTML statistics panel.

        Args:
            reversals: DataFrame containing only reversal points
            pair: Trading pair name

        Returns:
            HTML string with statistics
        """
        if len(reversals) == 0:
            return "<p>未发现反转点</p>"

        # Calculate statistics
        total = len(reversals)
        top_count = len(reversals[reversals['reversal_type'] == 'top'])
        bottom_count = len(reversals[reversals['reversal_type'] == 'bottom'])

        avg_magnitude = reversals['reversal_magnitude'].mean()
        median_magnitude = reversals['reversal_magnitude'].median()
        max_magnitude = reversals['reversal_magnitude'].max()

        # Calculate time intervals between reversals
        reversals_sorted = reversals.sort_values('date')
        time_diffs = reversals_sorted['date'].diff()
        avg_interval = time_diffs.mean()
        median_interval = time_diffs.median()

        # Magnitude distribution
        mag_under_5 = len(reversals[reversals['reversal_magnitude'] < 5])
        mag_5_to_10 = len(reversals[(reversals['reversal_magnitude'] >= 5) &
                                     (reversals['reversal_magnitude'] < 10)])
        mag_over_10 = len(reversals[reversals['reversal_magnitude'] >= 10])

        # Generate HTML
        html = f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; color: #e0e0e0;">
            <h2 style="color: #4fc3f7;">反转点统计 - {pair}</h2>

            <h3>基础统计</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>总反转点数量:</b></td>
                    <td style="padding: 8px;">{total}</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>顶部反转:</b></td>
                    <td style="padding: 8px; color: #ef5350;">{top_count} ({top_count/total*100:.1f}%)</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>底部反转:</b></td>
                    <td style="padding: 8px; color: #26a69a;">{bottom_count} ({bottom_count/total*100:.1f}%)</td>
                </tr>
            </table>

            <h3 style="margin-top: 20px;">反转幅度</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>平均幅度:</b></td>
                    <td style="padding: 8px;">{avg_magnitude:.2f}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>中位数幅度:</b></td>
                    <td style="padding: 8px;">{median_magnitude:.2f}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>最大幅度:</b></td>
                    <td style="padding: 8px;">{max_magnitude:.2f}%</td>
                </tr>
            </table>

            <h3 style="margin-top: 20px;">幅度分布</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>&lt; 5%:</b></td>
                    <td style="padding: 8px;">{mag_under_5} ({mag_under_5/total*100:.1f}%)</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>5% - 10%:</b></td>
                    <td style="padding: 8px;">{mag_5_to_10} ({mag_5_to_10/total*100:.1f}%)</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>&gt; 10%:</b></td>
                    <td style="padding: 8px;">{mag_over_10} ({mag_over_10/total*100:.1f}%)</td>
                </tr>
            </table>

            <h3 style="margin-top: 20px;">时间间隔</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>平均间隔:</b></td>
                    <td style="padding: 8px;">{avg_interval}</td>
                </tr>
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;"><b>中位数间隔:</b></td>
                    <td style="padding: 8px;">{median_interval}</td>
                </tr>
            </table>
        </div>
        """

        return html

    def create_reversal_table_html(self, reversals: DataFrame) -> str:
        """
        Generate HTML table listing all reversal points.

        Args:
            reversals: DataFrame containing only reversal points

        Returns:
            HTML string with reversal table
        """
        if len(reversals) == 0:
            return "<p>未发现反转点</p>"

        # Sort by date descending
        reversals_sorted = reversals.sort_values('date', ascending=False)

        # Generate table rows
        rows = []
        for _, row in reversals_sorted.iterrows():
            type_color = '#ef5350' if row['reversal_type'] == 'top' else '#26a69a'
            type_text = '顶部' if row['reversal_type'] == 'top' else '底部'
            price = row['high'] if row['reversal_type'] == 'top' else row['low']

            rows.append(f"""
                <tr style="border-bottom: 1px solid #424242;">
                    <td style="padding: 8px;">{row['date'].strftime('%Y-%m-%d %H:%M')}</td>
                    <td style="padding: 8px;">${price:,.2f}</td>
                    <td style="padding: 8px; color: {type_color}; font-weight: bold;">{type_text}</td>
                    <td style="padding: 8px;">{row['reversal_magnitude']:.2f}%</td>
                    <td style="padding: 8px;">{row['confidence']:.2f}</td>
                    <td style="padding: 8px;">{row.get('detector_name', 'Unknown')}</td>
                </tr>
            """)

        table_html = f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; color: #e0e0e0; margin-top: 30px;">
            <h2 style="color: #4fc3f7;">反转点详细列表</h2>
            <div style="max-height: 600px; overflow-y: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead style="position: sticky; top: 0; background-color: #2e2e2e;">
                        <tr style="border-bottom: 2px solid #4fc3f7;">
                            <th style="padding: 10px; text-align: left;">时间</th>
                            <th style="padding: 10px; text-align: left;">价格</th>
                            <th style="padding: 10px; text-align: left;">类型</th>
                            <th style="padding: 10px; text-align: left;">幅度</th>
                            <th style="padding: 10px; text-align: left;">置信度</th>
                            <th style="padding: 10px; text-align: left;">识别方法</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        </div>
        """

        return table_html

    def create_complete_html(
        self,
        dataframe: DataFrame,
        pair: str,
        detector_name: str = "Unknown",
        output_path: str = "reversal_analysis.html"
    ) -> str:
        """
        Create a complete standalone HTML file with chart, statistics, and table.

        Args:
            dataframe: OHLCV data with reversal detection results
            pair: Trading pair name
            detector_name: Name of the detector used
            output_path: Path to save the HTML file

        Returns:
            Path to the created HTML file
        """
        # Create main chart
        fig = self.create_chart(dataframe, pair, detector_name)

        # Get reversals
        reversals = dataframe[dataframe['is_reversal'] == True].copy()

        # Generate statistics HTML
        stats_html = self.create_statistics_html(reversals, pair)

        # Generate table HTML
        table_html = self.create_reversal_table_html(reversals)

        # Create complete HTML
        fig_html = fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={'displayModeBar': True, 'displaylogo': False}
        )

        complete_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>反转点分析 - {pair}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1600px;
                    margin: 0 auto;
                }}
                .warning {{
                    background-color: #ff6f00;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="warning">
                    ⚠️ 前瞻偏差警告：此分析使用未来数据标记历史反转点，仅用于训练数据创建和历史分析，不可直接用于实盘交易！
                </div>

                <div id="chart">
                    {fig_html}
                </div>

                {stats_html}

                {table_html}
            </div>
        </body>
        </html>
        """

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(complete_html)

        return output_path
