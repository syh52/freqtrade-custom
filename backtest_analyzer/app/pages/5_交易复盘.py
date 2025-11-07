"""
交易复盘页面 - 最核心功能

深度分析每笔交易，找出最优入场/出场点，分析被拒绝的信号
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest_analyzer.core.data_fetcher import DataFetcher
from backtest_analyzer.core.strategy_runner import StrategyRunner
from backtest_analyzer.analyzers.trade_replay import TradeReplayEngine
from backtest_analyzer.visualizers.kline_chart import create_trade_replay_chart

st.set_page_config(page_title="交易复盘", page_icon="🔬", layout="wide")

st.title("🔬 交易深度复盘")
st.markdown("分析每笔交易的入场/出场时机，找出改进空间")
st.markdown("---")

# 检查是否已加载数据
if 'data' not in st.session_state:
    st.warning("⚠️ 请先在主页加载回测数据")
    st.stop()

data = st.session_state['data']
trades_df = data['trades']

# 侧边栏 - 交易筛选
with st.sidebar:
    st.header("🔍 筛选条件")

    # 筛选类型
    filter_type = st.selectbox(
        "快速筛选",
        ["全部交易", "需要复盘的交易", "亏损交易", "微利交易(<1%)", "爆仓交易", "Grind模式"]
    )

    # 应用筛选
    filtered_df = trades_df.copy()
    if filter_type == "需要复盘的交易":
        filtered_df = filtered_df[filtered_df['needs_review']]
    elif filter_type == "亏损交易":
        filtered_df = filtered_df[filtered_df['profit_ratio'] < 0]
    elif filter_type == "微利交易(<1%)":
        filtered_df = filtered_df[(filtered_df['profit_ratio'] > 0) & (filtered_df['profit_ratio'] < 0.01)]
    elif filter_type == "爆仓交易":
        if 'is_liquidation' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['is_liquidation']]
    elif filter_type == "Grind模式":
        if 'is_grind_entry' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['is_grind_entry']]

    st.info(f"筛选结果：{len(filtered_df)} 笔交易")

    # 排序
    sort_by = st.selectbox(
        "排序方式",
        ["收益从低到高", "收益从高到低", "时间顺序", "持仓时长"]
    )

    if sort_by == "收益从低到高":
        filtered_df = filtered_df.sort_values('profit_ratio')
    elif sort_by == "收益从高到低":
        filtered_df = filtered_df.sort_values('profit_ratio', ascending=False)
    elif sort_by == "时间顺序":
        filtered_df = filtered_df.sort_values('open_date')
    elif sort_by == "持仓时长":
        if 'duration_minutes' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('duration_minutes', ascending=False)

# 交易列表
st.header("📋 交易列表")

if len(filtered_df) == 0:
    st.warning("没有符合条件的交易")
    st.stop()

# 显示交易表格
display_columns = ['pair', 'open_date', 'profit_ratio', 'profit_abs', 'duration_minutes', 'entry_mode', 'exit_reason']
available_columns = [col for col in display_columns if col in filtered_df.columns]

# 格式化显示
display_df = filtered_df[available_columns].copy()
if 'profit_ratio' in display_df.columns:
    display_df['收益%'] = (display_df['profit_ratio'] * 100).round(2)
    display_df = display_df.drop('profit_ratio', axis=1)
if 'duration_minutes' in display_df.columns:
    display_df['持仓(小时)'] = (display_df['duration_minutes'] / 60).round(1)
    display_df = display_df.drop('duration_minutes', axis=1)

# 选择要复盘的交易
selected_idx = st.selectbox(
    "选择要复盘的交易（按索引）",
    options=filtered_df.index.tolist(),
    format_func=lambda idx: f"#{idx} - {filtered_df.loc[idx, 'pair']} ({filtered_df.loc[idx, 'profit_ratio']*100:.2f}%)"
)

st.dataframe(display_df.head(10), use_container_width=True)

st.markdown("---")

# 复盘选中的交易
if selected_idx is not None:
    trade = filtered_df.loc[selected_idx]

    st.header(f"🔬 交易 #{selected_idx} 详细复盘")

    # 交易基本信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("币种", trade['pair'])
        st.metric("方向", "空头" if trade.get('is_short', False) else "多头")
    with col2:
        st.metric("开仓时间", str(trade['open_date']))
        st.metric("平仓时间", str(trade['close_date']))
    with col3:
        profit_pct = trade['profit_ratio'] * 100
        st.metric("收益率", f"{profit_pct:.2f}%", delta=f"{trade.get('profit_abs', 0):.2f} USDT")
    with col4:
        st.metric("入场模式", trade.get('entry_mode', 'Unknown'))
        st.metric("出场原因", trade.get('exit_reason', 'Unknown'))

    st.markdown("---")

    # 加载K线数据和分析
    with st.spinner("正在加载K线数据并分析..."):
        try:
            # 获取K线数据
            fetcher = DataFetcher(config=data.get('config'))
            candles_df = fetcher.get_data_for_trade(
                pair=trade['pair'],
                open_date=pd.to_datetime(trade['open_date']),
                close_date=pd.to_datetime(trade['close_date']),
                expand_candles=100
            )

            if candles_df.empty:
                st.error(f"⚠️ 未找到 {trade['pair']} 的K线数据")
                st.info(fetcher.download_missing_data_command([trade['pair']]))
                st.stop()

            # 重新计算技术指标
            runner = StrategyRunner(strategy_name=data['strategy_name'], config=data.get('config'))
            indicators_df = runner.populate_indicators(candles_df, {'pair': trade['pair']})

            # 执行复盘分析
            engine = TradeReplayEngine(trade, candles_df, indicators_df)
            analysis = engine.analyze()

            # 显示K线图
            st.subheader("📊 K线图分析")

            # 准备入场/出场点
            actual_entry = {'date': trade['open_date'], 'price': trade['open_rate']}
            actual_exit = {'date': trade['close_date'], 'price': trade['close_rate']}

            optimal_entry = None
            optimal_exit = None
            if 'optimal_points' in analysis and 'entry' in analysis['optimal_points']:
                optimal_entry = {
                    'date': analysis['optimal_points']['entry']['date'],
                    'price': analysis['optimal_points']['entry']['price']
                }
            if 'optimal_points' in analysis and 'exit' in analysis['optimal_points']:
                optimal_exit = {
                    'date': analysis['optimal_points']['exit']['date'],
                    'price': analysis['optimal_points']['exit']['price']
                }

            # 创建图表
            fig = create_trade_replay_chart(
                candles_df=indicators_df,
                pair=trade['pair'],
                actual_entry=actual_entry,
                actual_exit=actual_exit,
                optimal_entry=optimal_entry,
                optimal_exit=optimal_exit,
                indicators=['ema_12', 'ema_26', 'rsi_14'] if 'rsi_14' in indicators_df.columns else None
            )

            st.plotly_chart(fig, use_container_width=True)

            # 复盘报告
            st.markdown("---")
            st.subheader("📝 复盘报告")

            # 反思部分
            if 'reflection' in analysis:
                reflection = analysis['reflection']

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🔴 发现的问题")
                    if reflection['problems']:
                        for problem in reflection['problems']:
                            st.error(f"{problem['severity']} {problem['issue']}")
                    else:
                        st.success("✅ 未发现明显问题")

                    # 入场分析
                    if 'entry_analysis' in analysis and 'assessment' in analysis['entry_analysis']:
                        st.markdown("### 🎯 入场时机分析")
                        for assessment in analysis['entry_analysis']['assessment']:
                            if '❌' in assessment:
                                st.error(assessment)
                            elif '✓' in assessment:
                                st.success(assessment)
                            else:
                                st.info(assessment)

                with col2:
                    st.markdown("### 💡 改进建议")
                    if 'recommendations' in analysis:
                        for rec in analysis['recommendations']:
                            st.info(f"✓ {rec}")

                    # 反事实分析
                    if reflection['what_if']:
                        st.markdown("### 🤔 如果...")
                        for scenario in reflection['what_if']:
                            st.warning(f"**{scenario['scenario']}**\n\n{scenario['result']}")

            # 最优点分析
            if 'optimal_points' in analysis:
                st.markdown("---")
                st.subheader("🎯 最优入场/出场点分析")

                col1, col2 = st.columns(2)

                with col1:
                    if 'entry' in analysis['optimal_points']:
                        opt_entry = analysis['optimal_points']['entry']
                        st.markdown("#### 🟢 最优入场点")
                        st.info(f"""
                        **时间**: {opt_entry['date']}
                        **价格**: {opt_entry['price']:.6f}
                        **时间差**: {opt_entry['time_diff_minutes']:.0f} 分钟
                        **收益改善**: +{opt_entry['improvement_pct']:.2f}%
                        """)

                with col2:
                    if 'exit' in analysis['optimal_points']:
                        opt_exit = analysis['optimal_points']['exit']
                        st.markdown("#### 🔴 最优出场点")
                        st.info(f"""
                        **时间**: {opt_exit['date']}
                        **价格**: {opt_exit['price']:.6f}
                        **时间差**: {opt_exit['time_diff_minutes']:.0f} 分钟
                        **收益改善**: +{opt_exit['improvement_pct']:.2f}%
                        """)

                # 理论最优收益
                if 'theoretical_best' in analysis['optimal_points']:
                    theo = analysis['optimal_points']['theoretical_best']
                    st.success(f"""
                    **🏆 理论最优收益**: {theo['profit_pct']:.2f}%
                    （vs 实际收益 {profit_pct:.2f}%，差距 {theo['vs_actual_diff_pct']:.2f}%）
                    """)

            # 持仓期间分析
            if 'holding_analysis' in analysis:
                holding = analysis['holding_analysis']

                st.markdown("---")
                st.subheader("⏱️ 持仓期间分析")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if 'mfe' in holding:
                        st.metric("最大未实现盈利(MFE)", f"{holding['mfe']['ratio_pct']:.2f}%")
                        st.caption(f"时间: {holding['mfe']['date']}")

                with col2:
                    if 'mae' in holding:
                        st.metric("最大未实现亏损(MAE)", f"{holding['mae']['ratio_pct']:.2f}%")
                        st.caption(f"时间: {holding['mae']['date']}")

                with col3:
                    if 'profit_efficiency' in holding:
                        st.metric("盈利效率", f"{holding['profit_efficiency']['ratio']:.1%}")
                        st.caption(holding['profit_efficiency']['assessment'])

                # DCA订单
                if 'dca_orders' in holding and len(holding['dca_orders']) > 1:
                    st.markdown("#### 📊 DCA加仓订单")
                    dca_df = pd.DataFrame(holding['dca_orders'])
                    st.dataframe(dca_df, use_container_width=True)

        except Exception as e:
            st.error(f"❌ 分析失败: {e}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.caption("💡 提示：复盘分析结合了K线数据和技术指标，帮助您理解每笔交易的执行情况")
