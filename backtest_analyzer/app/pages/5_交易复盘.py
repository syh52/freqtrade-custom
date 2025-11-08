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

# 新增：决策分析器
from backtest_analyzer.analyzers.entry_decision_analyzer import (
    EntryDecisionAnalyzer,
    format_entry_diagnosis_report
)
from backtest_analyzer.analyzers.exit_decision_analyzer import (
    ExitDecisionAnalyzer,
    format_exit_diagnosis_report
)
from backtest_analyzer.analyzers.parameter_simulator import (
    ParameterSimulator,
    format_simulation_report
)
# 新增：决策回放器（用于加载决策日志）
from backtest_analyzer.analyzers.decision_replay import DecisionReplay

st.set_page_config(page_title="交易复盘", page_icon="🔬", layout="wide")

st.title("🔬 交易深度复盘")
st.markdown("分析每笔交易的入场/出场时机，找出改进空间")
st.markdown("---")

# 自动加载数据
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.auto_loader import ensure_data_loaded

# 确保数据已加载
if not ensure_data_loaded():
    st.warning("⚠️ 未找到回测数据")
    st.info("💡 提示：在左侧边栏选择 'main' 页面，选择回测文件并点击「加载数据」按钮")
    st.stop()

data = st.session_state['data']
trades_df = data['trades']

# 🆕 尝试加载决策日志
decision_replay = None
if 'backtest_file' in st.session_state and st.session_state['backtest_file']:
    backtest_file = Path(st.session_state['backtest_file'])
    decision_log_file = DecisionReplay.find_log_for_backtest(backtest_file)

    if decision_log_file:
        decision_replay = DecisionReplay(decision_log_file)
        if decision_replay.loaded:
            stats = decision_replay.get_statistics()
            st.success(f"✅ 已加载决策日志：{stats['entry_count']} 个入场信号，{stats['exit_count']} 个出场信号")
        else:
            decision_replay = None

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

            # ==================== 新增：决策诊断面板 ====================
            st.markdown("---")
            st.header("🧠 决策过程深度还原")
            st.caption("重现入场/出场时刻的所有技术指标和条件评估")

            # Tab标签页：入场诊断 / 出场诊断 / 参数模拟
            tab1, tab2, tab3 = st.tabs(["📍 入场决策诊断", "🚪 出场决策诊断", "🧪 参数模拟实验"])

            # Tab 1: 入场决策诊断
            with tab1:
                st.subheader("📍 入场时刻决策还原")

                # 🆕 优先尝试从决策日志加载
                entry_log_data = None
                if decision_replay and decision_replay.loaded:
                    entry_log_data = decision_replay.find_entry_decision(
                        pair=trade['pair'],
                        timestamp=pd.to_datetime(trade['open_date']),
                        tag=trade.get('enter_tag'),
                        tolerance_seconds=600  # 10分钟容差，覆盖信号生成到实际入场的延迟
                    )

                    if entry_log_data:
                        st.info("✨ 使用决策日志数据（100%准确）")
                    else:
                        st.warning("⚠️ 未找到对应的决策日志，使用条件推断（可能不准确）")
                else:
                    st.warning("⚠️ 此回测未启用决策日志，使用条件推断分析")
                    st.caption("💡 提示：使用 NostalgiaForInfinityX7WithLogging 策略重新回测可获得100%准确的决策数据")

                try:
                    # 如果有决策日志，优先显示日志数据
                    if entry_log_data:
                        # 显示触发信息
                        st.success(f"✅ 入场信号: {entry_log_data.get('side', '').upper()} - Tag {entry_log_data.get('tag')}")

                        # 显示所有技术指标值（从日志）
                        st.markdown("---")
                        st.subheader("📊 入场时刻技术指标值（决策日志）")
                        st.caption(f"时间: {entry_log_data['timestamp']}")

                        indicators = entry_log_data['data']['indicators']

                        # 按类别分组显示
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**RSI系列**")
                            rsi_indicators = {k: v for k, v in indicators.items() if 'rsi' in k.lower() and v is not None}
                            for name, value in list(rsi_indicators.items())[:10]:
                                st.metric(name, f"{value:.2f}" if isinstance(value, (int, float)) else str(value))

                        with col2:
                            st.markdown("**EMA/SMA系列**")
                            ma_indicators = {k: v for k, v in indicators.items() if ('ema' in k.lower() or 'sma' in k.lower()) and v is not None}
                            for name, value in list(ma_indicators.items())[:10]:
                                st.metric(name, f"{value:.2f}" if isinstance(value, (int, float)) else str(value))

                        with col3:
                            st.markdown("**其他指标**")
                            other_indicators = {k: v for k, v in indicators.items()
                                              if 'rsi' not in k.lower() and 'ema' not in k.lower() and 'sma' not in k.lower()
                                              and k not in ['date', 'open', 'high', 'low', 'close', 'volume']
                                              and v is not None}
                            for name, value in list(other_indicators.items())[:10]:
                                st.metric(name, f"{value:.2f}" if isinstance(value, (int, float)) else str(value))

                        # 提供完整指标下载
                        with st.expander("📥 下载完整指标数据（JSON）"):
                            st.json(indicators)

                    else:
                        # 回退到原有的条件推断分析
                        # 创建入场分析器
                        entry_analyzer = EntryDecisionAnalyzer(trade, candles_df, indicators_df)
                        entry_diagnosis = entry_analyzer.analyze()

                        # 显示触发的条件
                        if entry_diagnosis['triggered_tags']:
                            st.success(f"✅ 触发条件: {', '.join(f'Tag {tag}' for tag in entry_diagnosis['triggered_tags'])}")
                            st.caption(f"入场模式: {entry_diagnosis['entry_mode']}")
                        else:
                            st.warning("⚠️ 未识别到触发条件")

                        # 对每个触发的条件显示详细分析
                        for triggered in entry_diagnosis['triggered_analysis']:
                            with st.expander(f"🔍 {triggered['condition_name']} (Tag {triggered['tag']}) - 详细分析", expanded=True):
                                # 三层结构展示
                                layer_tabs = st.tabs(["🛡️ 第1层: 保护条件", "⏱️ 第2层: 多时间框架", "🎯 第3层: 入场逻辑"])

                                # 第1层：保护条件
                                with layer_tabs[0]:
                                    layer1 = triggered['layer1_protection']
                                    if layer1['all_satisfied']:
                                        st.success("✅ 所有保护条件满足")
                                    else:
                                        st.error("❌ 部分保护条件不满足")

                                    for cond in layer1['conditions']:
                                        icon = "✅" if cond['satisfied'] else "❌"
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.markdown(f"{icon} **{cond['description']}**")
                                        with col2:
                                            st.caption(cond.get('details', ''))

                                # 第2层：多时间框架过滤
                                with layer_tabs[1]:
                                    layer2 = triggered['layer2_mtf_filter']
                                    if layer2['all_satisfied']:
                                        st.success("✅ 所有多时间框架条件满足")
                                    else:
                                        st.error("❌ 部分多时间框架条件不满足")

                                    for i, cond in enumerate(layer2['conditions'][:5], 1):  # 只显示前5个
                                        icon = "✅" if cond['satisfied'] else "❌"
                                        st.markdown(f"**{icon} 条件组 {i} ({cond['logic'].upper()}逻辑)**")

                                        # 显示子条件
                                        sub_df_data = []
                                        for sub in cond['sub_conditions']:
                                            sub_df_data.append({
                                                '状态': "✅" if sub['satisfied'] else "❌",
                                                '指标': sub['indicator'],
                                                '条件': f"{sub['operator']} {sub['threshold']}",
                                                '实际值': f"{sub['actual_value']:.2f}"
                                            })

                                        if sub_df_data:
                                            st.dataframe(pd.DataFrame(sub_df_data), hide_index=True, use_container_width=True)

                                # 第3层：入场逻辑
                                with layer_tabs[2]:
                                    layer3 = triggered['layer3_entry_logic']
                                    if layer3['all_satisfied']:
                                        st.success("✅ 所有入场条件满足")
                                    else:
                                        st.error("❌ 部分入场条件不满足")

                                    # 以表格形式展示
                                    logic_data = []
                                    for cond in layer3['conditions']:
                                        logic_data.append({
                                            '状态': "✅" if cond['satisfied'] else "❌",
                                            '条件': cond['description'],
                                            '详情': cond.get('details', '')
                                        })

                                    if logic_data:
                                        st.dataframe(pd.DataFrame(logic_data), hide_index=True, use_container_width=True)

                        # 显示所有相关指标值
                        st.markdown("---")
                        st.subheader("📊 入场时刻技术指标值")

                        if entry_diagnosis['all_indicators']:
                            # 按类别分组显示
                            indicators = entry_diagnosis['all_indicators']

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.markdown("**RSI系列**")
                                rsi_indicators = {k: v for k, v in indicators.items() if 'RSI' in k}
                                for name, value in list(rsi_indicators.items())[:10]:
                                    st.metric(name, f"{value:.2f}")

                            with col2:
                                st.markdown("**AROON系列**")
                                aroon_indicators = {k: v for k, v in indicators.items() if 'AROON' in k}
                                for name, value in list(aroon_indicators.items())[:10]:
                                    st.metric(name, f"{value:.2f}")

                            with col3:
                                st.markdown("**其他指标**")
                                other_indicators = {k: v for k, v in indicators.items() if 'RSI' not in k and 'AROON' not in k}
                                for name, value in list(other_indicators.items())[:10]:
                                    st.metric(name, f"{value:.2f}")

                        # 显示接近触发的条件
                        if entry_diagnosis['near_miss_analysis']:
                            st.markdown("---")
                            st.subheader("🔍 接近触发但未满足的条件")
                            st.caption("这些条件几乎满足，可能是替代的入场机会")

                            for near_miss in entry_diagnosis['near_miss_analysis']:
                                with st.expander(f"⚠️ {near_miss['condition_name']} (Tag {near_miss['tag']}) - {near_miss['layers_satisfied']}/3层满足"):
                                    st.warning(f"满足层数: {near_miss['layers_satisfied']}/3")
                                    st.markdown("**未满足的条件:**")
                                    for detail in near_miss['unsatisfied_details'][:10]:
                                        st.text(f"  ❌ {detail}")

                except Exception as e:
                    st.error(f"❌ 入场决策分析失败: {e}")
                    with st.expander("查看错误详情"):
                        import traceback
                        st.code(traceback.format_exc())

            # Tab 2: 出场决策诊断
            with tab2:
                st.subheader("🚪 出场时刻决策还原")

                # 🆕 检查是否有出场决策日志
                exit_log_data = None
                if decision_replay and decision_replay.loaded:
                    exit_log_data = decision_replay.find_exit_decision(
                        pair=trade['pair'],
                        timestamp=pd.to_datetime(trade.get('close_date', trade.get('open_date'))),
                        tag=trade.get('enter_tag'),
                        tolerance_seconds=10
                    )

                    if exit_log_data:
                        st.info("✨ 找到决策日志数据")
                        # 显示基本信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("出场原因", exit_log_data['data'].get('exit_reason', 'N/A'))
                        with col2:
                            st.metric("出场利润", f"{exit_log_data['data'].get('current_profit', 0)*100:.2f}%")
                        with col3:
                            st.metric("出场时间", exit_log_data['timestamp'])

                        # 显示出场时刻指标
                        with st.expander("📊 出场时刻技术指标（决策日志）", expanded=True):
                            st.json(exit_log_data['data']['indicators'])
                    else:
                        st.warning("⚠️ 未找到对应的出场决策日志，使用条件推断分析")
                else:
                    st.warning("⚠️ 此回测未启用决策日志")

                try:
                    # 创建出场分析器（条件推断fallback）
                    exit_analyzer = ExitDecisionAnalyzer(trade, candles_df, indicators_df)
                    exit_diagnosis = exit_analyzer.analyze()

                    # 基本信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("出场函数", exit_diagnosis['exit_function'])
                    with col2:
                        st.metric("信号类型", exit_diagnosis['exit_signal_type'])
                    with col3:
                        st.metric("持仓时长", str(exit_diagnosis['holding_time']))

                    st.markdown("---")

                    # 决策路径追踪
                    st.subheader("🛤️ 决策路径追踪")
                    st.caption("按照策略代码的执行顺序，展示每个检查点")

                    for step in exit_diagnosis['decision_path']:
                        step_num = step.get('step', '?')
                        description = step.get('description', '')
                        details = step.get('details', '')
                        satisfied = step.get('satisfied')
                        triggered = step.get('triggered', False)

                        if triggered:
                            st.error(f"**🔴 步骤 {step_num}: {description}** 【触发出场】")
                        elif satisfied is True:
                            st.success(f"**✅ 步骤 {step_num}: {description}**")
                        elif satisfied is False:
                            st.info(f"**❌ 步骤 {step_num}: {description}**")
                        else:
                            st.info(f"**🔍 步骤 {step_num}: {description}**")

                        if details:
                            st.caption(f"   {details}")

                        if 'condition' in step:
                            st.caption(f"   条件: {step['condition']}")

                    # 所有出场条件检查
                    st.markdown("---")
                    st.subheader("📋 所有出场条件检查")

                    # 按类别分组
                    categories = {}
                    for check in exit_diagnosis['all_checks']:
                        cat = check['category']
                        if cat not in categories:
                            categories[cat] = []
                        categories[cat].append(check)

                    category_names = {
                        'profit_target': '💰 盈利目标',
                        'stoploss': '🛑 止损',
                        'technical_rsi': '📊 技术指标 (RSI)',
                        'technical_williams': '📊 技术指标 (Williams %R)',
                        'trend_reversal': '🔄 趋势反转',
                        'time_based': '⏰ 时间止损',
                        'profit_drawback': '📉 盈利回撤'
                    }

                    for cat, checks in categories.items():
                        cat_name = category_names.get(cat, cat)

                        with st.expander(f"{cat_name} ({len(checks)}个条件)"):
                            check_data = []
                            for check in checks:
                                if not check.get('checked', False):
                                    icon = '⏭️'
                                    status = '未检查'
                                elif check.get('triggered', False):
                                    icon = '🔴'
                                    status = '【已触发】'
                                elif check['satisfied']:
                                    icon = '✅'
                                    status = '满足'
                                else:
                                    icon = '❌'
                                    status = '不满足'

                                check_data.append({
                                    '状态': icon,
                                    '描述': check['description'],
                                    '检查': status,
                                    '详情': check.get('details', '')
                                })

                            if check_data:
                                st.dataframe(pd.DataFrame(check_data), hide_index=True, use_container_width=True)

                    # 出场时刻指标值
                    st.markdown("---")
                    st.subheader("📊 出场时刻技术指标")

                    if exit_diagnosis['all_indicators']:
                        indicators = exit_diagnosis['all_indicators']

                        # 显示为多列
                        cols = st.columns(4)
                        for i, (name, value) in enumerate(list(indicators.items())[:20]):
                            with cols[i % 4]:
                                st.metric(name, f"{value:.2f}")

                except Exception as e:
                    st.error(f"❌ 出场决策分析失败: {e}")
                    with st.expander("查看错误详情"):
                        import traceback
                        st.code(traceback.format_exc())

            # Tab 3: 参数模拟实验
            with tab3:
                st.subheader("🧪 参数模拟实验")
                st.caption("调整策略参数，查看对入场决策的影响")

                try:
                    # 创建模拟器
                    entry_analyzer_for_sim = EntryDecisionAnalyzer(trade, candles_df, indicators_df)
                    simulator = ParameterSimulator(entry_analyzer_for_sim)

                    # 选择要模拟的条件
                    if entry_analyzer_for_sim.triggered_tags:
                        selected_tag = st.selectbox(
                            "选择要模拟的条件",
                            options=entry_analyzer_for_sim.triggered_tags,
                            format_func=lambda t: f"Tag {t}"
                        )

                        st.markdown("---")
                        st.markdown("### 🎚️ 调整参数")

                        # 提供常见参数的调节滑块
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**RSI参数**")
                            rsi_14_threshold = st.slider(
                                "RSI_14 阈值",
                                min_value=20.0,
                                max_value=60.0,
                                value=36.0,
                                step=1.0,
                                help="调整RSI_14的入场阈值"
                            )

                            rsi_4_threshold = st.slider(
                                "RSI_4 阈值",
                                min_value=20.0,
                                max_value=60.0,
                                value=46.0,
                                step=1.0,
                                help="调整RSI_4的入场阈值"
                            )

                        with col2:
                            st.markdown("**SMA参数**")
                            sma_16_offset = st.slider(
                                "SMA_16 偏离率",
                                min_value=0.90,
                                max_value=1.05,
                                value=0.96,
                                step=0.01,
                                help="调整价格相对SMA_16的偏离率"
                            )

                        # 执行模拟按钮
                        if st.button("🔄 运行模拟", type="primary"):
                            with st.spinner("正在模拟..."):
                                # 构建参数变化字典
                                parameter_changes = {
                                    'RSI_14_threshold': rsi_14_threshold,
                                    'RSI_4_threshold': rsi_4_threshold,
                                    'SMA_16_offset': sma_16_offset
                                }

                                # 执行模拟
                                sim_result = simulator.simulate_entry_parameter_change(selected_tag, parameter_changes)

                                if sim_result.get('success'):
                                    st.markdown("---")
                                    st.markdown("### 📊 模拟结果")

                                    # 对比结果
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.markdown("**📍 原始参数**")
                                        if sim_result['original']['triggered']:
                                            st.success("✅ 会触发入场")
                                        else:
                                            st.error("❌ 不会触发入场")

                                    with col2:
                                        st.markdown("**🔮 模拟参数**")
                                        if sim_result['simulated']['would_trigger']:
                                            st.success("✅ 会触发入场")
                                        else:
                                            st.error("❌ 不会触发入场")

                                    # 变化描述
                                    comparison = sim_result['comparison']
                                    if comparison['change_type'] == 'no_change':
                                        st.info(comparison['description'])
                                    elif comparison['change_type'] in ['would_trigger', 'would_not_trigger']:
                                        st.warning(f"⚠️ {comparison['description']}")

                                    # 受影响的条件
                                    if comparison['changed_conditions']:
                                        st.markdown("**受影响的条件:**")
                                        for cond in comparison['changed_conditions']:
                                            icon = '✅→❌' if cond['original_satisfied'] and not cond['simulated_satisfied'] else '❌→✅'
                                            st.text(f"{icon} 第{cond['layer']}层: {cond['description']}")

                                    # 敏感度分析
                                    st.markdown("---")
                                    st.markdown("### 📈 参数敏感度分析")

                                    sensitivity = sim_result['sensitivity']
                                    st.info(sensitivity['description'])

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("敏感度等级", sensitivity['level'].upper())
                                    with col2:
                                        st.metric("敏感度评分", f"{sensitivity['score']:.2f}")

                                    if sensitivity['affected_conditions'] > 0:
                                        st.caption(f"影响了 {sensitivity['affected_conditions']} 个条件")

                                else:
                                    st.error(f"❌ 模拟失败: {sim_result.get('error', '未知错误')}")

                except Exception as e:
                    st.error(f"❌ 参数模拟功能出错: {e}")
                    with st.expander("查看错误详情"):
                        import traceback
                        st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"❌ 分析失败: {e}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.caption("💡 提示：复盘分析结合了K线数据和技术指标，帮助您理解每笔交易的执行情况")
