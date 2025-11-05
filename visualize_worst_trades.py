#!/usr/bin/env python3
"""
可视化最差交易的K线图和技术指标
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import sys

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class TradeVisualizer:
    def __init__(self, backtest_results_path: str, data_dir: str, output_dir: str = 'user_data/plot'):
        self.backtest_results_path = Path(backtest_results_path)
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_ohlcv_data(self, pair: str, timeframe: str, start_date: str, end_date: str):
        """加载K线数据"""
        pair_filename = pair.replace('/', '_').replace(':', '')

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

                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)

                    mask = (df.index >= start_date) & (df.index <= end_date)
                    return df.loc[mask]

                except Exception as e:
                    print(f"Failed to load {file_path}: {e}")
                    continue

        return None

    def calculate_indicators(self, df: pd.DataFrame):
        """计算常用技术指标"""
        # 移动平均线
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()

        # 布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']

        # 成交量MA
        df['Volume_MA'] = df['volume'].rolling(window=20).mean()

        return df

    def plot_trade_analysis(self, trade: dict, save_path: Path = None):
        """
        绘制单笔交易的完整分析图表

        包括:
        - K线图 + 布林带 + 移动平均线
        - 成交量
        - RSI指标
        - MACD指标
        - 入场/出场标记
        """
        pair = trade.get('pair')
        open_date = pd.to_datetime(trade.get('open_date'))
        close_date = pd.to_datetime(trade.get('close_date'))
        profit_pct = trade.get('profit_pct', 0)

        # 扩展时间范围获取上下文
        start_date = open_date - timedelta(hours=48)
        end_date = close_date + timedelta(hours=24)

        # 加载数据
        df = self.load_ohlcv_data(pair, '5m', start_date.strftime('%Y-%m-%d'),
                                   end_date.strftime('%Y-%m-%d'))

        if df is None or len(df) < 10:
            print(f"Insufficient data for {pair}")
            return None

        # 计算技术指标
        df = self.calculate_indicators(df)

        # 创建子图
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.05)

        # 1. K线图 + 技术指标
        ax1 = fig.add_subplot(gs[0])
        ax1.set_title(f'{pair} | Profit: {profit_pct:.2f}% | Entry: {open_date} | Exit: {close_date}',
                     fontsize=14, fontweight='bold')

        # 绘制K线
        for idx in range(len(df)):
            row = df.iloc[idx]
            date = df.index[idx]
            color = 'g' if row['close'] >= row['open'] else 'r'
            alpha = 0.8 if open_date <= date <= close_date else 0.3

            # 实体
            ax1.plot([date, date], [row['open'], row['close']],
                    color=color, linewidth=2, alpha=alpha)
            # 影线
            ax1.plot([date, date], [row['low'], row['high']],
                    color=color, linewidth=0.5, alpha=alpha)

        # 布林带
        ax1.plot(df.index, df['BB_upper'], 'b--', linewidth=1, alpha=0.5, label='BB Upper')
        ax1.plot(df.index, df['BB_middle'], 'b-', linewidth=1, alpha=0.5, label='BB Middle')
        ax1.plot(df.index, df['BB_lower'], 'b--', linewidth=1, alpha=0.5, label='BB Lower')

        # 移动平均线
        ax1.plot(df.index, df['MA20'], 'orange', linewidth=1.5, alpha=0.7, label='MA20')
        ax1.plot(df.index, df['MA50'], 'purple', linewidth=1.5, alpha=0.7, label='MA50')

        # 标记入场和出场
        entry_price = trade.get('open_rate', 0)
        exit_price = trade.get('close_rate', 0)

        ax1.scatter([open_date], [entry_price], color='blue', s=200, marker='^',
                   zorder=5, label='Entry', edgecolors='black', linewidths=2)
        ax1.scatter([close_date], [exit_price], color='red', s=200, marker='v',
                   zorder=5, label='Exit', edgecolors='black', linewidths=2)

        # 标记理想入场/出场
        trade_period = df[open_date:close_date]
        if len(trade_period) > 0:
            ideal_entry = trade_period['low'].min()
            ideal_exit = trade_period['high'].max()
            ideal_entry_date = trade_period['low'].idxmin()
            ideal_exit_date = trade_period['high'].idxmax()

            ax1.scatter([ideal_entry_date], [ideal_entry], color='green', s=150,
                       marker='*', zorder=5, label='Ideal Entry', alpha=0.7)
            ax1.scatter([ideal_exit_date], [ideal_exit], color='gold', s=150,
                       marker='*', zorder=5, label='Ideal Exit', alpha=0.7)

        ax1.axvspan(open_date, close_date, alpha=0.1, color='yellow')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylabel('Price', fontsize=10)

        # 2. 成交量
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        colors = ['g' if df['close'].iloc[i] >= df['open'].iloc[i] else 'r'
                 for i in range(len(df))]
        ax2.bar(df.index, df['volume'], color=colors, alpha=0.5, width=0.002)
        ax2.plot(df.index, df['Volume_MA'], 'blue', linewidth=1, label='Volume MA20')
        ax2.axvspan(open_date, close_date, alpha=0.1, color='yellow')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylabel('Volume', fontsize=10)

        # 3. RSI
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        ax3.plot(df.index, df['RSI'], 'purple', linewidth=1.5)
        ax3.axhline(y=70, color='r', linestyle='--', linewidth=1, alpha=0.5)
        ax3.axhline(y=30, color='g', linestyle='--', linewidth=1, alpha=0.5)
        ax3.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        ax3.axvspan(open_date, close_date, alpha=0.1, color='yellow')
        ax3.set_ylim(0, 100)
        ax3.legend(['RSI', 'Overbought', 'Oversold'], loc='upper left', fontsize=8)
        ax3.grid(True, alpha=0.3)
        ax3.set_ylabel('RSI', fontsize=10)

        # 4. MACD
        ax4 = fig.add_subplot(gs[3], sharex=ax1)
        ax4.plot(df.index, df['MACD'], 'blue', linewidth=1.5, label='MACD')
        ax4.plot(df.index, df['MACD_signal'], 'red', linewidth=1.5, label='Signal')
        colors = ['g' if val > 0 else 'r' for val in df['MACD_hist']]
        ax4.bar(df.index, df['MACD_hist'], color=colors, alpha=0.5, width=0.002, label='Histogram')
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.axvspan(open_date, close_date, alpha=0.1, color='yellow')
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3)
        ax4.set_ylabel('MACD', fontsize=10)
        ax4.set_xlabel('Time', fontsize=10)

        # 格式化x轴
        for ax in [ax1, ax2, ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)

        plt.tight_layout()

        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Chart saved: {save_path}")

        plt.close()

        return fig

    def visualize_worst_trades(self, backtest_results_path: str, n_worst: int = 10):
        """为最差的N笔交易生成可视化图表"""
        print(f"Loading backtest results from: {backtest_results_path}")

        with open(backtest_results_path, 'r') as f:
            results = json.load(f)

        # 提取交易记录
        if 'strategy' in results:
            strategy_name = list(results['strategy'].keys())[0]
            trades = results['strategy'][strategy_name]['trades']
        else:
            trades = results.get('trades', [])

        trades_df = pd.DataFrame(trades)

        if 'profit_ratio' in trades_df.columns:
            trades_df['profit_pct'] = trades_df['profit_ratio'] * 100
        elif 'profit_abs' in trades_df.columns and 'stake_amount' in trades_df.columns:
            trades_df['profit_pct'] = (trades_df['profit_abs'] / trades_df['stake_amount']) * 100

        # 获取最差的N笔交易
        worst_trades = trades_df.nsmallest(n_worst, 'profit_pct')

        print(f"\nGenerating charts for {len(worst_trades)} worst trades...")

        for idx, (_, trade) in enumerate(worst_trades.iterrows(), 1):
            pair_clean = trade['pair'].replace('/', '_').replace(':', '')
            filename = f"worst_trade_{idx:02d}_{pair_clean}_{trade.get('profit_pct', 0):.2f}pct.png"
            save_path = self.output_dir / filename

            print(f"[{idx}/{n_worst}] Plotting {trade['pair']} (Profit: {trade.get('profit_pct', 0):.2f}%)")

            try:
                self.plot_trade_analysis(trade.to_dict(), save_path)
            except Exception as e:
                print(f"  Error: {e}")
                continue

        print(f"\nAll charts saved to: {self.output_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Visualize worst trades from backtest results')
    parser.add_argument('--backtest-results', type=str, required=True,
                       help='Path to backtest results JSON file')
    parser.add_argument('--data-dir', type=str, default='user_data/data/binance',
                       help='Path to OHLCV data directory')
    parser.add_argument('--output-dir', type=str, default='user_data/plot',
                       help='Output directory for charts')
    parser.add_argument('--n-worst', type=int, default=10,
                       help='Number of worst trades to visualize (default: 10)')

    args = parser.parse_args()

    if not Path(args.backtest_results).exists():
        print(f"Error: Backtest results file not found: {args.backtest_results}")
        sys.exit(1)

    visualizer = TradeVisualizer(args.backtest_results, args.data_dir, args.output_dir)
    visualizer.visualize_worst_trades(args.backtest_results, n_worst=args.n_worst)


if __name__ == '__main__':
    main()
