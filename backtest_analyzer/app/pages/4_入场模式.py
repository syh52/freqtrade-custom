"""
入场模式分析页面

分析17种入场模式的效果，提供优化建议
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest_analyzer.analyzers.entry_mode_analyzer import EntryModeAnalyzer

st.set_page_config(page_title="入场模式分析", page_icon="🎯", layout="wide")

st.title("🎯 入场模式分析")
st.markdown("NostalgiaForInfinityX7 的 17种入场模式效果对比")
st.markdown("---")

# 自动加载数据
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.auto_loader import ensure_data_loaded

if not ensure_data_loaded():
    st.warning("⚠️ 未找到回测数据")
    st.info("💡 提示：在左侧边栏选择 'main' 页面，选择回测文件并点击「加载数据」按钮")
    st.stop()

data = st.session_state['data']
trades_df = data['trades']

# 执行入场模式分析
with st.spinner("正在分析入场模式..."):
    analyzer = EntryModeAnalyzer(trades_df)
    analysis = analyzer.analyze()

# 模式表现总览
st.header("📊 模式表现总览")

mode_perf = analysis['mode_performance']

# 关键指标卡片
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_modes = len(mode_perf)
    active_modes = len(mode_perf[mode_perf['trades'] > 0])
    st.metric("活跃模式", f"{active_modes}/{total_modes}")

with col2:
    best_mode = mode_perf.iloc[0] if not mode_perf.empty else None
    if best_mode is not None:
        st.metric("最佳模式", best_mode['entry_mode'][:15])
        st.caption(f"+{best_mode['total_profit_abs']:.2f} USDT")

with col3:
    top_win_rate = mode_perf.nlargest(1, 'win_rate').iloc[0] if not mode_perf.empty else None
    if top_win_rate is not None:
        st.metric("最高胜率", f"{top_win_rate['win_rate']:.1f}%")
        st.caption(top_win_rate['entry_mode'][:15])

with col4:
    most_used = mode_perf.nlargest(1, 'trades').iloc[0] if not mode_perf.empty else None
    if most_used is not None:
        st.metric("最常用", most_used['entry_mode'][:15])
        st.caption(f"{most_used['trades']} 笔交易")

st.markdown("---")

# 可视化：模式对比
st.header("📈 模式对比分析")

# 选择对比指标
comparison_metric = st.selectbox(
    "选择对比指标",
    ["总收益", "胜率", "平均收益", "交易数量", "Sharpe比率"]
)

# 映射到DataFrame列名
metric_map = {
    "总收益": "total_profit_abs",
    "胜率": "win_rate",
    "平均收益": "avg_profit_pct",
    "交易数量": "trades",
    "Sharpe比率": "sharpe_like"
}

col_name = metric_map[comparison_metric]

# 创建条形图
fig = px.bar(
    mode_perf.sort_values(col_name, ascending=False),
    x='entry_mode',
    y=col_name,
    title=f'各模式{comparison_metric}对比',
    color=col_name,
    color_continuous_scale='RdYlGn' if col_name != 'trades' else 'Blues',
    labels={'entry_mode': '入场模式', col_name: comparison_metric}
)
fig.update_layout(height=500, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Long vs Short 对比
st.header("⚔️ Long vs Short 对比")

comparison = analysis['mode_comparison']

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🟢 Long模式")
    st.metric("交易数", comparison['long']['count'])
    st.metric("胜率", f"{comparison['long']['win_rate']:.2f}%")
    st.metric("总收益", f"{comparison['long']['total_profit_abs']:.2f} USDT")

with col2:
    st.subheader("🔴 Short模式")
    st.metric("交易数", comparison['short']['count'])
    st.metric("胜率", f"{comparison['short']['win_rate']:.2f}%")
    st.metric("总收益", f"{comparison['short']['total_profit_abs']:.2f} USDT")

with col3:
    st.subheader("🏆 胜者")
    winner = comparison['winner']
    if winner == 'Long':
        st.success("✅ Long模式表现更好")
    elif winner == 'Short':
        st.success("✅ Short模式表现更好")
    else:
        st.info("⚖️ 两者表现相当")

# 可视化对比
long_short_data = pd.DataFrame({
    '方向': ['Long', 'Short'],
    '交易数': [comparison['long']['count'], comparison['short']['count']],
    '总收益': [comparison['long']['total_profit_abs'], comparison['short']['total_profit_abs']],
    '胜率': [comparison['long']['win_rate'], comparison['short']['win_rate']]
})

fig = go.Figure()
fig.add_trace(go.Bar(name='交易数', x=long_short_data['方向'], y=long_short_data['交易数'], yaxis='y', offsetgroup=1))
fig.add_trace(go.Bar(name='总收益(USDT)', x=long_short_data['方向'], y=long_short_data['总收益'], yaxis='y2', offsetgroup=2))
fig.update_layout(
    title='Long vs Short 综合对比',
    yaxis=dict(title='交易数'),
    yaxis2=dict(title='总收益(USDT)', overlaying='y', side='right'),
    barmode='group',
    height=400
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 模式排名
st.header("🏅 模式排名")

rankings = analysis['mode_rankings']

col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 按总收益排名")
    top_profit = pd.DataFrame(rankings['by_profit'])
    if not top_profit.empty:
        for idx, row in top_profit.iterrows():
            st.metric(
                row['entry_mode'],
                f"+{row['total_profit_abs']:.2f} USDT",
                delta=f"{row['trades']} 笔交易"
            )

    st.markdown("")
    st.subheader("🎯 按胜率排名")
    top_winrate = pd.DataFrame(rankings['by_win_rate'])
    if not top_winrate.empty:
        for idx, row in top_winrate.iterrows():
            st.metric(
                row['entry_mode'],
                f"{row['win_rate']:.1f}%",
                delta=f"{row['trades']} 笔交易"
            )

with col2:
    st.subheader("📊 按使用频率排名")
    top_usage = pd.DataFrame(rankings['by_usage'])
    if not top_usage.empty:
        for idx, row in top_usage.iterrows():
            st.metric(
                row['entry_mode'],
                f"{row['trades']} 笔",
                delta=f"+{row['total_profit_abs']:.2f} USDT"
            )

    st.markdown("")
    st.subheader("⚡ 按Sharpe比率排名")
    top_sharpe = pd.DataFrame(rankings['by_sharpe'])
    if not top_sharpe.empty:
        for idx, row in top_sharpe.iterrows():
            st.metric(
                row['entry_mode'],
                f"{row['sharpe_like']:.2f}",
                delta=f"{row['trades']} 笔交易"
            )

st.markdown("---")

# 使用不足的优质模式
st.header("💎 使用不足的优质模式")

underutilized = analysis['underutilized_modes']

if underutilized:
    st.info(f"发现 {len(underutilized)} 个使用不足但表现优秀的模式")

    under_df = pd.DataFrame(underutilized)
    under_df.columns = ['模式', '交易数', '平均收益(%)', '胜率(%)']
    st.dataframe(under_df, use_container_width=True)

    st.warning("💡 建议：考虑放宽这些模式的入场条件，增加信号数量")
else:
    st.success("✅ 未发现明显使用不足的优质模式")

st.markdown("---")

# 问题模式
st.header("⚠️ 表现不佳的模式")

problematic = analysis['problematic_modes']

if problematic:
    st.error(f"发现 {len(problematic)} 个表现不佳的模式")

    prob_df = pd.DataFrame(problematic)
    prob_df.columns = ['模式', '交易数', '胜率(%)', '平均收益(%)', '总收益(USDT)']
    st.dataframe(prob_df, use_container_width=True)

    st.warning("💡 建议：检查策略代码，收紧这些模式的入场条件或临时禁用")
else:
    st.success("✅ 所有模式表现良好")

st.markdown("---")

# 优化建议
st.header("💡 优化建议")

recommendations = analysis['recommendations']

for rec in recommendations:
    priority = rec['priority']
    if '🔴' in priority:
        st.error(f"**{priority}** - {rec['type']}")
    elif '🟠' in priority:
        st.warning(f"**{priority}** - {rec['type']}")
    elif '🟡' in priority:
        st.info(f"**{priority}** - {rec['type']}")
    else:
        st.success(f"**{priority}** - {rec['type']}")

    st.markdown(f"**{rec['title']}**")
    st.markdown(f"{rec['description']}")
    st.markdown(f"👉 **行动**: {rec['action']}")
    st.markdown("")

st.markdown("---")

# 详细表格
st.header("📋 完整模式数据")

display_df = mode_perf.copy()
st.dataframe(display_df, use_container_width=True)

# 下载CSV
csv = display_df.to_csv(index=False)
st.download_button(
    label="📥 下载模式数据CSV",
    data=csv,
    file_name="entry_modes_performance.csv",
    mime="text/csv"
)

st.markdown("---")

# ========== 新增：Entry Tag 详细分析 ==========
st.header("🏷️ Entry Tag 详细分析")
st.markdown("**Entry Tag 直接对应策略代码中的入场条件，比 Mode 更精确**")

entry_tag_analysis = analysis.get('entry_tag_analysis', {})

if 'error' not in entry_tag_analysis:
    tag_perf = entry_tag_analysis.get('tag_performance', pd.DataFrame())

    if not tag_perf.empty:
        # 概览卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_tags = len(tag_perf)
            st.metric("总Tag数", total_tags)

        with col2:
            long_tags = len(tag_perf[tag_perf['tag_type'] == 'Long'])
            st.metric("Long Tags", long_tags)

        with col3:
            short_tags = len(tag_perf[tag_perf['tag_type'] == 'Short'])
            st.metric("Short Tags", short_tags)

        with col4:
            best_tag = entry_tag_analysis.get('top_tags', [{}])[0]
            if best_tag:
                st.metric("最佳Tag", best_tag.get('tag_number', 'N/A'))
                st.caption(f"+{best_tag.get('total_profit_abs', 0):.2f} USDT")

        st.markdown("---")

        # Top 10 最佳和最差 Tags
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏆 Top 10 最佳 Entry Tags")
            top_tags = entry_tag_analysis.get('top_tags', [])
            if top_tags:
                top_df = pd.DataFrame(top_tags)
                top_df.columns = ['Tag', 'Tag编号', '交易数', '胜率(%)', '总收益(USDT)']
                st.dataframe(top_df, use_container_width=True, hide_index=True)

                # 可视化
                fig = px.bar(
                    top_df,
                    x='Tag编号',
                    y='总收益(USDT)',
                    color='胜率(%)',
                    title='Top 10 Tags收益对比',
                    color_continuous_scale='Greens',
                    labels={'Tag编号': 'Entry Tag编号', '总收益(USDT)': '总收益 (USDT)'}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("⚠️ Top 10 最差 Entry Tags")
            worst_tags = entry_tag_analysis.get('worst_tags', [])
            if worst_tags:
                worst_df = pd.DataFrame(worst_tags)
                worst_df.columns = ['Tag', 'Tag编号', '交易数', '胜率(%)', '总收益(USDT)']
                st.dataframe(worst_df, use_container_width=True, hide_index=True)

                # 可视化
                fig = px.bar(
                    worst_df,
                    x='Tag编号',
                    y='总收益(USDT)',
                    color='胜率(%)',
                    title='表现最差Tags',
                    color_continuous_scale='Reds',
                    labels={'Tag编号': 'Entry Tag编号', '总收益(USDT)': '总收益 (USDT)'}
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 高频低效 vs 低频高效
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔴 高频但低效的Tags（需优化）")
            high_freq_low = entry_tag_analysis.get('high_frequency_low_performance', [])
            if high_freq_low:
                high_freq_df = pd.DataFrame(high_freq_low)
                high_freq_df.columns = ['Tag', 'Tag编号', '交易数', '胜率(%)', '平均收益(%)', '总收益(USDT)']
                st.dataframe(high_freq_df, use_container_width=True, hide_index=True)
                st.warning("💡 这些Tags使用频繁但表现不佳，应该收紧入场条件或禁用")
            else:
                st.success("✅ 未发现明显的高频低效Tags")

        with col2:
            st.subheader("💎 低频但高效的Tags（可扩大）")
            low_freq_high = entry_tag_analysis.get('low_frequency_high_performance', [])
            if low_freq_high:
                low_freq_df = pd.DataFrame(low_freq_high)
                low_freq_df.columns = ['Tag', 'Tag编号', '交易数', '胜率(%)', '平均收益(%)']
                st.dataframe(low_freq_df, use_container_width=True, hide_index=True)
                st.info("💡 这些Tags表现优秀但使用较少，可以考虑放宽条件增加信号")
            else:
                st.info("未发现明显的低频高效Tags")

        st.markdown("---")

        # 完整Tag表格
        st.subheader("📊 完整Entry Tag数据")
        st.dataframe(tag_perf, use_container_width=True)

        # 下载按钮
        tag_csv = tag_perf.to_csv(index=False)
        st.download_button(
            label="📥 下载Entry Tag数据CSV",
            data=tag_csv,
            file_name="entry_tags_performance.csv",
            mime="text/csv"
        )
else:
    st.warning("⚠️ 无法分析Entry Tags：数据中缺少enter_tag字段")

st.markdown("---")

# ========== 新增：Exit Tag/Reason 分析 ==========
st.header("🚪 Exit Reason 详细分析")
st.markdown("**出场原因包含tag编号，可以定位到策略代码中的出场逻辑**")

exit_tag_analysis = analysis.get('exit_tag_analysis', {})

if 'error' not in exit_tag_analysis:
    # 出场分类汇总
    st.subheader("📊 出场类型汇总")
    category_summary = exit_tag_analysis.get('category_summary', [])
    if category_summary:
        cat_df = pd.DataFrame(category_summary)
        cat_df.columns = ['出场类型', '交易数', '平均收益(%)', '总收益(USDT)']

        # 可视化
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='交易数',
            x=cat_df['出场类型'],
            y=cat_df['交易数'],
            yaxis='y',
            offsetgroup=1
        ))
        fig.add_trace(go.Bar(
            name='平均收益(%)',
            x=cat_df['出场类型'],
            y=cat_df['平均收益(%)'],
            yaxis='y2',
            offsetgroup=2
        ))
        fig.update_layout(
            title='各出场类型对比',
            yaxis=dict(title='交易数'),
            yaxis2=dict(title='平均收益(%)', overlaying='y', side='right'),
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 最常见的出场原因
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 最常见的Exit Reasons")
        most_common = exit_tag_analysis.get('most_common_exits', [])
        if most_common:
            common_df = pd.DataFrame(most_common)
            common_df.columns = ['Exit Reason', 'Exit Tag', '交易数', '胜率(%)', '平均收益(%)']
            st.dataframe(common_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("⚠️ 表现最差的Exit Reasons")
        worst_exits = exit_tag_analysis.get('worst_exits', [])
        if worst_exits:
            worst_df = pd.DataFrame(worst_exits)
            worst_df.columns = ['Exit Reason', 'Exit Tag', '交易数', '胜率(%)', '平均收益(%)', '总收益(USDT)']
            st.dataframe(worst_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 完整Exit Reason表格
    st.subheader("📋 完整Exit Reason数据")
    exit_perf = exit_tag_analysis.get('exit_performance', pd.DataFrame())
    if not exit_perf.empty:
        st.dataframe(exit_perf, use_container_width=True)

        # 下载按钮
        exit_csv = exit_perf.to_csv(index=False)
        st.download_button(
            label="📥 下载Exit Reason数据CSV",
            data=exit_csv,
            file_name="exit_reasons_performance.csv",
            mime="text/csv"
        )
else:
    st.warning("⚠️ 无法分析Exit Reasons：数据中缺少exit_reason字段")

# 页脚
st.markdown("---")
st.caption("💡 提示：通过Tag编号可以在策略代码中精确定位入场/出场条件，从而针对性优化")
