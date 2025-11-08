"""
币种分析页面

币种表现分析和毒瘤币检测，支持黑名单生成
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest_analyzer.analyzers.toxic_pair_detector import ToxicPairDetector

st.set_page_config(page_title="币种分析", page_icon="💰", layout="wide")

st.title("💰 币种表现分析")
st.markdown("识别优质币种和毒瘤币，生成黑名单配置")
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
stats = data['stats']

# 获取币种表现（从stats中）
strategy_name = list(stats['strategy'].keys())[0]
strategy_stats = stats['strategy'][strategy_name]

# 侧边栏 - 筛选
with st.sidebar:
    st.header("🔍 筛选选项")

    view_mode = st.radio(
        "查看模式",
        ["全部币种", "毒瘤币检测", "优质币种"]
    )

    if view_mode == "全部币种":
        sort_by = st.selectbox(
            "排序方式",
            ["总收益", "胜率", "交易数量", "平均收益"]
        )

# 执行毒瘤币检测
with st.spinner("正在分析币种..."):
    detector = ToxicPairDetector(trades_df)
    toxic_analysis = detector.analyze()

summary = toxic_analysis['summary']

# 顶部摘要
st.header("📊 币种统计摘要")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("总币种数", summary['total_pairs'])

with col2:
    st.metric("🔴 致命风险", summary['level1_count'])

with col3:
    st.metric("🟠 警告风险", summary['level2_count'])

with col4:
    st.metric("🟡 需监控", summary['level3_count'])

with col5:
    st.metric("✅ 安全币种", summary['safe_count'])

st.markdown("---")

# 根据视图模式显示内容
if view_mode == "毒瘤币检测":
    st.header("🔴 毒瘤币检测结果")

    # Level 1: 致命风险
    if toxic_analysis['level1_deadly']:
        st.subheader("🔴 Level 1: 致命风险（立即拉黑）")
        st.error(f"发现 {len(toxic_analysis['level1_deadly'])} 个致命风险币种")

        level1_data = []
        for item in toxic_analysis['level1_deadly']:
            stats = item['stats']
            level1_data.append({
                '币种': item['pair'],
                '风险原因': item['reason'],
                '交易数': stats['total_trades'],
                '胜率(%)': f"{stats['win_rate']:.1f}",
                '总盈亏(USDT)': f"{stats['total_profit']:.2f}",
                '爆仓次数': stats.get('liquidation_count', 0)
            })

        st.dataframe(pd.DataFrame(level1_data), use_container_width=True)
    else:
        st.success("✅ 未发现致命风险币种")

    st.markdown("---")

    # Level 2: 警告风险
    if toxic_analysis['level2_warning']:
        st.subheader("🟠 Level 2: 警告风险（建议限制Grind模式）")
        st.warning(f"发现 {len(toxic_analysis['level2_warning'])} 个警告风险币种")

        level2_data = []
        for item in toxic_analysis['level2_warning']:
            stats = item['stats']
            level2_data.append({
                '币种': item['pair'],
                '警告信号': ' | '.join(item['signals']),
                '交易数': stats['total_trades'],
                '胜率(%)': f"{stats['win_rate']:.1f}",
                '总盈亏(USDT)': f"{stats['total_profit']:.2f}"
            })

        st.dataframe(pd.DataFrame(level2_data), use_container_width=True)
    else:
        st.success("✅ 未发现警告风险币种")

    st.markdown("---")

    # 黑名单配置生成
    st.header("📋 黑名单配置")

    blacklist_config = toxic_analysis['blacklist_config']

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("完全拉黑列表")
        if blacklist_config['full_blacklist']:
            st.code('\n'.join(blacklist_config['full_blacklist']))
            st.metric("数量", len(blacklist_config['full_blacklist']))
        else:
            st.success("无需拉黑的币种")

    with col2:
        st.subheader("限制Grind列表")
        if blacklist_config['grind_restricted']:
            st.code('\n'.join(blacklist_config['grind_restricted']))
            st.metric("数量", len(blacklist_config['grind_restricted']))
        else:
            st.info("无需限制Grind的币种")

    # 生成Freqtrade配置格式
    if blacklist_config['full_blacklist']:
        st.subheader("💾 Freqtrade配置格式")
        config_json = json.dumps(blacklist_config['freqtrade_format'], indent=2, ensure_ascii=False)
        st.code(config_json, language='json')

        # 下载按钮
        st.download_button(
            label="📥 下载黑名单配置",
            data=config_json,
            file_name="blacklist-dynamic.json",
            mime="application/json"
        )

elif view_mode == "优质币种":
    st.header("⭐ 优质币种")

    if toxic_analysis['safe_pairs']:
        # 按总收益排序
        safe_data = []
        for item in toxic_analysis['safe_pairs']:
            stats = item['stats']
            safe_data.append({
                '币种': item['pair'],
                '交易数': stats['total_trades'],
                '胜率(%)': stats['win_rate'],
                '总收益(USDT)': stats['total_profit'],
                'Grind交易': stats.get('grind_trades', 0),
                'Grind收益(USDT)': stats.get('grind_profit', 0)
            })

        safe_df = pd.DataFrame(safe_data)
        safe_df = safe_df.sort_values('总收益(USDT)', ascending=False)

        # Top 10 可视化
        top10 = safe_df.head(10)
        fig = px.bar(
            top10,
            x='总收益(USDT)',
            y='币种',
            orientation='h',
            title='Top 10 优质币种（按总收益）',
            color='胜率(%)',
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # 完整表格
        st.dataframe(safe_df, use_container_width=True)
    else:
        st.warning("未找到符合条件的优质币种")

else:  # 全部币种
    st.header("📈 全部币种表现")

    if 'results_per_pair' in strategy_stats:
        pairs_df = pd.DataFrame(strategy_stats['results_per_pair'])

        # 排序
        if sort_by == "总收益":
            pairs_df = pairs_df.sort_values('profit_total_abs', ascending=False)
        elif sort_by == "胜率":
            pairs_df = pairs_df.sort_values('wins', ascending=False)
        elif sort_by == "交易数量":
            pairs_df = pairs_df.sort_values('trades', ascending=False)
        elif sort_by == "平均收益":
            pairs_df = pairs_df.sort_values('profit_mean', ascending=False)

        # 热力图
        st.subheader("🗺️ 币种表现热力图")

        # 准备热力图数据
        heatmap_data = pairs_df.head(20)[['key', 'trades', 'wins', 'profit_total_abs']].copy()
        heatmap_data.columns = ['币种', '交易数', '胜利数', '总收益']

        # 归一化
        for col in ['交易数', '胜利数', '总收益']:
            max_val = heatmap_data[col].max()
            if max_val > 0:
                heatmap_data[f'{col}_归一化'] = heatmap_data[col] / max_val

        fig = go.Figure(data=go.Heatmap(
            z=[heatmap_data['交易数_归一化'], heatmap_data['胜利数_归一化'], heatmap_data['总收益_归一化']],
            x=heatmap_data['币种'],
            y=['交易数', '胜利数', '总收益'],
            colorscale='RdYlGn',
            text=[[f"{v:.0f}" for v in heatmap_data['交易数']],
                  [f"{v:.0f}" for v in heatmap_data['胜利数']],
                  [f"{v:.2f}" for v in heatmap_data['总收益']]],
            texttemplate='%{text}',
            textfont={"size": 10}
        ))
        fig.update_layout(title='Top 20 币种表现（归一化）', height=300)
        st.plotly_chart(fig, use_container_width=True)

        # 详细表格
        st.subheader("📊 详细数据")
        display_cols = ['key', 'trades', 'wins', 'profit_total_abs', 'profit_mean', 'duration_avg']
        available_cols = [col for col in display_cols if col in pairs_df.columns]

        display_df = pairs_df[available_cols].copy()
        display_df.columns = ['币种', '交易数', '胜利数', '总收益(USDT)', '平均收益', '平均持仓']

        st.dataframe(display_df, use_container_width=True)

        # 下载CSV
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 下载完整数据CSV",
            data=csv,
            file_name="pairs_performance.csv",
            mime="text/csv"
        )
    else:
        st.error("未找到币种统计数据")

# 页脚
st.markdown("---")
st.caption("💡 提示：定期更新黑名单可以避免重复在高风险币种上亏损")
