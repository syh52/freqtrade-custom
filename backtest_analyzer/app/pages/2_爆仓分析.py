"""
爆仓分析页面

深度分析爆仓交易，识别风险因素并提供预防建议
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

from backtest_analyzer.analyzers.liquidation_analyzer import LiquidationAnalyzer

st.set_page_config(page_title="爆仓分析", page_icon="🔴", layout="wide")

st.title("🔴 爆仓深度分析")
st.markdown("识别爆仓原因，生成预防措施")
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

# 执行爆仓分析
with st.spinner("正在分析爆仓交易..."):
    analyzer = LiquidationAnalyzer(trades_df)
    analysis = analyzer.analyze()

summary = analysis['summary']

# 顶部摘要
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("爆仓数量", summary['liquidation_count'])
    st.metric("爆仓率", f"{summary['liquidation_rate']:.2f}%")

with col2:
    st.metric("总亏损", f"{summary['total_loss_abs']:.2f} USDT")
    st.metric("平均单笔", f"{summary['avg_loss_per_liquidation']:.2f} USDT")

with col3:
    st.metric("最大单笔亏损", f"{summary['max_single_loss']:.2f} USDT")
    if 'avg_duration_hours' in summary:
        st.metric("平均持仓", f"{summary['avg_duration_hours']:.1f} 小时")

with col4:
    if 'avg_leverage' in summary:
        st.metric("平均杠杆", f"{summary['avg_leverage']:.1f}x")
        st.metric("最大杠杆", f"{summary['max_leverage']:.0f}x")

st.markdown("---")

# 如果没有爆仓
if summary['liquidation_count'] == 0:
    st.success("🎉 恭喜！未发现爆仓交易，风险控制良好！")
    st.balloons()
    st.stop()

# 爆仓风险币种
st.header("💣 高风险币种")

risk_pairs = analysis['risk_pairs']
if not risk_pairs.empty:
    # 风险评分可视化
    fig = px.bar(
        risk_pairs.head(10),
        x='risk_score',
        y='pair',
        orientation='h',
        color='risk_level',
        color_discrete_map={'🟡 中等风险': '#FFA500', '🟠 高风险': '#FF4500', '🔴 极高风险': '#DC143C'},
        title='Top 10 高风险币种（按风险评分）',
        labels={'risk_score': '风险评分', 'pair': '币种'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # 详细表格
    st.subheader("📊 风险币种详情")
    display_df = risk_pairs[['pair', 'liq_count', 'liq_rate', 'total_loss', 'risk_score', 'risk_level']].copy()
    display_df.columns = ['币种', '爆仓次数', '爆仓率(%)', '总亏损(USDT)', '风险评分', '风险等级']
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("未发现特定的高风险币种")

st.markdown("---")

# 爆仓风险模式
st.header("🎯 高风险入场模式")

risk_modes = analysis['risk_modes']
if not risk_modes.empty:
    fig = go.Figure(data=[
        go.Bar(name='爆仓次数', x=risk_modes['entry_mode'], y=risk_modes['liq_count']),
    ])
    fig.update_layout(title='各入场模式爆仓统计', xaxis_title='入场模式', yaxis_title='爆仓次数', height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(risk_modes, use_container_width=True)
else:
    st.info("未发现特定的高风险入场模式")

st.markdown("---")

# DCA/加仓分析
if 'dca_analysis' in analysis and analysis['dca_analysis']:
    st.header("📈 DCA/加仓行为分析")

    dca = analysis['dca_analysis']

    col1, col2 = st.columns(2)

    with col1:
        st.metric("平均订单数", f"{dca.get('avg_order_count', 0):.1f}")
        st.metric("最多订单数", f"{dca.get('max_order_count', 0)}")

    with col2:
        st.metric("涉及DCA的爆仓", f"{dca.get('liq_with_dca', 0)} 笔")
        st.metric("DCA爆仓率", f"{dca.get('liq_with_dca_rate', 0):.1f}%")

    if dca.get('dca_increases_risk', False):
        st.error("⚠️ 数据显示：加仓次数与亏损呈负相关，说明加仓越多亏损越大！")
        st.warning(f"相关系数: {dca.get('order_loss_correlation', 0):.2f}")
    else:
        st.success("✓ DCA行为未显著增加爆仓风险")

    st.markdown("---")

# 时间分析
if 'timeline_analysis' in analysis and analysis['timeline_analysis']:
    st.header("⏰ 爆仓时间分布")

    timeline = analysis['timeline_analysis']

    col1, col2 = st.columns(2)

    with col1:
        if 'by_weekday' in timeline:
            st.subheader("按星期几")
            weekday_df = pd.DataFrame(list(timeline['by_weekday'].items()), columns=['星期', '次数'])
            fig = px.bar(weekday_df, x='星期', y='次数', title='爆仓星期分布')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'by_hour' in timeline:
            st.subheader("按小时")
            hour_df = pd.DataFrame(list(timeline['by_hour'].items()), columns=['小时', '次数'])
            fig = px.bar(hour_df, x='小时', y='次数', title='爆仓小时分布')
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

# 预防建议
st.header("💡 预防建议")

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

# 爆仓交易详情
st.header("📋 爆仓交易详情")

details = analyzer.get_liquidation_details()
if not details.empty:
    st.dataframe(details, use_container_width=True)

    # 下载按钮
    csv = details.to_csv(index=False)
    st.download_button(
        label="📥 下载爆仓交易CSV",
        data=csv,
        file_name="liquidation_trades.csv",
        mime="text/csv"
    )
else:
    st.info("无爆仓交易详情")

# 页脚
st.markdown("---")
st.caption("💡 提示：根据预防建议调整策略参数和黑名单配置，可显著降低爆仓风险")
